package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	rdata "github.com/Pallinder/go-randomdata"
	"github.com/gocelery/gocelery"
	"github.com/gomodule/redigo/redis"
)

const (
	redisHostEnvVar     = "REDIS_HOST"
	redisPasswordEnvVar = "REDIS_PASSWORD"
	taskName            = "users.registration.email"
)

var (
	redisHost string
)

func init() {
	redisHost = os.Getenv(redisHostEnvVar)
	if redisHost == "" {
		redisHost = "localhost:6379"
	}

}

func main() {
	redisPool := &redis.Pool{
		Dial: func() (redis.Conn, error) {
			c, err := redis.Dial("tcp", redisHost)

			if err != nil {
				return nil, err
			}
			return c, err
		},
	}

	celeryClient, err := gocelery.NewCeleryClient(
		gocelery.NewRedisBroker(redisPool),
		&gocelery.RedisCeleryBackend{Pool: redisPool},
		1,
	)

	if err != nil {
		log.Fatal(err)
	}

	exit := make(chan os.Signal, 1)
	signal.Notify(exit, syscall.SIGINT, syscall.SIGTERM)
	closed := false

	go func() {
		fmt.Println("celery producer started...")

		for !closed {
			res, err := celeryClient.Delay(taskName, rdata.FullName(rdata.RandomGender)+","+rdata.Email())
			if err != nil {
				panic(err)
			}
			fmt.Println("sent data and generated task", res.TaskID, "for worker")
			time.Sleep(1 * time.Second)
		}
	}()

	<-exit
	log.Println("exit signalled")

	closed = true
	log.Println("celery producer stopped")
}
