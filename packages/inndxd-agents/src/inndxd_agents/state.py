# packages/inndxd-agents/src/inndxd_agents/state.py

import operator
from typing import Annotated

from langgraph.graph import MessagesState


class ResearchState(MessagesState):
    brief_id: str
    tenant_id: str
    project_id: str
    natural_language: str
    plan: str | None
    collected_data: Annotated[list, operator.add]
    structured_items: Annotated[list, operator.add]
    errors: Annotated[list[str], operator.add]
