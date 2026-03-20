# Personal Web Agent

## What It Is

This site — jairathore.com — is Jai's personal web agent: an AI-powered interface to his professional identity. Rather than a static portfolio, it's a live agent that visitors can talk to, get real answers from, and use to book meetings with Jai.

## Why He Built It

Jai wanted a project that demonstrated what he actually believes about AI: that the right design puts an LLM in the center of the experience with real tools and real context, not as a gimmick but as the primary interface. A personal website as a conversational agent felt like a good canvas for that.

It also gave him an excuse to build something with Google's Agent Development Kit (ADK) end-to-end and explore the cross-domain design decisions that come up in production agentic systems.

## Tech Stack

- **Frontend:** React, TypeScript, Zustand, Tailwind CSS — deployed on Vercel
- **Backend:** Python, FastAPI, Google ADK, Gemini 3.1 Pro — deployed on Render
- **Agent:** Google ADK `Agent` with tool use, SSE streaming, session management
- **Auth:** Google OAuth2 with JWT session cookies (owner vs. visitor access)
- **Content:** File-based content pack system with on-demand knowledge retrieval
- **Workspace:** Google Calendar + Gmail tools via the `gws` CLI (owner-only)

## Key Design Decisions

**Content as tools, not system prompt stuffing:** Rather than dumping everything into the context window upfront, content packs with `visibility: "on_demand"` are retrieved via a `lookup_knowledge` tool only when relevant. This keeps the system prompt lean and lets the agent pull detail on demand.

**Two personas, not one:** The agent behaves differently depending on whether the visitor is authenticated as the owner (Jai). Visitors get a professional third-person representative. Jai gets a casual, proactive assistant with workspace access.

**SSE streaming from day one:** The frontend streams responses token-by-token via Server-Sent Events, giving a responsive feel without WebSocket complexity.

## Repository

https://github.com/jai-rathore/personal-web-agent
