FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple/ \
    --timeout 300 --retries 5 -r requirements.txt

# Copy project files
COPY . .

# Set script execution permissions
RUN chmod +x run.sh

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Start command
CMD ["./run.sh"] 
