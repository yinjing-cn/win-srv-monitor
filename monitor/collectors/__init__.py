"""Collector registry and base class.

Usage:
    from monitor.collectors import register_collector, BaseCollector

    @register_collector("gpu")
    class GPUCollector(BaseCollector):
        def collect(self, server):
            return {"gpu_usage": 42}
"""

from __future__ import annotations
from typing import Dict, Type, Any, Optional
from abc import ABC, abstractmethod

_REGISTRY: Dict[str, Type["BaseCollector"]] = {}


def register_collector(name: str):
    """Decorator to register a collector class."""
    def decorator(cls: Type[BaseCollector]) -> Type[BaseCollector]:
        if not issubclass(cls, BaseCollector):
            raise TypeError(f"{cls.__name__} must extend BaseCollector")
        _REGISTRY[name] = cls
        return cls
    return decorator


def get_collector(name: str) -> Optional["BaseCollector"]:
    """Instantiate a registered collector by name."""
    cls = _REGISTRY.get(name)
    return cls() if cls else None


def get_all_collectors() -> Dict[str, "BaseCollector"]:
    """Instantiate all registered collectors."""
    return {name: cls() for name, cls in _REGISTRY.items()}


def list_collector_names() -> list:
    """Return names of all registered collectors."""
    return list(_REGISTRY.keys())


class BaseCollector(ABC):
    """Base class for all data collectors."""

    @abstractmethod
    def collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Collect data for a single server.

        Args:
            server: Server info dict with keys like id, hostname, ip, role, os.

        Returns:
            Dict of collected metric data.
        """
        ...


# Auto-import collector modules so decorators execute
from monitor.collectors import cpu, memory, disk, service, network, process  # noqa: E402, F401

# Updated: 2026-09-07
