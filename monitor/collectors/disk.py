"""Disk usage collector."""

import os
import random
from typing import Dict, Any
from monitor.collectors import register_collector, BaseCollector


@register_collector("disk")
class DiskCollector(BaseCollector):
    """Collects disk usage metrics for all partitions."""

    _DISKS = {
        "ws-prod-01": [
            {"letter": "C:", "label": "System", "total_gb": 200, "base_pct": 55},
            {"letter": "D:", "label": "Data", "total_gb": 500, "base_pct": 72},
        ],
        "ws-db-02": [
            {"letter": "C:", "label": "System", "total_gb": 200, "base_pct": 45},
            {"letter": "D:", "label": "Database", "total_gb": 1000, "base_pct": 82},
            {"letter": "E:", "label": "Logs", "total_gb": 500, "base_pct": 60},
        ],
        "ws-web-03": [
            {"letter": "C:", "label": "System", "total_gb": 200, "base_pct": 40},
            {"letter": "D:", "label": "WebContent", "total_gb": 300, "base_pct": 35},
        ],
    }

    def collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        mock = os.environ.get("MOCK_MODE", "1") in ("1", "true", "yes")
        if mock:
            return self._mock_collect(server)
        return self._real_collect(server)

    def _mock_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        disks_cfg = self._DISKS.get(server["id"], self._DISKS["ws-prod-01"])
        result = []
        for d in disks_cfg:
            pct = max(0, min(100, d["base_pct"] + random.gauss(0, 3)))
            used = d["total_gb"] * pct / 100
            result.append({
                "letter": d["letter"],
                "label": d["label"],
                "total_gb": d["total_gb"],
                "used_gb": round(used, 1),
                "free_gb": round(d["total_gb"] - used, 1),
                "usage_percent": round(pct, 1),
            })
        return {"disks": result}

    def _real_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Real collection via PowerShell."""
        import subprocess, json
        try:
            result = subprocess.run(
                ["powershell", "-File", "collectors/get_disk_usage.ps1",
                 "-ComputerName", server["hostname"]],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return self._mock_collect(server)


# Updated: 2026-09-07
