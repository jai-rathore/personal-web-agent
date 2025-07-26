package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/jrathore/personal-web-agent/api/internal/chat"
	"github.com/jrathore/personal-web-agent/api/internal/config"
	"github.com/jrathore/personal-web-agent/api/internal/content"
	"github.com/jrathore/personal-web-agent/api/internal/guardrails"
	"github.com/jrathore/personal-web-agent/api/internal/providers"
	"github.com/jrathore/personal-web-agent/api/internal/server"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

func main() {
	// Configure logging
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr, TimeFormat: time.RFC3339})
	zerolog.SetGlobalLevel(zerolog.InfoLevel)
	
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to load configuration")
	}
	
	log.Info().
		Str("port", cfg.Port).
		Str("environment", cfg.Environment).
		Str("build_sha", cfg.BuildSHA).
		Str("timezone", cfg.Timezone.String()).
		Msg("Starting Jai's Personal Web Agent API")
	
	// Initialize content loader
	contentLoader := content.NewLoader(cfg.ContentDir)
	if err := contentLoader.Load(); err != nil {
		log.Fatal().Err(err).Msg("Failed to load content packs")
	}
	
	// Initialize Gemini provider
	geminiProvider, err := providers.NewGeminiProvider(cfg.GeminiAPIKey)
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to initialize Gemini provider")
	}
	defer geminiProvider.Close()
	
	// Initialize guardrails pipeline
	guardrailsPipe := guardrails.NewPipeline()
	
	// Initialize handlers
	chatHandler := chat.NewHandler(geminiProvider, contentLoader, guardrailsPipe, cfg)
	
	// Initialize HTTP server  
	webServer := server.NewServer(cfg, contentLoader, chatHandler)
	
	// Set up middleware chain
	handler := server.RecoveryMiddleware(
		server.RequestIDMiddleware(
			server.LoggingMiddleware(
				server.TimeoutMiddleware(cfg.RequestTimeout)(
					server.SecurityHeadersMiddleware(cfg)(
						server.CORSMiddleware(cfg).Handler(
							webServer.GetRouter(),
						),
					),
				),
			),
		),
	)
	
	// Create HTTP server
	httpServer := &http.Server{
		Addr:           ":" + cfg.Port,
		Handler:        handler,
		ReadTimeout:    30 * time.Second,
		WriteTimeout:   60 * time.Second, // Longer for SSE
		IdleTimeout:    120 * time.Second,
		MaxHeaderBytes: 1 << 20, // 1MB
	}
	
	// Start server in a goroutine
	go func() {
		log.Info().Str("addr", httpServer.Addr).Msg("Starting HTTP server")
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal().Err(err).Msg("Failed to start HTTP server")
		}
	}()
	
	// Wait for interrupt signal to gracefully shutdown the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	
	log.Info().Msg("Shutting down server...")
	
	// Give outstanding requests 30 seconds to complete
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	
	if err := httpServer.Shutdown(ctx); err != nil {
		log.Error().Err(err).Msg("Server forced to shutdown")
	} else {
		log.Info().Msg("Server exited gracefully")
	}
}