package main

import (
	"context"
	"log"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

// Use local Dragonfly instance address & credentials.
func createDragonflyClient() *redis.Client {
	client := redis.NewClient(&redis.Options{Addr: "localhost:6379"})

	err := client.Ping(context.Background()).Err()
	if err != nil {
		log.Fatal("failed to connect with dragonfly", err)
	}

	return client
}

func createServiceApp() *fiber.App {
	var (
		client             = createDragonflyClient()
		cacheExpiration    = time.Second * 100
		refreshAheadFactor = 0.5
	)

	// Create cache middleware using the refresh-ahead strategy connecting to the local Dragonfly instance.
	userCache := NewCacheByUUIDRefreshAheadMiddleware(
		client,
		cacheExpiration,
		refreshAheadFactor,
		UseRepo().ReadUserBytesByID,
	)
	blogCache := NewCacheByUUIDRefreshAheadMiddleware(
		client,
		cacheExpiration,
		refreshAheadFactor,
		UseRepo().ReadBlogBytesByID,
	)

	// Create Fiber application.
	app := fiber.New()
	app.Use(logger.New())

	// Register middleware & handlers.
	app.Get("/users/:id", userCache.Handler, getUserHandler)
	app.Get("/blogs/:id", blogCache.Handler, getBlogHandler)

	return app
}

func getUserHandler(c *fiber.Ctx) error {
	uid, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return err
	}
	user, err := UseRepo().ReadUserByID(uid)
	if err != nil {
		return err
	}
	return c.JSON(user)
}

func getBlogHandler(c *fiber.Ctx) error {
	uid, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return err
	}
	blog, err := UseRepo().ReadBlogByID(uid)
	if err != nil {
		return err
	}
	return c.JSON(blog)
}

func main() {
	app := createServiceApp()
	if err := app.Listen(":8080"); err != nil {
		log.Fatal("failed to start service app", err)
	}
}
