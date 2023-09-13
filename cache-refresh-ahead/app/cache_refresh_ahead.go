package main

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/log"
	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

type DataLoader = func(uid uuid.UUID) ([]byte, error)

// CacheRefreshAheadMiddleware is a middleware that implements the refresh-ahead strategy.
// The cache key is based on the request path (resource type and UUID).
type CacheRefreshAheadMiddleware struct {
	client               *redis.Client
	cacheExpiration      time.Duration
	refreshAheadDuration time.Duration
	dataLoader           DataLoader
}

func NewCacheRefreshAheadMiddleware(
	client *redis.Client,
	cacheExpiration time.Duration,
	refreshAheadFactor float64,
	dataLoader DataLoader,
) *CacheRefreshAheadMiddleware {
	// Calculate the refresh-ahead duration with sanity checks.
	// Note that a refresh-ahead factor of 25% means that the cache will be refreshed
	// 25% before the total cache expiration time, if the cache is accessed.
	//
	// Allow refresh-ahead factor to be between 10% and 90%.
	// Otherwise, use 25% as the default.
	refreshAheadDuration := time.Duration(0.25 * float64(cacheExpiration))
	if refreshAheadFactor >= 0.1 && refreshAheadFactor <= 0.9 {
		refreshAheadDuration = time.Duration(refreshAheadFactor * float64(cacheExpiration))
	}

	return &CacheRefreshAheadMiddleware{
		client:               client,
		cacheExpiration:      cacheExpiration,
		refreshAheadDuration: refreshAheadDuration,
		dataLoader:           dataLoader,
	}
}

func (m *CacheRefreshAheadMiddleware) Handler(c *fiber.Ctx) error {
	// Allow non-GET HTTP methods to pass through this middleware.
	if c.Method() != fiber.MethodGet {
		return c.Next()
	}

	var (
		ctx      = c.Context()
		cacheKey = c.Path()
	)

	uid, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return err
	}

	// Pipeline a GET command and a TTL command.
	commands, err := m.client.Pipelined(ctx, func(pipe redis.Pipeliner) error {
		pipe.Get(ctx, cacheKey)
		pipe.TTL(ctx, cacheKey)
		return nil
	})
	if err != nil && !errors.Is(err, redis.Nil) {
		return err
	}

	var (
		cacheData, dataErr = commands[0].(*redis.StringCmd).Bytes()
		cacheTTL, ttlErr   = commands[1].(*redis.DurationCmd).Result()
	)

	// Check for errors that we cannot proceed with.
	if dataErr != nil && !errors.Is(dataErr, redis.Nil) {
		return dataErr
	}
	if ttlErr != nil {
		return ttlErr
	}

	// Cache miss.
	//
	// This implies that the data is not in high demand anymore,
	// otherwise it would have been cached and continuously accessed/refreshed.
	//
	// In this case, just like Cache-Aside, we can passively load the data into the cache here.
	if errors.Is(dataErr, redis.Nil) {
		log.Info("cache miss - reading from database")
		return m.refreshCacheAndSendResponse(c, cacheKey)
	}

	// Cache hit.
	//
	// Determine whether to refresh the cache based on refresh-ahead duration.
	if cacheTTL < m.refreshAheadDuration {
		log.Info("cache hit - refreshing")
		m.sendResponseAndRefreshCacheAsync(uid, cacheKey)
		return m.sendResponse(c, cacheData)
	} else {
		log.Info("cache hit - no refreshing")
		return m.sendResponse(c, cacheData)
	}
}

// refreshCacheAndSendResponse delegates to the next handler to read the data from the database.
// The next handler normally should send the response, and the response body bound to the context
// can be used to refresh the cache here.
func (m *CacheRefreshAheadMiddleware) refreshCacheAndSendResponse(
	c *fiber.Ctx,
	cacheKey string,
) error {
	if err := c.Next(); err != nil {
		return err
	}
	if err := m.client.Set(
		c.Context(), cacheKey,
		c.Response().Body(), m.cacheExpiration,
	).Err(); err != nil {
		return err
	}
	return nil
}

// sendResponseAndRefreshCacheAsync refreshes the cache asynchronously.
// It first tries to acquire a lock to refresh the cache. Since multiple Fiber requests can be running
// concurrently for the same path, only one of them would be able to acquire the lock and refresh the cache.
func (m *CacheRefreshAheadMiddleware) sendResponseAndRefreshCacheAsync(
	uid uuid.UUID,
	cacheKey string,
) {
	go func(uid uuid.UUID, cacheKey string) {
		var (
			ctx     = context.Background()
			lockKey = fmt.Sprintf("%s:refresh_lock", cacheKey)
		)
		// Try to acquire the refresh-lock.
		// That the value of the refresh-lock is not important, we just need to know whether it is locked.
		// The refresh-lock will be released after the cache is refreshed.
		// However, a 10-second timeout is set to prevent the refresh-lock from being locked forever.
		locked, err := m.client.SetNX(ctx, lockKey, "", time.Second*10).Result()
		if err != nil && !errors.Is(err, redis.Nil) {
			log.Errorf("failed to acquire refresh-lock for %s: %v\n", uid, err)
			return
		}
		defer func() {
			_ = m.client.Del(ctx, lockKey).Err()
		}()

		// Failed to acquire the refresh-lock, do nothing.
		if !locked {
			log.Infof("someone else is refreshing cache for %s\n", uid)
			return
		}

		// Successfully acquired the refresh-lock, refresh the cache.
		// Load the data from the database and set the cache.
		data, err := m.dataLoader(uid)
		if err != nil {
			log.Errorf("failed to load data for %s: %v\n", uid, err)
			return
		}
		err = m.client.Set(ctx, cacheKey, data, m.cacheExpiration).Err()
		if err != nil {
			log.Errorf("failed to set cache for %s: %v\n", uid, err)
			return
		}

		log.Infof("successfully refreshed cache for %s\n", uid)
	}(uid, cacheKey)
}

func (m *CacheRefreshAheadMiddleware) sendResponse(c *fiber.Ctx, data []byte) error {
	c.Set("content-type", "application/json")
	return c.Send(data)
}
