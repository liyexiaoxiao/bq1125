FROM python:3.11-slim

WORKDIR /app

# 1. CHANGE APT SOURCE: Switch to Aliyun mirror for stability in China
# Note: python:3.11-slim is based on Debian 12 (Bookworm), which uses debian.sources
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 2. INSTALL SYSTEM DEPS: Now run update and install
RUN apt-get update && apt-get install -y \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# 3. CHANGE PIP SOURCE: Use Tsinghua mirror to speed up Python package install
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]