import logging
import logging.config
import tomllib
from pathlib import Path


def setup_logging() -> None:
    config_file = Path(__file__).parent / "config.toml"
    with open(config_file, "rb") as file:
        config = tomllib.load(file)

    logging.config.dictConfig(config)
