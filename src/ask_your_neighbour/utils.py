import functools
import logging

__all__ = ["LOGGER"]


@functools.lru_cache(maxsize=1)
def get_logger() -> logging.Logger:
    LOGGER = logging.getLogger(__name__)
    LOGGER.setLevel(logging.INFO)
    LOGGER.addHandler(logging.StreamHandler())
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s | %(name)s")
    LOGGER.handlers[-1].setFormatter(formatter)
    return LOGGER


LOGGER = get_logger()


PULSE_BOX = """
<style>
.pulse-box {{
  padding: 1rem;
  border-radius: .75rem;
  background: rgba(30,30,30,.85);
  color: #fff;
  font-family: 'Inter', sans-serif;
  white-space: pre-wrap;
  animation: pulse 2s ease-in-out infinite;
}}
@keyframes pulse {{
  0%   {{opacity:.25;}}
  50%  {{opacity:1;}}
  100% {{opacity:.25;}}
}}
</style>
<div class="pulse-box">{agent_state}</div>
"""
