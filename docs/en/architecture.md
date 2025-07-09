# ⚙️ System Architecture

## Overall Design

![Image](https://github.com/user-attachments/assets/69775011-1eb7-452f-adaf-cd6603a4dde5 ':size=600')

**When a user initiates a conversation:**

1. Web sends a create Agent request to Server, Server creates Sandbox through `/var/run/docker.sock` and returns session ID.
2. Sandbox is an Ubuntu Docker environment that starts Chrome browser and API services for File/Shell and other tools.
3. Web sends user messages to the session ID, Server receives user messages and forwards them to PlanAct Agent for processing.
4. PlanAct Agent calls relevant tools to complete tasks during processing.
5. All events generated during Agent processing are sent back to Web via SSE.

**When users browse tools:**

- Browser:
    1. The headless browser in Sandbox starts VNC service through xvfb and x11vnc, and converts VNC to WebSocket through websockify.
    2. Web's NoVNC component forwards to Sandbox through Server's WebSocket Forward, enabling browser viewing.
- Other tools: Other tools work on similar principles. 