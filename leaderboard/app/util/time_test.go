package util

import (
	"reflect"
	"testing"
	"time"
)

func TestMondayOfTime(t *testing.T) {
	tests := []struct {
		name string
		ts   time.Time
		want time.Time
	}{
		{
			name: "Monday of 2023-12-25 00:00:00 should return 2023-12-25",
			ts:   time.Date(2023, 12, 25, 0, 0, 0, 0, time.UTC),
			want: time.Date(2023, 12, 25, 0, 0, 0, 0, time.UTC),
		},
		{
			name: "Monday of 2023-12-25 some time should return 2023-12-25",
			ts:   time.Date(2023, 12, 25, 1, 2, 3, 4, time.UTC),
			want: time.Date(2023, 12, 25, 0, 0, 0, 0, time.UTC),
		},
		{
			name: "Monday of 2023-12-28 some time should return 2023-12-25",
			ts:   time.Date(2023, 12, 28, 1, 2, 3, 4, time.UTC),
			want: time.Date(2023, 12, 25, 0, 0, 0, 0, time.UTC),
		},
		{
			name: "Monday of 2023-12-31 23:59:59 should return 2023-12-25",
			ts:   time.Date(2023, 12, 31, 23, 59, 59, 999999999, time.UTC),
			want: time.Date(2023, 12, 25, 0, 0, 0, 0, time.UTC),
		},
		{
			name: "Monday of 2024-01-01 00:00:00 should return 2024-01-01",
			ts:   time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
			want: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		},
		{
			name: "Monday of 2024-01-01 some time should return 2024-01-01",
			ts:   time.Date(2024, 1, 1, 1, 2, 3, 4, time.UTC),
			want: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := MondayOfTime(tt.ts); !reflect.DeepEqual(got, tt.want) {
				t.Errorf("MondayOfTime() = %v, want %v", got, tt.want)
			}
		})
	}
}
