package providers

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/google/generative-ai-go/genai"
	"github.com/jrathore/personal-web-agent/api/internal/types"
	"github.com/rs/zerolog/log"
	"google.golang.org/api/iterator"
	"google.golang.org/api/option"
)

// GeminiProvider handles interactions with Google's Gemini API
type GeminiProvider struct {
	client *genai.Client
	model  *genai.GenerativeModel
}

// NewGeminiProvider creates a new Gemini provider
func NewGeminiProvider(apiKey string) (*GeminiProvider, error) {
	ctx := context.Background()
	client, err := genai.NewClient(ctx, option.WithAPIKey(apiKey))
	if err != nil {
		return nil, fmt.Errorf("failed to create Gemini client: %w", err)
	}
	
	// Use gemini-2.5-pro
	model := client.GenerativeModel("gemini-2.5-pro")
	
	// Configure model settings - keep it simple
	model.SetTemperature(0.7)
	
	// Define tool schema for scheduleCalendlyMeeting
	model.Tools = []*genai.Tool{
		{
			FunctionDeclarations: []*genai.FunctionDeclaration{
				{
					Name:        "scheduleCalendlyMeeting",
					Description: "Provide Jai's Calendly link for scheduling a 30-minute meeting",
					Parameters: &genai.Schema{
						Type: genai.TypeObject,
						Properties: map[string]*genai.Schema{
							"meetingType": {
								Type:        genai.TypeString,
								Description: "Type of meeting requested (e.g., 'general meeting', 'consultation', 'interview')",
							},
							"requestorName": {
								Type:        genai.TypeString,
								Description: "Name of the person requesting the meeting",
							},
						},
						Required: []string{"meetingType"},
					},
				},
			},
		},
	}
	
	return &GeminiProvider{
		client: client,
		model:  model,
	}, nil
}

// ClassifyIntent classifies the user's intent
func (p *GeminiProvider) ClassifyIntent(ctx context.Context, message string) (*types.Intent, error) {
	// Create a separate model without tools for classification
	classifierModel := p.client.GenerativeModel("gemini-2.5-pro")
	classifierModel.SetTemperature(0.3)
	
	prompt := fmt.Sprintf(`Classify the following user message into one of these intents:
- qa_about_jai: Questions about Jai's background, experience, skills, work, projects
- schedule_meeting: Requests to book, schedule, or arrange meetings with Jai
- contact_links: Requests for contact information, email, phone, LinkedIn
- unknown: Anything else that doesn't fit the above categories

Message: "%s"

Respond with a JSON object: {"type": "intent_type", "confidence": 0.0-1.0}`, message)
	
	resp, err := classifierModel.GenerateContent(ctx, genai.Text(prompt))
	if err != nil {
		return nil, fmt.Errorf("failed to classify intent: %w", err)
	}
	
	// Extract text from response
	var textContent string
	if len(resp.Candidates) == 0 {
		return nil, fmt.Errorf("no candidates in response")
	}
	
	for _, part := range resp.Candidates[0].Content.Parts {
		if text, ok := part.(genai.Text); ok {
			textContent += string(text)
		}
	}
	
	// Parse JSON response
	var intent types.Intent
	textContent = strings.TrimSpace(textContent)
	// Clean up markdown code blocks if present
	textContent = strings.TrimPrefix(textContent, "```json")
	textContent = strings.TrimSuffix(textContent, "```")
	textContent = strings.TrimSpace(textContent)
	
	if err := json.Unmarshal([]byte(textContent), &intent); err != nil {
		log.Warn().Err(err).Str("response", textContent).Msg("Failed to parse intent JSON, defaulting to unknown")
		return &types.Intent{Type: "unknown", Confidence: 0.5}, nil
	}
	
	return &intent, nil
}

// StreamChat handles a streaming chat conversation
func (p *GeminiProvider) StreamChat(ctx context.Context, messages []types.ChatMessage, systemPrompt string) (<-chan StreamResponse, error) {
	// Start chat session with empty history
	session := p.model.StartChat()
	
	// Get the last user message
	var lastUserMessage string
	for i := len(messages) - 1; i >= 0; i-- {
		if messages[i].Role == "user" {
			lastUserMessage = messages[i].Content
			break
		}
	}
	
	// Combine system prompt with user message for proper context
	if systemPrompt != "" && lastUserMessage != "" {
		lastUserMessage = systemPrompt + "\n\nUser: " + lastUserMessage
	}
	
	// Create response channel
	respChan := make(chan StreamResponse)
	
	// Start streaming
	go func() {
		defer close(respChan)
		
		// Log what we're sending
		log.Debug().
			Str("lastUserMessage", lastUserMessage).
			Int("historyLength", len(session.History)).
			Msg("Starting stream with Gemini")
		
		// Use streaming API for real-time token streaming
		stream := session.SendMessageStream(ctx, genai.Text(lastUserMessage))
		
		for {
			response, err := stream.Next()
			if err == iterator.Done {
				break
			}
			if err != nil {
				log.Error().
					Err(err).
					Str("lastUserMessage", lastUserMessage).
					Str("error_details", fmt.Sprintf("%+v", err)).
					Msg("Gemini streaming API error")
				respChan <- StreamResponse{Error: err}
				return
			}
			
			// Process each streaming chunk and send it immediately
			for _, cand := range response.Candidates {
				for _, part := range cand.Content.Parts {
					switch p := part.(type) {
					case genai.Text:
						respChan <- StreamResponse{
							Type:    "text",
							Content: string(p),
						}
					case genai.FunctionCall:
						// Convert parameters to map
						params := make(map[string]interface{})
						if p.Args != nil {
							for k, v := range p.Args {
								params[k] = v
							}
						}
						
						respChan <- StreamResponse{
							Type: "tool_call",
							Tool: &types.Tool{
								Name:       p.Name,
								Parameters: params,
							},
						}
					}
				}
			}
		}
		return

		// Original streaming code (commented out for now)
		/*
		... streaming code removed for brevity ...
		*/
	}()
	
	return respChan, nil
}

// StreamResponse represents a single response from the streaming API
type StreamResponse struct {
	Type    string      // "text" or "tool_call"
	Content string      // For text responses
	Tool    *types.Tool // For tool calls
	Error   error       // For errors
}

// Close closes the Gemini client
func (p *GeminiProvider) Close() error {
	return p.client.Close()
}