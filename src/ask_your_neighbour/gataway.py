import asyncio
import functools
import threading
from typing import cast

from agents import Agent, FunctionToolResult, ModelSettings, RunContextWrapper, Runner, TContext, ToolsToFinalOutputResult, trace
from agents.mcp.server import MCPServerSse

from ask_your_neighbour.agent_specs.orchestrator_agent import ORCHESTRATION_INSTRUCTIONS
from ask_your_neighbour.agent_specs.osm_agent import LOCATION_EXPLORER_DESCRIPTION, LOCATION_EXPLORER_INSTRUCTIONS
from ask_your_neighbour.agent_specs.summarization_agent import SUMMARIZATION_DESCRIPTION, SUMMARIZATION_INSTRUCTIONS
from ask_your_neighbour.conversation_state import ConversationState
from ask_your_neighbour.utils import LOGGER

# Dictionary to store event loops per thread
_thread_local = threading.local()


@functools.lru_cache(maxsize=1)
def _get_event_loop() -> asyncio.AbstractEventLoop:
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

    return _thread_local.loop  # type: ignore


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
                model_settings=ModelSettings(truncation="auto"),  # use truncation to avoid overflow of the context
            )

            summarization_agent = Agent(
                name="summarization_agent",
                instructions=SUMMARIZATION_INSTRUCTIONS,
                model="gpt-4.1",
            )

            agent = Agent(
                name="orchestrator_agent",
                instructions=ORCHESTRATION_INSTRUCTIONS,
                model="gpt-4.1-mini",
                tools=[
                    location_agent.as_tool(
                        tool_name="location_explorer",
                        tool_description=LOCATION_EXPLORER_DESCRIPTION,
                    ),
                    summarization_agent.as_tool(
                        tool_name="summarization_agent",
                        tool_description=SUMMARIZATION_DESCRIPTION,
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
    query = "Czy Powiśle w Warszawie jest dobrym miejscem do życia dla młodego rodzica? I czy jest dobre miejsce do jazdy samochodem elektrycznym?"
    result = user_query(query, conversation_state)
    print(result)
