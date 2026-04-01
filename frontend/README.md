# AI Manus × Claw Frontend

English | [中文](README_zh.md)

This is the frontend for AI Manus × Claw, built with Vue 3 + TypeScript + Vite.

## Features

- Chat interface with task sessions
- Tool panels (Search, Files, Terminal, Browser)
- **Claw page** — integrated [OpenClaw](https://github.com/anthropics/openclaw) chat experience with real-time WebSocket messaging, auto-expiry countdown, and file upload/download

## Installation

Create a `.env.development` file with the following configuration:

```
# Backend address
VITE_API_URL=http://127.0.0.1:8000
```

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

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
├── assets/          # Static resources and CSS files
├── components/      # Reusable components
│   ├── ChatInput.vue    # Chat input component
│   ├── ChatMessage.vue  # Chat message component
│   ├── Sidebar.vue      # Sidebar component
│   ├── ToolPanel.vue    # Tool panel component
│   └── ui/              # UI components
├── pages/           # Page components
│   ├── ChatPage.vue     # Chat page
│   └── HomePage.vue     # Home page
├── App.vue          # Root component
├── main.ts          # Entry file
└── index.css        # Global styles
``` 