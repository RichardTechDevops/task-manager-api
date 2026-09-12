# 统一日志格式，方便 Docker 和 kubectl logs 直接查看。
import logging
import sys

from src.config import get_log_level


def setup_logging() -> None:
    # force=True：避免被 uvicorn 默认配置覆盖。
    log_level = get_log_level()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        stream=sys.stdout,
        force=True,
    )
    # 关闭 uvicorn 自带 access log，改用我们自己的请求中间件打日志。
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
