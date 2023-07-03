package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/redis/go-redis/v9"
)

var db *sql.DB

const userID = 42

func init() {

	var err error
	// Connect to SQLite
	db, err = sql.Open("sqlite3", "./test.db")
	if err != nil {
		log.Fatal(err)
	}

	loadData(20)

	rdb = redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})

}

func getOrders(rw http.ResponseWriter, req *http.Request) {
	key := fmt.Sprintf("user:%d:orders", userID)
	var orders []Order

	val, err := rdb.Get(ctx, key).Result()
	if err == redis.Nil {

		fmt.Println("fetching data from 'orders' table")

		// Cache miss - get the data from the database
		rows, err := db.Query("SELECT order_id, user_id, product_id, quantity FROM orders WHERE user_id = ?", userID)
		if err != nil {
			http.Error(rw, err.Error(), 500)
			return
		}
		defer rows.Close()

		for rows.Next() {
			var order Order
			err = rows.Scan(&order.OrderID, &order.UserID, &order.ProductID, &order.Quantity)
			if err != nil {
				http.Error(rw, err.Error(), 500)
				return
			}
			orders = append(orders, order)
		}

		// Convert orders to JSON
		jsonOrders, err := json.Marshal(orders)
		if err != nil {
			http.Error(rw, err.Error(), 500)
			return
		}

		// Store the data in Redis with an expiration time of 5 seconds (for demonstration purposes)
		err = rdb.Set(ctx, key, string(jsonOrders), 5*time.Second).Err()
		if err != nil {
			http.Error(rw, err.Error(), 500)
			return
		}

		err = json.NewEncoder(rw).Encode(orders)
		if err != nil {
			http.Error(rw, err.Error(), 500)
			return
		}

		return

	} else if err != nil {
		http.Error(rw, err.Error(), 500)
		return
	}

	fmt.Println("fetching cached order data")

	// Cache hit - return the data from Redis

	err = json.Unmarshal([]byte(val), &orders)
	if err != nil {
		http.Error(rw, err.Error(), 500)
		return
	}

	err = json.NewEncoder(rw).Encode(orders)
	if err != nil {
		http.Error(rw, err.Error(), 500)
		return
	}
}

var ctx = context.Background()

func loadData(numberOfOrders int) {

	// Drop the existing orders table
	_, err := db.Exec("DROP TABLE IF EXISTS orders")
	if err != nil {
		log.Fatal("failed drop table", err)
	}

	// Create the orders table
	_, err = db.Exec(`CREATE TABLE orders (
			order_id INTEGER,
			user_id INTEGER,
			product_id INTEGER,
			quantity INTEGER
		)`)
	if err != nil {
		log.Fatal("failed create table", err)
	}

	fmt.Println("created table 'orders'")

	tx, err := db.Begin()
	if err != nil {
		log.Fatal("failed to begin db tx", err)
	}

	stmt, err := tx.Prepare("INSERT INTO orders(order_id, user_id, product_id, quantity) VALUES (?, ?, ?, ?)")
	if err != nil {
		log.Fatal("prepared statement creation failed failed", err)
	}
	defer stmt.Close()

	// Insert the orders
	for i := 1; i <= numberOfOrders; i++ {
		_, err = stmt.Exec(i, userID, i, i*2) // assuming product_id is same as i and quantity is twice i
		if err != nil {
			log.Fatal("load data failed", err)
		}
	}

	err = tx.Commit()
	if err != nil {
		log.Fatal("commit failed", err)
	}

	fmt.Println("inserted data in 'orders' table")

}

type Order struct {
	OrderID   int `json:"order_id"`
	UserID    int `json:"-"`
	ProductID int `json:"product_id"`
	Quantity  int `json:"quantity"`
}
