import functools
import logging

__all__ = ["LOGGER"]


@functools.lru_cache(maxsize=1)
def get_logger():
    LOGGER = logging.getLogger(__name__)
    LOGGER.setLevel(logging.INFO)
    LOGGER.addHandler(logging.StreamHandler())
    return LOGGER

LOGGER = get_logger()
