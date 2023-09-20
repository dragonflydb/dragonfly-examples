package main

import (
	"context"
	"encoding/json"
	"io/ioutil"
	"net/http"

	"leaderboard/app/memstore"
	"leaderboard/app/model"

	"github.com/redis/go-redis/v9"
)

func main() {
	client := redis.NewFailoverClient(&redis.FailoverOptions{
		MasterName:    "leaderboard-primary",
		SentinelAddrs: []string{"sentinel-1:5000", "sentinel-2:5000", "sentinel-3:5000"},
	})

	ctx := context.Background()
	_, err := client.Ping(ctx).Result()
	if err != nil {
		panic(err)
	}

	http.Handle("/leaderboard", http.HandlerFunc(
		func(w http.ResponseWriter, r *http.Request) {
			userID := r.URL.Query().Get("user_id")
			if userID == "" {
				panic("id is empty")
			}

			resp, err := memstore.UseLeaderboard(client).ReadTopRankList(ctx, userID)
			if err != nil {
				panic(err)
			}

			respBytes, err := json.Marshal(resp)
			if err != nil {
				panic(err)
			}

			_, _ = w.Write(respBytes)
		}),
	)

	http.Handle("/leaderboard/user", http.HandlerFunc(
		func(w http.ResponseWriter, r *http.Request) {
			body, err := ioutil.ReadAll(r.Body)
			if err != nil {
				panic(err)
			}
			defer func() {
				_ = r.Body.Close()
			}()

			req := &model.UserIncreaseScoreRequest{}
			err = json.Unmarshal(body, req)
			if err != nil {
				panic(err)
			}

			err = memstore.UseLeaderboard(client).IncreaseUserScore(ctx, &req.User, req.Score)
			if err != nil {
				panic(err)
			}
		}),
	)

	if err := http.ListenAndServe(":8080", nil); err != nil {
		panic(err)
	}
}
