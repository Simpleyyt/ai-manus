# 🤖 AI Manus 开源通用智能体

官网地址：<https://ai-manus.com>

GitHub：<https://github.com/simpleyyt/ai-manus> | Demo：<https://app.ai-manus.com>

博客文章：[我也复刻了一个 Manus，带高仿 WebUI 和沙盒](https://simpleyyt.com/2026/03/07/rebuild-manus-with-webui-and-sandbox/)

加入我们的社群：[QQ群(1005477581)](https://qun.qq.com/universal-share/share?ac=1&authKey=p4X3Da5iMpR4liAenxwvhs7IValPKiCFtUevRlJouz9qSTSZsMnPJc3hzsJjgQYv&busi_data=eyJncm91cENvZGUiOiIxMDA1NDc3NTgxIiwidG9rZW4iOiJNZmUrTmQ0UzNDZDNqNDFVdjVPS1VCRkJGRWVlV0R3RFJSRVFoZDAwRjFDeUdUM0t6aUIyczlVdzRjV1BYN09IIiwidWluIjoiMzQyMjExODE1In0%3D&data=C3B-E6BlEbailV32co77iXL5vxPIhtD9y_itWLSq50hKqosO_55_isOZym2Faaq4hs9-517tUY8GSWaDwPom-A&svctype=4&tempid=h5_group_info)

---

AI Manus 是一个通用的 AI Agent 系统，可以完全私有部署，支持在沙盒环境中运行各种工具和操作。

AI Manus 项目目标是希望成为可完全私有部署的企业级 Manus 应用。垂类 Manus 的应用有多种重复性的工程化工作，这个项目希望把这部分统一，让大家可以像搭积木一下建立起一个垂类 Manus 应用。

AI Manus 中每个服务与工具都包含一个 Built-in 版本，可以做到完全私有部署。后续可以通过 A2A 与 MCP 协议，把 Built-in 的 Agent 与 Tools 都置换掉。底层基建也可以通过提供多样的提供商配置或者简单的开发适配置换掉。AI Manus 从架构设计上便支持分布式多实例部署，方便横向扩展，达到企业级的部署要求。

---

## 基本功能

[](https://github.com/user-attachments/assets/37060a09-c647-4bcb-920c-959f7fa73ebe ':include :type=video controls width="100%"')

## 核心功能

 * **部署：**最小只需要一个 LLM 服务即可完成部署，不需要依赖其它外部服务。
 * **工具：**支持 Terminal、Browser、File、Web Search、消息工具，并支持实查看和接管。
 * **沙盒：**每个 Task 会分配单独的一个沙盒，沙盒在本地 Dock 环境里面运行。
 * **任务会话：**通过 Mongo/Redis 对会话历史进行管理，支持后台任务。
 * **对话：**支持停止与打断，支持文件上传与下载。
 * **多语言：**支持中文与英文。
 * **认证：**用户登录与认证。
