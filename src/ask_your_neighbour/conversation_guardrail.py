from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)
from pydantic import BaseModel

from ask_your_neighbour.utils import LOGGER


class ConversationGuardrail(BaseModel):
    """A guardrail for the conversation."""
    is_conversation_legit: bool
    reason: str


guardrail_agent = Agent(
    name="Guardrail check",
    instructions=(
        "You are a guardrail for the conversation. "
        "You are responsible for checking if the conversation is legit, or someone is trying to break the rules. "
    ),
    model="gpt-4.1-mini",
    output_type=ConversationGuardrail,
)

@input_guardrail
async def guardrail_check(
    context: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> ConversationGuardrail:
    """
    This is a guardrail for the conversation, which checks if the conversation is legit,
    or someone is trying to break the rules.
    """
    result = await Runner.run(guardrail_agent, input, context=context.context)
    final_output = result.final_output_as(ConversationGuardrail)
    LOGGER.info(f"Guardrail check result: {final_output}.")

    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_conversation_legit,
    )
