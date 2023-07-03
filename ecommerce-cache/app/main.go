package main

import (
	"context"
	"fmt"
	"log"
	"net/http"

	_ "github.com/mattn/go-sqlite3"
	"github.com/redis/go-redis/v9"
)

var rdb *redis.Client

func init() {

	rdb = redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})

	err := rdb.Ping(context.Background()).Err()
	if err != nil {
		log.Fatal("failed to connect with redis", err)
	}

	fmt.Println("connected to redis")

}

func main() {

	http.HandleFunc("/orders", getOrders)
	http.HandleFunc("/topviewed", getMostViewedItems)
	http.HandleFunc("/recommendations", getRecommendations)

	log.Fatal(http.ListenAndServe(":8080", nil))
}
