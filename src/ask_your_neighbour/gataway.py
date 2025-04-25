import asyncio
import functools
import threading
from typing import Any, cast

from agents import Agent, Runner, trace
from agents.mcp.server import MCPServerSse

from ask_your_neighbour.conversation_state import ConversationState
from ask_your_neighbour.osm_agent import LOCATION_EXPLORER_DESCRIPTION, LOCATION_EXPLORER_INSTRUCTIONS
from ask_your_neighbour.utils import LOGGER

# Dictionary to store event loops per thread
_thread_local = threading.local()


@functools.lru_cache(maxsize=1)
def _get_event_loop():
    """Get or create an event loop for the current thread."""
    if not hasattr(_thread_local, "loop") or _thread_local.loop is None:
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


async def _user_query(query: str, conversation_state: ConversationState) -> str:
    """Process a user query using an AI agent."""
    with trace("ask-your-neighbour"):
        async with MCPServerSse(
            params={"url": "http://localhost:8000/sse"},
            client_session_timeout_seconds=600,
        ) as server:
            location_agent = Agent(
                name="location_explorer",
                instructions=LOCATION_EXPLORER_INSTRUCTIONS,
                mcp_servers=[server],
                model="gpt-4.1",
            )

            agent = Agent(
                name="orchestrator_agent",
                instructions="""You are an orchestrator agent. You will be given a query and you will use the tools to
                generate a location description. After gathering the information, you will provide a final
                answer to the user. Respond in the user's language.""",
                model="gpt-4.1-mini",
                tools=[
                    location_agent.as_tool(
                        tool_name="location_explorer",
                        tool_description=LOCATION_EXPLORER_DESCRIPTION,
                    ),
                ],
            )

            result = await Runner.run(agent, query, max_turns=25)

            return cast(str, result.final_output)


def user_query(query: str, conversation_state: ConversationState) -> str:
    """Process a user query using an AI agent."""

    # Get event loop for the current thread
    loop = _get_event_loop()

    # Run the agent
    return loop.run_until_complete(_user_query(query, conversation_state))  # type: ignore


if __name__ == "__main__":
    # Example usage
    conversation_state = ConversationState()
    query = "Czy Powiśle w Warszawie jest dobrym miejscem do życia dla młodego rodzica?"
    result = user_query(query, conversation_state)
    print(result)
