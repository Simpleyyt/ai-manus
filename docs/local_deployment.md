# 🏠 本地部署

本指南介绍如何在本地机器上部署 AI Manus，提供从**一键部署**到**手动配置**的多种方式。

## 前置要求

- **Docker 20.10+** 和 **Docker Compose**
- 一个支持 Function Call 的 LLM 服务（如 DeepSeek、OpenAI GPT-4o）
- 推荐：2 核 CPU、4GB 内存以上

### Docker 安装

| 系统 | 安装方式 |
|------|----------|
| **Windows / macOS** | 安装 [Docker Desktop](https://docs.docker.com/desktop/) |
| **Linux** | 安装 [Docker Engine](https://docs.docker.com/engine/install/) |

## 方式一：一键部署（推荐）

项目提供了 `setup.sh` 脚本，支持交互式配置和一键启动：

```bash
git clone https://github.com/simpleyyt/ai-manus.git
cd ai-manus
./setup.sh
```

脚本会引导你完成：
1. **检查环境** — 自动检测 Docker 和 Docker Compose
2. **配置 LLM** — 设置 API 地址、密钥和模型名称
3. **配置认证** — 选择认证方式（本地单用户 / 无认证 / 密码注册）
4. **配置搜索** — 选择搜索引擎
5. **启动服务** — 拉取镜像并启动所有服务

### 脚本选项

```bash
./setup.sh                        # 交互式配置 + 使用预构建镜像
./setup.sh --build-from-source    # 交互式配置 + 从源码构建镜像
./setup.sh --skip-config          # 跳过配置（使用已有 .env 文件）
```

## 方式二：手动部署

### 步骤 1：下载项目

```bash
git clone https://github.com/simpleyyt/ai-manus.git
cd ai-manus
```

### 步骤 2：创建配置文件

```bash
cp .env.example .env
```

编辑 `.env` 文件，至少修改以下配置：

```env
# 必填：设置你的 LLM API 密钥
API_KEY=your-api-key-here

# 必填：设置 API 地址（根据你的模型服务商）
API_BASE=https://api.deepseek.com/v1

# 模型名称
MODEL_NAME=deepseek-chat

# 推荐：本地部署使用 local 认证，免注册
AUTH_PROVIDER=local
LOCAL_AUTH_EMAIL=admin@example.com
LOCAL_AUTH_PASSWORD=admin

# 推荐：使用 bing_web 搜索，无需 API 密钥
SEARCH_PROVIDER=bing_web
```

> **安全提示**：生产环境中，请务必修改 `JWT_SECRET_KEY` 为随机字符串。

### 步骤 3：启动服务

使用预构建的 Docker 镜像（推荐，速度更快）：

```bash
docker compose up -d
```

或从源码构建镜像：

```bash
docker compose build
docker compose up -d
```

### 步骤 4：访问服务

打开浏览器访问 http://localhost:5173

> **注意**：如果看到 `sandbox-1 exited with code 0`，这是正常现象，目的是确保 sandbox 镜像已拉取到本地。

## 常用模型配置示例

### DeepSeek

```env
API_BASE=https://api.deepseek.com/v1
API_KEY=your-deepseek-key
MODEL_NAME=deepseek-chat
MODEL_PROVIDER=openai
```

### OpenAI

```env
API_BASE=https://api.openai.com/v1
API_KEY=sk-your-openai-key
MODEL_NAME=gpt-4o
MODEL_PROVIDER=openai
```

### 本地 Ollama

```env
API_BASE=http://host.docker.internal:11434/v1
API_KEY=ollama
MODEL_NAME=qwen2.5:latest
MODEL_PROVIDER=ollama
```

> 使用 Ollama 时，需确保模型支持 Function Call 和 JSON 格式输出。`host.docker.internal` 是 Docker 容器访问宿主机的特殊域名。Linux 系统可能需要在 `docker compose` 启动时添加 `--add-host=host.docker.internal:host-gateway`。

### 兼容 OpenAI 接口的其他服务

任何兼容 OpenAI API 格式的服务都可以使用，只需修改 `API_BASE` 指向对应地址。

## 认证方式说明

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| `local` | 单用户模式，使用预设的邮箱和密码 | 个人本地使用（推荐） |
| `none` | 无需认证，直接使用 | 内网测试环境 |
| `password` | 邮箱注册，需配置 SMTP 邮箱服务 | 多用户生产环境 |

## 运维管理

### 查看服务状态

```bash
docker compose ps
```

### 查看日志

```bash
docker compose logs -f           # 所有服务日志
docker compose logs -f backend   # 仅后端日志
```

### 停止服务

```bash
docker compose down
```

### 重启服务

```bash
docker compose restart
```

### 更新版本

```bash
docker compose pull     # 拉取最新镜像
docker compose up -d    # 重启服务
```

### 清除数据

```bash
docker compose down -v  # 停止服务并删除数据卷
```

> **警告**：`-v` 参数会删除 MongoDB 数据卷，所有会话历史将丢失。

## 常见问题

### 1. sandbox-1 退出了怎么办？

`sandbox-1 exited with code 0` 是正常的。sandbox 服务在 compose 中的作用是确保 sandbox 镜像被预拉取到本地，供后端在创建任务时动态启动新容器使用。

### 2. 如何修改端口？

编辑 `docker-compose.yml`，修改 `frontend` 服务的端口映射：

```yaml
frontend:
  ports:
    - "8080:80"  # 将 5173 改为你想要的端口
```

### 3. 如何使用自定义 MCP 工具？

1. 创建 `mcp.json` 配置文件
2. 在 `docker-compose.yml` 中取消注释 MCP 相关的 volume 挂载：
   ```yaml
   backend:
     volumes:
       - ./mcp.json:/etc/mcp.json
   ```
3. 重启服务

详见 [MCP 配置](mcp.md)。

### 4. 如何配置代理？

在 `.env` 中设置代理相关变量：

```env
SANDBOX_HTTPS_PROXY=http://your-proxy:port
SANDBOX_HTTP_PROXY=http://your-proxy:port
SANDBOX_NO_PROXY=localhost,127.0.0.1
```

### 5. 如何从源码构建？

```bash
git clone https://github.com/simpleyyt/ai-manus.git
cd ai-manus
cp .env.example .env
# 编辑 .env 配置
docker compose build
docker compose up -d
```

或使用一键脚本：

```bash
./setup.sh --build-from-source
```
