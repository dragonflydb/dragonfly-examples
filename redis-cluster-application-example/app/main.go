package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/gorilla/mux"
	"github.com/redis/go-redis/v9"
)

var client redis.UniversalClient

func init() {
	hosts := os.Getenv("REDIS_HOSTS")
	if hosts == "" {
		log.Fatal("enter value for REDIS_HOSTS")
	}

	client = redis.NewClusterClient(&redis.ClusterOptions{Addrs: strings.Split(hosts, ",")})
	err := client.Ping(context.Background()).Err()
	if err != nil {
		log.Fatal("failed to connect", err)
	}

	fmt.Println("connected to redis", hosts)

	load := os.Getenv("LOAD_DATA")
	if load != "" {
		_load, err := strconv.ParseBool(load)
		if err != nil {
			log.Fatal("invalid value for LOAD_DATA. use true/false", load)
		}

		if _load {
			loadData()
		}
	}
}

func loadData() {
	fmt.Println("loading sample data into redis.....")

	user := map[string]string{}

	for i := 0; i < 100; i++ {
		key := "user:" + strconv.Itoa(i)
		name := "user-" + strconv.Itoa(i)
		email := name + "@foo.com"
		user["name"] = name
		user["email"] = email

		err := client.HMSet(context.Background(), key, user).Err()
		if err != nil {
			log.Fatal("failed to load data", err)
		}
	}

	fmt.Println("data load complete")
}

type User struct {
	Name  string `redis:"name" json:"name"`
	Email string `redis:"email" json:"email"`
}

func main() {
	r := mux.NewRouter()
	r.HandleFunc("/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := mux.Vars(r)["id"]
		hashName := "user:" + id
		fmt.Println("getting data for", hashName)

		var user User
		err := client.HMGet(context.Background(), hashName, "name", "email").Scan(&user)

		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		err = json.NewEncoder(w).Encode(user)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	})

	log.Fatal(http.ListenAndServe(":8080", r))
}
