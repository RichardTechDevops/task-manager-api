# 运行时配置：全部从环境变量读取，方便 Docker / Kubernetes 注入。
import os


def get_port() -> int:
    # 监听端口。作业要求默认 8080，容器和本地开发都走这个默认值。
    return int(os.getenv("PORT", "8080"))


def get_log_level() -> str:
    # 日志级别。K8s ConfigMap 里可以改成 DEBUG / WARNING。
    return os.getenv("LOG_LEVEL", "INFO").upper()
