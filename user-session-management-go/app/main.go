package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"

	"usm/app/session"

	"github.com/google/uuid"
	_ "github.com/mattn/go-sqlite3"
	"golang.org/x/crypto/bcrypt"
)

var db *sql.DB

func init() {
	// Initialize the SQLite database.
	var err error
	db, err = sql.Open("sqlite3", "./app.db")
	if err != nil {
		log.Fatalf("failed to connect to database: %v", err)
	}

	// Create users and sessions tables
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS users (
			id TEXT PRIMARY KEY,
			username TEXT UNIQUE,
			password_hash TEXT
		);
	`)
	if err != nil {
		log.Fatalf("failed to initialize database: %v", err)
	}
}

type UserRegisterOrLoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// hashPassword hashes the given password using bcrypt.
// It returns the hashed password and any error encountered during execution.
func hashPassword(password string) (hash string, err error) {
	// Generate bcrypt hash
	hashedBytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", fmt.Errorf("failed to hash password: %w", err)
	}

	// Convert hashed bytes to a string
	hash = string(hashedBytes)
	return hash, nil
}

// verifyPassword checks if the given password matches the hashed password.
// Returns nil if they match, otherwise an error.
func verifyPassword(password, hash string) error {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	if err != nil {
		return fmt.Errorf("password does not match: %w", err)
	}
	return nil
}

func userRegisterHandler(w http.ResponseWriter, r *http.Request) {
	var req UserRegisterOrLoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}

	// Check if the username is already taken.
	var count int
	err := db.QueryRow("SELECT COUNT(*) FROM users WHERE username = ?", req.Username).Scan(&count)
	if err != nil {
		http.Error(w, "internal server error", http.StatusInternalServerError)
		return
	}
	if count > 0 {
		http.Error(w, "username already taken", http.StatusBadRequest)
		return
	}

	// Hash the password.
	hash, err := hashPassword(req.Password)
	if err != nil {
		http.Error(w, "internal server error", http.StatusInternalServerError)
		return
	}

	// Insert the user into the database.
	userID := uuid.New().String()
	_, err = db.Exec("INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)", userID, req.Username, hash)
	if err != nil {
		http.Error(w, "internal server error", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
}

func loginHandler(w http.ResponseWriter, r *http.Request) {
	var req UserRegisterOrLoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}

	// Retrieve the user from the database.
	var userIDStr string
	var hashStr string
	err := db.QueryRow("SELECT id, password_hash FROM users WHERE username = ?", req.Username).Scan(&userIDStr, &hashStr)
	if err != nil {
		http.Error(w, "invalid username or password", http.StatusUnauthorized)
		return
	}

	// Verify the password.
	if err := verifyPassword(req.Password, hashStr); err != nil {
		http.Error(w, "invalid username or password", http.StatusUnauthorized)
		return
	}

	// Generate a pair of refresh and access tokens.
	userID, err := uuid.Parse(userIDStr)
	if err != nil {
		http.Error(w, fmt.Errorf("internal server error: %w", err).Error(), http.StatusInternalServerError)
		return
	}
	tokenResponse, err := session.GenerateTokens(context.Background(), userID)
	if err != nil {
		http.Error(w, fmt.Errorf("internal server error: %w", err).Error(), http.StatusInternalServerError)
		return
	}

	// Return the tokens in the response.
	respBytes, err := json.Marshal(tokenResponse)
	if err != nil {
		http.Error(w, fmt.Errorf("internal server error: %w", err).Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write(respBytes)
}

func logoutHandler(w http.ResponseWriter, r *http.Request) {
	refreshTokenStr := r.Header.Get("Authorization")
	refreshTokenStr = strings.TrimPrefix(refreshTokenStr, "Bearer ")

	// Validate the refresh token using MarshalText.
	refreshToken := new(session.RefreshToken)
	if err := refreshToken.UnmarshalText([]byte(refreshTokenStr)); err != nil {
		http.Error(w, fmt.Errorf("invalid refresh token: %w", err).Error(), http.StatusBadRequest)
		return
	}

	if err := session.RemoveRefreshToken(context.Background(), *refreshToken); err != nil {
		http.Error(w, "internal server error", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func refreshTokenHandler(w http.ResponseWriter, r *http.Request) {
	refreshTokenStr := r.Header.Get("Authorization")
	refreshTokenStr = strings.TrimPrefix(refreshTokenStr, "Bearer ")

	// Validate the refresh token using MarshalText.
	refreshToken := new(session.RefreshToken)
	if err := refreshToken.UnmarshalText([]byte(refreshTokenStr)); err != nil {
		http.Error(w, fmt.Errorf("invalid refresh token: %w", err).Error(), http.StatusBadRequest)
		return
	}

	// Generate a new pair of refresh and access tokens.
	tokenResponse, err := session.RefreshTokens(context.Background(), *refreshToken)
	if err != nil {
		http.Error(w, fmt.Errorf("internal server error: %w", err).Error(), http.StatusInternalServerError)
		return
	}

	// Return the tokens in the response.
	respBytes, err := json.Marshal(tokenResponse)
	if err != nil {
		http.Error(w, fmt.Errorf("internal server error: %w", err).Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write(respBytes)
}

func resourceHandler(w http.ResponseWriter, r *http.Request) {
	accessTokenStr := r.Header.Get("Authorization")
	accessTokenStr = strings.TrimPrefix(accessTokenStr, "Bearer ")

	_, err := session.VerifyAccessToken(accessTokenStr)
	if err != nil {
		http.Error(w, "invalid access token", http.StatusUnauthorized)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func main() {
	http.HandleFunc("/user/register", userRegisterHandler)
	http.HandleFunc("/user/login", loginHandler)
	http.HandleFunc("/user/logout", logoutHandler)
	http.HandleFunc("/user/refresh-session", refreshTokenHandler)
	http.HandleFunc("/resource", resourceHandler)

	fmt.Println("server started at port 8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
