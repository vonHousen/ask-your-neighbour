import functools
import os
from typing import Any
from agents import Agent, Runner
import asyncio
import threading
from ask_your_neighbour.utils import LOGGER
from ask_your_neighbour.conversation_state import ConversationState

# Dictionary to store event loops per thread
_thread_local = threading.local()


@functools.lru_cache(maxsize=1)
def _get_event_loop():
    """Get or create an event loop for the current thread."""
    if not hasattr(_thread_local, 'loop') or _thread_local.loop is None:
        try:
            # Try to get the current event loop
            _thread_local.loop = asyncio.get_event_loop()
        except RuntimeError:
            # If there's no event loop, create and set a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            _thread_local.loop = loop
            LOGGER.info(f"Created new event loop for thread: {threading.current_thread().name}")
    
    return _thread_local.loop


def user_query(query: str, conversation_state: ConversationState) -> str:
    """Process a user query using an AI agent."""
    agent = Agent(
        name="Assistant", 
        instructions="You are a helpful assistant",
        model="gpt-4o-mini",
    )
    
    # Get event loop for the current thread
    loop = _get_event_loop()
    
    # Run the agent
    result = loop.run_until_complete(Runner.run(agent, query))
    return result.final_output
