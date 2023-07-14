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

var client *redis.Client

func init() {
	// Connect to Redis
	client = redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
}

func main() {
	http.HandleFunc("/load", loadAds)
	http.HandleFunc("/ads", fetchAds)
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func loadAds(w http.ResponseWriter, r *http.Request) {

	ctx := context.Background()

	categories := []string{"sports", "technology", "fashion"}
	for i := 1; i <= 10; i++ {
		adID := "ad:" + strconv.Itoa(i)
		title := "Ad " + strconv.Itoa(i)
		category := categories[rand.Intn(len(categories))] // random category
		imageURL := "http://example.com/images/" + adID    // mock image URL
		clickURL := "http://example.com/ads/" + adID       // mock click URL
		client.HSet(ctx, adID, "title", title, "category", category, "imageURL", imageURL, "clickURL", clickURL)
		client.SAdd(ctx, "ad_category:"+category, adID)
	}

	// Seeding user interest data
	for i := 1; i <= 5; i++ {
		userID := "user:" + strconv.Itoa(i)
		numInterests := rand.Intn(3) + 1 // random number of interests between 1 and 3
		interests := make([]interface{}, numInterests)
		for j := 0; j < numInterests; j++ {
			interests[j] = categories[rand.Intn(len(categories))] // random interests
		}
		client.SAdd(ctx, userID+":interests", interests...)
	}

	fmt.Fprintf(w, "Ads and user interests loaded")
}

func fetchAds(w http.ResponseWriter, r *http.Request) {

	ctx := r.Context()

	user := r.URL.Query().Get("user") // The user ID should be passed as a query parameter
	if user == "" {
		http.Error(w, "User not specified", http.StatusBadRequest)
		return
	}

	fmt.Println("getting ad for user", user)

	interests, err := client.SMembers(ctx, "user:"+user+":interests").Result()
	if err != nil {
		http.Error(w, "Error fetching user interests", http.StatusInternalServerError)
		return
	}

	fmt.Println("user", user, "interests", interests)

	var ads []map[string]string
	for _, interest := range interests {

		fmt.Println("getting ad for", interest)

		adIDs, _ := client.SMembers(ctx, "ad_category:"+interest).Result()
		for _, adID := range adIDs {
			//var ad Ad
			ad, err := client.HGetAll(ctx, adID).Result()
			if err != nil {
				http.Error(w, "Error fetching ad info", http.StatusInternalServerError)
				return
			}
			//json.Unmarshal([]byte(adJson), &ad)
			ads = append(ads, ad)
		}
	}

	json.NewEncoder(w).Encode(ads)
}
