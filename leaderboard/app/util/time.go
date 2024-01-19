package util

import (
	"time"
)

// MondayOfTime returns the Monday of the week of the given time.
func MondayOfTime(ts time.Time) time.Time {
	tt := ts.UTC()
	weekday := tt.Weekday()
	if weekday == time.Monday {
		return tt.Truncate(24 * time.Hour)
	}
	daysToSubtract := (weekday - time.Monday + 7) % 7
	return tt.AddDate(0, 0, -int(daysToSubtract)).Truncate(24 * time.Hour)
}

// MondayOfTimeStr returns the Monday of the week of the given time in string format.
func MondayOfTimeStr(ts time.Time) string {
	return MondayOfTime(ts).Format("2006_01_02")
}
