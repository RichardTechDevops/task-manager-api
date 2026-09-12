# 多阶段构建：第一阶段装依赖，第二阶段只拷虚拟环境，减小最终镜像。
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
# --no-cache-dir：不把 pip 缓存留在镜像层里。
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# 运行阶段：官方 slim 镜像 + 非 root 用户。
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8080 \
    LOG_LEVEL=INFO

# 作业要求不以 root 跑应用。
RUN groupadd --system --gid 1000 appuser \
    && useradd --system --uid 1000 --gid appuser --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY src ./src

USER appuser

# 默认端口 8080，可用环境变量 PORT 覆盖。
EXPOSE 8080

CMD ["sh", "-c", "uvicorn src.app:app --host 0.0.0.0 --port ${PORT}"]
