import asyncio
import functools
import json
import threading
from typing import cast

import streamlit as st
from agents import (
    Agent,
    AgentHooks,
    FileSearchTool,
    FunctionTool,
    InputGuardrailTripwireTriggered,
    ModelSettings,
    RunContextWrapper,
    Runner,
    TContext,
    WebSearchTool,
    handoff,
    trace,
)
from agents.mcp.server import MCPServerSse
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputItemDoneEvent, ResponseTextDeltaEvent
from openai.types.responses.web_search_tool_param import UserLocation

from ask_your_neighbour.agent_specs.document_agent import DOCUMENT_EXPLORER_DESCRIPTION, DOCUMENT_EXPLORER_INSTRUCTIONS
from ask_your_neighbour.agent_specs.orchestrator_agent import ORCHESTRATION_INSTRUCTIONS
from ask_your_neighbour.agent_specs.osm_agent import LOCATION_EXPLORER_DESCRIPTION, LOCATION_EXPLORER_INSTRUCTIONS
from ask_your_neighbour.agent_specs.search_agent import SEARCH_AGENT_DESCRIPTION, SEARCH_AGENT_INSTRUCTIONS
from ask_your_neighbour.agent_specs.summarization_agent import SUMMARIZATION_DESCRIPTION, SUMMARIZATION_INSTRUCTIONS
from ask_your_neighbour.conversation_guardrail import guardrail_check
from ask_your_neighbour.conversation_state import ConversationState
from ask_your_neighbour.geoportal import (
    VisualizationRequest,
    visualize_data_to_user,
    visualize_spatial_development_plan_to_user,
)
from ask_your_neighbour.utils import LOGGER, PULSE_BOX

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


async def _user_query(conversation_state: ConversationState) -> str:
    """Process a user query using an AI agent."""
    with trace("ask-your-neighbour"):

        visualize_to_user = visualize_data_to_user(conversation_state)

        visuaize_to_user_tool = FunctionTool(
            name="visualize_map_to_user",
            description="Fetch and shows user visualization",
            params_json_schema=VisualizationRequest.model_json_schema(),
            on_invoke_tool=visualize_to_user,
        )

        visualze_spatial_development_plan = visualize_spatial_development_plan_to_user(conversation_state)
        visualize_spatial_development_plan_tool = FunctionTool(
            name="visualize_spatial_development_plan_to_user",
            description="Fetch and shows user visualization of spatial development plan",
            params_json_schema=VisualizationRequest.model_json_schema(),
            on_invoke_tool=visualze_spatial_development_plan,
        )

        async with MCPServerSse(
                params={"url": "http://localhost:8000/sse"},
                client_session_timeout_seconds=600,
                cache_tools_list=True,
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

            decument_agent = Agent(
                name="document_location_explorer",
                instructions=DOCUMENT_EXPLORER_INSTRUCTIONS,
                model="gpt-4o-mini",
                # at this point the vector store id is not known, it will be set in the hooks
                tools=[FileSearchTool(vector_store_ids=[])],
                hooks=DocumentAgentHooks(conversation_state),
            )

            search_agent = Agent(
                name="search_agent",
                instructions=SEARCH_AGENT_INSTRUCTIONS,
                model="gpt-4.1",
                tools=[
                    WebSearchTool(
                        user_location=UserLocation(
                            type="approximate",
                            country="PL",
                            city="Warsaw",   # TODO hardcoded
                            region="Warsaw",
                        )
                    )
                ],
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
                    decument_agent.as_tool(
                        tool_name="document_location_explorer",
                        tool_description=DOCUMENT_EXPLORER_DESCRIPTION,
                    ),
                    search_agent.as_tool(
                        tool_name="search_agent",
                        tool_description=SEARCH_AGENT_DESCRIPTION,
                    ),
                    visuaize_to_user_tool,
                    visualize_spatial_development_plan_tool

                ],
                handoffs=[handoff(
                    agent=summarization_agent,
                    tool_description_override=SUMMARIZATION_DESCRIPTION,
                )],
                input_guardrails=[guardrail_check],
            )

            placeholder = st.empty()
            try:
                with placeholder.container():
                    result = Runner.run_streamed(agent, conversation_state.all_messages, max_turns=25)

                    final_output = ""
                    agent_history = ""
                    async for event in result.stream_events():
                        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                            # print(event.data.delta, end="", flush=True)
                            final_output += event.data.delta
                            placeholder.markdown(final_output)
                        # When the agent updates, print that
                        elif event.type == "agent_updated_stream_event":
                            agent_history += f"Using Agent <b><i>{event.new_agent.name}</i></b>\n"
                            placeholder.markdown(PULSE_BOX.format(agent_state=agent_history), unsafe_allow_html=True)
                            continue
                        elif (
                            event.type == "raw_response_event"
                            and isinstance(event.data, ResponseOutputItemDoneEvent)
                            and isinstance(event.data.item, ResponseFunctionToolCall)
                        ):
                            agent_input = json.loads(event.data.item.arguments).get("input", "")
                            # Truncate agent_input if it's too long and add italic styling
                            truncated_input = agent_input[:50] + "..." if len(agent_input) > 50 else agent_input
                            agent_history += (
                                f"Using Tool <b><i>{event.data.item.name}</i></b> - <i>{truncated_input}</i>\n"
                            )
                            placeholder.markdown(PULSE_BOX.format(agent_state=agent_history), unsafe_allow_html=True)
                    return cast(str, result.final_output)
            except InputGuardrailTripwireTriggered:
                response = "I'm sorry, I can't answer that question."
                placeholder.markdown(response)
                return response


def user_query(conversation_state: ConversationState) -> str:
    """Process a user query using an AI agent."""
    # Get event loop for the current thread
    loop = _get_event_loop()
    # Run the agent
    return loop.run_until_complete(_user_query(conversation_state))  # type: ignore


class DocumentAgentHooks(AgentHooks):
    def __init__(self, conversation_state: ConversationState):
        self.conversation_state = conversation_state

    async def on_start(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent[TContext],
    ) -> None:
        LOGGER.info("Uploading files to the vector store")
        # before the agent is invoked, we need to upload all the files to the vector store
        await self.conversation_state.document_store.upload_files(self.conversation_state.files)
        # update the vector store id in the tool
        agent.tools[0].vector_store_ids = [self.conversation_state.document_store.vector_store_id]
        LOGGER.info("Files uploaded to the vector store")
