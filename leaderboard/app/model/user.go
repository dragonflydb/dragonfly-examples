package model

type User struct {
	ID       string `json:"id" redis:"id"`
	Email    string `json:"email,omitempty" redis:"email"`
	NickName string `json:"nick_name,omitempty" redis:"nick_name"`
	ImageURL string `json:"image_url,omitempty" redis:"image_url"`
}

type UserIncreaseScoreRequest struct {
	User  `json:",inline"`
	Score float64 `json:"score"`
}

type LeaderboardUser struct {
	User  `json:",inline"`
	Score float64 `json:"score"`
	Rank  int64   `json:"rank"`
}

type LeaderboardResponse struct {
	TopUsers    []LeaderboardUser `json:"topUsers"`
	CurrentUser LeaderboardUser   `json:"currentUser"`
}
