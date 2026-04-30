"""Custom node plugin interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AgentNodePlugin(ABC):
    name: str = "base_plugin"

    @abstractmethod
    async def execute(self, state: dict) -> dict: ...


_plugin_registry: dict[str, type[AgentNodePlugin]] = {}


def register_plugin(name: str, plugin_cls: type[AgentNodePlugin]) -> None:
    _plugin_registry[name] = plugin_cls


def get_plugin(name: str) -> type[AgentNodePlugin] | None:
    return _plugin_registry.get(name)


def list_plugins() -> list[str]:
    return list(_plugin_registry.keys())
