# ⚙️ System Architecture

## Overall Design

![Image](https://github.com/user-attachments/assets/69775011-1eb7-452f-adaf-cd6603a4dde5 ':size=600')

**When a user initiates a conversation:**

1. Web sends a create Agent request to Server, Server creates Sandbox through `/var/run/docker.sock` and returns session ID.
2. Sandbox is an Ubuntu Docker environment that starts Chrome browser and API services for File/Shell and other tools.
3. Web sends user messages to the session ID, Server receives user messages and forwards them to PlanAct Agent for processing.
4. PlanAct Agent plans and executes steps: the planner/executor submit structured results through native tool calls (e.g. `create_plan` / `complete_step`), and invoke sandbox tools (Shell / Browser / File / Search / MCP) as needed.
5. All events generated during Agent processing flow through Redis queues and are pushed back to the Web over WebSocket (`/api/v1/ws/chat` with `join_session` / `leave_session`); session-list updates use `/api/v1/ws/sessions`.

**When users browse tools:**

- Browser:
    1. The headless browser in Sandbox starts VNC service through xvfb and x11vnc, and converts VNC to WebSocket through websockify.
    2. Web's NoVNC component connects via Server `/api/v1/ws/vnc/{session_id}` (Cookie / Bearer) and forwards to the Sandbox, enabling browser viewing.
- Other tools: Other tools work on similar principles.

## Library

Library is a dedicated sidebar page (route `/library`) for browsing files the current user uploaded or produced across task sessions.

**Overview:**

- **Aggregation:** The backend collects files from all of the user's sessions (`session.files`) via `GET /api/v1/library/files`, ordered by recent session activity.
- **Filter & search:** Filter by document type (documents, images, etc.), search by filename, and toggle **My favorites**.
- **File favorites:** Favorite state is stored **per file id** in MongoDB `file_favorites` (`POST/DELETE /api/v1/library/files/{file_id}/favorite`), independent of session-level task favorites.
- **Preview & locate:** Open FilePreviewer for content, or jump back to the source session.
