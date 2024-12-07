package handler

import (
	"database/sql"
	"log"

	_ "github.com/mattn/go-sqlite3"
)

var db *sql.DB

func init() {
	// Initialize the SQLite database.
	var err error
	db, err = sql.Open("sqlite3", "./app.db")
	if err != nil {
		log.Fatalf("failed to connect to database: %v", err)
	}

	// Create the 'users' table.
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
