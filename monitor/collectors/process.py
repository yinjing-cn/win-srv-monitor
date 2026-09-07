"""Process ranking collector."""

import os
import random
from typing import Dict, Any
from monitor.collectors import register_collector, BaseCollector

_PROCESSES = [
    "sqlservr.exe", "w3wp.exe", "java.exe", "dotnet.exe",
    "Memory Compression", "svchost.exe", "WerFault.exe", "msmdsrv.exe",
]


@register_collector("process")
class ProcessCollector(BaseCollector):
    """Collects top processes by CPU usage."""

    def collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        mock = os.environ.get("MOCK_MODE", "1") in ("1", "true", "yes")
        if mock:
            return self._mock_collect(server)
        return self._real_collect(server)

    def _mock_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        random.seed(hash(server["id"]) % 2**32 + random.randint(0, 1000))
        procs = []
        for i, name in enumerate(random.sample(_PROCESSES, min(5, len(_PROCESSES)))):
            cpu_pct = max(0, random.gauss(15 - i * 2, 5))
            mem_mb = max(10, random.gauss(500 - i * 50, 100))
            procs.append({
                "pid": random.randint(1000, 50000),
                "name": name,
                "cpu_percent": round(cpu_pct, 1),
                "memory_mb": round(mem_mb, 0),
            })
        procs.sort(key=lambda p: p["cpu_percent"], reverse=True)
        return {"processes": procs[:5]}

    def _real_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Real collection - not yet implemented, fallback to mock."""
        return self._mock_collect(server)


# Updated: 2026-09-07
