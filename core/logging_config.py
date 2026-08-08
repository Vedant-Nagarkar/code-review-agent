import logging
import json
import sys
from core.config import settings
import time
import functools


class JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "agent": getattr(record, "agent", None),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
    root = logging.getLogger()
    root.setLevel(settings.log_level)
    root.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_node(agent_name: str):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(state, *args, **kwargs):
            logger = get_logger(f"agent.{agent_name}")
            start = time.monotonic()
            try:
                result = fn(state, *args, **kwargs)
                duration = time.monotonic() - start
                logger.info(
                    "node completed",
                    extra={"agent": agent_name, "duration_s": round(duration, 2)}
                )
                return result
            except Exception:
                logger.exception("node failed", extra={"agent": agent_name})
                raise
        return wrapper
    return decorator