# Docker 环境下的 Crawl4AI 浏览器集成指南

## 概述

本项目已成功集成 Crawl4AI 浏览器功能，支持在 Docker 环境中运行。Crawl4AI 提供了快速的内容提取模式，相比传统的 Playwright 浏览器，具有更快的响应速度和更低的资源消耗。

## 功能特性

### 🚀 快速模式 (Crawl4AI)
- **快速内容提取**: 直接以 Markdown 格式提取网页内容
- **低资源消耗**: 无需完整的浏览器环境
- **快速响应**: 平均响应时间约 1.4 秒
- **适合场景**: 内容阅读、信息提取、快速浏览

### 🎯 完整模式 (Playwright)
- **完整浏览器功能**: 支持所有交互操作
- **实时截图**: 提供页面截图预览
- **JavaScript 执行**: 支持动态内容
- **适合场景**: 复杂交互、表单填写、动态内容

## Docker 部署

### 1. 构建镜像

```bash
# 构建包含 Playwright 浏览器的后端镜像
docker-compose build backend

# 构建所有服务
docker-compose build
```

### 2. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 3. 访问应用

- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 使用说明

### 浏览器模式切换

在前端界面中，你可以通过以下方式切换浏览器模式：

1. **快速模式**: 选择 "快速浏览" 选项
   - 使用 Crawl4AI 进行内容提取
   - 以 Markdown 格式显示内容
   - 支持基本的链接导航

2. **完整模式**: 选择 "完整浏览" 选项
   - 使用 Playwright 浏览器
   - 提供实时截图预览
   - 支持所有交互操作

### API 使用

#### 快速模式 API

```python
from app.infrastructure.external.browser.browser_tool import BrowserTool

# 创建浏览器工具实例
browser = BrowserTool()

# 使用快速模式浏览页面
result = await browser.view_page("https://example.com", use_fast_mode=True)

if result.success:
    content = result.data["content"]  # Markdown 格式内容
    elements = result.data["interactive_elements"]  # 交互元素列表
```

#### 完整模式 API

```python
# 使用完整模式浏览页面
result = await browser.view_page("https://example.com", use_fast_mode=False)

if result.success:
    content = result.data["content"]  # HTML 内容
    screenshot = result.data["screenshot"]  # 截图数据
    elements = result.data["interactive_elements"]  # 交互元素列表
```

## 测试验证

### 运行测试

```bash
# 在 Docker 容器中运行测试
docker-compose exec backend python test_crawl4ai.py

# 或者使用测试脚本
chmod +x test_crawl4ai_docker.sh
./test_crawl4ai_docker.sh
```

### 测试内容

测试脚本会验证以下功能：

1. **基本功能测试**: 页面内容提取
2. **导航功能测试**: URL 导航
3. **交互元素提取**: 链接和按钮识别
4. **点击模拟测试**: 链接点击功能
5. **性能测试**: 响应时间和成功率

## 配置说明

### 环境变量

```bash
# 浏览器模式配置
BROWSER_FAST_MODE_ENABLED=true  # 启用快速模式
BROWSER_FULL_MODE_ENABLED=true  # 启用完整模式

# Crawl4AI 配置
CRAWL4AI_HEADLESS=true  # 无头模式
CRAWL4AI_TIMEOUT=30     # 超时时间（秒）
```

### Docker 配置

Dockerfile 已包含以下配置：

- **系统依赖**: 安装 Playwright 所需的系统库
- **浏览器安装**: 自动安装 Chromium 浏览器
- **环境变量**: 设置 Playwright 浏览器路径
- **权限设置**: 配置必要的执行权限

## 性能对比

| 功能 | 快速模式 (Crawl4AI) | 完整模式 (Playwright) |
|------|-------------------|---------------------|
| 响应时间 | ~1.4 秒 | ~3-5 秒 |
| 内存使用 | 低 | 中等 |
| CPU 使用 | 低 | 中等 |
| 内容格式 | Markdown | HTML |
| 截图支持 | ❌ | ✅ |
| 交互操作 | 基础 | 完整 |
| JavaScript | ❌ | ✅ |

## 故障排除

### 常见问题

1. **Playwright 浏览器未安装**
   ```bash
   # 在容器中安装浏览器
   docker-compose exec backend playwright install chromium
   docker-compose exec backend playwright install-deps chromium
   ```

2. **权限问题**
   ```bash
   # 检查容器权限
   docker-compose exec backend ls -la /ms-playwright
   ```

3. **网络连接问题**
   ```bash
   # 检查网络连接
   docker-compose exec backend curl -I https://httpbin.org/html
   ```

### 日志查看

```bash
# 查看后端日志
docker-compose logs -f backend

# 查看特定服务的日志
docker-compose logs -f frontend
docker-compose logs -f mongodb
docker-compose logs -f redis
```

## 开发指南

### 添加新的浏览器功能

1. 在 `Crawl4AIBrowser` 类中添加新方法
2. 在 `PlaywrightBrowser` 类中添加对应实现
3. 在 `BrowserTool` 类中统一接口
4. 更新前端组件以支持新功能
5. 添加相应的测试用例

### 自定义配置

```python
# 自定义 Crawl4AI 配置
crawler = AsyncWebCrawler(
    headless=True,
    browser_args=[
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu'
    ],
    timeout=30
)
```

## 总结

Crawl4AI 集成成功实现了双模式浏览器功能：

- ✅ **快速模式**: 适合内容阅读和信息提取
- ✅ **完整模式**: 适合复杂交互和动态内容
- ✅ **Docker 支持**: 完整的容器化部署
- ✅ **性能优化**: 显著提升响应速度
- ✅ **用户友好**: 直观的模式切换界面

通过这种设计，用户可以根据具体需求选择合适的浏览器模式，既保证了功能的完整性，又提供了性能优化的选择。 