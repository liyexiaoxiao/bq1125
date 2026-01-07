# 1. CHANGE BASE IMAGE: Use "bullseye" (Debian 11) for better compatibility with older Docker hosts
FROM python:3.11-slim-bullseye

WORKDIR /app

# 2. CHANGE APT SOURCE: 
# For Bullseye, we modify /etc/apt/sources.list (not debian.sources)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 3. INSTALL SYSTEM DEPS:
RUN apt-get update && apt-get install -y \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 4. INSTALL PYTHON DEPS: Use Tsinghua mirror
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]