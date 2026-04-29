from __future__ import annotations

from operator import add
from typing import Annotated, Any, Sequence
from uuid import UUID
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    brief_id: UUID
    tenant_id: UUID
    project_id: UUID
    natural_language: str
    messages: Annotated[Sequence[dict[str, Any]], add_messages]
    plan: str | None
    collected_data: Annotated[list[dict[str, Any]], add]
    structured_items: Annotated[list[dict[str, Any]], add]
    errors: Annotated[list[str], add]