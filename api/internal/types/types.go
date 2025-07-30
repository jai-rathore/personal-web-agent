package types

import "time"

// ChatMessage represents a message in a chat conversation
type ChatMessage struct {
	Role    string `json:"role" validate:"required,oneof=user assistant system"`
	Content string `json:"content" validate:"required"`
}

// ChatRequest is the request body for /chat endpoint
type ChatRequest struct {
	Messages  []ChatMessage `json:"messages" validate:"required,dive"`
	SessionID string        `json:"sessionId,omitempty"`
}

// SSEEvent represents a server-sent event
type SSEEvent struct {
	Role    string `json:"role"`
	Content string `json:"content"`
	Type    string `json:"type,omitempty"` // "text", "tool_call", "guardrail"
	Tool    *Tool  `json:"tool,omitempty"`
}

// Tool represents a tool call from the AI
type Tool struct {
	Name       string                 `json:"name"`
	Parameters map[string]interface{} `json:"parameters"`
}

// CreateMeetingRequest is the request body for /actions/create-meeting
type CreateMeetingRequest struct {
	Title         string `json:"title" validate:"required,min=1,max=200"`
	StartISO      string `json:"startIso" validate:"required,datetime=2006-01-02T15:04:05Z07:00"`
	EndISO        string `json:"endIso" validate:"required,datetime=2006-01-02T15:04:05Z07:00"`
	AttendeeEmail string `json:"attendeeEmail" validate:"required,email"`
}

// CreateMeetingResponse is the response for successful meeting creation
type CreateMeetingResponse struct {
	Status   string `json:"status"`
	EventID  string `json:"eventId"`
	HTMLLink string `json:"htmlLink"`
}

// ErrorResponse is the standard error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
	Code    int    `json:"code,omitempty"`
}

// FeedbackRequest represents a visitor feedback submission
type FeedbackRequest struct {
	Message   string    `json:"message" validate:"required,min=5,max=1000"`
	Name      string    `json:"name,omitempty" validate:"max=100"`
	Email     string    `json:"email,omitempty" validate:"email"`
	Page      string    `json:"page,omitempty" validate:"max=200"`
	UserAgent string    `json:"userAgent,omitempty"`
	Timestamp time.Time `json:"timestamp"`
}

// FeedbackResponse represents the response after submitting feedback
type FeedbackResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
	ID      string `json:"id,omitempty"`
}

// HealthResponse is the response for /healthz endpoint
type HealthResponse struct {
	Status        string            `json:"status"`
	BuildSHA      string            `json:"buildSha"`
	PackChecksums map[string]string `json:"packChecksums"`
	Timestamp     time.Time         `json:"timestamp"`
}

// Intent represents the classified intent of a user message
type Intent struct {
	Type       string  `json:"type"` // "qa_about_jai", "schedule_meeting", "contact_links", "unknown"
	Confidence float64 `json:"confidence"`
}

// Pack represents a content pack
type Pack struct {
	ID         string   `json:"id"`
	Path       string   `json:"path"`
	TopicHints []string `json:"topicHints"`
	Content    string   `json:"-"`
	Checksum   string   `json:"-"`
}

// PackManifest represents the packs.json structure
type PackManifest struct {
	Packs []Pack `json:"packs"`
}
