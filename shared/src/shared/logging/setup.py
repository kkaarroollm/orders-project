import logging
import logging.config
import tomllib
from pathlib import Path


def _default_logging_config() -> dict[str, object]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "shared.logging.json_formatter.JSONFormatter",
                "fmt_keys": {
                    "level": "levelname",
                    "message": "message",
                    "timestamp": "timestamp",
                    "logger": "name",
                    "module": "module",
                    "function": "funcName",
                    "line": "lineno",
                    "thread_name": "threadName",
                },
            }
        },
        "handlers": {
            "json_stdout": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "json",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {"level": "INFO", "handlers": ["json_stdout"]},
    }


def setup_logging() -> None:
    config_file = Path(__file__).parent / "config.toml"
    if config_file.exists():
        with open(config_file, "rb") as file:
            config = tomllib.load(file)
    else:
        # Fallback keeps logging working when non-Python package data is missing.
        config = _default_logging_config()

    logging.config.dictConfig(config)
