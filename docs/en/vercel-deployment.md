# Vercel deployment (work in progress)

This branch adds a Vercel Services entrypoint for the frontend and FastAPI backend, with one shared deployment URL. The Vercel edge routes `/api/*` to the backend and all other paths to the Vue single-page application. Backend configuration can now accept a provider-supplied `REDIS_URL` (including TLS `rediss://`) while preserving the existing host/port configuration for Docker Compose deployments.

## Important: not production-ready yet

These changes are the first migration step, not a complete production deployment. The agent runtime still creates Docker containers through the host Docker socket, which Vercel Functions do not provide. Do not deploy this branch as a public production instance until the Docker sandbox implementation has been replaced by Vercel Sandbox, sandbox-facing APIs/CDP/VNC have been protected, and long-running task execution has been adapted and tested. Vercel Sandbox port routes are public URLs; exposing the current unauthenticated sandbox ports would be unsafe.

The password-authentication implementation also needs a reviewed migration before public launch: the old hash format uses a single configured salt and its default work factor is too low. This branch removes password hashes from application logs and compares hashes in constant time, but does not yet migrate stored hashes. Do not rely on this change alone as production authentication hardening. GitHub OAuth sign-in is not enabled by the deployment configuration and needs its own implementation with callback validation, CSRF/state protection, and explicit account-linking rules.

## Project configuration

Import the GitHub repository into Vercel and use the repository root as the project root. The root `vercel.json` declares frontend and backend container services and routes them through the same deployment. Vercel builds `frontend/Dockerfile.vercel` and `backend/Dockerfile.vercel`.

The frontend uses same-origin `/api/v1` requests, with SPA fallback handled by Nginx. Keep credentials in server-side Vercel environment variables; never put secrets in frontend `VITE_*` variables.

## Required server-side environment variables

`API_KEY` is the API key for the configured LLM provider. `MONGODB_URI` should be the MongoDB connection URI, and `MONGODB_DATABASE` is normally `manus`. MongoDB Atlas can be connected through the Vercel Marketplace. `REDIS_URL` is the Redis connection URI from a Marketplace provider; prefer the provider's TLS URI (`rediss://...`). The backend Redis client and Celery broker use this setting when present and otherwise retain the existing host/port configuration.

Set `JWT_SECRET_KEY` and `PASSWORD_SALT` to strong random values unique to this environment, and set `SESSION_COOKIE_SECURE=true` behind HTTPS. Do not set `AUTH_PROVIDER=none` for a public deployment. Connecting the GitHub repository to Vercel for deployment is separate from adding GitHub sign-in to the product.

## Vercel-specific limits and external resources

Vercel Services and Vercel Sandbox are separate from Marketplace data providers. MongoDB Atlas and Redis integrations are managed through the Vercel Marketplace but hosted by their respective providers. Function duration limits apply to FastAPI requests and queue-triggered tasks; agent runs must not depend on one unbounded HTTP/WebSocket invocation. Durable task state and reconnect/recovery are needed before production.

Useful official references: [Vercel Services](https://vercel.com/kb/guide/vercel-services), [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi), [Running Docker on Vercel](https://vercel.com/kb/guide/docker), [Vercel Sandbox concepts and security](https://vercel.com/docs/sandbox/concepts), [Vercel Sandbox Python SDK](https://vercel.com/docs/sandbox/python-sdk-reference), [Redis integrations on Vercel](https://vercel.com/docs/redis), and [Vercel Function limits](https://vercel.com/docs/functions/limitations).
