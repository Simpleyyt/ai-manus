# 📅 Development Roadmap

> Ongoing: Deploy & Expose, multi-cluster deployment, enterprise sandbox security

## Claw (Manus × Claw)

 * [x] Integrated [OpenClaw](https://github.com/anthropics/openclaw) AI assistant
 * [x] One-click deployment with per-user isolated containers
 * [x] Auto-expiry countdown
 * [x] Full chat history (MongoDB + OpenClaw session merge)
 * [x] File upload and download
 * [x] OpenAI-compatible LLM proxy

## Tools

 * [x] Support browser takeover
 * [x] Support external MCP tool integration
 * [ ] Support Deploy & Expose tools

## User Authentication

 * [x] Support multi-user

## Deployment

 * [x] Support Docker Compose deployment
 * [ ] Support Docker Swarm / K8s multi-cluster deployment

## UI

 * [x] Support settings
 * [ ] Support timeline playback

## Task Sessions

 * [x] Support sharing

## Agent / Context Engineering

 * [x] Native structured output tools (`create_plan` / `complete_step`, etc.)
 * [x] Composable system prompts (assembled from bound toolkits)
 * [x] Token-aware memory compaction

## Infrastructure

 * [ ] Support Windows & mobile access
 * [x] Support Bing, Google, Tavily, Serper and other search providers
 * [x] Support Celery task backend (`TASK_BACKEND=celery`)
 * [ ] Support Alibaba Cloud and other file storage providers
 * [ ] Support e2b and other sandbox providers
 * [ ] Support mem0 memory providers
 * [ ] Enterprise-level security construction for sandbox
