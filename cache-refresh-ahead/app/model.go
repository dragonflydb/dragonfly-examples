package main

import (
	"encoding/json"
	"time"

	"github.com/google/uuid"
)

type Repo struct{}

// UseRepo returns a singleton instance of Repo.
// Practically, the singleton instance should be initialized with a database connection
// and other necessary dependencies, concurrency-safely using sync.Once.
func UseRepo() *Repo {
	return repoSingleton
}

var repoSingleton = &Repo{}

// User model and repository methods.
type User struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

func (r *Repo) ReadUserByID(id uuid.UUID) (*User, error) {
	return r.readUserByID(id)
}

func (r *Repo) ReadUserBytesByID(id uuid.UUID) ([]byte, error) {
	user, err := r.readUserByID(id)
	if err != nil {
		return nil, err
	}
	return json.Marshal(user)
}

func (r *Repo) readUserByID(id uuid.UUID) (*User, error) {
	// This is for simplicity and demonstration.
	// Pretend we are reading user from database.
	time.Sleep(time.Millisecond * 200)
	return &User{
		ID:   id.String(),
		Name: "John Doe",
	}, nil
}

// Blog model and repository methods.
type Blog struct {
	ID      string `json:"id"`
	Content string `json:"content"`
}

func (r *Repo) ReadBlogByID(id uuid.UUID) (*Blog, error) {
	return r.readBlogByID(id)
}

func (r *Repo) ReadBlogBytesByID(id uuid.UUID) ([]byte, error) {
	blog, err := r.readBlogByID(id)
	if err != nil {
		return nil, err
	}
	return json.Marshal(blog)
}

func (r *Repo) readBlogByID(id uuid.UUID) (*Blog, error) {
	// This is for simplicity and demonstration.
	// Pretend we are reading blog from database.
	time.Sleep(time.Millisecond * 200)
	return &Blog{
		ID:      id.String(),
		Content: "This is a micro-blog limited to 140 characters.",
	}, nil
}
