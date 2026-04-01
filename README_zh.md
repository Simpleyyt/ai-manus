# AI Manus × Claw

[English](README.md) | 中文 | [官方网站](https://ai-manus.com) | [文档](https://docs.ai-manus.com)

[![GitHub stars](https://img.shields.io/github/stars/simpleyyt/ai-manus?style=social)](https://github.com/simpleyyt/ai-manus/stargazers)
&ensp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI Manus 是一个通用的 AI Agent 系统，支持在沙盒环境中运行各种工具和操作。现已深度集成 **Claw** —— 基于 [OpenClaw](https://github.com/anthropics/openclaw) 的 AI 助手，一键部署、用户隔离容器、无缝聊天历史，为 Manus 生态带来全新体验。

用 AI Manus × Claw 开启你的智能体之旅吧！

👏 欢迎加入 [QQ群(1005477581)](https://qun.qq.com/universal-share/share?ac=1&authKey=p4X3Da5iMpR4liAenxwvhs7IValPKiCFtUevRlJouz9qSTSZsMnPJc3hzsJjgQYv&busi_data=eyJncm91cENvZGUiOiIxMDA1NDc3NTgxIiwidG9rZW4iOiJNZmUrTmQ0UzNDZDNqNDFVdjVPS1VCRkJGRWVlV0R3RFJSRVFoZDAwRjFDeUdUM0t6aUIyczlVdzRjV1BYN09IIiwidWluIjoiMzQyMjExODE1In0%3D&data=C3B-E6BlEbailV32co77iXL5vxPIhtD9y_itWLSq50hKqosO_55_isOZym2Faaq4hs9-517tUY8GSWaDwPom-A&svctype=4&tempid=h5_group_info)

❤️ 喜欢 AI Manus? 点亮小星星 🌟 或 [赞助开发者](docs/sponsor.md)! ❤️

🚀 [Demo 演示](https://app.ai-manus.com)

📝 [博客：我也复刻了一个 Manus，带高仿 WebUI 和沙盒](https://simpleyyt.com/2026/03/07/rebuild-manus-with-webui-and-sandbox/)

## 示例

### 基本功能

https://github.com/user-attachments/assets/37060a09-c647-4bcb-920c-959f7fa73ebe

### Browser Use

* 任务：llm 最新论文

https://github.com/user-attachments/assets/8f7788a4-fbda-49f5-b836-949a607c64ac

### Code Use

* 任务：写一个复杂的 python 示例

https://github.com/user-attachments/assets/5cb2240b-0984-4db0-8818-a24f81624b04


## 主要特性

 * 部署：最小只需要一个 LLM 服务即可完成部署，不需要依赖其它外部服务。
 * 工具：支持 Terminal、Browser、File、Web Search、消息工具，并支持实查看和接管，支持外部 MCP 工具集成。
 * Claw：集成 [OpenClaw](https://github.com/anthropics/openclaw) AI 助手，一键部署、用户隔离容器、自动过期倒计时、完整聊天历史。
 * 沙盒：每个 Task 会分配单独的一个沙盒，沙盒在本地 Dock 环境里面运行。
 * 任务会话：通过 Mongo/Redis 对会话历史进行管理，支持后台任务。
 * 对话：支持停止与打断，支持文件上传与下载。
 * 多语言：支持中文与英文。
 * 认证：用户登录与认证。

## 开发计划

 * 工具：支持 Deploy & Expose。
 * 沙盒：支持手机与 Windows 电脑接入。
 * 部署：支持 K8s 和 Dock Swarm 多集群部署。

## 环境要求

本项目主要依赖Docker进行开发与部署，需要安装较新版本的Docker：
- Docker 20.10+
- Docker Compose

模型能力要求：
- 支持 LangChain Chat Model（默认 `openai` 提供商）
- 支持FunctionCall
- 支持Json Format输出

推荐使用Deepseek与GPT模型。


## 部署指南

推荐使用Docker Compose进行部署：

<!-- docker-compose-example.yml -->
```yaml
services:
  frontend:
    image: simpleyyt/manus-frontend
    ports:
      - "5173:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - manus-network
    environment:
      - BACKEND_URL=http://backend:8000

  backend:
    image: simpleyyt/manus-backend
    depends_on:
      - sandbox
      - claw
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      #- ./mcp.json:/etc/mcp.json # Mount MCP servers directory
    networks:
      - manus-network
    environment:
      # OpenAI API base URL
      - API_BASE=https://api.openai.com/v1
      # OpenAI API key, replace with your own
      - API_KEY=sk-xxxx
      # LLM model name
      - MODEL_NAME=gpt-4o
      # LLM model provider
      - MODEL_PROVIDER=openai
      # LLM temperature parameter, controls randomness
      - TEMPERATURE=0.7
      # Maximum tokens for LLM response
      - MAX_TOKENS=2000

      # MongoDB connection URI
      #- MONGODB_URI=mongodb://mongodb:27017
      # MongoDB database name
      #- MONGODB_DATABASE=manus
      # MongoDB username (optional)
      #- MONGODB_USERNAME=
      # MongoDB password (optional)
      #- MONGODB_PASSWORD=

      # Redis server hostname
      #- REDIS_HOST=redis
      # Redis server port
      #- REDIS_PORT=6379
      # Redis database number
      #- REDIS_DB=0
      # Redis password (optional)
      #- REDIS_PASSWORD=

      # Sandbox server address (optional)
      #- SANDBOX_ADDRESS=
      # Docker image used for the sandbox
      - SANDBOX_IMAGE=simpleyyt/manus-sandbox
      # Prefix for sandbox container names
      - SANDBOX_NAME_PREFIX=sandbox
      # Time-to-live for sandbox containers in minutes
      - SANDBOX_TTL_MINUTES=30
      # Docker network for sandbox containers
      - SANDBOX_NETWORK=manus-network
      # Chrome browser arguments for sandbox (optional)
      #- SANDBOX_CHROME_ARGS=
      # HTTPS proxy for sandbox (optional)
      #- SANDBOX_HTTPS_PROXY=
      # HTTP proxy for sandbox (optional)
      #- SANDBOX_HTTP_PROXY=
      # No proxy hosts for sandbox (optional)
      #- SANDBOX_NO_PROXY=
      
      # Claw (OpenClaw) configuration
      # Enable or disable Claw feature (hides sidebar entry when false)
      #- CLAW_ENABLED=true
      # Docker image used for Claw containers
      #- CLAW_IMAGE=manus-claw:latest
      # Prefix for Claw container names
      #- CLAW_NAME_PREFIX=manus-claw
      # Time-to-live for Claw containers in seconds (0 = unlimited)
      #- CLAW_TTL_SECONDS=3600
      # Docker network for Claw containers
      #- CLAW_NETWORK=manus-network
      # Max seconds to wait for Claw container to become ready (default 5 minutes)
      #- CLAW_READY_TIMEOUT=300
      # Backend API URL used by Claw containers for callbacks
      #- MANUS_API_BASE_URL=http://backend:8000

      # Search engine configuration
      # Options: baidu, google, bing, bing_web, tavily
      - SEARCH_PROVIDER=bing_web

      # Bing search configuration, only used when SEARCH_PROVIDER=bing
      #- BING_SEARCH_API_KEY=

      # Google search configuration, only used when SEARCH_PROVIDER=google
      #- GOOGLE_SEARCH_API_KEY=
      #- GOOGLE_SEARCH_ENGINE_ID=

      # Tavily search configuration, only used when SEARCH_PROVIDER=tavily
      #- TAVILY_API_KEY=

      # Auth configuration
      # Options: password, none, local
      - AUTH_PROVIDER=password

      # Password auth configuration, only used when AUTH_PROVIDER=password
      - PASSWORD_SALT=
      - PASSWORD_HASH_ROUNDS=10

      # Local auth configuration, only used when AUTH_PROVIDER=local
      #- LOCAL_AUTH_EMAIL=admin@example.com
      #- LOCAL_AUTH_PASSWORD=admin

      # JWT configuration
      - JWT_SECRET_KEY=your-secret-key-here
      - JWT_ALGORITHM=HS256
      - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
      - JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

      # Email configuration
      # Only used when AUTH_PROVIDER=password
      #- EMAIL_HOST=smtp.gmail.com
      #- EMAIL_PORT=587
      #- EMAIL_USERNAME=your-email@gmail.com
      #- EMAIL_PASSWORD=your-password
      #- EMAIL_FROM=your-email@gmail.com

      # MCP configuration file path
      #- MCP_CONFIG_PATH=/etc/mcp.json

      # Application log level
      - LOG_LEVEL=INFO

  sandbox:
    image: simpleyyt/manus-sandbox
    command: /bin/sh -c "exit 0"  # prevent sandbox from starting, ensure image is pulled
    restart: "no"
    networks:
      - manus-network

  claw:
    image: simpleyyt/manus-claw
    command: /bin/sh -c "exit 0"  # prevent claw from starting, ensure image is pulled
    restart: "no"
    networks:
      - manus-network

  mongodb:
    image: mongo:7.0
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped
    #ports:
    #  - "27017:27017"
    networks:
      - manus-network

  redis:
    image: redis:7.0
    restart: unless-stopped
    networks:
      - manus-network

volumes:
  mongodb_data:
    name: manus-mongodb-data

networks:
  manus-network:
    name: manus-network
    driver: bridge
```
<!-- /docker-compose-example.yml -->

保存成`docker-compose.yml`文件，并运行

```shell
docker compose up -d
```

> 注意：如果提示`sandbox-1 exited with code 0`，这是正常的，这是为了让 sandbox 镜像成功拉取到本地。

打开浏览器访问<http://localhost:5173>即可访问 Manus。

## 开发指南

### 项目结构

本项目由四个独立的子项目组成：

* `frontend`: Manus 前端
* `backend`: Manus 后端
* `sandbox`: Manus 沙盒
* `claw`: Manus Claw —— OpenClaw 插件与容器镜像，桥接 OpenClaw Gateway 与 Manus 后端

### 整体设计

![Image](https://github.com/user-attachments/assets/69775011-1eb7-452f-adaf-cd6603a4dde5)

**当用户发起对话时：**

1. Web 向 Server 发送创建 Agent 请求，Server 通过`/var/run/docker.sock`创建出 Sandbox，并返回会话 ID。
2. Sandbox 是一个 Ubuntu Docker 环境，里面会启动 chrome 浏览器及 File/Shell 等工具的 API 服务。
3. Web 往会话 ID 中发送用户消息，Server 收到用户消息后，将消息发送给 PlanAct Agent 处理。
4. PlanAct Agent 处理过程中会调用相关工具完成任务。
5. Agent 处理过程中产生的所有事件通过 SSE 发回 Web。

**当用户浏览工具时：**

- 浏览器：
    1. Sandbox 的无头浏览器通过 xvfb 与 x11vnc 启动了 vnc 服务，并且通过 websockify 将 vnc 转化成 websocket。
    2. Web 的 NoVNC 组件通过 Server 的 Websocket Forward 转发到 Sandbox，实现浏览器查看。
- 其它工具：其它工具原理也是差不多。

### 环境准备

1. 下载项目：
```bash
git clone https://github.com/simpleyyt/ai-manus.git
cd ai-manus
```

2. 复制配置文件：
```bash
cp .env.example .env
```

3. 修改配置文件：

<!-- .env.example -->
```env
# Model provider configuration
API_KEY=
API_BASE=http://mockserver:8090/v1

# Model configuration
MODEL_NAME=deepseek-chat
MODEL_PROVIDER=openai
TEMPERATURE=0.7
MAX_TOKENS=2000

# MongoDB configuration
#MONGODB_URI=mongodb://mongodb:27017
#MONGODB_DATABASE=manus
#MONGODB_USERNAME=
#MONGODB_PASSWORD=

# Redis configuration
#REDIS_HOST=redis
#REDIS_PORT=6379
#REDIS_DB=0
#REDIS_PASSWORD=

# Sandbox configuration
#SANDBOX_ADDRESS=
SANDBOX_IMAGE=simpleyyt/manus-sandbox
SANDBOX_NAME_PREFIX=sandbox
SANDBOX_TTL_MINUTES=30
SANDBOX_NETWORK=manus-network
#SANDBOX_CHROME_ARGS=
#SANDBOX_HTTPS_PROXY=
#SANDBOX_HTTP_PROXY=
#SANDBOX_NO_PROXY=

# Claw (OpenClaw) configuration
# Enable or disable Claw feature (hides sidebar entry when false)
#CLAW_ENABLED=true
# Docker image used for Claw containers
#CLAW_IMAGE=simpleyyt/manus-claw
# Prefix for Claw container names
#CLAW_NAME_PREFIX=manus-claw
# Time-to-live for Claw containers in seconds (0 = unlimited)
#CLAW_TTL_SECONDS=3600
# Docker network bridge name for Claw containers
#CLAW_NETWORK=manus-network
# Max seconds to wait for Claw container to become ready
#CLAW_READY_TIMEOUT=300
# Fixed Claw address (for development; skips Docker container creation)
#CLAW_ADDRESS=
# Static API key for Claw (for development / fixed container)
#CLAW_API_KEY=
# Backend API URL used by Claw containers for callbacks
#MANUS_API_BASE_URL=http://backend:8000

# Search engine configuration
# Options: baidu, baidu_web, google, bing, bing_web, tavily
SEARCH_PROVIDER=bing_web

# Baidu search configuration, only used when SEARCH_PROVIDER=baidu
#BAIDU_SEARCH_API_KEY=

# Bing search configuration, only used when SEARCH_PROVIDER=bing
#BING_SEARCH_API_KEY=

# Google search configuration, only used when SEARCH_PROVIDER=google
#GOOGLE_SEARCH_API_KEY=
#GOOGLE_SEARCH_ENGINE_ID=

# Tavily search configuration, only used when SEARCH_PROVIDER=tavily
#TAVILY_API_KEY=

# Auth configuration
# Options: password, none, local
AUTH_PROVIDER=password

# Password auth configuration, only used when AUTH_PROVIDER=password
PASSWORD_SALT=
PASSWORD_HASH_ROUNDS=10

# Local auth configuration, only used when AUTH_PROVIDER=local
#LOCAL_AUTH_EMAIL=admin@example.com
#LOCAL_AUTH_PASSWORD=admin

# JWT configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email configuration
# Only used when AUTH_PROVIDER=password
#EMAIL_HOST=smtp.gmail.com
#EMAIL_PORT=587
#EMAIL_USERNAME=your-email@gmail.com
#EMAIL_PASSWORD=your-password
#EMAIL_FROM=your-email@gmail.com

# Extra headers for LLM API requests (JSON format)
#EXTRA_HEADERS={"X-Custom-Header": "value"}

# MCP configuration
#MCP_CONFIG_PATH=/etc/mcp.json

# Log configuration
LOG_LEVEL=INFO
```
<!-- /.env.example -->

### 开发调试

1. 运行调试：
```bash
# 相当于 docker compose -f docker-compose-development.yaml up
./dev.sh up
```

各服务会以 reload 模式运行，代码改动会自动重新加载。暴露的端口如下：
- 5173: Web前端端口
- 8000: Server API服务端口
- 8080: Sandbox API服务端口
- 5900: Sandbox VNC端口
- 9222: Sandbox Chrome浏览器CDP端口

> *注意：在 Debug 模式全局只会启动一个沙盒*

2. 当依赖变化时（`backend/pyproject.toml` 或 `frontend/package.json`），清理并重新构建：
```bash
# 清理所有相关资源
./dev.sh down -v

# 重新构建镜像
./dev.sh build

# 调试运行
./dev.sh up
```

### 镜像发布

```bash
export IMAGE_REGISTRY=your-registry-url
export IMAGE_TAG=latest

# 构建镜像
./run build

# 推送到相应的镜像仓库
./run push
```

## ⭐️ Star 记录

[![Star History Chart](https://api.star-history.com/svg?repos=Simpleyyt/ai-manus&type=Date)](https://www.star-history.com/#Simpleyyt/ai-manus&Date)