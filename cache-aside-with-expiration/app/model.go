package main

type User struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

type Blog struct {
	ID      string `json:"id"`
	Content string `json:"content"`
}
