# AI Manus 沙盒服务

[English](README.md) | 中文

AI Manus 沙盒是一个基于Docker容器的隔离执行环境，为 AI Agent 提供安全的 Shell 命令执行、文件操作和浏览器自动化能力。该服务通过 FastAPI 提供API接口，支持与后端服务交互。

## 技术架构

沙盒服务集成多项技术，提供 AI Agent 操作环境：

```
sandbox/
├── app/                   # 应用主目录
│   ├── api/               # API接口定义
│   │   └── v1/            # API版本 v1
│   │       ├── shell.py   # Shell命令执行接口
│   │       ├── file.py    # 文件操作接口
│   │       └── supervisor.py # 进程管理接口
│   ├── services/          # 服务实现
│   ├── schemas/           # FastAPI 接口模型
│   ├── models/            # 数据模型
│   ├── core/              # 核心配置
│   └── main.py            # 应用入口
├── Dockerfile             # Docker构建文件
├── pyproject.toml         # Python依赖（uv）
├── supervisord.conf       # Supervisor配置
└── README.md              # 文档
```

## 核心功能

沙盒环境提供以下核心功能：

1. **Shell 命令执行**：安全地执行 Shell 命令，支持会话管理
2. **文件操作**：读取、写入、搜索和操作文件系统
3. **浏览器环境**：
   - 内置 Google Chrome 浏览器
   - 支持 Chrome DevTools Protocol
   - 提供远程调试接口
4. **VNC 远程访问**：
   - VNC 远程桌面服务
   - WebSocket 接口
5. **进程管理**：通过 Supervisor 管理各组件进程

## 运行环境要求

- Python 3.10+
- Docker 20.10+

## 安装配置

### 本地开发环境

1. **安装 uv**：
```bash
pip install uv
```

2. **安装依赖**：
```bash
uv sync --dev
```


3. **启动开发服务器**：
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Docker部署

```bash
# 构建镜像
docker build -t manus-sandbox .

# 运行容器
docker run -p 8080:8080 -p 9222:9222 -p 5900:5900 -p 5901:5901 manus-sandbox
```

## 端口说明

- **8080**: FastAPI 服务端口
- **9222**: Chrome 远程调试端口
- **5900**: VNC 服务端口
- **5901**: VNC WebSocket 端口

## 配置说明

沙盒服务支持以下配置项，可通过环境变量或`.env`文件设置：

- **ORIGINS**: 允许的CORS源列表，默认为`["*"]`。可设置为逗号分隔的字符串或JSON数组。
- **SERVICE_TIMEOUT_MINUTES**: 服务超时时间（分钟），默认为无限制。设置后服务将在指定时间后自动终止。
- **LOG_LEVEL**: 日志级别，可设置为`DEBUG`、`INFO`、`WARNING`、`ERROR`或`CRITICAL`，默认为`INFO`。

示例`.env`文件：
```
ORIGINS=http://localhost:3000,https://example.com
SERVICE_TIMEOUT_MINUTES=60
LOG_LEVEL=DEBUG
```

## API接口文档

基础URL: `/api/v1`

### 1. Shell相关接口

#### 执行Shell命令

- **接口**: `POST /api/v1/shell/exec`
- **描述**: 在指定的 shell 会话中执行命令
- **请求体**:

  ```json
  {
    "id": "session_id",  /* 可选，不提供则自动创建会话ID */
    "exec_dir": "/path/to/dir",  /* 可选，命令执行的工作目录（必须使用绝对路径） */
    "command": "ls -la"  /* 要执行的命令 */
  }
  ```


- **响应**:
  ```json
  {
    "success": true,
    "message": "Command executed",
    "data": {
      "session_id": "session_id",
      "command": "ls -la",
      "status": "running"
    }
  }
  ```

#### 查看 Shell 会话内容

