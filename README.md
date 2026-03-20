# Jai's Personal Web Agent

An AI-powered personal website that lets visitors chat with an intelligent agent to learn about Jai Rathore's background, skills, and projects – and lets Jai himself manage his Google Workspace (calendar, mail) through the same interface.

**Live at [jairathore.com](https://jairathore.com)**

---

## Features

- **Interactive AI Chat** – Powered by Google Gemini 3.1 Pro via the ADK framework
- **Real-time Streaming** – Server-Sent Events for smooth, token-by-token responses
- **Meeting Scheduling** – Direct Calendly integration for booking 30-minute meetings
- **Owner Mode** – When Jai signs in with Google, he gets additional workspace tools (calendar, Gmail) powered by the Google Workspace CLI
- **Guardrails** – Multi-layer input validation and prompt injection protection
- **Feedback Form** – Async email delivery via SMTP

---

## Tech Stack

### Frontend
- **React 18** + TypeScript
- **Vite 5** for build tooling
- **Tailwind CSS** for styling
- **Zustand** for state management

### Backend
- **Python 3.12** + **FastAPI** + Uvicorn
- **Google ADK** (`google-adk`) for agent orchestration
- **Gemini 3.1 Pro Preview** as the chat model
- **Google Workspace CLI** (`gws`) for owner calendar/Gmail tools
- **SlowAPI** for rate limiting
- **Pydantic Settings** for configuration

### Infrastructure
| Component | Platform | URL |
|---|---|---|
| Frontend | [Vercel](https://vercel.com) | [jairathore.com](https://jairathore.com) |
| Backend API | [Render](https://render.com) | personal-web-agent.onrender.com |
| Domain / SSL | Vercel / Render | Automatic |
| CI/CD | GitHub Actions | On push to `main` |

---

## Deployment Architecture

```
Push to main branch
        │
        ├─── GitHub Actions CI (ci.yml)
        │         ├── Python tests (pytest)
        │         ├── Frontend type-check + build
        │         └── pip-audit / npm audit
        │
        └─── GitHub Actions Deploy (deploy.yml)
                  │
                  ├── Backend → Render
                  │     Service: personal-web-agent-api
                  │     Runtime: Python 3.12
                  │     Build:   pip install -r requirements.txt
                  │     Start:   uvicorn app.main:app
                  │     Triggered via Render API (RENDER_API_KEY secret)
                  │
                  └── Frontend → Vercel
                        Build:   npm run build (Vite)
                        Output:  web/dist/
                        Triggered via Vercel CLI (VERCEL_TOKEN secret)
```

### Required GitHub Secrets

| Secret | Used for |
|---|---|
| `RENDER_API_KEY` | Trigger Render deployments |
| `RENDER_SERVICE_ID` | ID of the Render backend service |
| `VERCEL_TOKEN` | Vercel CLI authentication |
| `VERCEL_ORG_ID` | Vercel organization |
| `VERCEL_PROJECT_ID` | Vercel project |

### Render Environment Variables

Set these in the Render dashboard for `personal-web-agent-api`:

| Variable | Value |
|---|---|
| `GOOGLE_API_KEY` | Your Gemini API key |
| `GOOGLE_CLIENT_ID` | Google OAuth2 client ID (for owner sign-in) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth2 client secret |
| `SMTP_PASSWORD` | Gmail app password for feedback emails |
| All others | Pre-configured in `render.yaml` |

---

## Project Structure

```
personal-web-agent/
├── api/                        # Python FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app, middleware, lifespan
│   │   ├── config.py           # Pydantic Settings (env vars)
│   │   ├── dependencies.py     # FastAPI dependency injection
│   │   ├── agent/
│   │   │   ├── agent.py        # ADK Agent definition (public + owner modes)
│   │   │   ├── content.py      # Content pack loader
│   │   │   ├── guardrails.py   # Input validation, blocked patterns
│   │   │   └── tools/
│   │   │       ├── public.py   # schedule_calendly_meeting, get_contact_info
│   │   │       └── workspace.py # Google Calendar + Gmail tools (gws CLI)
│   │   ├── routers/
│   │   │   ├── chat.py         # POST /chat – SSE streaming
│   │   │   ├── auth.py         # GET /auth/google, /auth/me, POST /auth/logout
│   │   │   ├── health.py       # GET /healthz, GET /privacy
│   │   │   └── feedback.py     # POST /feedback
│   │   ├── services/
│   │   │   ├── auth_service.py # Google OAuth2 token exchange + JWT sessions
│   │   │   └── email_service.py # Async SMTP for feedback
│   │   └── middleware/
│   │       ├── rate_limit.py   # SlowAPI rate limiter
│   │       └── security.py     # Security headers
│   ├── tests/                  # pytest test suite
│   ├── requirements.txt
│   └── pyproject.toml
├── web/                        # React frontend
│   ├── src/
│   │   ├── components/         # ChatShell, Header (with sign-in), MessageList…
│   │   ├── state/
│   │   │   ├── chatStore.ts    # Zustand chat state
│   │   │   └── authStore.ts    # Zustand auth state
│   │   └── lib/sse.ts          # SSE streaming client
│   └── vercel.json
├── content/
│   ├── packs.json              # Content manifest
│   └── jai_rathore_resume.md   # Resume content fed to the agent
├── .github/workflows/
│   ├── ci.yml                  # Python tests + frontend build
│   └── deploy.yml              # Render + Vercel deploy on push to main
├── Dockerfile                  # Python 3.12 + Node.js (for gws CLI)
├── docker-compose.yml
├── render.yaml                 # Render IaC config
└── Makefile
```

---

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### Setup

```bash
# 1. Clone
git clone https://github.com/jai-rathore/personal-web-agent.git
cd personal-web-agent

# 2. Create backend .env
cp .env.example api/.env
# Edit api/.env – set GOOGLE_API_KEY at minimum

# 3. Install backend deps
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Install frontend deps
cd ../web
npm ci
```

### Running

```bash
# Backend only (from repo root)
make dev-api       # starts uvicorn with --reload on :8080

# Frontend only
make dev-web       # starts Vite on :5173

# Both at once
make dev
```

### Testing

```bash
make test-api      # pytest
make test-web      # tsc + eslint
```

### Docker

```bash
docker-compose up
# API at http://localhost:8080, point your browser at the frontend separately
```

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/healthz` | None | Health + content checksums |
| `GET` | `/privacy` | None | Privacy notice |
| `POST` | `/chat` | Optional cookie | SSE streaming chat |
| `POST` | `/feedback` | None | Submit feedback (email) |
| `GET` | `/auth/google` | None | Start Google OAuth2 login |
| `GET` | `/auth/google/callback` | None | OAuth2 callback, sets cookie |
| `GET` | `/auth/me` | Cookie | Current user info |
| `POST` | `/auth/logout` | Cookie | Clear session cookie |

Interactive API docs (dev only): `http://localhost:8080/docs`

### Chat request format

```json
POST /chat
{ "messages": [{"role": "user", "content": "What does Jai do at Tesla?"}], "sessionId": "optional" }
```

Response is an SSE stream:
```
data: {"type": "connected"}
data: {"type": "text", "role": "assistant", "content": "Jai is a Staff Software Engineer..."}
data: {"type": "tool_call", "role": "assistant", "tool": {"name": "schedule_calendly_meeting", ...}}
```

---

## Owner Mode (Google Workspace)

When Jai signs in with Google (the sign-in button in the header), he gets access to additional workspace tools:

- **Calendar** – list events, create, update, delete
- **Gmail** – list, search, read, send emails

These tools are backed by the [Google Workspace CLI (`gws`)](https://github.com/googleworkspace/cli). To enable this locally:

```bash
# Install gws CLI
make setup-gws

# Authenticate with your Google account
gws auth setup
```

The `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` env vars must be set (from a Google Cloud OAuth2 Web Application credential) for the sign-in flow to work.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini API key from AI Studio |
| `GOOGLE_GENAI_USE_VERTEXAI` | No | Set `TRUE` to use Vertex AI instead |
| `CHAT_MODEL` | No | Defaults to `gemini-3.1-pro-preview` |
| `FAST_MODEL` | No | Defaults to `gemini-3.1-flash-lite-preview` |
| `ALLOWED_ORIGIN` | Yes (prod) | Frontend URL for CORS |
| `GOOGLE_CLIENT_ID` | Optional | Enables Google sign-in / owner mode |
| `GOOGLE_CLIENT_SECRET` | Optional | Enables Google sign-in / owner mode |
| `GOOGLE_REDIRECT_URI` | Optional | OAuth2 callback URL |
| `OWNER_EMAILS` | Optional | Comma-separated emails with workspace access |
| `JWT_SECRET` | Optional | Secret for session tokens (auto-generated if unset) |
| `SMTP_USERNAME` | Optional | Gmail address for feedback emails |
| `SMTP_PASSWORD` | Optional | Gmail app password |

Full list in [`.env.example`](.env.example).

---

## Contact

- **Website**: [jairathore.com](https://jairathore.com)
- **Email**: [jaiadityarathore@gmail.com](mailto:jaiadityarathore@gmail.com)
- **LinkedIn**: [linkedin.com/in/jrathore](https://www.linkedin.com/in/jrathore)
- **X**: [@Jai_A_Rathore](https://x.com/Jai_A_Rathore)

---

*Built by Jai Rathore*
