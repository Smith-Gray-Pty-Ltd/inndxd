"""Chat planner — streaming LLM agent for interactive project/brief setup."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI

from inndxd_agents.config import settings as agent_settings
from inndxd_agents.llm import create_openai_compatible_client

logger = logging.getLogger(__name__)


async def chat_with_planner(
    messages: list[dict[str, str]],
    context: dict[str, Any] | None = None,
    mode: str = "brief_setup",
    _client: AsyncOpenAI | None = None,
    _model: str | None = None,
) -> AsyncGenerator[str, None]:
    client = _client or create_openai_compatible_client()
    model = _model or agent_settings.llm_model

    system_prompt = _build_system_prompt(mode, context)
    full_messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    full_messages.extend(messages)

    stream = await client.chat.completions.create(
        model=model,
        messages=full_messages,  # type: ignore[arg-type]
        temperature=0.3,
        max_tokens=2048,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content


async def extract_project_context(
    messages: list[dict[str, str]],
    _client: AsyncOpenAI | None = None,
    _model: str | None = None,
) -> dict[str, Any]:
    client = _client or create_openai_compatible_client()
    model = _model or agent_settings.llm_model

    prompt = _EXTRACT_PROJECT_CONTEXT_PROMPT + json.dumps(
        [{"role": m["role"], "content": m["content"]} for m in messages], indent=2
    )

    response = await client.chat.completions.create(
        model=model,
        temperature=0.1,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content or "{}"
    return _parse_json_dict(content)


async def extract_brief_config(
    messages: list[dict[str, str]],
    project_context: dict[str, Any] | None = None,
    _client: AsyncOpenAI | None = None,
    _model: str | None = None,
) -> dict[str, Any]:
    client = _client or create_openai_compatible_client()
    model = _model or agent_settings.llm_model

    ctx_text = json.dumps(project_context) if project_context else "None"
    prompt = _EXTRACT_BRIEF_CONFIG_PROMPT.format(project_context=ctx_text)
    prompt += json.dumps(
        [{"role": m["role"], "content": m["content"]} for m in messages], indent=2
    )

    response = await client.chat.completions.create(
        model=model,
        temperature=0.1,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content or "{}"
    return _parse_json_dict(content)


def _build_system_prompt(mode: str, context: dict[str, Any] | None) -> str:
    if mode == "project_setup":
        return (
            "You are an account manager and research analyst at Inndxd, an AI-powered "
            "research platform. Your job is to interview the user to understand their "
            "project goals, target domains, stakeholders, and data needs.\n\n"
            "Ask focused questions one at a time. Be conversational but precise. "
            "Cover these areas:\n"
            "1. What is the project about? (domains, industries, topics)\n"
            "2. Who are the stakeholders? (who will use this research)\n"
            "3. What kind of data do they need? (structured facts, news, social media)\n"
            "4. Any specific sources, competitors, or companies to track?\n"
            "5. How often should data be refreshed?\n\n"
            "When you have enough information, summarize what you've learned and "
            "suggest they click 'Finish Setup' to save the context."
        )
    if mode == "brief_setup":
        ctx_text = ""
        if context:
            ctx_text = (
                f"\n\nCurrent project context:\n{json.dumps(context, indent=2)}\n\n"
                "Use this context to guide your questions. The user has already "
                "defined these project goals."
            )
        return (
            "You are a research planner at Inndxd. Your job is to help the user "
            "define a specific research brief for their project.\n\n"
            "Given the project context and conversation, help them define:\n"
            "1. What specific data should be collected? (define a data schema)\n"
            "2. Where should we search? (specific domains, social media, APIs)\n"
            "3. How many records do they need?\n"
            "4. Any filters or constraints?\n\n"
            "When you have a clear picture of the data schema, output it as a "
            "```json block so the user can review and approve.\n\n"
            "Be collaborative — the user should feel like they're working with "
            "a research partner, not filling out a form."
        ) + ctx_text
    return mode


_EXTRACT_PROJECT_CONTEXT_PROMPT = """\
Analyze this conversation between a user and an account manager. Extract the project
context as JSON with these fields (use empty arrays/strings if not discussed):

{
  "domains": ["list of domains/topics/industries"],
  "stakeholders": ["who will use this research"],
  "goals": ["what the user wants to achieve"],
  "data_types": ["kinds of data needed"],
  "refresh_frequency": "how often to refresh (e.g. daily, weekly, one-time)",
  "notes": "any other important context"
}

Output ONLY valid JSON, no markdown, no explanation.

Conversation:
"""

_EXTRACT_BRIEF_CONFIG_PROMPT = """\
Project context: {project_context}

Analyze this conversation between a user and a research planner. Extract the
brief configuration as JSON with these fields:

{
  "data_schema": {{"field_name": "description of what to extract"}},
  "sources": ["specific websites, APIs, or domains to search"],
  "max_records": number,
  "refresh_policy": "one-time" or "daily" or "weekly",
  "filters": {{"field": "value constraint"}}
}

Output ONLY valid JSON, no markdown, no explanation.

Conversation:
"""


def _parse_json_dict(text: str) -> dict[str, Any]:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    try:
        return json.loads(text)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from: %s", text[:200])
        return {}
