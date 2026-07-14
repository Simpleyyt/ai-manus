# AI Manus × Claw Frontend

English | [中文](README_zh.md)

This is the frontend for AI Manus × Claw, built with Vue 3 + TypeScript + Vite.

## Features

- Chat interface with task sessions, plan panel, and SSE event streaming
- Tool panels with rich renderers (Search, Files, Terminal, Browser, MCP)
- VNC viewer for real-time sandbox viewing and takeover
- Login/authentication, session sharing, and file upload/download
- Internationalization (Chinese and English) via vue-i18n
- **Claw page** — integrated [OpenClaw](https://github.com/anthropics/openclaw) chat experience with real-time WebSocket messaging, auto-expiry countdown, and file upload/download

## Installation

Create a `.env.development` file with the following configuration:

```
# Backend address
VITE_API_URL=http://127.0.0.1:8000
```

Alternatively, set `BACKEND_URL` when starting the dev server to enable the Vite `/api` proxy:

```bash
BACKEND_URL=http://localhost:8000 npm run dev
```

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Run unit tests (Vitest)
npm run test

# Type checking (vue-tsc)
npm run type-check

# Lint (ESLint)
npm run lint

# Build production version
npm run build
```

## Docker Deployment

This project supports containerized deployment using Docker:

```bash
# Build Docker image
docker build -t ai-chatbot-vue .

# Run container (map container port 80 to host port 8080)
docker run -d -p 8080:80 ai-chatbot-vue

# Access the application
# Open browser and visit http://localhost:8080
```

## Project Structure

```
src/
├── api/             # API layer (axios client, SSE, auth, files, claw, config)
├── assets/          # Static resources and CSS files
├── components/      # Reusable components
│   ├── toolViews/       # Rich tool renderers (Browser, File, Shell, Search, MCP)
│   ├── filePreviews/    # File preview components
│   ├── login/           # Login-related components
│   ├── settings/        # Settings dialog components
│   ├── icons/           # Icon components
│   └── ui/              # Base UI components (reka-ui based)
├── composables/     # Reusable composition functions (useAgentEvents, useAuth, ...)
├── constants/       # Shared constants
├── lib/             # Utility libraries
├── locales/         # i18n messages (Chinese and English)
├── pages/           # Page components
│   ├── HomePage.vue     # Home page
│   ├── ChatPage.vue     # Chat page
│   ├── ClawPage.vue     # Claw (OpenClaw) page
│   ├── LoginPage.vue    # Login page
│   ├── SharePage.vue    # Shared session page
│   ├── MainLayout.vue   # Main layout
│   └── ShareLayout.vue  # Share layout
├── router/          # Vue Router configuration
├── types/           # TypeScript type definitions
├── utils/           # Utility functions
├── App.vue          # Root component
└── main.ts          # Entry file
```