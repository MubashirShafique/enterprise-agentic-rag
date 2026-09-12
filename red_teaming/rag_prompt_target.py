"""
Custom PyRIT PromptTarget adapter for the live Enterprise RAG endpoint.
"""

import uuid
from typing import Any

from pyrit.models import Message, MessagePiece
from pyrit.prompt_target import PromptTarget
from pyrit.prompt_target.common.target_capabilities import TargetCapabilities
from pyrit.prompt_target.common.target_configuration import TargetConfiguration

from rag_client import query_rag_system


class EnterpriseRagTarget(PromptTarget):
    """
    Adapts the Enterprise RAG /query endpoint to PyRIT's PromptTarget interface.

    The target uses a LangGraph thread_id to maintain conversation state
    across multiple Crescendo turns.
    """

    def __init__(self, **kwargs: Any) -> None:
        capabilities = TargetCapabilities(
            supports_multi_turn=True,
            supports_editable_history=True,
        )

        configuration = TargetConfiguration(
            capabilities=capabilities,
        )

        super().__init__(
            custom_configuration=configuration,
            **kwargs,
        )

        # One LangGraph conversation/thread for this target instance.
        self._thread_id = str(uuid.uuid4())

    async def _send_prompt_to_target_async(
        self,
        *,
        normalized_conversation: list[Message],
    ) -> list[Message]:
        """
        Send the latest user message to the Enterprise RAG backend.
        """

        if not normalized_conversation:
            raise ValueError("normalized_conversation cannot be empty")

        # Crescendo sends the conversation history to PyRIT.
        # The Enterprise RAG backend only needs the latest user prompt because
        # LangGraph maintains the conversation using thread_id.
        current_message = normalized_conversation[-1]

        message_piece = current_message.get_piece()

        if message_piece is None:
            raise ValueError("The latest message contains no message piece")

        user_text = message_piece.original_value

        if not user_text:
            raise ValueError("The latest user message is empty")

        # Send request to the actual RAG system.
        rag_response_text = await query_rag_system(
            user_text,
            thread_id=self._thread_id,
        )

        return [
            Message(
                message_pieces=[
                    MessagePiece(
                        role="assistant",
                        original_value=str(rag_response_text),
                    )
                ]
            )
        ]