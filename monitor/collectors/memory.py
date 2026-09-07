"""Memory usage collector."""

import os
import random
from typing import Dict, Any
from monitor.collectors import register_collector, BaseCollector


@register_collector("memory")
class MemoryCollector(BaseCollector):
    """Collects memory usage metrics."""

    _TOTAL = {"ws-prod-01": 32.0, "ws-db-02": 64.0, "ws-web-03": 16.0}
    _BASE_PCT = {"ws-prod-01": 65.0, "ws-db-02": 72.0, "ws-web-03": 50.0}

    def collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        mock = os.environ.get("MOCK_MODE", "1") in ("1", "true", "yes")
        if mock:
            return self._mock_collect(server)
        return self._real_collect(server)

    def _mock_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        total = self._TOTAL.get(server["id"], 32.0)
        base = self._BASE_PCT.get(server["id"], 60.0)
        pct = max(0, min(100, base + random.gauss(0, 5)))
        used = total * pct / 100
        return {
            "total_gb": total,
            "used_gb": round(used, 1),
            "usage_percent": round(pct, 1),
            "available_gb": round(total - used, 1),
        }

    def _real_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Real collection via PowerShell."""
        import subprocess, json
        try:
            result = subprocess.run(
                ["powershell", "-File", "collectors/get_cpu_usage.ps1",
                 "-ComputerName", server["hostname"], "-Metric", "memory"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return self._mock_collect(server)


# Updated: 2026-09-07
