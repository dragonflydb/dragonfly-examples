package handler

import (
	"fmt"

	"golang.org/x/crypto/bcrypt"
)

func hashPassword(password string) (hash string, err error) {
	hashedBytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", fmt.Errorf("failed to hash password: %w", err)
	}
	hash = string(hashedBytes)
	return hash, nil
}

func verifyPassword(password, hash string) error {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
}