- **接口**: `POST /api/v1/shell/view`
- **描述**: 查看指定 shell 会话的输出内容
- **请求体**:
  ```json
  {
    "id": "session_id"  /* 目标会话ID */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "Session content retrieved successfully",
    "data": {
      "output": "会话输出内容",
      "session_id": "session_id",
      "console": [
        {
          "ps1": "user@host:~/dir $",
          "command": "ls -la",
          "output": "文件列表输出"
        }
      ]
    }
  }
  ```

#### 等待进程

- **接口**: `POST /api/v1/shell/wait`
- **描述**: 等待指定会话中的进程完成
- **请求体**:
  ```json
  {
    "id": "session_id",  /* 目标会话ID */
    "seconds": 10  /* 可选，等待时间（秒） */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "Process completed, return code: 0",
    "data": {
      "session_id": "session_id",
      "returncode": 0,
      "status": "completed"
    }
  }
  ```

#### 写入输入

- **接口**: `POST /api/v1/shell/write`
- **描述**: 向指定会话中的进程写入输入
- **请求体**:
  ```json
  {
    "id": "session_id",  /* 目标会话ID */
    "input": "example input",  /* 写入的内容 */
    "press_enter": true  /* 是否在输入后模拟按下回车键 */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "Input written",
    "data": {
      "session_id": "session_id",
      "input": "example input"
    }
  }
  ```

#### 终止进程

- **接口**: `POST /api/v1/shell/kill`
- **描述**: 终止指定会话中的进程
- **请求体**:
  ```json
  {
    "id": "session_id"  /* 目标会话ID */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "Process terminated",
    "data": {
      "session_id": "session_id",
      "status": "terminated"
    }
  }
  ```

### 2. 文件操作接口

#### 读取文件

- **接口**: `POST /api/v1/file/read`
- **描述**: 读取指定文件内容
- **请求体**:
  ```json
  {
    "file": "/path/to/file",  /* 文件绝对路径 */
    "start_line": 0,  /* 可选，起始行（从0开始计数） */
    "end_line": 100,  /* 可选，结束行（不包含该行） */
    "sudo": false  /* 可选，是否使用sudo权限读取 */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "File read successfully",
    "data": {
      "content": "文件内容",
      "line_count": 100,
      "file": "/path/to/file"
    }
  }
  ```

#### 写入文件

- **接口**: `POST /api/v1/file/write`
- **描述**: 写入内容到指定文件
- **请求体**:
  ```json
  {
    "file": "/path/to/file",  /* 文件绝对路径 */
    "content": "文件内容",  /* 要写入的内容 */
    "append": false,  /* 可选，是否使用追加模式 */
    "leading_newline": false,  /* 可选，是否在内容前添加换行符 */
    "trailing_newline": false,  /* 可选，是否在内容后添加换行符 */
    "sudo": false  /* 可选，是否使用sudo权限写入 */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "File written successfully",
    "data": {
      "file": "/path/to/file",
      "bytes_written": 123
    }
  }
  ```

#### 替换文件内容

- **接口**: `POST /api/v1/file/replace`
- **描述**: 替换文件中的字符串
- **请求体**:
  ```json
  {
    "file": "/path/to/file",  /* 文件绝对路径 */
    "old_str": "原字符串",  /* 要替换的原始字符串 */
    "new_str": "新字符串",  /* 替换后的新字符串 */
    "sudo": false  /* 可选，是否使用sudo权限 */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "Replacement completed, replaced 5 occurrences",
    "data": {
      "file": "/path/to/file",
      "replaced_count": 5
    }
  }
  ```

#### 搜索文件内容

- **接口**: `POST /api/v1/file/search`
- **描述**: 使用正则表达式搜索文件内容
- **请求体**:
  ```json
  {
    "file": "/path/to/file",  /* 文件绝对路径 */
    "regex": "search pattern",  /* 正则表达式模式 */
    "sudo": false  /* 可选，是否使用sudo权限 */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "Search completed, found 3 matches",
    "data": {
      "file": "/path/to/file",
      "matches": [
        {
          "line_number": 10,
          "line": "匹配的行内容",
          "match": "匹配的内容"
        }
      ]
    }
  }
  ```

