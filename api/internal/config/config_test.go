package config

import (
	"os"
	"testing"
	"time"
)

func TestLoad(t *testing.T) {
	// Set required environment variables
	os.Setenv("GEMINI_API_KEY", "test-key")
	defer os.Unsetenv("GEMINI_API_KEY")
	
	cfg, err := Load()
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}
	
	// Test default values
	if cfg.Port != "8080" {
		t.Errorf("Expected port 8080, got %s", cfg.Port)
	}
	
	if cfg.GeminiAPIKey != "test-key" {
		t.Errorf("Expected GeminiAPIKey to be 'test-key', got %s", cfg.GeminiAPIKey)
	}
	
	if cfg.ChatRateLimit != 60 {
		t.Errorf("Expected ChatRateLimit 60, got %d", cfg.ChatRateLimit)
	}
	
	if cfg.ChatRateWindow != 5*time.Minute {
		t.Errorf("Expected ChatRateWindow 5m, got %v", cfg.ChatRateWindow)
	}
}

func TestLoadMissingAPIKey(t *testing.T) {
	// Ensure API key is not set
	os.Unsetenv("GEMINI_API_KEY")
	
	_, err := Load()
	if err == nil {
		t.Fatal("Expected error for missing GEMINI_API_KEY, got nil")
	}
}