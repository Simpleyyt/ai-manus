# Skills 技能

## 简介

Skills（技能）是可复用的工作流说明包：每个技能包含名称、描述，以及一份完整的 `SKILL.md` 指令（可附带脚本与资源文件）。格式对齐 [Agent Skills](https://agentskills.io/what-are-skills)。

在 AI Manus 中，你可以：

- 从**官方目录**添加技能，或上传 ZIP / 从 **GitHub 公库**导入
- 在对话输入框用 **`/`** 插入技能 chip，或发送以 `/{name}` 开头的文本
- 让 Agent 按需 **`load_skill`** 加载完整说明，并把技能文件同步进沙盒

> Skills 与 [MCP](mcp.md) 不同：MCP 接入外部工具服务；Skills 是给模型看的专项工作流说明（并可附带沙盒内文件）。

## 使用方式

### 1. 在设置中管理技能

打开 **设置 → 技能**：

| 操作 | 说明 |
|------|------|
| **已添加列表** | 搜索、查看；用开关 **启用 / 停用**（停用不等于删除订阅） |
| **浏览技能** | 从官方 / 个人目录添加未订阅的技能 |
| **创建 ▾** | 从官方库添加、上传包、GitHub 导入，或「与 Manus 一起创建」跳转聊天 |

首次进入时会自动订阅并启用全部官方技能（`skill-creator`、`web-research`、`summarize`、`slides`、`market-research`），并 seed 一个个人示例 `data-viz`。

### 2. 添加自定义技能

**上传**

- 支持 `.zip` / `.skill` 包（后端也可接受可解析的 `SKILL.md` 并打包）
- 包内需含可解析的 `SKILL.md`（YAML frontmatter：`name`、`description` + Markdown 正文）
- `name` 需匹配：`小写字母/数字`，段之间用 `-`（如 `my-skill`）
- 包大小上限：**20MB**

**从 GitHub 导入**

- 仅支持公开仓库：`https://github.com/{owner}/{repo}`
- 拉取默认分支 zipball（先 `main`，再试 `master`）
- 仓库根目录（或单一顶层文件夹）需包含 `SKILL.md`

导入或上传成功后会自动加入「已添加」并启用。

### 3. 在对话中调用

1. 在输入框输入 **`/`**，从菜单选择已**启用**的技能（插入技能 chip）
2. 或直接发送：`/skill-name 后面跟你的任务说明`
3. 发送后，前端会带上 `required_skills`；后端也会解析文本里的 `/{name}`

未添加或已停用的技能引用会被**静默忽略**（当作普通消息处理）。

**Agent 模式（完整能力）**

- 系统提示中只放技能名与描述（L1）
- 用户显式调用时，要求模型先调用工具 **`load_skill`** 拉取完整 `SKILL.md`（L2）
- 启用中的技能包会同步到沙盒：`/home/ubuntu/skills/{name}/`（L3）

**Chat / Lite 模式**

- 不会同步沙盒文件，也没有 `load_skill`；技能能力弱于 Agent 模式

## 官方捆绑技能

仓库内置官方包（目录 `backend/app/application/data/official_skills/`）：

| name | 说明（概要） |
|------|----------------|
| `skill-creator` | 协助创建可复用技能 |
| `web-research` | 网络调研类任务 |
| `summarize` | 长文摘要 |
| `slides` | 演示文稿 / 幻灯片 |
| `market-research` | 市场调研 |

## HTTP API

前缀：`/api/v1`（需登录）。

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/skills` | 返回目录 catalog + 已添加列表（含 enabled） |
| `POST` | `/skills/added` | body `{ "skill_ids": [...] }` 添加 / 重新启用 |
| `PATCH` | `/skills/added/{skill_id}` | body `{ "enabled": true/false }` |
| `POST` | `/skills/import/github` | body `{ "url": "https://github.com/owner/repo" }` |
| `POST` | `/skills/import/upload` | multipart 字段 `file` |

聊天调用走 WebSocket `/api/v1/ws/chat`（可带 `required_skills`），没有单独的「执行技能」REST 接口。

当前**没有**从已添加列表中彻底删除订阅的 API；只能停用。

## 配置说明

Skills **没有**专用环境变量；不依赖 `.env` 开关。包大小、沙盒路径等为代码内约定。

相关实现入口（开发者）：

- 后端服务：`backend/app/application/services/skill_service.py`、`skill_runtime_service.py`
- 官方包：`backend/app/application/data/official_skills/`
- 前端：设置页 Skills、输入框 `/` slash 与 skill chip

## 注意事项

- **Team** 技能页签目前为空占位，无团队技能。
- GitHub 仅公库、简单 `owner/repo` URL；私库、非 `main`/`master` 默认分支、子目录包可能失败。
- Chat 模式不要期望沙盒脚本与完整 `load_skill` 行为。
- 技能包内非 UTF-8 文件同步到沙盒时可能被跳过。

## 更多资源

- [Agent Skills 规范](https://agentskills.io/what-are-skills)
- [MCP 配置](mcp.md)（外部工具接入）
