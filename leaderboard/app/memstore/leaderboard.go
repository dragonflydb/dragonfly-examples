package memstore

import (
	"context"
	"errors"
	"fmt"
	"time"

	"leaderboard/app/model"
	"leaderboard/app/util"

	"github.com/redis/go-redis/v9"
)

type Leaderboard struct {
	client *redis.Client
}

func UseLeaderboard(client *redis.Client) *Leaderboard {
	return &Leaderboard{client: client}
}

func (l *Leaderboard) hashKey(userID string) string {
	return fmt.Sprintf("leaderboard:users:%v", userID)
}

func (l *Leaderboard) zsetKey() string {
	return fmt.Sprintf("leaderboard:user_scores")
}

func (l *Leaderboard) IncreaseUserScore(
	ctx context.Context,
	user *model.User,
	score float64,
) error {
	if score <= 0 {
		return nil
	}

	var (
		now        = time.Now().UTC()
		zsetKey    = l.zsetKey()
		hashKey    = l.hashKey(user.ID)
		nextMonday = util.MondayOfTime(now.Add(7 * 24 * time.Hour)).Sub(now)
	)

	_, err := l.client.Pipelined(ctx, func(pipe redis.Pipeliner) error {
		pipe.ZIncrBy(ctx, zsetKey, score, hashKey)
		pipe.HSet(ctx, hashKey, user)
		pipe.Expire(ctx, zsetKey, nextMonday)
		pipe.Expire(ctx, hashKey, nextMonday)
		return nil
	})

	return err
}

func (l *Leaderboard) ReadTopRankList(
	ctx context.Context,
	userID string,
) (*model.LeaderboardResponse, error) {
	var (
		resp    = new(model.LeaderboardResponse)
		zsetKey = l.zsetKey()
		hashKey = l.hashKey(userID)
	)

	// Read top 100 users and the current user rank in a pipeline from the Redis Sorted-Set.
	commandsZ, err := l.client.Pipelined(ctx, func(pipe redis.Pipeliner) error {
		pipe.ZRevRangeWithScores(ctx, zsetKey, 0, 100)
		pipe.ZRevRank(ctx, zsetKey, hashKey)
		pipe.ZScore(ctx, zsetKey, hashKey)
		return nil
	})
	// Need to check for the 'redis.Nil' error here because:
	// - These commands are read operations.
	// - The user may not be in the Redis Sorted-Set.
	if err != nil && !errors.Is(err, redis.Nil) {
		return nil, err
	}

	var (
		topRanks                = commandsZ[0].(*redis.ZSliceCmd).Val()
		currRank, currRankErr   = commandsZ[1].(*redis.IntCmd).Result()
		currScore, currScoreErr = commandsZ[2].(*redis.FloatCmd).Result()
	)
	if currRankErr != nil && !errors.Is(currRankErr, redis.Nil) {
		return nil, currRankErr
	}
	if currScoreErr != nil && !errors.Is(currScoreErr, redis.Nil) {
		return nil, currScoreErr
	}
	// Add 1 since Redis Sorted-Set rank starts from 0.
	currRank += 1

	// Read the user information for the top 100 users in a pipeline from multiple Redis Hashes.
	commandsH, err := l.client.Pipelined(ctx, func(pipe redis.Pipeliner) error {
		for idx := range topRanks {
			pipe.HGetAll(ctx, topRanks[idx].Member.(string))
		}
		return nil
	})

	// Construct the response for the current user.
	resp.CurrentUser = model.LeaderboardUser{
		User: model.User{
			ID: userID,
		},
	}
	// The Redis Sorted-Set can potentially store more than constant.LeaderboardMaxRankLimit elements.
	// However, we only want to return the current user rank if it is within the limit.
	// This aligns with the behaviour of previous-week and all-time leaderboards.
	if currRankErr == nil && currRank > 0 {
		resp.CurrentUser.Rank = currRank
	}
	if currScoreErr == nil {
		resp.CurrentUser.Score = currScore
	}

	// Construct the response for top users with rank.
	// This relies on the fact that query response items are sorted DESC.
	var (
		rank         = 1
		prevScoreIdx = 0
		prevScoreVal = float64(0)
	)
	for idx, command := range commandsH {
		u := model.User{}
		if err := command.(*redis.MapStringStringCmd).Scan(&u); err != nil {
			return nil, err
		}
		score := topRanks[idx].Score
		// Initialize 'prevScoreVal' to the first element score value.
		if idx == 0 {
			prevScoreVal = score
		}
		if score != prevScoreVal {
			rank += idx - prevScoreIdx
			prevScoreIdx = idx
			prevScoreVal = score
		}
		resp.TopUsers = append(resp.TopUsers, model.LeaderboardUser{
			User:  u,
			Score: score,
			Rank:  int64(rank),
		})
		// Adjust rank for the current user if the user is in the top rank list to get the correct
		// dense-rank value. If the user is not in the top rank list, we keep the value returned by
		// ZRevRank directly (i.e., currRank), since dense-rank is not necessary in this case.
		if u.ID == userID {
			resp.CurrentUser.Rank = int64(rank)
		}
	}

	return resp, nil
}
