package main

import (
	"context"
	"time"

	"github.com/redis/go-redis/v9"
)

// CacheStorage implements the fiber.Storage interface.
type CacheStorage struct {
	client *redis.Client
}

func (m *CacheStorage) Get(key string) ([]byte, error) {
	// Use the actual GET command of Dragonfly.
	return m.client.Get(context.Background(), key).Bytes()
}

func (m *CacheStorage) Set(key string, val []byte, exp time.Duration) error {
	// Use the actual SET command of Dragonfly.
	return m.client.Set(context.Background(), key, val, exp).Err()
}

func (m *CacheStorage) Delete(key string) error {
	// Use the actual DEL command of Dragonfly.
	return m.client.Del(context.Background(), key).Err()
}

func (m *CacheStorage) Close() error {
	return m.client.Close()
}

func (m *CacheStorage) Reset() error {
	return nil
}
