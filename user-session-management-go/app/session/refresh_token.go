package session

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

const (
	refreshTokenExpiryInSeconds = 7 * 24 * 60 * 60 // 7 days
	refreshTokenKeyFormat       = "user:%s:sessions"
	refreshTokenTextDelimiter   = "__"
)

var dragonfly *redis.Client

func init() {
	// Initialize a Redis client, which can be used to manipulate data in Dragonfly.
	// Make sure to have a Dragonfly instance running on localhost:6380.
	dragonfly = redis.NewClient(&redis.Options{
		Addr: "localhost:6380",
	})
}

type RefreshToken struct {
	UserID uuid.UUID
	Token  uuid.UUID
}

// UnmarshalText implements the encoding.TextUnmarshaler interface for RefreshToken,
// which parses a string with the format "userID__token" into a RefreshToken struct.
func (t *RefreshToken) UnmarshalText(data []byte) error {
	parts := strings.SplitN(string(data), refreshTokenTextDelimiter, 2)
	if len(parts) != 2 {
		return errors.New("invalid refresh token format")
	}

	userIDStr, tokenStr := parts[0], parts[1]
	userID, err := uuid.Parse(userIDStr)
	if err != nil {
		return err
	}
	token, err := uuid.Parse(tokenStr)
	if err != nil {
		return err
	}

	t.UserID = userID
	t.Token = token
	return nil
}

// UnmarshalJSON implements the json.Unmarshaler interface for RefreshToken,
// which parses a string with the format `"userID__token"` into a RefreshToken struct.
func (t *RefreshToken) UnmarshalJSON(data []byte) error {
	var text string
	if err := json.Unmarshal(data, &text); err != nil {
		return err
	}
	return t.UnmarshalText([]byte(text))
}

// MarshalText implements the encoding.TextMarshaler interface for RefreshToken,
// which formats a RefreshToken struct into a string with the format "userID__token".
func (t *RefreshToken) MarshalText() ([]byte, error) {
	return []byte(fmt.Sprintf("%s%s%s", t.UserID.String(), refreshTokenTextDelimiter, t.Token.String())), nil
}

// MarshalJSON implements the json.Marshaler interface for RefreshToken,
// which formats a RefreshToken struct into a string with the format `"userID__token"`.
func (t *RefreshToken) MarshalJSON() ([]byte, error) {
	text, err := t.MarshalText()
	if err != nil {
		return nil, err
	}
	return json.Marshal(string(text))
}

type TokenResponse struct {
	AccessToken  string       `json:"access_token"`
	RefreshToken RefreshToken `json:"refresh_token"`
}

// GenerateTokens creates a new pair of refresh and access tokens.
// The refresh token is stored in Dragonfly with the key "user:<userID>:sessions".
// This function should be called when a user logs in.
func GenerateTokens(ctx context.Context, userID uuid.UUID) (*TokenResponse, error) {
	// Generate a new pair of tokens.
	newRefreshToken := RefreshToken{
		UserID: userID,
		Token:  uuid.New(),
	}
	newAccessToken, err := generateAccessToken(userID.String())
	if err != nil {
		return nil, err
	}

	// Using a pipeline to perform the following operations:
	// - Store the new refresh token in Dragonfly.
	// - Set the expiry time for the new refresh token using Dragonfly's FIELDEXPIRE command.
	key := fmt.Sprintf(refreshTokenKeyFormat, userID.String())
	_, err = dragonfly.Pipelined(ctx, func(pipe redis.Pipeliner) error {
		newRefreshTokenStr := newRefreshToken.Token.String()
		pipe.SAdd(ctx, key, newRefreshTokenStr)
		pipe.Do(ctx, "FIELDEXPIRE", key, refreshTokenExpiryInSeconds, newRefreshTokenStr)
		return nil
	})
	if err != nil {
		return nil, err
	}

	// Return the new pair of refresh and access tokens.
	return &TokenResponse{
		AccessToken:  newAccessToken,
		RefreshToken: newRefreshToken,
	}, nil
}

var ErrInvalidOrExpiredRefreshToken = errors.New("invalid or expired refresh token")

// RefreshTokens validates the refresh token and issues a new pair of refresh and access tokens.
// The refresh token is stored in Dragonfly with the key "user:<userID>:sessions".
// The old refresh token is removed from Dragonfly.
// This function should be called when a user requests a pair of new tokens using a refresh token.
func RefreshTokens(ctx context.Context, refreshToken RefreshToken) (*TokenResponse, error) {
	// Validate the refresh token in Dragonfly.
	key := fmt.Sprintf(refreshTokenKeyFormat, refreshToken.UserID.String())
	isMember, err := dragonfly.SIsMember(ctx, key, refreshToken.Token.String()).Result()
	if err != nil {
		return nil, err
	}
	if !isMember {
		return nil, ErrInvalidOrExpiredRefreshToken
	}

	// Generate a new pair of tokens.
	newRefreshToken := RefreshToken{
		UserID: refreshToken.UserID,
		Token:  uuid.New(),
	}
	newAccessToken, err := generateAccessToken(refreshToken.UserID.String())
	if err != nil {
		return nil, err
	}

	// Using a pipeline to perform the following operations:
	// - Store the new refresh token in Dragonfly.
	// - Set the expiry time for the new refresh token using Dragonfly's FIELDEXPIRE command.
	// - Remove the old refresh token from Dragonfly.
	_, err = dragonfly.Pipelined(ctx, func(pipe redis.Pipeliner) error {
		var (
			newRefreshTokenStr = newRefreshToken.Token.String()
			oldRefreshTokenStr = refreshToken.Token.String()
		)
		pipe.SAdd(ctx, key, newRefreshTokenStr)
		pipe.Do(ctx, "FIELDEXPIRE", key, refreshTokenExpiryInSeconds, newRefreshTokenStr)
		pipe.SRem(ctx, key, oldRefreshTokenStr)
		return nil
	})
	if err != nil {
		return nil, err
	}

	// Return the new pair of tokens.
	return &TokenResponse{
		AccessToken:  newAccessToken,
		RefreshToken: newRefreshToken,
	}, nil
}

// RemoveRefreshToken removes the refresh token from Dragonfly.
// If the refresh token is not found, this function does nothing and returns nil.
func RemoveRefreshToken(ctx context.Context, refreshToken RefreshToken) error {
	key := fmt.Sprintf(refreshTokenKeyFormat, refreshToken.UserID.String())
	_, err := dragonfly.SRem(ctx, key, refreshToken.Token.String()).Result()
	return err
}
