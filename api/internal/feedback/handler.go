package feedback

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/jrathore/personal-web-agent/api/internal/config"
	"github.com/jrathore/personal-web-agent/api/internal/types"
	"github.com/jrathore/personal-web-agent/api/internal/utils"
	"github.com/rs/zerolog/log"
)

// Handler handles feedback-related HTTP requests
type Handler struct {
	config       *config.Config
	emailService EmailService
}

// EmailService interface for sending emails
type EmailService interface {
	SendFeedbackEmail(ctx context.Context, feedback *types.FeedbackRequest) error
}

// NewHandler creates a new feedback handler
func NewHandler(cfg *config.Config, emailService EmailService) *Handler {
	return &Handler{
		config:       cfg,
		emailService: emailService,
	}
}

// HandleSubmitFeedback handles POST /feedback
func (h *Handler) HandleSubmitFeedback(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	requestID := utils.GetRequestID(ctx)
	startTime := utils.GetStartTime(ctx)

	// Parse request
	var req types.FeedbackRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		log.Error().
			Str("request_id", requestID).
			Err(err).
			Msg("Failed to decode feedback request")

		h.sendJSONError(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Set timestamp and user agent
	req.Timestamp = time.Now()
	req.UserAgent = r.Header.Get("User-Agent")

	// Validate request
	if err := h.validateFeedback(&req); err != nil {
		log.Warn().
			Str("request_id", requestID).
			Err(err).
			Msg("Feedback validation failed")

		h.sendJSONError(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Generate unique ID for this feedback
	feedbackID := fmt.Sprintf("fb_%d_%s", time.Now().Unix(), requestID[:8])

	log.Info().
		Str("request_id", requestID).
		Str("feedback_id", feedbackID).
		Str("name", req.Name).
		Str("email", req.Email).
		Msg("Processing feedback submission")

	// Send email notification
	if err := h.emailService.SendFeedbackEmail(ctx, &req); err != nil {
		log.Error().
			Str("request_id", requestID).
			Str("feedback_id", feedbackID).
			Err(err).
			Msg("Failed to send feedback email")

		// Don't fail the request if email fails - still return success to user
		log.Warn().Msg("Feedback received but email notification failed")
	}

	// Return success response
	response := types.FeedbackResponse{
		Status:  "success",
		Message: "Thank you for your feedback! Jai will review it soon.",
		ID:      feedbackID,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		log.Error().
			Str("request_id", requestID).
			Err(err).
			Msg("Failed to encode feedback response")
	}

	log.Info().
		Str("request_id", requestID).
		Str("feedback_id", feedbackID).
		Dur("duration", time.Since(startTime)).
		Msg("Feedback submitted successfully")
}

// validateFeedback validates the feedback request
func (h *Handler) validateFeedback(req *types.FeedbackRequest) error {
	if len(req.Message) < 5 {
		return fmt.Errorf("message must be at least 5 characters")
	}

	if len(req.Message) > 1000 {
		return fmt.Errorf("message must be less than 1000 characters")
	}

	if req.Name != "" && len(req.Name) > 100 {
		return fmt.Errorf("name must be less than 100 characters")
	}

	return nil
}

// sendJSONError sends a JSON error response
func (h *Handler) sendJSONError(w http.ResponseWriter, message string, statusCode int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)

	response := types.ErrorResponse{
		Error:   http.StatusText(statusCode),
		Message: message,
		Code:    statusCode,
	}

	json.NewEncoder(w).Encode(response)
}
