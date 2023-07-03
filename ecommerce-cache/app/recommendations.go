package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
)

const recommendations = "user:42:recommendations"

func init() {

	//we are loading sample data. but imagine this being populated in real-time while user is interacting with the ecommerce system

	for i := 1; i <= 5; i++ {
		rdb.SAdd(context.Background(), recommendations, "product-"+strconv.Itoa(i))
	}

	fmt.Println("loaded recommendations sample data")
}

func getRecommendations(rw http.ResponseWriter, req *http.Request) {

	items := rdb.SMembers(context.Background(), recommendations).Val()

	resp := RecommendationsResponse{UserID: 42, Items: items}

	err := json.NewEncoder(rw).Encode(resp)
	if err != nil {
		http.Error(rw, err.Error(), 500)
		return
	}
}

type RecommendationsResponse struct {
	UserID int      `json:"user_id"`
	Items  []string `json:"recommended"`
}
