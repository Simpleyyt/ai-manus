# ⚙️ 系统架构

## 整体设计

![Image](https://github.com/user-attachments/assets/69775011-1eb7-452f-adaf-cd6603a4dde5 ':size=600')

**当用户发起对话时：**

1. Web 向 Server 发送创建 Agent 请求，Server 通过`/var/run/docker.sock`创建出 Sandbox，并返回会话 ID。
2. Sandbox 是一个 Ubuntu Docker 环境，里面会启动 chrome 浏览器及 File/Shell 等工具的 API 服务。
3. Web 往会话 ID 中发送用户消息，Server 收到用户消息后，将消息发送给 PlanAct Agent 处理。
4. PlanAct Agent 进行规划与执行：规划器/执行器通过原生工具调用提交结构化结果（如 `create_plan` / `complete_step`），并按需调用沙盒工具（Shell / Browser / File / Search / MCP）。
5. Agent 处理过程中产生的所有事件经 Redis 队列，通过 WebSocket（`/api/v1/ws/chat`，`join_session` / `leave_session`）推回 Web；会话列表增量通过 `/api/v1/ws/sessions` 推送。

**当用户浏览工具时：**

- 浏览器：
    1. Sandbox 的无头浏览器通过 xvfb 与 x11vnc 启动了 vnc 服务，并且通过 websockify 将 vnc 转化成 websocket。
    2. Web 的 NoVNC 组件通过 Server 的 `/api/v1/ws/vnc/{session_id}`（Cookie / Bearer）转发到 Sandbox，实现浏览器查看。
- 其它工具：其它工具原理也是差不多。

## 库（Library）

「库」是侧栏中的独立页面（路由 `/library`），用于浏览当前用户在各任务会话中产生或上传的文件。

**能力概览：**

- **聚合来源：**后端从用户全部会话的 `session.files` 汇总文件列表（`GET /api/v1/library/files`），按会话最近活跃时间排序。
- **筛选与搜索：**支持按文档类型（文档 / 图片等）筛选、关键词搜索文件名，以及「我的收藏」过滤。
- **文件收藏：**收藏状态按 **文件 ID** 持久化在 MongoDB `file_favorites` 集合（`POST/DELETE /api/v1/library/files/{file_id}/favorite`），与会话级「收藏任务」相互独立。
- **预览与定位：**卡片可打开 FilePreviewer 预览内容，或跳转到所属会话继续查看。
