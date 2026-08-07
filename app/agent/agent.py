# agent/agent.py
import logfire
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.nodes.chat_node import chat
from app.agent.state import AgentState
from app.agent.tools.rag_tool import rag_search_tool

"""Agent Graph Definition Module.

This module sets up the stateful execution graph using LangGraph.
It wires the main chat node with the RAG tool node and manages conditional routing
and short-term conversational memory.
"""

# Track graph compilation and setup via Logfire
with logfire.span("Initializing Agent Graph"):
    # Initialize in-memory state checkpointer for short-term thread memory
    checkpointer = InMemorySaver()

    # Initialize State Graph with schema
    builder = StateGraph(AgentState)

    # Register graph nodes
    builder.add_node("chat_node", chat)

    tools = [rag_search_tool]
    builder.add_node("tools", ToolNode(tools))

    # Define graph execution flow (Edges)
    builder.set_entry_point("chat_node")

    # Route conditionally: Send to 'tools' if tool calls exist, else route to END
    builder.add_conditional_edges("chat_node", tools_condition)
    
    # Loop tool outputs back to the chat node to synthesize final answer
    builder.add_edge("tools", "chat_node")

    # Compile executable graph instance with checkpointer
    rag_agent= builder.compile(checkpointer=checkpointer)