# Vercel 部署（进行中）

此分支为前端和 FastAPI 后端添加了 Vercel Services 入口，并通过同一个部署 URL 对外提供服务。Vercel 将 `/api/*` 路由到后端，其余路径路由到 Vue 单页应用。后端现在可以接受服务商提供的 `REDIS_URL`（包括 TLS `rediss://`），同时保留 Docker Compose 所使用的 host/port 配置。

## 重要：暂不可用于生产

这些改动只是迁移的第一步，并非完整的生产部署。智能体运行时目前仍通过宿主机 Docker socket 创建 Docker 容器，而 Vercel Functions 不提供该 socket。在把 Docker sandbox 替换为 Vercel Sandbox、保护 sandbox API/CDP/VNC 访问并完成长任务执行适配和测试之前，不要将此分支作为公开生产实例部署。Vercel Sandbox 端口路由是公开 URL；直接暴露当前未认证的 sandbox 端口是不安全的。

密码认证也需要在公开上线前完成审查和迁移：现有哈希格式使用单个配置盐值，默认计算强度过低。本分支已停止在应用日志中输出密码哈希，并改用常量时间比较，但尚未迁移已存储的哈希。仅凭这些改动不足以实现生产级认证。该部署配置也没有启用 GitHub OAuth 登录；该功能需要单独实现，并验证回调地址、CSRF/state、防止未经授权的账号关联，并将密钥保存在 Vercel 服务端环境变量中。

## 项目配置

将 GitHub 仓库导入 Vercel，并把仓库根目录设为项目根目录。根目录的 `vercel.json` 声明前端和后端容器服务，并通过同一部署路由请求。Vercel 会构建 `frontend/Dockerfile.vercel` 和 `backend/Dockerfile.vercel`。

前端通过同源 `/api/v1` 访问 API，Nginx 提供 SPA 回退。凭据只应保存在 Vercel 服务端环境变量中，不要放入前端 `VITE_*` 变量。

## 必需的服务端环境变量

`API_KEY` 是所选 LLM 服务商的 API 密钥。`MONGODB_URI` 应为 MongoDB 连接 URI，`MONGODB_DATABASE` 通常为 `manus`。可以通过 Vercel Marketplace 连接 MongoDB Atlas。`REDIS_URL` 是 Marketplace Redis 服务提供的连接 URI；若服务商提供 TLS URI（`rediss://...`），请优先使用。若未设置该变量，后端仍会使用原有 host/port 配置。

请设置只属于此环境的强随机 `JWT_SECRET_KEY` 和 `PASSWORD_SALT`，并在 HTTPS 环境下设置 `SESSION_COOKIE_SECURE=true`。公开部署不要设置 `AUTH_PROVIDER=none`。将 GitHub 仓库连接到 Vercel 进行部署，与在产品中提供“使用 GitHub 登录”是两件不同的事。

## Vercel 限制与外部资源

Vercel Services、Vercel Sandbox 与 Marketplace 数据服务相互独立。MongoDB Atlas 和 Redis 虽可通过 Vercel Marketplace 管理，但实际由各自的服务商托管。FastAPI 请求和队列任务受 Vercel Functions 的执行时长限制。智能体任务不能依赖单个无限期 HTTP/WebSocket 请求；上线前需要实现持久化任务状态、断线重连和故障恢复。

官方参考：[Vercel Services](https://vercel.com/kb/guide/vercel-services)、[Vercel FastAPI](https://vercel.com/docs/frameworks/backend/fastapi)、[Vercel Docker](https://vercel.com/kb/guide/docker)、[Vercel Sandbox 安全说明](https://vercel.com/docs/sandbox/concepts)、[Vercel Sandbox Python SDK](https://vercel.com/docs/sandbox/python-sdk-reference)、[Vercel Redis](https://vercel.com/docs/redis)、[Vercel Functions 限制](https://vercel.com/docs/functions/limitations)。
