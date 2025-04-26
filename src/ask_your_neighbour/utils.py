import functools
import logging

__all__ = ["LOGGER"]


@functools.lru_cache(maxsize=1)
def get_logger():
    LOGGER = logging.getLogger(__name__)
    LOGGER.setLevel(logging.INFO)
    LOGGER.addHandler(logging.StreamHandler())
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s | %(name)s")
    LOGGER.handlers[-1].setFormatter(formatter)
    return LOGGER

LOGGER = get_logger()
