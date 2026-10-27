FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
EXPOSE 5000
# 单 worker + 多线程，保证 SSE 流式讲解稳定。
# 用 shell 形式让 ${PORT} 展开：Render 用 $PORT 注入端口，本地/自建则回退 5000。
CMD gunicorn -b 0.0.0.0:${PORT:-5000} -w 1 --threads 8 --timeout 300 app:app
