FROM python:3.8-bullseye

WORKDIR /app

COPY requirements.txt .

# Use Tsinghua mirror for pip to speed up installation in China
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

COPY . .

# Install dos2unix and convert entrypoint.sh to Unix format
RUN apt-get update && apt-get install -y dos2unix && dos2unix entrypoint.sh && apt-get clean && rm -rf /var/lib/apt/lists/*

# Make entrypoint executable
RUN chmod +x entrypoint.sh

EXPOSE 5000

ENV FLASK_APP=start.py

ENTRYPOINT ["./entrypoint.sh"]
