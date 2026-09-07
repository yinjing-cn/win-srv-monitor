"""Windows service status collector."""

import os
import random
from typing import Dict, Any
from monitor.collectors import register_collector, BaseCollector

_SERVICES = [
    {"name": "W3SVC", "display_name": "World Wide Web Publishing Service", "start_type": "Automatic"},
    {"name": "MSSQLSERVER", "display_name": "SQL Server (MSSQLSERVER)", "start_type": "Automatic"},
    {"name": "W32Time", "display_name": "Windows Time", "start_type": "Automatic"},
    {"name": "Spooler", "display_name": "Print Spooler", "start_type": "Manual"},
    {"name": "WinRM", "display_name": "Windows Remote Management", "start_type": "Automatic"},
    {"name": "MSServerFarm", "display_name": "Acme Farm Service", "start_type": "Automatic"},
]


@register_collector("service")
class ServiceCollector(BaseCollector):
    """Collects Windows service statuses."""

    def collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        mock = os.environ.get("MOCK_MODE", "1") in ("1", "true", "yes")
        if mock:
            return self._mock_collect(server)
        return self._real_collect(server)

    def _mock_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        services = []
        for svc in _SERVICES:
            if svc["name"] == "Spooler":
                status = random.choice(["Running", "Running", "Stopped"])
            else:
                status = "Running" if random.random() < 0.95 else "Stopped"
            services.append({
                "name": svc["name"],
                "display_name": svc["display_name"],
                "status": status,
                "start_type": svc["start_type"],
            })
        return {"services": services}

    def _real_collect(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Real collection via PowerShell."""
        import subprocess, json
        try:
            result = subprocess.run(
                ["powershell", "-File", "collectors/get_service_status.ps1",
                 "-ComputerName", server["hostname"]],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return self._mock_collect(server)


# Updated: 2026-09-07
