"""CPU usage collector."""

import os
import random
from typing import Dict, Any
from monitor.collectors import register_collector, BaseCollector


@register_collector("cpu")
class CPUCollector(BaseCollector):
    """Collects CPU usage metrics."""

    _BASE = {"ws-prod-01": 55.0, "ws-db-02": 40.0, "ws-web-03": 35.0}

    def collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        mock = os.environ.get("MOCK_MODE", "1") in ("1", "true", "yes")
        if mock:
            return self._mock_collect(server)
        return self._real_collect(server)

    def _mock_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        base = self._BASE.get(server["id"], 45.0)
        usage = max(0, min(100, base + random.gauss(0, 8)))
        return {
            "usage_percent": round(usage, 1),
            "core_count": 8,
            "load_1m": round(usage / 100 * 8 * random.uniform(0.8, 1.2), 2),
            "load_5m": round(usage / 100 * 8 * random.uniform(0.85, 1.15), 2),
            "load_15m": round(usage / 100 * 8 * random.uniform(0.9, 1.1), 2),
        }

    def _real_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Real collection via PowerShell (requires Windows)."""
        import subprocess, json
        script = "collectors/get_cpu_usage.ps1"
        try:
            result = subprocess.run(
                ["powershell", "-File", script, "-ComputerName", server["hostname"]],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return self._mock_collect(server)


# Updated: 2026-09-07
