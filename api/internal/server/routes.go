package server

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/gorilla/mux"
	"github.com/jrathore/personal-web-agent/api/internal/chat"
	"github.com/jrathore/personal-web-agent/api/internal/config"
	"github.com/jrathore/personal-web-agent/api/internal/content"
	"github.com/jrathore/personal-web-agent/api/internal/feedback"
	"github.com/jrathore/personal-web-agent/api/internal/types"
	"github.com/ulule/limiter/v3"
)

// Server holds all the handlers and dependencies
type Server struct {
	config          *config.Config
	contentLoader   *content.Loader
	chatHandler     *chat.Handler
	feedbackHandler *feedback.Handler
	router          *mux.Router
}

// NewServer creates a new HTTP server
func NewServer(
	cfg *config.Config,
	contentLoader *content.Loader,
	chatHandler *chat.Handler,
	feedbackHandler *feedback.Handler,
) *Server {
	s := &Server{
		config:          cfg,
		contentLoader:   contentLoader,
		chatHandler:     chatHandler,
		feedbackHandler: feedbackHandler,
		router:          mux.NewRouter(),
	}

	s.setupRoutes()
	return s
}

// setupRoutes configures all the routes
func (s *Server) setupRoutes() {

	// Health check endpoint (no rate limiting)
	s.router.HandleFunc("/healthz", s.handleHealth).Methods("GET")

	// Privacy endpoint (no rate limiting)
	s.router.HandleFunc("/privacy", s.handlePrivacy).Methods("GET")

	// Chat endpoint with rate limiting
	chatRouter := s.router.PathPrefix("/chat").Subrouter()
	chatRouter.Use(RateLimitMiddleware(limiter.Rate{
		Period: s.config.ChatRateWindow,
		Limit:  int64(s.config.ChatRateLimit),
	}, s.config.ChatRateLimit))
	chatRouter.HandleFunc("", s.chatHandler.HandleChat).Methods("POST")

	// Feedback endpoint with rate limiting
	feedbackRouter := s.router.PathPrefix("/feedback").Subrouter()
	feedbackRouter.Use(RateLimitMiddleware(limiter.Rate{
		Period: s.config.ActionRateWindow,
		Limit:  int64(s.config.ActionRateLimit),
	}, s.config.ActionRateLimit))
	feedbackRouter.HandleFunc("", s.feedbackHandler.HandleSubmitFeedback).Methods("POST")

	// CORS preflight for all routes
	s.router.Methods("OPTIONS").HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})
}

// GetRouter returns the configured router
func (s *Server) GetRouter() *mux.Router {
	return s.router
}

// handleHealth handles GET /healthz
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	response := types.HealthResponse{
		Status:        "healthy",
		BuildSHA:      s.config.BuildSHA,
		PackChecksums: s.contentLoader.GetChecksums(),
		Timestamp:     time.Now(),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// handlePrivacy handles GET /privacy
func (s *Server) handlePrivacy(w http.ResponseWriter, r *http.Request) {
	privacyContent := buildPrivacyContent()

	// Return as JSON for API consistency
	response := map[string]interface{}{
		"title":       "Privacy Notice",
		"content":     privacyContent,
		"lastUpdated": time.Now().Format("2006-01-02"),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// buildPrivacyContent creates the privacy notice content
func buildPrivacyContent() string {
	return `# Privacy Notice

## Data Collection
- We log IP addresses for security and rate limiting purposes
- Chat messages are processed by AI services but are not stored persistently
- No cookies or persistent tracking mechanisms are used
- No personal information is retained beyond temporary processing

## Data Processing
- Your messages are sent to Google's Gemini AI service for processing
- Meeting scheduling requests result in providing a Calendly link for direct booking
- All data processing follows the principle of minimal data collection

## Data Retention
- Access logs are retained for up to 30 days for security purposes
- Chat conversations are not stored after processing
- Meeting scheduling is handled entirely through Calendly (no data stored by this service)

## Your Rights
- You can request deletion of any logged data by contacting us
- You have the right to know what data we process
- You can opt out of using this service at any time

## Third-Party Services
This service integrates with:
- Google Gemini AI (for chat processing)
- Calendly (for meeting scheduling links)

Please review their respective privacy policies for how they handle data.

## Contact
For privacy-related inquiries or data deletion requests, contact: jaiadityarathore@gmail.com

Last updated: ` + time.Now().Format("January 2, 2006")
}
