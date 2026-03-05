# AI Manus Sandbox Service

English | [中文](README_zh.md)

AI Manus Sandbox is an isolated execution environment based on Docker containers, providing AI Agents with secure Shell command execution, file operations, and browser automation capabilities. The service offers API interfaces through FastAPI and supports interaction with backend services.

## Technical Architecture

The sandbox service integrates multiple technologies to provide an operational environment for AI Agents:

```
sandbox/
├── app/                   # Main application directory
│   ├── api/               # API interface definitions
│   │   └── v1/            # API version v1
│   │       ├── shell.py   # Shell command execution interface
│   │       ├── file.py    # File operation interface
│   │       └── supervisor.py # Process management interface
│   ├── services/          # Service implementations
│   ├── schemas/           # FastAPI interface models
│   ├── models/            # Data models
│   ├── core/              # Core configurations
│   └── main.py            # Application entry point
├── Dockerfile             # Docker build file
├── pyproject.toml         # Python dependencies (uv)
├── supervisord.conf       # Supervisor configuration
└── README.md              # Documentation
```

## Core Features

The sandbox environment provides the following core features:

1. **Shell Command Execution**: Securely execute Shell commands with session management support
2. **File Operations**: Read, write, search, and manipulate the file system
3. **Browser Environment**:
   - Built-in Google Chrome browser
   - Chrome DevTools Protocol support
   - Remote debugging interface
4. **VNC Remote Access**:
   - VNC remote desktop service
   - WebSocket interface
5. **Process Management**: Manage component processes through Supervisor

## System Requirements

- Python 3.10+
- Docker 20.10+

## Installation and Configuration

### Local Development Environment

1. **Install uv**:
```bash
pip install uv
```

2. **Install dependencies**:
```bash
uv sync --dev
```

3. **Start the development server**:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Docker Deployment

```bash
# Build the image
docker build -t manus-sandbox .

# Run the container
docker run -p 8080:8080 -p 9222:9222 -p 5900:5900 -p 5901:5901 manus-sandbox
```

## Port Information

- **8080**: FastAPI service port
- **9222**: Chrome remote debugging port
- **5900**: VNC service port
- **5901**: VNC WebSocket port

## Configuration Options

The sandbox service supports the following configuration options, which can be set through environment variables or a `.env` file:

