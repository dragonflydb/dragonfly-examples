package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"strings"
	"sync"

	"github.com/redis/go-redis/v9"
)

var ctx = context.Background()

// Number of goroutines to use
const numGoroutines = 10

// Length of each value in bytes
const valueLength = 1024

func main() {
	var dataSizeGB int
	var keyPrefix string

	flag.IntVar(&dataSizeGB, "dataSizeGB", 1, "Amount of data to create in GB")
	flag.StringVar(&keyPrefix, "keyPrefix", "", "prefix for key")
	flag.Parse()

	if keyPrefix == "" {
		log.Fatal("missing keyPrefix")
	}

	// value that is approximately 10 KB

	value := strings.Repeat("a", 10*1024)

	// Calculate the number of keys to create
	numKeys := (dataSizeGB * 1024 * 1024 * 1024) / len(value)

	fmt.Println("loading", dataSizeGB, "GB data")
	fmt.Println("numKeys ==", numKeys)

	// Connect to Redis
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})

	err := rdb.Ping(context.Background()).Err()
	if err != nil {
		log.Fatal("failed to connect with redis", err)
	}

	fmt.Println("connected to redis")

	ctx := context.Background()
	var wg sync.WaitGroup

	// Create 10 Go routines
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			for j := i * numKeys / 10; j < (i+1)*numKeys/10; j += 1000 {
				pipe := rdb.Pipeline()
				for k := 0; k < 1000 && j+k < numKeys; k++ {
					pipe.Set(ctx, fmt.Sprintf(keyPrefix+"-key%d", j+k), value, 0)
				}
				_, err := pipe.Exec(ctx)
				if err != nil {
					log.Fatal("pipeline exec failed: ", err)
				}
			}
		}(i)
	}

	wg.Wait()

	rdb.Close()

	fmt.Println("finished loading data")
}