#### 查找文件

- **接口**: `POST /api/v1/file/find`
- **描述**: 根据文件名模式查找文件
- **请求体**:
  ```json
  {
    "path": "/path/to/dir",  /* 要搜索的目录路径 */
    "glob": "*.txt"  /* 文件名模式（glob语法） */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "Search completed, found 5 files",
    "data": {
      "files": [
        "/path/to/dir/file1.txt",
        "/path/to/dir/file2.txt"
      ]
    }
  }
  ```

### 3. 进程管理接口

#### 获取进程状态

- **接口**: `GET /api/v1/supervisor/status`
- **描述**: 获取所有服务进程状态
- **响应**:
  ```json
  {
    "success": true,
    "message": "Services status retrieved successfully",
    "data": [
      {
        "name": "chrome",
        "status": "RUNNING",
        "description": "pid 123, uptime 10:30:45"
      }
    ]
  }
  ```

#### 停止所有服务

- **接口**: `POST /api/v1/supervisor/stop`
- **描述**: 停止所有服务
- **响应**:
  ```json
  {
    "success": true,
    "message": "All services stopped",
    "data": {
      "status": "stopped"
    }
  }
  ```

#### 关闭 Supervisor

- **接口**: `POST /api/v1/supervisor/shutdown`
- **描述**: 仅关闭 supervisord 服务本身
- **响应**:
  ```json
  {
    "success": true,
    "message": "Supervisord service shutdown",
    "data": {
      "status": "shutdown"
    }
  }
  ```

#### 重启所有服务

- **接口**: `POST /api/v1/supervisor/restart`
- **描述**: 重启所有服务
- **响应**:
  ```json
  {
    "success": true,
    "message": "All services restarted",
    "data": {
      "status": "restarted"
    }
  }
  ```

#### 激活超时

- **接口**: `POST /api/v1/supervisor/timeout/activate`
- **描述**: 重置超时功能，在指定时间后自动关闭所有服务
- **请求体**:
  ```json
  {
    "minutes": 60  /* 可选，超时时间（分钟），若不提供则使用系统默认配置 */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "Timeout reset, all services will be shut down after 60 minutes",
    "data": {
      "timeout_minutes": 60,
      "timeout_timestamp": "2023-07-01T12:34:56",
      "status": "timeout_set"
    }
  }
  ```

#### 延长超时

- **接口**: `POST /api/v1/supervisor/timeout/extend`
- **描述**: 延长超时时间
- **请求体**:
  ```json
  {
    "minutes": 30  /* 可选，延长的分钟数，若不提供则使用系统默认配置 */
  }
  ```
- **响应**:
  ```json
  {
    "success": true,
    "message": "Timeout extended, all services will be shut down after 90 minutes",
    "data": {
      "timeout_minutes": 90,
      "timeout_timestamp": "2023-07-01T14:04:56",
      "status": "timeout_extended"
    }
  }
  ```

#### 取消超时

- **接口**: `POST /api/v1/supervisor/timeout/cancel`
- **描述**: 取消超时功能
- **响应**:
  ```json
  {
    "success": true,
    "message": "Timeout cancelled",
    "data": {
      "status": "timeout_cancelled"
    }
  }
  ```

#### 获取超时状态

- **接口**: `GET /api/v1/supervisor/timeout/status`
- **描述**: 获取超时功能的状态
- **响应**:
  ```json
  {
    "success": true,
    "message": "Remaining time: 45 minutes",
    "data": {
      "active": true,
      "timeout_timestamp": "2023-07-01T14:04:56",
      "remaining_seconds": 2700
    }
  }
  ```

## 容器环境配置

沙盒容器内置以下环境：

- Ubuntu 22.04
- Python 3.10
- Node.js 20.18.0
- Google Chrome

## 调试指南

### 浏览器调试

1. 通过VNC客户端连接`localhost:5900`
2. 在浏览器中访问`http://localhost:9222/devtools/inspector.html`