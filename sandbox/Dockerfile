FROM ubuntu:22.04

# Avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Set hostname to sandbox
ENV HOSTNAME=sandbox

# Update and install basic tools
RUN apt-get update && apt-get install -y \
    sudo \
    bc \
    curl \
    wget \
    gnupg \
    software-properties-common \
    xvfb \
    x11vnc \
    xterm \
    socat \
    supervisor \
    websockify \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create user ubuntu and grant sudo privileges
RUN useradd -m -d /home/ubuntu -s /bin/bash ubuntu && \
    echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ubuntu

# Install Python 3.10.12
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-venv python3.10-dev python3-pip && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js 20.18.0
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN add-apt-repository ppa:xtradeb/apps -y && \
    apt-get update && \
    apt-get install -y chromium  --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Chinese fonts and language support
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    language-pack-zh-hans \
    locales \
    && locale-gen zh_CN.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install cybersecurity tools
RUN apt-get update && apt-get install -y \
    libegl1 \
    whois \
    nmap \
    wireshark \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set default locale
ENV LANG=zh_CN.UTF-8 \
    LANGUAGE=zh_CN:zh \
    LC_ALL=zh_CN.UTF-8

# Set working directory
WORKDIR /app

# Copy project files (copy dependency files first to leverage cache)
COPY requirements.txt .
COPY app/builtin-bin /usr/local/bin

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy remaining project files
COPY . .

# Configure supervisor
COPY supervisord.conf /etc/supervisor/conf.d/app.conf

# Expose ports
EXPOSE 8080 9222 5900 5901

ENV UVI_ARGS=""
ENV CHROME_ARGS=""

# Use supervisor to start all services
CMD ["supervisord", "-n", "-c", "/app/supervisord.conf"] 
