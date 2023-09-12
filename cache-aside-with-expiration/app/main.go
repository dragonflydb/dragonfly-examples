package main

import (
	"context"
	"log"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cache"
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
	client := createDragonflyClient()

	// Create cache middleware connecting to the local Dragonfly instance.
	cacheMiddleware := cache.New(cache.Config{
		Storage:              &CacheStorage{client: client},
		Expiration:           time.Second * 30,
		Methods:              []string{fiber.MethodGet},
		MaxBytes:             0, // 0 means no limit
		StoreResponseHeaders: false,
	})

	// Create Fiber application.
	app := fiber.New()

	// Register the cache middleware globally.
	// However, the cache middleware itself will only cache GET requests.
	app.Use(cacheMiddleware)

	// Register handlers.
	app.Get("/users/:id", getUserHandler)
	app.Get("/blogs/:id", getBlogHandler)

	return app
}

func getUserHandler(c *fiber.Ctx) error {
	// This is for simplicity and demonstration.
	// Handler should read blog from database by ID, let's pretend we are doing so.
	time.Sleep(time.Millisecond * 200)
	user := User{
		ID:   c.Params("id"),
		Name: "John Doe",
	}
	return c.JSON(user)
}

func getBlogHandler(c *fiber.Ctx) error {
	// This is for simplicity and demonstration.
	// Handler should read blog from database by ID, let's pretend we are doing so.
	time.Sleep(time.Millisecond * 200)
	blog := Blog{
		ID:      c.Params("id"),
		Content: "This is a micro-blog limited to 140 characters.",
	}
	return c.JSON(blog)
}

func main() {
	app := createServiceApp()
	if err := app.Listen(":8080"); err != nil {
		log.Fatal("failed to start service app", err)
	}
}
