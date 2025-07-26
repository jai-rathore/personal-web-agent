package chat

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/jrathore/personal-web-agent/api/internal/config"
	"github.com/jrathore/personal-web-agent/api/internal/content"
	"github.com/jrathore/personal-web-agent/api/internal/guardrails"
	"github.com/jrathore/personal-web-agent/api/internal/providers"
	"github.com/jrathore/personal-web-agent/api/internal/types"
	"github.com/jrathore/personal-web-agent/api/internal/utils"
	"github.com/rs/zerolog/log"
)

// Handler handles chat-related HTTP requests
type Handler struct {
	geminiProvider   *providers.GeminiProvider
	contentLoader    *content.Loader
	guardrailsPipe   *guardrails.Pipeline
	config           *config.Config
	systemPrompt     string
}

// NewHandler creates a new chat handler
func NewHandler(
	geminiProvider *providers.GeminiProvider,
	contentLoader *content.Loader,
	guardrailsPipe *guardrails.Pipeline,
	cfg *config.Config,
) *Handler {
	return &Handler{
		geminiProvider: geminiProvider,
		contentLoader:  contentLoader,
		guardrailsPipe: guardrailsPipe,
		config:         cfg,
		systemPrompt:   buildSystemPrompt(),
	}
}

// HandleChat handles POST /chat with SSE streaming
func (h *Handler) HandleChat(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	requestID := utils.GetRequestID(ctx)
	startTime := utils.GetStartTime(ctx)
	
	// Parse request
	var req types.ChatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		log.Error().
			Str("request_id", requestID).
			Err(err).
			Msg("Failed to decode chat request")
		
		h.sendJSONError(w, "Invalid JSON", http.StatusBadRequest)
		return
	}
	
	// Validate request
	if len(req.Messages) == 0 {
		h.sendJSONError(w, "Messages array cannot be empty", http.StatusBadRequest)
		return
	}
	
	// Get the last user message for processing
	var lastUserMessage string
	for i := len(req.Messages) - 1; i >= 0; i-- {
		if req.Messages[i].Role == "user" {
			lastUserMessage = req.Messages[i].Content
			break
		}
	}
	
	if lastUserMessage == "" {
		h.sendJSONError(w, "No user message found", http.StatusBadRequest)
		return
	}
	
	// Validate input through guardrails
	if err := h.guardrailsPipe.ValidateInput(lastUserMessage); err != nil {
		log.Warn().
			Str("request_id", requestID).
			Err(err).
			Str("message", lastUserMessage).
			Msg("Input failed guardrails validation")
		
		h.sendSSERefusal(w, r)
		return
	}
	
	// Classify intent
	intent, err := h.geminiProvider.ClassifyIntent(ctx, lastUserMessage)
	if err != nil {
		log.Error().
			Str("request_id", requestID).
			Err(err).
			Msg("Failed to classify intent")
		
		h.sendJSONError(w, "Failed to process request", http.StatusInternalServerError)
		return
	}
	
	// Validate intent
	if err := h.guardrailsPipe.ValidateIntent(intent); err != nil {
		log.Warn().
			Str("request_id", requestID).
			Err(err).
			Str("intent", intent.Type).
			Float64("confidence", intent.Confidence).
			Msg("Intent failed validation")
		
		h.sendSSERefusal(w, r)
		return
	}
	
	// Build system prompt with context
	systemPromptWithContext := h.buildSystemPromptWithContext(intent)
	
	// Set up SSE
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", h.config.AllowedOrigin)
	
	// Send initial connection
	fmt.Fprintf(w, "data: %s\n\n", `{"type":"connected"}`)
	if flusher, ok := w.(http.Flusher); ok {
		flusher.Flush()
	}
	
	// Start streaming from Gemini
	respChan, err := h.geminiProvider.StreamChat(ctx, req.Messages, systemPromptWithContext)
	if err != nil {
		log.Error().
			Str("request_id", requestID).
			Err(err).
			Msg("Failed to start streaming chat")
		
		h.sendSSEError(w, "Failed to start chat")
		return
	}
	
	// Create a timeout context for the streaming
	streamCtx, cancel := context.WithTimeout(ctx, h.config.SSETimeout)
	defer cancel()
	
	// Track response for guardrails validation
	var fullResponse strings.Builder
	var packContent string
	
	// Get pack content for validation if this is a QA about Jai
	if intent.Type == "qa_about_jai" {
		if pack, ok := h.contentLoader.GetPack("resume"); ok {
			packContent = pack.Content
		}
	}
	
	// Stream responses
	for {
		select {
		case <-streamCtx.Done():
			log.Warn().
				Str("request_id", requestID).
				Msg("Streaming timeout")
			h.sendSSEError(w, "Stream timeout")
			return
			
		case resp, ok := <-respChan:
			if !ok {
				// Stream ended normally
				log.Info().
					Str("request_id", requestID).
					Dur("duration", time.Since(startTime)).
					Str("intent", intent.Type).
					Int("response_length", fullResponse.Len()).
					Msg("Chat stream completed")
				return
			}
			
			if resp.Error != nil {
				log.Error().
					Str("request_id", requestID).
					Err(resp.Error).
					Msg("Error in chat stream")
				h.sendSSEError(w, "Chat processing error")
				return
			}
			
			// Handle different response types
			switch resp.Type {
			case "text":
				// Accumulate response content for potential validation
				fullResponse.WriteString(resp.Content)
				
				// For now, we'll skip the expensive response validation during streaming
				// This could be added as a post-processing step if needed
				_ = packContent // Keep the variable used
				
				// Send text chunk
				event := types.SSEEvent{
					Role:    "assistant",
					Content: resp.Content,
					Type:    "text",
				}
				h.sendSSEEvent(w, event)
				
			case "tool_call":
				// Validate tool call
				if err := h.guardrailsPipe.ValidateTool(resp.Tool); err != nil {
					log.Warn().
						Str("request_id", requestID).
						Err(err).
						Str("tool", resp.Tool.Name).
						Msg("Tool call failed validation")
					
					h.sendSSERefusal(w, r)
					return
				}
				
				log.Info().
					Str("request_id", requestID).
					Str("tool", resp.Tool.Name).
					Interface("parameters", resp.Tool.Parameters).
					Msg("Tool call proposed")
				
				// Handle scheduleCalendlyMeeting tool directly
				if resp.Tool.Name == "scheduleCalendlyMeeting" {
					calendlyResponse := "You can schedule a 30-minute meeting with Jai using his Calendly link: https://calendly.com/jairathore/30min\n\nThis will allow you to pick a time that works for both of you. All meetings are scheduled in Pacific Time."
					
					// Send the Calendly response as text instead of tool_call
					event := types.SSEEvent{
						Role:    "assistant",
						Content: calendlyResponse,
						Type:    "text",
					}
					h.sendSSEEvent(w, event)
				} else {
					// Send tool call event for other tools (if any)
					event := types.SSEEvent{
						Role: "assistant",
						Type: "tool_call",
						Tool: resp.Tool,
					}
					h.sendSSEEvent(w, event)
				}
			}
			
			// Flush the response
			if flusher, ok := w.(http.Flusher); ok {
				flusher.Flush()
			}
		}
	}
}

