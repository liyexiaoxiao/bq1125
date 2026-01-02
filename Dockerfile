FROM python:3.8-bullseye

WORKDIR /app

COPY requirements.txt .

# Use Tsinghua mirror for pip to speed up installation in China
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

EXPOSE 5000

ENV FLASK_APP=start.py

ENTRYPOINT ["./entrypoint.sh"]
