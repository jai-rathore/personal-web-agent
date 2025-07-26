package utils

import (
	"context"
	"time"
)

// contextKey is used for context keys to avoid collisions
type contextKey string

const (
	RequestIDKey contextKey = "requestId"
	StartTimeKey contextKey = "startTime"
)

// GetRequestID extracts request ID from context
func GetRequestID(ctx context.Context) string {
	if id, ok := ctx.Value(RequestIDKey).(string); ok {
		return id
	}
	return ""
}

// GetStartTime extracts start time from context
func GetStartTime(ctx context.Context) time.Time {
	if t, ok := ctx.Value(StartTimeKey).(time.Time); ok {
		return t
	}
	return time.Now()
}