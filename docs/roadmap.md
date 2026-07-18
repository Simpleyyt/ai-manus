# 📅 开发计划

> 持续迭代中：Deploy & Expose、多集群部署、企业级沙盒安全

## Claw（Manus × Claw）

 * [x] 集成 [OpenClaw](https://github.com/anthropics/openclaw) AI 助手
 * [x] 一键部署、用户隔离容器
 * [x] 自动过期倒计时
 * [x] 完整聊天历史（MongoDB + OpenClaw 会话合并）
 * [x] 文件上传与下载
 * [x] OpenAI 兼容 LLM 代理

## 工具

 * [x] 支持浏览器接管
 * [x] 支持外部 MCP 工具集成
 * [ ] 支持 Deploy & Expose 工具

## 用户认证

 * [x] 支持多用户

## 部署

 * [x] 支持 Docker Compose 部署
 * [ ] 支持 Docker Swarm / K8s 多集群部署

## UI

 * [x] 支持设置
 * [ ] 支持时间轴回放

## 任务会话

 * [x] 支持分享

## Agent / 上下文工程

 * [x] 原生结构化输出工具（`create_plan` / `complete_step` 等）
 * [x] 可组合 System Prompt（按已绑定工具集拼装）
 * [x] Token 感知 Memory 压缩

## 基建

 * [ ] 支持 Windows & 手机接入
 * [x] 支持 Bing、Google、Tavily、Serper 等搜索提供商
 * [x] 支持 Celery 任务后端（`TASK_BACKEND=celery`）
 * [ ] 支持阿里云等文件存储提供商
 * [ ] 支持 e2b 等沙盒提供商
 * [ ] 支持 mem0 记忆提供商
 * [ ] 沙盒企业级安全建设
