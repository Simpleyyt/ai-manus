# Skills 技能

## 简介

Skills（技能）是可复用的工作流说明包：每个技能包含名称、描述，以及一份完整的 `SKILL.md` 指令（可附带脚本与资源文件）。格式对齐 [Agent Skills](https://agentskills.io/what-are-skills)。

在 AI Manus 中，你可以：

- 在 **设置 → 功能 → 技能** 管理已添加技能，从**官方目录**添加，或 **上传 ZIP / `.skill`**、从 **GitHub 公库**导入
- 在对话输入框用 **`/`** 插入技能 chip，或通过输入框 **`+` → 使用技能** 选择并插入
- 发送后消息会带上 `required_skills`；历史消息以 chip 展示，悬停可查看描述（官方技能有 Official 标识）
- 让 Agent 按需调用 **`load_skill`** 加载完整说明，并把技能文件同步进沙盒

> Skills 与 [MCP](mcp.md) 不同：MCP 接入外部工具服务；Skills 是给模型看的专项工作流说明（并可附带沙盒内文件）。

## 使用方式

### 1. 在设置中管理技能

打开 **设置 → 功能 → 技能**（面板标题为「已添加的技能」）：

| 操作 | 说明 |
|------|------|
| **已添加列表** | 搜索、查看；用开关 **启用 / 停用**（停用不等于删除订阅） |
| **浏览技能** | 弹窗浏览 **官方 / 团队 / 个人** 目录并添加（团队目前为空占位） |
| **创建 ▾** | **使用 Manus 创建技能**、**上传技能**、**从 GitHub 导入技能**、**从官方技能添加** |

首次进入时会自动订阅并启用全部官方技能（`skill-creator`、`web-research`、`summarize`、`slides`、`market-research`），并 seed 一个个人示例 `data-viz`。

### 2. 添加自定义技能

**上传**

- 支持 `.zip` / `.skill` 包（后端也可接受可解析的 `SKILL.md` 并打包）
- 包内需含可解析的 `SKILL.md`（YAML frontmatter：`name`、`description` + Markdown 正文）
- `name` 需匹配：`小写字母/数字`，段之间用 `-`（如 `my-skill`）
- 包大小上限：**20MB**

**从 GitHub 导入**

- 仅支持公开仓库（`github.com` 的 http/https URL）
- 可粘贴仓库根、或子目录链接：`…/tree/<branch>/path/to/skill`、`…/blob/<branch>/…/SKILL.md`
- 拉取 zipball：优先 URL 中的分支，否则依次尝试 `main` / `master`
- 指定子目录时，该目录下需有 `SKILL.md`；未指定时，归档内需有且仅有一个 `SKILL.md`

导入或上传成功后会自动加入「已添加」并启用。

**使用 Manus 创建技能**

- 从创建菜单选择后，会确保已添加 `skill-creator`，并在首页输入框预填带该技能 chip 的草稿，引导你在对话里一起写技能。

### 3. 在对话中调用

任选其一：

1. 在输入框输入 **`/`**，从菜单「技能」分区选择已**启用**的技能（插入技能 chip）
2. 点击输入框 **`+` → 使用技能**：搜索并选择技能；面板内还可 **添加技能**（上传 / GitHub / 官方）或 **管理技能**（打开设置页）
3. 直接发送：`/skill-name 后面跟你的任务说明`

发送后，前端会附带 `required_skills: [{ id, name }, …]`；后端也会解析文本里的 `/{name}`。结构化引用优先于纯文本解析。

未添加或已停用的技能引用会被**静默忽略**（当作普通消息处理）。

**历史消息**

- 用户消息中的技能以 chip 渲染（优先使用持久化的 `required_skills`；旧消息无该字段时回退解析行首 `/{name}`）
- 悬停 chip 显示名称、描述（最多约三行）以及官方技能的 Official 标识

**Agent 模式（完整能力）**

- **L1：**系统提示与 `load_skill` 工具说明中只放启用技能的 name / description（及 `<available_skills>` 目录）
- **软 L2：**用户显式调用后，注入 `<active_skill>` 激活标记（**不**注入 `SKILL.md` 正文），要求模型先 `load_skill`
- **硬 L2：**完整 `SKILL.md` 仅通过工具 **`load_skill`** 的结果进入上下文
- **L3：**启用中的技能包同步到沙盒：`/home/ubuntu/skills/{name}/`
- **计划首步：**Planner 被要求、且宿主会校正计划的第一步为「加载 {name} 技能」/ `Load {name} skill`，以便执行器先调用 `load_skill`

**Chat 模式**

- 不会同步沙盒文件，也没有 `load_skill`；仅有激活提示，技能能力弱于 Agent 模式

### 沙盒路径映射（L3）

Skills **不是**通过 Docker `-v` / compose `volumes` 挂载进容器，而是在 **Agent 模式**任务启动时，由后端把已启用技能包**写入**沙盒文件系统。

| 方向 | 路径 | 说明 |
|------|------|------|
| 官方技能源（后端宿主机） | `backend/app/application/data/official_skills/{name}/` | 仓库内置目录，整包拷贝 |
| 个人 / 导入技能源 | MongoDB GridFS 中的技能包 zip | 解包后按相对路径写出 |
| 沙盒容器内目标 | `/home/ubuntu/skills/{name}/` | 常量 `SKILLS_ROOT`；主文件为 `SKILL.md` |
| 示例 | `/home/ubuntu/skills/web-research/SKILL.md` | Agent 可用 `file_read` / shell 读取 |

**何时同步**

- 仅 **Agent 模式**（非 Chat）：`AgentTaskRunner` 在确保沙盒就绪后调用 `SkillRuntimeService.sync_enabled_skills_to_sandbox`
- Chat 模式跳过同步

**怎么写入**

1. 列出用户已启用技能
2. 对每个技能：先 `rm -rf /home/ubuntu/skills/{name}`，再按包内相对路径调用沙盒 `file_write`（HTTP → 沙盒容器内落盘）
3. 删除沙盒里已停用技能的残留目录
4. 非 UTF-8 文件会被跳过并打日志

因此容器内看到的是普通目录树，不是 bind mount；重启/重建沙盒后会在下次 Agent 任务启动时重新同步。

实现入口：`backend/app/application/services/skill_runtime_service.py`（`sync_enabled_skills_to_sandbox`）、路径常量 `backend/app/domain/skills/package.py`（`SKILLS_ROOT = "/home/ubuntu/skills"`）。

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
| `GET` | `/skills` | 返回目录 catalog + 已添加列表（含 enabled）；首次访问会 seed 默认订阅 |
| `POST` | `/skills/added` | body `{ "skill_ids": [...] }` 添加 / 重新启用 |
| `PATCH` | `/skills/added/{skill_id}` | body `{ "enabled": true/false }` |
| `POST` | `/skills/import/github` | body `{ "url": "https://github.com/owner/repo" }`（支持 tree/blob 子路径） |
| `POST` | `/skills/import/upload` | multipart 字段 `file` |

聊天调用走 WebSocket `/api/v1/ws/chat`（可选字段 `required_skills: [{ "id", "name" }]`），没有单独的「执行技能」REST 接口。

当前**没有**从已添加列表中彻底删除订阅的 API；只能停用。

## 配置说明

Skills **没有**专用环境变量；不依赖 `.env` 开关。包大小（20MB）、沙盒路径等为代码内约定。

相关实现入口（开发者）：

- 后端服务：`backend/app/application/services/skill_service.py`、`skill_runtime_service.py`
- 技能工具：`backend/app/domain/services/tools/skill.py`（`load_skill`）
- 计划首步：`backend/app/domain/services/skills/plan_steps.py`
- 官方包：`backend/app/application/data/official_skills/`
- 前端：设置页 Skills、输入框 `/` slash、`+`「使用技能」面板、历史 skill chip / hover

## 注意事项

- **团队**技能页签目前为空占位，无团队技能。
- GitHub 仅公库；支持仓库根与子目录 URL。未指定子目录时，归档内需有且仅有一个 `SKILL.md`。
- Chat 模式不要期望沙盒脚本与完整 `load_skill` 行为。
- 技能包内非 UTF-8 文件同步到沙盒时可能被跳过。

## 更多资源

- [Agent Skills 规范](https://agentskills.io/what-are-skills)
- [MCP 配置](mcp.md)（外部工具接入）
