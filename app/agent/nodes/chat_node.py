
import logfire
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from app.agent.nodes.prompt import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.agent.tools.rag_tool import rag_search_tool
from app.gateways.chat_client import get_langchain_llm

# Load environment variables from .env file
load_dotenv()

# Configure observability and tracing
logfire.configure()
logfire.instrument_openai()

# Initialize LLM (Portkey Gateway handles load balancing, fallback & retries) and bind tools
llm = get_langchain_llm(feature="rag")

tools = [rag_search_tool]
llm_with_tools = llm.bind_tools(tools)


def chat(state: AgentState) -> dict:
    """Executes the chat node within the agent workflow.

    This function processes the input state, appends the system prompt if missing,
    invokes the LLM with tool-calling capabilities, and logs execution details
    using Logfire for observability.

    Args:
        state (AgentState): The current state of the agent containing conversation history.

    Returns:
        dict: Updated state containing the new LLM message response and the extracted current query.
    """
    with logfire.span("chat_node_execution") as span:
        messages = state.get("messages", [])

        # Prevent adding duplicate System Messages
        if not messages or not isinstance(messages[0], SystemMessage):
            messages_with_prompt = [SYSTEM_PROMPT] + list(messages)
        else:
            messages_with_prompt = messages

        # Log total input messages to Logfire span
        span.set_attribute("input_message_count", len(messages_with_prompt))

        # Invoke the LLM with the prepared message chain
        try:
            with logfire.span("llm_call"):
                response = llm_with_tools.invoke(messages_with_prompt)
                span.set_attribute("llm_provider", "portkey")

        except Exception as e:
            logfire.exception(
                "LLM call via Portkey Gateway failed.",
                exc_info=e,
            )
            span.set_attribute("error", str(e))
            raise

        # Track tool usage for observability
        has_tool_calls = bool(response.tool_calls)
        span.set_attribute("tool_called", has_tool_calls)

        if has_tool_calls:
            span.set_attribute("tool_name", response.tool_calls[0]["name"])

        # Return the updated state update dictionary
        return {"messages": [response],}