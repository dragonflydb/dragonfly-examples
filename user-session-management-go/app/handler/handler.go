package handler

import (
	"context"
	"database/sql"
	"errors"
	"strings"

	"usm/app/session"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
)

const (
	tokenHeader = "Authorization"
	tokenPrefix = "Bearer"
)

type UserRegisterOrLoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// UserRegistration registers a new user in the database.
func UserRegistration(c *fiber.Ctx) error {
	var req UserRegisterOrLoginRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).SendString(err.Error())
	}

	var count int
	err := db.QueryRow("SELECT COUNT(*) FROM users WHERE username = ?", req.Username).Scan(&count)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
	}
	if count > 0 {
		return c.Status(fiber.StatusBadRequest).SendString("username already taken")
	}

	hash, err := hashPassword(req.Password)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
	}

	userID, err := uuid.NewV7()
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
	}
	_, err = db.Exec(
		"INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
		userID.String(), req.Username, hash,
	)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
	}

	return c.SendStatus(fiber.StatusCreated)
}

// UserLogin verifies the user's credentials and generates a pair of refresh and access tokens.
func UserLogin(c *fiber.Ctx) error {
	var req UserRegisterOrLoginRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).SendString(err.Error())
	}

	var userIDStr, hashStr string
	err := db.QueryRow(
		"SELECT id, password_hash FROM users WHERE username = ?", req.Username,
	).Scan(&userIDStr, &hashStr)
	if err != nil && errors.Is(err, sql.ErrNoRows) {
		return c.Status(fiber.StatusUnauthorized).SendString("invalid username or password")
	}
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
	}

	if err := verifyPassword(req.Password, hashStr); err != nil {
		return c.Status(fiber.StatusUnauthorized).SendString(err.Error())
	}

	userID, err := uuid.Parse(userIDStr)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
	}

	tokenResponse, err := session.GenerateTokens(context.Background(), userID)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
	}

	return c.JSON(tokenResponse)
}

// UserLogout requires the user's refresh token to be removed from Dragonfly.
func UserLogout(c *fiber.Ctx) error {
	refreshTokenStr := c.Get(tokenHeader)
	refreshTokenStr = strings.TrimPrefix(refreshTokenStr, tokenPrefix)
	refreshTokenStr = strings.TrimSpace(refreshTokenStr)

	refreshToken := new(session.RefreshToken)
	if err := refreshToken.UnmarshalText([]byte(refreshTokenStr)); err != nil {
		return c.Status(fiber.StatusBadRequest).SendString(err.Error())
	}

	if err := session.RemoveRefreshToken(context.Background(), *refreshToken); err != nil {
		return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
	}

	return c.SendStatus(fiber.StatusOK)
}

// UserRefreshToken requires the user's refresh token to generate a new pair of refresh and access tokens.
// The newly generated refresh token replaces the old one in Dragonfly.
func UserRefreshToken(c *fiber.Ctx) error {
	refreshTokenStr := c.Get(tokenHeader)
	refreshTokenStr = strings.TrimPrefix(refreshTokenStr, tokenPrefix)
	refreshTokenStr = strings.TrimSpace(refreshTokenStr)

	refreshToken := new(session.RefreshToken)
	if err := refreshToken.UnmarshalText([]byte(refreshTokenStr)); err != nil {
		return c.Status(fiber.StatusBadRequest).SendString(err.Error())
	}

	tokenResponse, err := session.RefreshTokens(context.Background(), *refreshToken)
	if err != nil && errors.Is(err, session.ErrRefreshTokensNotAuthorized) {
		return c.Status(fiber.StatusUnauthorized).SendString(err.Error())
	}
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
	}

	return c.JSON(tokenResponse)
}

// UserReadResource requires the user's access token to access the protected resource.
// Normally, the access token would be used to authenticate the user in a middleware.
func UserReadResource(c *fiber.Ctx) error {
	accessTokenStr := c.Get(tokenHeader)
	accessTokenStr = strings.TrimPrefix(accessTokenStr, tokenPrefix)
	accessTokenStr = strings.TrimSpace(accessTokenStr)

	_, err := session.VerifyAccessToken(accessTokenStr)
	if err != nil {
		return c.Status(fiber.StatusUnauthorized).SendString(err.Error())
	}

	return c.SendStatus(fiber.StatusOK)
}
