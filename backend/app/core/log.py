import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from app.core.request_id import get_request_id


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
            "file": record.filename,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


class Logger:
    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def warn(self, msg: str) -> None:
        self._logger.warning(msg)

    def error(self, msg: str, exc_info: bool = False) -> None:
        self._logger.error(msg, exc_info=exc_info)

    @contextmanager
    def time(self, msg: str) -> Generator[None, None, None]:
        start = time.perf_counter()
        try:
            yield
        except Exception:
            elapsed = time.perf_counter() - start
            formatted = msg.replace("{elapsed}", f"{elapsed:.3f}s")
            self._logger.error(f"{formatted} | FAILED", exc_info=True)
            raise
        else:
            elapsed = time.perf_counter() - start
            formatted = msg.replace("{elapsed}", f"{elapsed:.3f}s")
            self._logger.info(formatted)


def get_logger(name: str) -> Logger:
    return Logger(name)


def setup_logging(level: str = "INFO", log_dir: str | None = None) -> None:
    formatter = JSONFormatter()
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers = []

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    root.addHandler(stdout_handler)

    if log_dir is None:
        candidate = Path(__file__).resolve().parent.parent.parent / "logs"
        if candidate.exists():
            log_dir = str(candidate)

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "app.jsonl"), encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
