# 🤖 AI Manus Open Source General AI Agent

Official Site: <https://ai-manus.com>

GitHub: <https://github.com/simpleyyt/ai-manus> | Demo: <https://app.ai-manus.com>

Blog: [Rebuild Manus with WebUI and Sandbox](https://simpleyyt.com/2026/03/07/rebuild-manus-with-webui-and-sandbox/)

Join our community: [QQ Group (1005477581)](https://qun.qq.com/universal-share/share?ac=1&authKey=p4X3Da5iMpR4liAenxwvhs7IValPKiCFtUevRlJouz9qSTSZsMnPJc3hzsJjgQYv&busi_data=eyJncm91cENvZGUiOiIxMDA1NDc3NTgxIiwidG9rZW4iOiJNZmUrTmQ0UzNDZDNqNDFVdjVPS1VCRkJGRWVlV0R3RFJSRVFoZDAwRjFDeUdUM0t6aUIyczlVdzRjV1BYN09IIiwidWluIjoiMzQyMjExODE1In0%3D&data=C3B-E6BlEbailV32co77iXL5vxPIhtD9y_itWLSq50hKqosO_55_isOZym2Faaq4hs9-517tUY8GSWaDwPom-A&svctype=4&tempid=h5_group_info)

---

AI Manus is a general-purpose AI Agent system that can be fully privately deployed and supports running various tools and operations in a sandbox environment.

The goal of AI Manus project is to become a fully privately deployable enterprise-level Manus application. Vertical Manus applications have many repetitive engineering tasks, and this project hopes to unify this part, allowing everyone to build vertical Manus applications like building blocks.

Each service and tool in AI Manus includes a Built-in version that can be fully privately deployed. Later, through A2A and MCP protocols, both Built-in Agents and Tools can be replaced. The underlying infrastructure can also be replaced by providing diverse provider configurations or simple development adaptations. AI Manus supports distributed multi-instance deployment from the architectural design, facilitating horizontal scaling to meet enterprise-level deployment requirements.

---

## Basic Features

[](https://github.com/user-attachments/assets/37060a09-c647-4bcb-920c-959f7fa73ebe ':include :type=video controls width="100%"')

## Core Features

 * **Deployment:** Only requires one LLM service for deployment, no dependency on other external services.
 * **Tools:** Supports Terminal, Browser, File, Web Search, message tools, with real-time viewing and takeover capabilities.
 * **Sandbox:** Each Task is allocated a separate sandbox that runs in a local Docker environment.
 * **Task Sessions:** Manages session history through Mongo/Redis, supports background tasks.
 * **Conversations:** Supports stopping and interruption, supports file upload and download.
 * **Multi-language:** Supports Chinese and English. 
 * **Authentication:** User login and authentication.