# 🚀 快速上手

## 环境准备

本项目主要依赖Docker进行开发与部署，需要安装较新版本的Docker：

 * Docker 20.10+
 * Docker Compose

模型能力要求：

 * 兼容 OpenAI 接口
 * 支持 FunctionCall
 * 支持 Json Format 输出

推荐使用 Deepseek 与 ChatGPT 模型。


## Docker 安装

### Windows & Mac 系统

按照官方要求安装 Docker Desktop ：https://docs.docker.com/desktop/

### Linux 系统

按照官方要求安装 Docker Engine：https://docs.docker.com/engine/

## 部署

使用Docker Compose进行部署，需要修改`API_BASE`与`API_KEY`环境变量：

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
      
      # Search engine configuration (options: baidu, google)
      - SEARCH_PROVIDER=baidu
      # Google Search API key for web search capability (only needed when SEARCH_PROVIDER=google)
      #- GOOGLE_SEARCH_API_KEY=
      # Google Custom Search Engine ID (only needed when SEARCH_PROVIDER=google)
      #- GOOGLE_SEARCH_ENGINE_ID=

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

保存成`docker-compose.yml`文件，并运行：

```bash
docker compose up -d
```

> 注意：如果提示`sandbox-1 exited with code 0`，这是正常的，这是为了让 sandbox 镜像成功拉取到本地。

打开浏览器访问 <http://localhost:5173> 即可访问 Manus。
