# Jai's Personal Web Agent API

A Go-based backend API that serves as Jai's internet representative, providing:
- Grounded Q&A about Jai using content from his resume  
- Meeting scheduling via Calendly integration
- Direct contact information
- Guardrails to ensure responses stay within scope

## Features

- **Chat API**: Real-time streaming chat responses via Server-Sent Events (SSE) with loading spinner UX
- **Gemini 2.5 Pro Integration**: Uses Google's Gemini 2.5 Pro API for chat, classification, and tool reasoning
- **Calendly Integration**: Provides direct Calendly links for easy meeting scheduling
- **Content System**: Loads and serves information from resume and other content packs
- **Security**: Rate limiting, CORS, CSP headers, input validation, and guardrails
- **Health Monitoring**: Health check endpoint with pack checksums
- **Privacy Compliant**: Privacy endpoint and minimal data retention

## Architecture

```
api/
├── cmd/server/main.go              # Application entry point
├── internal/
│   ├── config/config.go            # Environment configuration
│   ├── server/                     # HTTP server and middleware
│   │   ├── middleware.go           # Security, logging, rate limiting
│   │   └── routes.go               # Route definitions
│   ├── chat/handler.go             # SSE streaming chat handler with Calendly integration
│   ├── content/loader.go           # Content pack system
│   ├── guardrails/pipeline.go      # Security guardrails
│   ├── providers/                  # External API providers
│   │   └── gemini.go              # Gemini AI client
│   ├── types/types.go              # Data structures
│   └── utils/http.go               # HTTP utilities
├── go.mod                          # Go dependencies
└── go.sum
content/
├── packs.json                      # Content manifest
└── jai_rathore_resume.md           # Jai's resume content
```

## Quick Start

### Prerequisites

- Go 1.21 or later
- Gemini API key (required)
- Node.js 18+ and npm (for frontend)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd personal-web-agent
make init
```

### 2. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Server configuration
PORT=8080
ALLOWED_ORIGIN=http://localhost:3000
ENVIRONMENT=development

# Meeting scheduling uses Calendly (no setup required)
# Direct link: https://calendly.com/jairathore/30min
```

### 3. Add Your Resume Content

Copy your resume to the content directory:

```bash
# Resume file already exists at content/jai_rathore_resume.md
# Edit this file with your resume content
```

### 4. Run the Full Application

#### Backend (API Server)

```bash
# Option 1: Using Make (from project root)
make build && make run

# Option 2: Direct Go commands (from project root)
cd api && go build -o ../bin/server ./cmd/server
cd .. && ./bin/server

# Option 3: From api directory
cd api
cp ../.env .env  # Copy env file to api directory
go run ./cmd/server
```

The backend API will be available at `http://localhost:8080`

#### Frontend (React App)

In a new terminal:

```bash
# Navigate to web directory
cd web

# Install dependencies (first time only)
npm install

# Update .env to point to backend
echo "VITE_API_BASE=http://localhost:8080" > .env

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173` (Vite's default port)

### 5. Verify Everything is Running

```bash
# Check backend health
curl http://localhost:8080/healthz

# Frontend should be accessible at
open http://localhost:5173
```

## API Endpoints

### Chat (SSE Streaming)
```
POST /chat
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "Tell me about Jai's experience"}
  ],
  "sessionId": "optional-session-id"
}

Response: text/event-stream
```

### Meeting Scheduling
Meeting scheduling requests automatically respond with Jai's Calendly link for direct booking:
```
https://calendly.com/jairathore/30min
```

### Health Check
```
GET /healthz

Response:
{
  "status": "healthy",
  "buildSha": "abc123",
  "packChecksums": {"resume": "def456"},
  "timestamp": "2024-01-15T10:00:00Z"
}
```

### Privacy Information
```
GET /privacy

Response:
{
  "title": "Privacy Notice",
  "content": "...",
  "lastUpdated": "2024-01-15"
}
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | `8080` | Server port |
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `ALLOWED_ORIGIN` | No | `http://localhost:3000` | CORS allowed origin (frontend URL) |
| `ENVIRONMENT` | No | `development` | Environment (development/production) |
| `TZ` | No | `America/Los_Angeles` | Timezone |

### Rate Limiting

- Chat endpoint: 60 requests per 5 minutes

## Development

### Commands

```bash
# Install dependencies
make deps

# Build application
make build

# Run application
make run

# Run with auto-reload (requires air)
make dev

# Run tests
make test

# Clean build artifacts
make clean

# Tidy go.mod
make tidy
```

### Docker

```bash
# Build Docker image
make docker-build

# Run with Docker
make docker-run

# Or use docker-compose
docker-compose up
```

### Content Management

Content is managed through the `content/` directory:

- `packs.json`: Defines available content packs
- `jai_rathore_resume.md`: Jai's resume content
- Additional content files can be added and referenced in `packs.json`

## Security Features

- **Input Validation**: Comprehensive input sanitization and validation
- **Rate Limiting**: IP-based rate limiting for all endpoints
- **CORS**: Strict CORS policy for allowed origins
- **CSP Headers**: Content Security Policy headers
- **Guardrails**: Multi-layer filtering to prevent prompt injection and off-topic responses
- **Tool Validation**: Strict validation of AI tool calls
- **Content Validation**: Ensures responses stay grounded in provided content

## Monitoring

### Health Checks

The `/healthz` endpoint provides:
- Service status
- Build SHA for deployment tracking
- Content pack checksums for cache invalidation
- Timestamp

### Logging

Structured JSON logging with:
- Request IDs for tracing
- Performance metrics
- Security events
- Error details

## Production Deployment

### Required Environment Variables

```bash
ENVIRONMENT=production
GEMINI_API_KEY=<your-production-key>
ALLOWED_ORIGIN=<your-frontend-domain>
BUILD_SHA=<deployment-commit-sha>
```

### Security Checklist

- [ ] All API keys stored in secure secret management
- [ ] HTTPS enabled with proper certificates
- [ ] CORS configured for production domain only
- [ ] Rate limits appropriate for expected traffic
- [ ] Monitoring and alerting configured
- [ ] Log retention policies in place

## Troubleshooting

### Common Issues

1. **Build fails**: Ensure Go 1.21+ is installed and `go mod tidy` has been run
2. **Rate limiting too aggressive**: Adjust rate limit environment variables
3. **CORS errors**: Check `ALLOWED_ORIGIN` matches your frontend domain
4. **Meeting scheduling not working**: Calendly link is hard-coded to https://calendly.com/jairathore/30min

### Debug Mode

Set `ENVIRONMENT=development` for:
- Detailed error messages
- More verbose logging
- Relaxed validation (where appropriate)

## License

This project is part of Jai's personal web presence. Please contact for usage permissions.