"""Prometheus metrics for the inndxd API."""

from fastapi import Response
from prometheus_client import REGISTRY, Counter, Histogram, generate_latest

briefs_created = Counter(
    "inndxd_briefs_created_total",
    "Total number of briefs created",
)

agent_run_duration = Histogram(
    "inndxd_agent_run_duration_seconds",
    "Duration of agent graph execution",
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

data_items_collected = Counter(
    "inndxd_data_items_collected_total",
    "Total number of data items collected",
)


def get_metrics() -> Response:
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain",
    )
