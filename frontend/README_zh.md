# AI Manus × Claw 前端

[English](README.md) | 中文

这是 AI Manus × Claw 的前端，使用 Vue 3 + TypeScript + Vite 构建。

## 特性

- 聊天界面与任务会话，支持计划面板与 SSE 事件流
- 工具面板与富渲染视图（搜索、文件、终端、浏览器、MCP）
- VNC 查看器，支持实时查看与接管沙盒
- 登录认证、会话分享、文件上传与下载
- 基于 vue-i18n 的国际化（中文与英文）
- **Claw 页面** —— 集成 [OpenClaw](https://github.com/anthropics/openclaw) 聊天体验，支持 WebSocket 实时通信、自动过期倒计时、文件上传与下载

## 安装

创建`.env.development`文件，并创建以下配置：

```
# 后端地址
VITE_API_URL=http://127.0.0.1:8000
```

也可以在启动开发服务器时设置 `BACKEND_URL`，启用 Vite 的 `/api` 代理：

```bash
BACKEND_URL=http://localhost:8000 npm run dev
```

```bash
# 安装依赖
npm install

# 开发模式运行
npm run dev

# 运行单元测试（Vitest）
npm run test

# 类型检查（vue-tsc）
npm run type-check

# 代码检查（ESLint）
npm run lint

# 构建生产版本
npm run build
```

## Docker 部署

本项目支持使用 Docker 进行容器化部署：

```bash
# 构建 Docker 镜像
docker build -t ai-chatbot-vue .

# 运行容器（将容器的80端口映射到主机的8080端口）
docker run -d -p 8080:80 ai-chatbot-vue

# 访问应用
# 打开浏览器访问 http://localhost:8080
```

## 项目结构

```
src/
├── api/             # API 层（axios 客户端、SSE、认证、文件、Claw、配置）
├── assets/          # 静态资源和CSS文件
├── components/      # 可复用组件
│   ├── toolViews/       # 工具富渲染视图（浏览器、文件、终端、搜索、MCP）
│   ├── filePreviews/    # 文件预览组件
│   ├── login/           # 登录相关组件
│   ├── settings/        # 设置对话框组件
│   ├── icons/           # 图标组件
│   └── ui/              # 基础 UI 组件（基于 reka-ui）
├── composables/     # 可复用组合式函数（useAgentEvents、useAuth 等）
├── constants/       # 共享常量
├── lib/             # 工具库
├── locales/         # i18n 文案（中文与英文）
├── pages/           # 页面组件
│   ├── HomePage.vue     # 首页
│   ├── ChatPage.vue     # 聊天页面
│   ├── ClawPage.vue     # Claw（OpenClaw）页面
│   ├── LoginPage.vue    # 登录页面
│   ├── SharePage.vue    # 分享会话页面
│   ├── MainLayout.vue   # 主布局
│   └── ShareLayout.vue  # 分享布局
├── router/          # Vue Router 配置
├── types/           # TypeScript 类型定义
├── utils/           # 工具函数
├── App.vue          # 根组件
└── main.ts          # 入口文件
```
