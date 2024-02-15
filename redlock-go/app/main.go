package main

import (
	"net/http"
	"time"

	"github.com/go-redsync/redsync/v4"
	redsyncredis "github.com/go-redsync/redsync/v4/redis"
	redsyncpool "github.com/go-redsync/redsync/v4/redis/goredis/v9"
	"github.com/redis/go-redis/v9"
)

// These hosts are reachable from within the Docker network.
const (
	dragonflyHost0 = "dragonfly-instance-0:6379"
	dragonflyHost1 = "dragonfly-instance-1:6379"
	dragonflyHost2 = "dragonfly-instance-2:6379"
)

const (
	// The name of the global lock.
	globalLockKeyName = "my-global-lock"

	// The expiry of the global lock.
	globalLockExpiry = time.Minute

	// Number of retries to acquire the global lock.
	globalLockRetries = 8

	// The delay between retries to acquire the global lock.
	globalLockRetryDelay = 10 * time.Millisecond
)

func main() {
	// Create three clients for each instance of Dragonfly.
	var (
		hosts   = []string{dragonflyHost0, dragonflyHost1, dragonflyHost2}
		clients = make([]redsyncredis.Pool, len(hosts))
	)
	for idx, addr := range hosts {
		client := redis.NewClient(&redis.Options{
			Addr: addr,
		})
		clients[idx] = redsyncpool.NewPool(client)
	}

	// Create an instance of 'Redsync' to work with locks.
	rs := redsync.New(clients...)

	// Create a global lock mutex.
	globalMutex := rs.NewMutex(
		globalLockKeyName,
		redsync.WithExpiry(globalLockExpiry),
		redsync.WithTries(globalLockRetries),
		redsync.WithRetryDelay(globalLockRetryDelay),
	)

	// Create an HTTP server that exposes an endpoint to acquire the global lock.
	// Normally, the lock should be released after the work is done.
	// For demonstration purposes, the lock is released after the configured expiry,
	// so that you can check the lock keys in Dragonfly instances.
	http.HandleFunc("/try-to-acquire-global-lock", func(w http.ResponseWriter, r *http.Request) {
		if err := globalMutex.Lock(); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("lock acquired"))
	})

	if err := http.ListenAndServe(":8080", nil); err != nil {
		panic(err)
	}
}
