# ⚙️ System Architecture

## High-Level Overview

![Architecture Diagram](https://github.com/user-attachments/assets/69775011-1eb7-452f-adaf-cd6603a4dde5)

AI Manus is a general-purpose AI Agent system designed to execute complex tasks in a secure, sandboxed environment. The system's architecture is composed of three primary components: a web-based frontend, a backend server, and a sandbox environment. This modular design promotes a clear separation of concerns, which enhances security, scalability, and maintainability.

- **Frontend (Manus Web):** A rich client interface that serves as the user's command center. It allows users to initiate tasks, monitor the agent's progress in real-time, and directly interact with the tools the agent is using, such as a web browser or a shell.
- **Backend (Manus Server):** The brain of the operation. It manages the agent's lifecycle, interprets user requests, and orchestrates the execution of tasks by invoking tools within the sandbox. It maintains the state of the conversation and streams updates to the frontend.
- **Sandbox:** An isolated Docker container that provides a secure execution environment for the agent's tools. Each task is allocated a dedicated sandbox, preventing any potential interference with the host system or other tasks.

### Workflow

The system's workflow is designed to be robust and transparent. When a user initiates a conversation:

1.  **Session Initiation:** The Frontend sends a request to the Backend to create a new agent session. The Backend then provisions a dedicated Sandbox container for the session by interacting with the Docker daemon.
2.  **Task Processing:** The user sends a message (a task or a query) to the Backend. The Backend's "PlanAct Agent" receives the message, formulates a plan, and begins executing the plan by calling the necessary tools (e.g., web search, file I/O, shell commands).
3.  **Tool Execution:** Tool execution requests are sent from the Backend to the Sandbox's API. The Sandbox executes the commands and returns the results to the Backend.
4.  **Real-time Feedback:** Throughout the process, all events—such as the agent's plan, tool usage, and results—are streamed from the Backend to the Frontend using Server-Sent Events (SSE), providing the user with a live view of the agent's activities.
5.  **Interactive Control:** The Frontend provides a view of the tools being used (e.g., a VNC view of the browser). This allows the user to observe the agent's actions and, if necessary, take over manual control.

## Frontend (Manus Web)

The frontend is a modern, single-page application (SPA) that provides a dynamic and responsive user interface for interacting with the AI Manus system.

### Responsibilities

- **User Interaction:** Provides the main interface for users to submit tasks, send messages, and manage conversations.
- **Real-time Updates:** Listens for Server-Sent Events (SSE) from the backend to display the agent's actions, plans, and tool outputs in real-time.
- **Tool Visualization:** Renders specialized views for different tools. This includes a VNC client for the browser, a terminal emulator for the shell, and viewers for files.
- **Interactive Control:** Allows users to take over manual control of tools, providing a seamless transition between autonomous agent operation and direct user intervention.

### Tech Stack

The frontend is built with a modern, robust tech stack:

- **Framework:** [Vue.js 3](https://vuejs.org/)
- **Build Tool:** [Vite](https://vitejs.dev/)
- **Language:** [TypeScript](https://www.typescriptlang.org/)
- **Styling:** [Tailwind CSS](https://tailwindcss.com/)
- **Routing:** [Vue Router](https://router.vuejs.org/)
- **State Management:** Vue's built-in reactivity and composables.
- **HTTP Client:** [Axios](https://axios-http.com/) for API requests.
- **SSE Client:** [`@microsoft/fetch-event-source`](https://github.com/Azure/fetch-event-source) for handling real-time events from the backend.
- **VNC Client:** [`@novnc/novnc`](https://github.com/novnc/noVNC) for rendering the remote desktop of the sandbox's browser.
- **Code Editor:** [Monaco Editor](https://microsoft.github.io/monaco-editor/) for displaying and editing code.

## Backend (Manus Server)

The backend server is the core of the AI Manus system, acting as the central nervous system that orchestrates the agent's behavior and manages the overall workflow.

### Responsibilities

- **API Server:** Exposes a RESTful API for the frontend to communicate with the system. This includes endpoints for managing sessions, sending messages, and interacting with the agent.
- **Agent Orchestration:** Implements the "PlanAct Agent" logic. It receives user requests, interacts with the LLM to create a plan, and executes the plan by calling the appropriate tools.
- **Session Management:** Manages the lifecycle of agent sessions, including creating and destroying sandboxes, and storing conversation history (using MongoDB or Redis).
- **Tool Brokering:** Acts as an intermediary between the agent and the tools in the sandbox. It forwards tool execution requests to the sandbox's API and returns the results to the agent.
- **Real-time Event Streaming:** Pushes real-time updates to the frontend via Server-Sent Events (SSE), keeping the user informed of the agent's progress.
- **WebSocket Proxying:** Forwards WebSocket connections from the frontend's noVNC client to the sandbox's VNC server, enabling interactive browser sessions.

### Tech Stack

The backend is a high-performance asynchronous application built on Python.

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Web Server:** [Uvicorn](https://www.uvicorn.org/)
- **LLM Integration:** [OpenAI Python client](https://github.com/openai/openai-python)
- **Data Validation:** [Pydantic](https://docs.pydantic.dev/)
- **Sandbox Management:** [Docker SDK for Python](https://docker-py.readthedocs.io/)
- **Browser Automation:** [Playwright](https://playwright.dev/python/)
- **Database:** [MongoDB](https://www.mongodb.com/) (with [Motor](https://motor.readthedocs.io/) and [Beanie](https://beanie-odm.dev/)) and [Redis](https://redis.io/) for session storage and caching.
- **Architecture:** Follows a clean, layered architecture pattern, separating domain logic, application services, and infrastructure concerns.

## Sandbox

The sandbox is a critical component of the AI Manus architecture, providing a secure and isolated environment for the agent to perform its tasks. Each agent session is allocated its own dedicated sandbox, which is a Docker container built on a customized Ubuntu image.

### Purpose

- **Security:** The primary purpose of the sandbox is to isolate the agent's operations from the host system and from other agent sessions. This prevents any accidental or malicious damage to the host environment.
- **Reproducibility:** The sandboxed environment is consistent and reproducible, ensuring that the agent's tools and dependencies are always available and configured correctly.
- **Resource Control:** Docker allows for the management of resources (CPU, memory) allocated to each sandbox, preventing any single agent session from consuming excessive system resources.

### Services

The sandbox runs a suite of services, managed by `supervisord`, to provide the agent with the tools it needs:

- **Tool API:** A FastAPI application that exposes endpoints for the backend to execute commands in the sandbox. This includes services for:
    - **File System Access:** Reading, writing, and listing files.
    - **Shell Access:** Executing shell commands.
- **Headless Browser:** A pre-installed Google Chrome browser runs in a virtual display (`Xvfb`), allowing the agent to browse the web for information gathering and task execution.
- **VNC Server:** The virtual display is served via `x11vnc`, allowing the browser session to be viewed remotely.
- **WebSocket Proxy:** `websockify` bridges the VNC server to a WebSocket connection, enabling the frontend's noVNC client to display the browser.
- **Chrome DevTools:** The Chrome DevTools Protocol is exposed, allowing for fine-grained control and automation of the browser via Playwright from the backend.

## Communication Protocols

The components of the AI Manus system communicate through a set of well-defined protocols, ensuring a clear and efficient flow of information.

### Frontend ↔ Backend

- **REST API:** The primary communication between the frontend and the backend is via a RESTful API. The frontend uses this API to initiate sessions, send user messages, and retrieve session information. The API is defined using FastAPI on the backend.
- **Server-Sent Events (SSE):** For real-time updates, the backend uses SSE to stream a continuous flow of events to the frontend. This is a one-way communication channel where the server pushes data to the client. This is used to display the agent's plan, the tools it's using, and the results of its actions as they happen.

### Backend → Sandbox

- **HTTP API:** The backend communicates with the sandbox by making requests to the sandbox's internal FastAPI server. This API exposes the tool functionality (file system, shell) to the backend, allowing the agent to execute commands in the isolated environment.

### Frontend ↔ Sandbox (via Backend)

- **WebSockets:** To provide an interactive view of the browser running in the sandbox, a WebSocket connection is used.
    1. The frontend's noVNC client establishes a WebSocket connection to the backend.
    2. The backend acts as a proxy, forwarding the WebSocket traffic to the `websockify` service running in the sandbox.
    3. `websockify` translates the WebSocket traffic to a standard VNC connection, which is then sent to the `x11vnc` server.

This setup allows the user to see and interact with the sandboxed browser in real-time, directly from the frontend.

## Development Guide

This guide provides a high-level overview for developers who want to contribute to the AI Manus project, with a focus on how to add new tools to the agent.

### Adding a New Tool

Adding a new tool to the agent typically involves three steps:

1.  **Implement the Tool's Logic:**
    The core logic for the tool should be implemented in the `backend` project. The backend's layered architecture makes it easy to add new functionality. You would typically start by adding a new service in the `backend/app/domain/services` directory. This service would contain the business logic for your tool.

2.  **Expose the Tool to the Agent:**
    Once the logic is implemented, you need to make the tool available to the "PlanAct Agent". This is done by creating a new tool definition in the `backend/app/domain/models/tools` directory. This definition tells the agent about the tool's name, its purpose, and the parameters it accepts. The agent can then decide to use this tool as part of its plan.

3.  **Create a Frontend Component (Optional):**
    If the tool has a visual component that you want to display to the user (similar to the browser or shell), you can create a new Vue component in the `frontend/src/components` directory. This component would be responsible for visualizing the tool's state and, if necessary, allowing for user interaction.

### Example: The Shell Tool

The existing `ShellTool` serves as a good example.

-   **Backend:** The logic for executing shell commands is implemented as a service that communicates with the `shell` service in the sandbox's API.
-   **Agent Integration:** A tool definition for the `shell` is provided to the agent, allowing it to execute shell commands to achieve its goals.
-   **Frontend:** A `ShellToolView.vue` component provides a terminal-like interface for the user to view the shell's output and input commands.