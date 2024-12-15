import logging
import os
import sys


def setup_server_logger() -> logging.Logger:
    logger = logging.getLogger("monex_server")

    logger.propagate = False

    logger.setLevel(os.environ.get("LOG_LEVEL", logging.INFO))
    stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    return logger
