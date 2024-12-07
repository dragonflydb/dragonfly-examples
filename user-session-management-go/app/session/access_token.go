package session

import (
	"errors"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

const (
	jwtSecret = "your-secret-key"
	jwtExpiry = 15 * time.Minute

	jwtClaimAlgorithm = "alg"
	jwtClaimUserID    = "sub"
	jwtClaimExpiry    = "exp"
)

// generateAccessToken creates a JWT.
// Since JWTs are stateless, the access token is only valid for a short period of time.
func generateAccessToken(userID string) (string, error) {
	claims := jwt.MapClaims{
		jwtClaimUserID: userID,
		jwtClaimExpiry: time.Now().UTC().Add(jwtExpiry).Unix(),
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(jwtSecret))
}

// VerifyAccessToken validates the JWT and returns the user ID.
func VerifyAccessToken(tokenString string) (string, error) {
	token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header[jwtClaimAlgorithm])
		}
		return []byte(jwtSecret), nil
	})
	if err != nil || !token.Valid {
		return "", fmt.Errorf("invalid token: %w", err)
	}

	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok || !token.Valid {
		return "", errors.New("invalid token claims")
	}

	userID, ok := claims[jwtClaimUserID].(string)
	if !ok {
		return "", errors.New("invalid user ID claim")
	}

	return userID, nil
}
