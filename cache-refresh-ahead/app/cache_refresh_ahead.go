package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

type DataLoader = func(uid uuid.UUID) ([]byte, error)

// CacheByUUIDRefreshAheadMiddleware is a middleware that implements the refresh-ahead strategy.
// The cache key is based on the UUID of the resource.
type CacheByUUIDRefreshAheadMiddleware struct {
	client               *redis.Client
	cacheExpiration      time.Duration
	refreshAheadDuration time.Duration
	dataLoader           DataLoader
}

func NewCacheByUUIDRefreshAheadMiddleware(
	client *redis.Client,
	cacheExpiration time.Duration,
	refreshAheadFactor float64,
	dataLoader DataLoader,
) *CacheByUUIDRefreshAheadMiddleware {
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

	return &CacheByUUIDRefreshAheadMiddleware{
		client:               client,
		cacheExpiration:      cacheExpiration,
		refreshAheadDuration: refreshAheadDuration,
		dataLoader:           dataLoader,
	}
}

func (m *CacheByUUIDRefreshAheadMiddleware) Handler(c *fiber.Ctx) error {
	ctx := c.Context()
	// Allow non-GET HTTP methods to pass through this middleware.
	if c.Method() != fiber.MethodGet {
		return c.Next()
	}

	uid, err := m.parseUUID(c)
	if err != nil {
		return err
	}

	cacheKey := m.cacheKeyForUUID(uid)

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
		cacheData, getErr = commands[0].(*redis.StringCmd).Bytes()
		cacheTTL, ttlErr  = commands[1].(*redis.DurationCmd).Result()
	)

	// Check for errors that we cannot proceed with.
	if getErr != nil && !errors.Is(getErr, redis.Nil) {
		return getErr
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
	if errors.Is(getErr, redis.Nil) {
		log.Println("cache miss, reading from database")
		return m.refreshCacheAndSendResponse(c, uid)
	}

	// Cache hit.
	//
	// Determine whether to refresh the cache based on refresh-ahead duration.
	if cacheTTL < m.refreshAheadDuration {
		log.Println("cache hit with refreshing")
		m.sendResponseAndRefreshCacheAsync(uid)
		return m.sendResponse(c, cacheData)
	} else {
		log.Println("cache hit without refreshing")
		return m.sendResponse(c, cacheData)
	}
}

// refreshCacheAndSendResponse delegates to the next handler to read the data from the database.
// The next handler normally should send the response, and the response body bound to the context
// can be used to refresh the cache here.
func (m *CacheByUUIDRefreshAheadMiddleware) refreshCacheAndSendResponse(
	c *fiber.Ctx,
	uid uuid.UUID,
) error {
	if err := c.Next(); err != nil {
		return err
	}
	if err := m.client.Set(
		c.Context(), m.cacheKeyForUUID(uid),
		c.Response().Body(), m.cacheExpiration,
	).Err(); err != nil {
		return err
	}
	return nil
}

// sendResponseAndRefreshCacheAsync refreshes the cache asynchronously.
// It first tries to acquire a lock to refresh the cache. Since multiple Fiber requests can be running
// concurrently for the same path, only one of them would be able to acquire the lock and refresh the cache.
func (m *CacheByUUIDRefreshAheadMiddleware) sendResponseAndRefreshCacheAsync(
	uid uuid.UUID,
) {
	go func(uid uuid.UUID) {
		var (
			ctx      = context.Background()
			cacheKey = m.cacheKeyForUUID(uid)
			lockKey  = fmt.Sprintf("%s:refresh_lock", cacheKey)
		)
		// Try to acquire the refresh-lock.
		// Note that the value of the refresh-lock is not important, we just need to know whether it is locked.
		locked, err := m.client.SetNX(ctx, lockKey, "", time.Second*30).Result()
		if err != nil && !errors.Is(err, redis.Nil) {
			log.Printf("failed to acquire refresh-lock for %s: %v\n", uid, err)
			return
		}

		// Failed to acquire the refresh-lock, do nothing.
		if !locked {
			log.Printf("someone else is refreshing cache for %s\n", uid)
			return
		}

		// Successfully acquired the refresh-lock, refresh the cache.
		// Load the data from the database and set the cache.
		data, err := m.dataLoader(uid)
		if err != nil {
			log.Printf("failed to load data for %s: %v\n", uid, err)
			return
		}
		err = m.client.Set(ctx, cacheKey, data, m.cacheExpiration).Err()
		if err != nil {
			log.Printf("failed to set cache for %s: %v\n", uid, err)
			return
		}

		log.Printf("successfully refreshed cache for %s\n", uid)
	}(uid)
}

func (m *CacheByUUIDRefreshAheadMiddleware) sendResponse(c *fiber.Ctx, data []byte) error {
	c.Set("content-type", "application/json")
	return c.Send(data)
}

func (m *CacheByUUIDRefreshAheadMiddleware) parseUUID(c *fiber.Ctx) (uuid.UUID, error) {
	return uuid.Parse(c.Params("id"))
}

func (m *CacheByUUIDRefreshAheadMiddleware) cacheKeyForUUID(uid uuid.UUID) string {
	return fmt.Sprintf("cache_by_uuid:%s", uid.String())
}
