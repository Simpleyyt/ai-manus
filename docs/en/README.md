# 🤖 AI Manus Open Source General AI Agent

Official Site: <https://ai-manus.com>

GitHub: <https://github.com/simpleyyt/ai-manus> | Demo: <https://app.ai-manus.com>

Blog: [Rebuild Manus with WebUI and Sandbox](https://simpleyyt.com/2026/03/07/rebuild-manus-with-webui-and-sandbox/)

---

AI Manus is a general-purpose AI Agent system that can be fully privately deployed and supports running various tools and operations in a sandbox environment.

The goal of AI Manus project is to become a fully privately deployable enterprise-level Manus application. Vertical Manus applications have many repetitive engineering tasks, and this project hopes to unify this part, allowing everyone to build vertical Manus applications like building blocks.

Each service and tool in AI Manus includes a Built-in version that can be fully privately deployed. Later, through A2A and MCP protocols, both Built-in Agents and Tools can be replaced. The underlying infrastructure can also be replaced by providing diverse provider configurations or simple development adaptations. AI Manus supports distributed multi-instance deployment from the architectural design, facilitating horizontal scaling to meet enterprise-level deployment requirements.

---

## Basic Features

[](https://github.com/user-attachments/assets/a73e5be2-822a-4aa9-b2c1-08adc30629a5 ':include :type=video controls width="100%"')

## Core Features

 * **Deployment:** Only requires one LLM service for deployment, no dependency on other external services.
 * **Agent loop:** Plan-and-execute with composable system prompts and native structured output tools (`create_plan` / `complete_step`, etc.).
 * **Tools:** Supports Terminal, Browser, File, Web Search, message tools, with real-time viewing and takeover capabilities, and supports external MCP tool integration.
 * **Sandbox:** Each Task is allocated a separate sandbox that runs in a local Docker environment.
 * **Task Sessions:** Manages session history through Mongo/Redis, supports background tasks.
 * **Library:** The sidebar Library page aggregates attachments and artifacts across the user's sessions, with type filters, search, per-file favorites, preview, and navigation back to the source task.
 * **Conversations:** Supports stopping and interruption, supports file upload and download.
 * **Multi-language:** Supports Chinese and English. 
 * **Authentication:** User login and authentication.