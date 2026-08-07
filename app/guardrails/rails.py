
import logfire
from nemoguardrails import RailsConfig, LLMRails

from app.gateways.chat_client import get_langchain_llm
from app.guardrails.colang_rules import (
    COLANG_CONTENT,
    YAML_CONTENT,
    RAIL_INDICATORS,
)

_rails: LLMRails | None = None


def initialize_rails() -> None:
    """
    Build the NeMo Guardrails singleton at application startup.
    """
    global _rails

    guard_llm = get_langchain_llm(feature="guardrails")

    config = RailsConfig.from_content(
        colang_content=COLANG_CONTENT,
        yaml_content=YAML_CONTENT,
    )

    _rails = LLMRails(config=config, llm=guard_llm)

    logfire.info("NeMo Guardrails initialized successfully.")


async def guard(message: str) -> tuple[bool, str | None]:
    if _rails is None:
        logfire.warning("Guardrails not initialized. Skipping validation.")
        return False, None

    with logfire.span("Guardrails Check"):
        result = await _rails.generate_async(
            messages=[{"role": "user", "content": message}]
        )
        
        # 1. Content Safe Extract
        if isinstance(result, dict):
            content = result.get("content", "")
        elif hasattr(result, "content"):
            content = str(result.content)
        else:
            content = str(result)

        content_lower = content.lower()

        # 2. Dynamic check for any refusal / rail signature
        fired = any(
            indicator.lower() in content_lower
            for indicator in RAIL_INDICATORS
        ) or "pydantic-ai" in content_lower  # Short-circuit check if bot re-routes to scope

        if fired:
            logfire.info(f"Guardrail triggered | query='{message[:80]}'")
            return True, content

        logfire.info("Guardrails passed.")
        return False, None