"""Network statistics collector."""

import os
import random
from typing import Dict, Any
from monitor.collectors import register_collector, BaseCollector


@register_collector("network")
class NetworkCollector(BaseCollector):
    """Collects network interface statistics."""

    _BASE_BW = {
        "ws-prod-01": {"sent": 50_000_000, "recv": 120_000_000},
        "ws-db-02": {"sent": 30_000_000, "recv": 80_000_000},
        "ws-web-03": {"sent": 80_000_000, "recv": 40_000_000},
    }

    def collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        mock = os.environ.get("MOCK_MODE", "1") in ("1", "true", "yes")
        if mock:
            return self._mock_collect(server)
        return self._real_collect(server)

    def _mock_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        base = self._BASE_BW.get(server["id"], {"sent": 40_000_000, "recv": 60_000_000})
        sent = max(0, base["sent"] + random.gauss(0, base["sent"] * 0.1))
        recv = max(0, base["recv"] + random.gauss(0, base["recv"] * 0.1))
        return {
            "network": [{
                "interface": "Ethernet0",
                "bytes_sent_per_sec": round(sent, 0),
                "bytes_recv_per_sec": round(recv, 0),
                "packets_sent_per_sec": round(sent / 1200, 0),
                "packets_recv_per_sec": round(recv / 1200, 0),
            }]
        }

    def _real_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Real collection via PowerShell."""
        import subprocess, json
        try:
            result = subprocess.run(
                ["powershell", "-File", "collectors/get_network_stats.ps1",
                 "-ComputerName", server["hostname"]],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return self._mock_collect(server)


# Updated: 2026-09-07
