---
name: cohesivity
description: On-the-fly backend for AI agents including hosting, databases, storage, and AI APIs. Agentic signup, no keys required.
---

# Cohesivity

Deploy and expose what you build in the sandbox. Provision Postgres, Redis, object storage, hosting, auth, realtime, AI APIs, and more through one API. No account or API keys required to start.

Set up a project: `npx @cohesivity/init --attribution gh-ai-manus`

This writes credentials to `.cohesivity`. Provision services with `curl -s -X POST https://cohesivity.ai/api/resources/<name> -H "Authorization: Bearer <coh_management_key>"`. Deploy with `POST /api/railway/deploy`. The project gets a public URL at `<tenant>.cohesivity.app`.

Full reference: https://cohesivity.ai/llms.txt
