package config

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/joho/godotenv"
)

// Config holds all configuration for the application
type Config struct {
	// Server
	Port           string
	AllowedOrigin  string
	Environment    string
	BuildSHA       string
	
	// API Keys
	GeminiAPIKey string
	
	// Rate Limiting
	ChatRateLimit    int           // requests per window
	ChatRateWindow   time.Duration // window duration
	ActionRateLimit  int
	ActionRateWindow time.Duration
	
	// Timeouts
	RequestTimeout time.Duration
	SSETimeout     time.Duration
	
	// Content
	ContentDir string
	
	// Timezone
	Timezone *time.Location
}

// Load loads configuration from environment variables
func Load() (*Config, error) {
	// Load .env file if it exists (for local development)
	_ = godotenv.Load()
	
	// Get timezone
	tzName := getEnv("TZ", "America/Los_Angeles")
	tz, err := time.LoadLocation(tzName)
	if err != nil {
		return nil, fmt.Errorf("invalid timezone %s: %w", tzName, err)
	}
	
	cfg := &Config{
		// Server
		Port:          getEnv("PORT", "8080"),
		AllowedOrigin: getEnv("ALLOWED_ORIGIN", "http://localhost:3000"),
		Environment:   getEnv("ENVIRONMENT", "development"),
		BuildSHA:      getEnv("BUILD_SHA", "local"),
		
		// API Keys
		GeminiAPIKey: getEnv("GEMINI_API_KEY", ""),
		
		// Rate Limiting
		ChatRateLimit:    getEnvInt("CHAT_RATE_LIMIT", 60),
		ChatRateWindow:   getEnvDuration("CHAT_RATE_WINDOW", 5*time.Minute),
		ActionRateLimit:  getEnvInt("ACTION_RATE_LIMIT", 5),
		ActionRateWindow: getEnvDuration("ACTION_RATE_WINDOW", 10*time.Minute),
		
		// Timeouts
		RequestTimeout: getEnvDuration("REQUEST_TIMEOUT", 30*time.Second),
		SSETimeout:     getEnvDuration("SSE_TIMEOUT", 5*time.Minute),
		
		// Content
		ContentDir: getEnv("CONTENT_DIR", "../content"),
		
		// Timezone
		Timezone: tz,
	}
	
	// Validate required fields
	if cfg.GeminiAPIKey == "" {
		return nil, fmt.Errorf("GEMINI_API_KEY is required")
	}
	
	return cfg, nil
}

// getEnv gets an environment variable with a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getEnvInt gets an environment variable as an integer with a default value
func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

// getEnvDuration gets an environment variable as a duration with a default value
func getEnvDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
	}
	return defaultValue
}