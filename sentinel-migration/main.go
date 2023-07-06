package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"

	"github.com/gorilla/mux"
	"github.com/redis/go-redis/v9"
)

var client *redis.Client

const (
	httpPort                 = ":8080"
	sentinelEndpoint         = "localhost:5000"
	masterNameInSentinelConf = "the_master"
)

func main() {

	r := mux.NewRouter()

	r.HandleFunc("/{id}", get).Methods(http.MethodGet)
	r.HandleFunc("/{id}", set).Methods(http.MethodPost)

	log.Fatal(http.ListenAndServe(httpPort, r))

}

func init() {
	client = redis.NewFailoverClient(&redis.FailoverOptions{
		MasterName:    masterNameInSentinelConf,
		SentinelAddrs: []string{sentinelEndpoint},
	})

	err := client.Ping(context.Background()).Err()
	if err != nil {
		log.Fatalf("failed to connect %v", err)
	}

	fmt.Println("connected to redis")

}

func get(rw http.ResponseWriter, req *http.Request) {
	id := mux.Vars(req)["id"]
	val, err := client.Get(context.Background(), "key-"+id).Result()

	if err != nil {
		if errors.Is(err, redis.Nil) {
			//http.Error(rw, "key-"+id+" not found", http.StatusNotFound)
			errResp := ErrorResponse{Op: "get", Message: "key-" + id + " not found", Code: http.StatusNotFound}
			json.NewEncoder(rw).Encode(errResp)
			return
		}

		//http.Error(rw, err.Error(), http.StatusInternalServerError)
		fmt.Println("get failed with error", err)

		errResp := ErrorResponse{Op: "get", Message: err.Error(), Code: http.StatusInternalServerError}
		json.NewEncoder(rw).Encode(errResp)
		return
	}

	s := redis.NewSentinelClient(&redis.Options{
		Addr: sentinelEndpoint,
	})

	info, err := s.Master(context.Background(), masterNameInSentinelConf).Result()
	if err != nil {
		//http.Error(rw, err.Error(), http.StatusInternalServerError)
		fmt.Println("sentinel command failed with error", err)

		errResp := ErrorResponse{Op: "get", Message: err.Error(), Code: http.StatusInternalServerError}
		json.NewEncoder(rw).Encode(errResp)

		return
	}

	node := info["ip"] + ":" + info["port"]

	response := GetResponse{Key: "key-" + id, Value: val, FromNode: node}

	err = json.NewEncoder(rw).Encode(response)
	if err != nil {
		http.Error(rw, err.Error(), http.StatusInternalServerError)
		fmt.Println("json response encoding failed with error", err)
		return
	}

	fmt.Println("key-" + id + "=" + val + " (from) " + node)

}

type GetResponse struct {
	Key      string `json:"key"`
	Value    string `json:"value"`
	FromNode string `json:"from_node"`
}

type ErrorResponse struct {
	Op      string `json:"operation"`
	Message string `json:"msg"`
	Code    int    `json:"code"`
}

func set(rw http.ResponseWriter, req *http.Request) {
	id := mux.Vars(req)["id"]
	err := client.Set(context.Background(), "key-"+id, "value-"+id, 0).Err()

	if err != nil {
		//http.Error(rw, err.Error(), http.StatusInternalServerError)
		fmt.Println("set failed with error", err)

		errResp := ErrorResponse{Op: "set", Message: err.Error(), Code: http.StatusInternalServerError}
		json.NewEncoder(rw).Encode(errResp)
		return
	}

	fmt.Println("set key-" + id + "=" + "value-" + id)
}
