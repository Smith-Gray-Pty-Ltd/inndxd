"""Benchmark endpoint — admin only."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from inndxd_agents.benchmark import benchmark_research

from inndxd_api.auth_deps import require_admin

router = APIRouter()


@router.post("/")
async def run_benchmark(
    query: str,
    runs: int = 3,
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    result = await benchmark_research(query, runs=runs)
    return result
