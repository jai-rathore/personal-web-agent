# Personal Web Agent - Frontend

A modern React-based frontend for Jai's personal web agent. Built with TypeScript, Vite, and Tailwind CSS for a responsive and interactive chat experience.

## Features

- **Real-time Chat Interface**: Stream responses using Server-Sent Events
- **Responsive Design**: Optimized for both desktop and mobile devices
- **Modern UI**: Clean, professional design with Tailwind CSS
- **Type Safety**: Full TypeScript support for better development experience
- **Fast Development**: Powered by Vite for instant hot module replacement
- **State Management**: Zustand for simple and effective state management

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling and development
- **Tailwind CSS** for styling
- **Zustand** for state management
- **ESLint** for code quality
- **PostCSS** for CSS processing

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Quick Start

For a quick setup, run the provided installation script:
```bash
./install.sh
```

This will install dependencies and create a `.env` file with default configuration.

### Manual Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create `.env` file with your API configuration:
   ```bash
   echo "VITE_API_BASE=http://localhost:8080" > .env
   ```
   
   Note: If your backend runs on a different port, update the URL accordingly.

3. Start development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:5173](http://localhost:5173) in your browser

   Note: Vite runs on port 5173 by default. The actual port will be displayed in the terminal after starting.

### Build

```bash
npm run build
```

### Lint

```bash
npm run lint
```

## Project Structure

```
src/
├── components/          # React components
│   ├── ChatShell.tsx   # Main chat container
│   ├── Composer.tsx    # Message input component
│   ├── MessageList.tsx # Chat message display
│   ├── ActionCard.tsx  # Meeting confirmation UI
│   ├── GuardrailNotice.tsx # Out-of-scope notice
│   ├── Header.tsx      # Clean header with home icon and contact links
│   ├── Footer.tsx      # Site footer with privacy link
│   └── PrivacyPage.tsx # Privacy policy page
├── lib/
│   └── sse.ts          # Server-sent events client
├── state/
│   └── chatStore.ts    # Zustand store for chat state
├── styles/
│   └── index.css       # Tailwind CSS imports and custom styles
├── types.ts            # TypeScript type definitions
├── App.tsx             # Root application component
└── main.tsx            # Application entry point
```

## State Management

The app uses Zustand for state management with the following key states:

- `idle`: Initial state with centered composer and starter chips
- `chatting`: Active chat with message history and docked composer
- `tool-proposal`: Showing meeting confirmation modal
- `guardrail`: Displaying out-of-scope notice

## API Integration

The frontend communicates with the Go backend via:

- `POST /chat`: SSE streaming chat endpoint
- `POST /actions/create-meeting`: Meeting creation endpoint

Environment variable `VITE_API_BASE` configures the API base URL.

## Features

### Chat Flow

1. **Initial State**: Centered composer with starter chips
2. **First Message**: Transitions to chat view with message history
3. **Loading**: Shows spinning wheel before first token arrives
4. **Streaming**: Progressive text rendering as tokens arrive from Gemini 2.5 Pro
5. **Actions**: Meeting requests provide direct Calendly link
6. **Guardrails**: Out-of-scope requests show helpful notice

### Keyboard Shortcuts

- `Enter`: Send message
- `Shift + Enter`: New line in message
- `⌘K` / `Ctrl+K`: Focus composer

### Meeting Scheduling

1. User requests meeting in natural language
2. AI automatically provides Calendly link for direct booking
3. Link opens https://calendly.com/jairathore/30min for 30-minute meetings
4. No confirmation flow needed - direct scheduling via Calendly

## Deployment

The app is designed to be deployed to static hosting platforms like:

- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

Configure `VITE_API_BASE` environment variable to point to your production API.