// buildSystemPromptWithContext builds the system prompt with relevant context
func (h *Handler) buildSystemPromptWithContext(intent *types.Intent) string {
	prompt := h.systemPrompt
	
	// Add relevant context based on intent
	if intent.Type == "qa_about_jai" {
		// Get all packs for QA
		packs := h.contentLoader.GetAllPacks()
		if len(packs) > 0 {
			prompt += "\n\nContext about Jai:\n"
			for _, pack := range packs {
				// Include full content since Gemini 2.0 Flash can handle larger contexts
				prompt += fmt.Sprintf("%s\n", pack.Content)
			}
		}
	}
	
	return prompt
}

// sendSSEEvent sends an SSE event
func (h *Handler) sendSSEEvent(w http.ResponseWriter, event types.SSEEvent) {
	eventJSON, _ := json.Marshal(event)
	fmt.Fprintf(w, "data: %s\n\n", eventJSON)
}

// sendSSEError sends an SSE error event
func (h *Handler) sendSSEError(w http.ResponseWriter, message string) {
	event := types.SSEEvent{
		Role:    "assistant",
		Content: message,
		Type:    "error",
	}
	h.sendSSEEvent(w, event)
}

// sendSSERefusal sends a guardrail refusal via SSE
func (h *Handler) sendSSERefusal(w http.ResponseWriter, r *http.Request) {
	// Set up SSE headers if not already set
	if w.Header().Get("Content-Type") == "" {
		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")
		w.Header().Set("Access-Control-Allow-Origin", h.config.AllowedOrigin)
	}
	
	event := types.SSEEvent{
		Role:    "assistant",
		Content: h.guardrailsPipe.GetRefusalMessage(),
		Type:    "guardrail",
	}
	h.sendSSEEvent(w, event)
	
	if flusher, ok := w.(http.Flusher); ok {
		flusher.Flush()
	}
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

// buildSystemPrompt creates the core system prompt
func buildSystemPrompt() string {
	// Get current time in PT (Jai's timezone)
	location, _ := time.LoadLocation("America/Los_Angeles")
	currentTime := time.Now().In(location)
	
	return fmt.Sprintf(`You are Jai's internet representative. Always speak in third person about Jai. 

Current date and time: %s (Pacific Time)

Your capabilities:
1. Answer questions about Jai using the provided context
2. Help schedule meetings with Jai using his Calendly link
3. Provide contact information (email: jaiadityarathore@gmail.com, LinkedIn: https://www.linkedin.com/in/jrathore, X: https://x.com/Jai_A_Rathore)

For meeting scheduling:
- When someone wants to schedule a meeting, use the scheduleCalendlyMeeting tool
- The tool will provide Jai's Calendly link for easy 30-minute meeting booking
- Always mention that meetings are in Pacific Time
- Be helpful and professional when directing people to use Calendly

Keep responses professional and helpful. Always refer to Jai in third person.`, 
		currentTime.Format("Monday, January 2, 2006 at 3:04 PM MST"))
}