- **ORIGINS**: List of allowed CORS origins, default is `["*"]`. Can be set as a comma-separated string or JSON array.
- **SERVICE_TIMEOUT_MINUTES**: Service timeout in minutes, default is unlimited. When set, the service will automatically terminate after the specified time.
- **LOG_LEVEL**: Log level, can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`, default is `INFO`.

Example `.env` file:
```
ORIGINS=http://localhost:3000,https://example.com
SERVICE_TIMEOUT_MINUTES=60
LOG_LEVEL=DEBUG
```

## API Documentation

Base URL: `/api/v1`

### 1. Shell-related Endpoints

#### Execute Shell Command

- **Endpoint**: `POST /api/v1/shell/exec`
- **Description**: Execute a command in the specified shell session
- **Request Body**:
  ```json
  {
    "id": "session_id",  /* Optional, automatically created if not provided */
    "exec_dir": "/path/to/dir",  /* Optional, command execution working directory (must use absolute path) */
    "command": "ls -la"  /* Command to execute */
  }
  ```
- **Response**:
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

#### View Shell Session Content

- **Endpoint**: `POST /api/v1/shell/view`
- **Description**: View the content of the specified shell session
- **Request Body**:
  ```json
  {
    "id": "session_id"  /* Target session ID */
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Session content retrieved successfully",
    "data": {
      "output": "Session output content",
      "session_id": "session_id",
      "console": [
        {
          "ps1": "user@host:~/dir $",
          "command": "ls -la",
          "output": "File listing output"
        }
      ]
    }
  }
  ```

#### Wait for Process

- **Endpoint**: `POST /api/v1/shell/wait`
- **Description**: Wait for the process in the specified session to complete
- **Request Body**:
  ```json
  {
    "id": "session_id",  /* Target session ID */
    "seconds": 10  /* Optional, wait time (seconds) */
  }
  ```
- **Response**:
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

#### Write Input

- **Endpoint**: `POST /api/v1/shell/write`
- **Description**: Write input to the process in the specified session
- **Request Body**:
  ```json
  {
    "id": "session_id",  /* Target session ID */
    "input": "example input",  /* Content to write */
    "press_enter": true  /* Whether to simulate pressing Enter after input */
  }
  ```
- **Response**:
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

#### Terminate Process

- **Endpoint**: `POST /api/v1/shell/kill`
- **Description**: Terminate the process in the specified session
- **Request Body**:
  ```json
  {
    "id": "session_id"  /* Target session ID */
  }
  ```
- **Response**:
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

### 2. File Operation Endpoints

#### Read File

- **Endpoint**: `POST /api/v1/file/read`
- **Description**: Read the content of the specified file
- **Request Body**:
  ```json
  {
    "file": "/path/to/file",  /* Absolute file path */
    "start_line": 0,  /* Optional, start line (counting from 0) */
    "end_line": 100,  /* Optional, end line (excluding this line) */
    "sudo": false  /* Optional, whether to read with sudo permissions */
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "File read successfully",
    "data": {
      "content": "File content",
      "line_count": 100,
      "file": "/path/to/file"
    }
  }
  ```

#### Write File

- **Endpoint**: `POST /api/v1/file/write`
- **Description**: Write content to the specified file
- **Request Body**:
  ```json
  {
    "file": "/path/to/file",  /* Absolute file path */
    "content": "File content",  /* Content to write */
    "append": false,  /* Optional, whether to use append mode */
    "leading_newline": false,  /* Optional, whether to add a newline before the content */
    "trailing_newline": false,  /* Optional, whether to add a newline after the content */
    "sudo": false  /* Optional, whether to write with sudo permissions */
  }
  ```
- **Response**:
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

#### Replace File Content

- **Endpoint**: `POST /api/v1/file/replace`
- **Description**: Replace strings in the file
- **Request Body**:
  ```json
  {
    "file": "/path/to/file",  /* Absolute file path */
    "old_str": "Original string",  /* Original string to replace */
    "new_str": "New string",  /* New replacement string */
    "sudo": false  /* Optional, whether to use sudo permissions */
  }
  ```
- **Response**:
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

#### Search File Content

- **Endpoint**: `POST /api/v1/file/search`
- **Description**: Search file content using regular expressions
- **Request Body**:
  ```json
  {
    "file": "/path/to/file",  /* Absolute file path */
    "regex": "search pattern",  /* Regular expression pattern */
    "sudo": false  /* Optional, whether to use sudo permissions */
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Search completed, found 3 matches",
    "data": {
      "file": "/path/to/file",
      "matches": [
        {
          "line_number": 10,
          "line": "Matching line content",
          "match": "Matching content"
        }
      ]
    }
  }
  ```

#### Find Files

- **Endpoint**: `POST /api/v1/file/find`
- **Description**: Find files based on filename patterns
- **Request Body**:
  ```json
  {
    "path": "/path/to/dir",  /* Directory path to search */
    "glob": "*.txt"  /* Filename pattern (glob syntax) */
  }
  ```
- **Response**:
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

### 3. Process Management Endpoints

#### Get Process Status

- **Endpoint**: `GET /api/v1/supervisor/status`
- **Description**: Get the status of all service processes
- **Response**:
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

#### Stop All Services

- **Endpoint**: `POST /api/v1/supervisor/stop`
- **Description**: Stop all services
- **Response**:
  ```json
  {
    "success": true,
    "message": "All services stopped",
    "data": {
      "status": "stopped"
    }
  }
  ```

#### Shutdown Supervisor

- **Endpoint**: `POST /api/v1/supervisor/shutdown`
- **Description**: Only shut down the supervisord service itself
- **Response**:
  ```json
  {
    "success": true,
    "message": "Supervisord service shutdown",
    "data": {
      "status": "shutdown"
    }
  }
  ```

#### Restart All Services

- **Endpoint**: `POST /api/v1/supervisor/restart`
- **Description**: Restart all services
- **Response**:
  ```json
  {
    "success": true,
    "message": "All services restarted",
    "data": {
      "status": "restarted"
    }
  }
  ```

#### Activate Timeout

- **Endpoint**: `POST /api/v1/supervisor/timeout/activate`
- **Description**: Reset the timeout function to automatically shut down all services after a specified time
- **Request Body**:
  ```json
  {
    "minutes": 60  /* Optional, timeout in minutes, if not provided, uses the system default configuration */
  }
  ```
- **Response**:
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

#### Extend Timeout

- **Endpoint**: `POST /api/v1/supervisor/timeout/extend`
- **Description**: Extend the timeout
- **Request Body**:
  ```json
  {
    "minutes": 30  /* Optional, minutes to extend, if not provided, uses the system default configuration */
  }
  ```
- **Response**:
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

#### Cancel Timeout

- **Endpoint**: `POST /api/v1/supervisor/timeout/cancel`
- **Description**: Cancel the timeout function
- **Response**:
  ```json
  {
    "success": true,
    "message": "Timeout cancelled",
    "data": {
      "status": "timeout_cancelled"
    }
  }
  ```

#### Get Timeout Status

- **Endpoint**: `GET /api/v1/supervisor/timeout/status`
- **Description**: Get the status of the timeout function
- **Response**:
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

## Container Environment Configuration

The sandbox container includes the following environments:

- Ubuntu 22.04
- Python 3.10
- Node.js 20.18.0
- Google Chrome

## Debugging Guide

### Browser Debugging

1. Connect to `localhost:5900` using a VNC client
2. Access `http://localhost:9222/devtools/inspector.html` in your browser 