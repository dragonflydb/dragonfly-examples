package main

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

var client *redis.Client

func init() {
	client = redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
}

func main() {
	ctx := context.Background()
	now := time.Now().UTC()
	for i := 0; i < 1000; i++ {
		_, err := client.Pipelined(ctx, func(pipe redis.Pipeliner) error {
			for j := 0; j < 1000; j++ {
				key := fmt.Sprintf("key_%d_%d", i, j)
				val := fmt.Sprintf("val_%d_%d", i, j)
				pipe.Set(ctx, key, val, 0)
			}
			return nil
		})
		if err != nil {
			panic(err)
		}
	}
	fmt.Println(time.Now().UTC().Sub(now))
}
