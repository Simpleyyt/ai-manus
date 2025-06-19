FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 简单的Node.js安装方法
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip

# 显示当前pip和python位置
RUN echo "=== DEBUG: Python and pip info ===" && \
    which python3 && python3 --version && \
    which pip && pip --version

# 安装主要依赖
RUN echo "=== DEBUG: Installing main requirements ===" && \
    cat requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# 检查关键依赖是否安装成功
RUN echo "=== DEBUG: Checking installed packages ===" && \
    pip list && \
    echo "=== DEBUG: Checking specific packages ===" && \
    python3 -c "import fastapi; print('FastAPI version:', fastapi.__version__)" && \
    python3 -c "import uvicorn; print('Uvicorn version:', uvicorn.__version__)"

# MCP服务器依赖已删除，如需要请在主requirements.txt中添加

# 复制应用代码和MCP服务器
COPY app/ ./app/
COPY mcp_servers/ ./mcp_servers/



# 设置Python路径和权限
ENV PYTHONPATH=/app
ENV PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# 验证Python安装
RUN python3 --version && which python3 && ln -sf /usr/local/bin/python3 /usr/local/bin/python

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["python3", "-m", "app.main"] 