package main

import (
	"log"

	"usm/app/handler"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/logger"
	_ "github.com/mattn/go-sqlite3"
)

func main() {
	app := fiber.New()
	app.Use(logger.New())

	app.Post("/user/register", handler.UserRegistration)
	app.Post("/user/login", handler.UserLogin)
	app.Post("/user/logout", handler.UserLogout)
	app.Post("/user/refresh-token", handler.UserRefreshToken)
	app.Get("/resource", handler.UserReadResource)

	log.Fatal(app.Listen(":8080"))
}
