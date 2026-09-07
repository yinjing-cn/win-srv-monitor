"""Configuration management with environment variable support."""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any

DEFAULT_SERVERS = [
    {
        "id": "ws-prod-01",
        "hostname": "WS-PROD-01",
        "ip": "10.0.1.10",
        "role": "Production Application Server",
        "os": "Windows Server 2022",
    },
    {
        "id": "ws-db-02",
        "hostname": "WS-DB-02",
        "ip": "10.0.1.20",
        "role": "Database Server",
        "os": "Windows Server 2022",
    },
    {
        "id": "ws-web-03",
        "hostname": "WS-WEB-03",
        "ip": "10.0.1.30",
        "role": "Web Frontend Server",
        "os": "Windows Server 2019",
    },
]

DEFAULT_THRESHOLDS = {"cpu": 80.0, "memory": 85.0, "disk": 90.0}


@dataclass
class AppConfig:
    """Application configuration loaded from environment."""

    mock_mode: bool = True
    flask_host: str = "0.0.0.0"
    flask_port: int = 5000
    collect_interval: int = 30
    data_dir: str = "data"
    servers: List[Dict[str, Any]] = field(default_factory=lambda: list(DEFAULT_SERVERS))
    thresholds: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_THRESHOLDS))
    history_points: int = 120

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables."""
        mock_mode = os.environ.get("MOCK_MODE", "1").strip() in ("1", "true", "yes")
        flask_host = os.environ.get("FLASK_HOST", "0.0.0.0")
        flask_port = int(os.environ.get("FLASK_PORT", "5000"))
        collect_interval = int(os.environ.get("COLLECT_INTERVAL", "30"))
        data_dir = os.environ.get("DATA_DIR", "data")
        servers_raw = os.environ.get("SERVERS", "")
        if servers_raw:
            try:
                servers = json.loads(servers_raw)
            except json.JSONDecodeError:
                servers = list(DEFAULT_SERVERS)
        else:
            servers = list(DEFAULT_SERVERS)
        return cls(
            mock_mode=mock_mode,
            flask_host=flask_host,
            flask_port=flask_port,
            collect_interval=collect_interval,
            data_dir=data_dir,
            servers=servers,
        )

    def ensure_data_dir(self) -> Path:
        """Ensure data directory exists and return its path."""
        p = Path(self.data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


# Updated: 2026-09-07
