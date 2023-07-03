package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"strconv"

	"github.com/redis/go-redis/v9"
)

const key = "user:42:item_views"

func init() {

	//we are loading sample data. but imagine this being populated in real-time while user is interacting with the ecommerce system

	var items []redis.Z

	for i := 1; i <= 10; i++ {
		item := "product-" + strconv.Itoa(i)
		items = append(items, redis.Z{Score: float64(rand.Intn(5000) + 1), Member: item})
	}

	err := rdb.ZAdd(context.Background(), key, items...).Err()
	if err != nil {
		log.Fatal("failed to load items data", err)
	}

	fmt.Println("loaded items views sample data")
}

func getMostViewedItems(rw http.ResponseWriter, req *http.Request) {
	items := rdb.ZRevRangeWithScores(context.Background(), key, 0, 4).Val()

	var resp ViewedItemsResponse
	resp.UserID = 42
	var viewed []string

	for _, item := range items {
		viewed = append(viewed, fmt.Sprint(item.Member))
	}

	resp.Items = viewed

	err := json.NewEncoder(rw).Encode(resp)
	if err != nil {
		http.Error(rw, err.Error(), 500)
		return
	}
}

type ViewedItemsResponse struct {
	UserID int      `json:"user_id"`
	Items  []string `json:"viewed"`
}
