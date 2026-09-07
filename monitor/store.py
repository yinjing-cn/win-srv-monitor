"""In-memory data store with JSON file persistence."""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

from monitor.models import ServerMetrics, AlertRecord


class DataStore:
    """Thread-safe in-memory store with JSON persistence."""

    def __init__(self, data_dir: str = "data", max_history: int = 120):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_history = max_history
        self._metrics: Dict[str, List[ServerMetrics]] = defaultdict(list)
        self._alerts: List[AlertRecord] = []
        self._thresholds: Dict[str, float] = {"cpu": 80.0, "memory": 85.0, "disk": 90.0}
        self._load()

    def add_metrics(self, metrics: ServerMetrics) -> None:
        """Add a metrics snapshot and persist."""
        history = self._metrics[metrics.server_id]
        history.append(metrics)
        if len(history) > self.max_history:
            self._metrics[metrics.server_id] = history[-self.max_history:]
        self._save_metrics()

    def get_latest(self, server_id: str) -> Optional[ServerMetrics]:
        """Get the latest metrics for a server."""
        history = self._metrics.get(server_id, [])
        return history[-1] if history else None

    def get_history(self, server_id: str, metric: str, points: int = 60) -> List[Dict[str, Any]]:
        """Get time series for a specific metric."""
        history = self._metrics.get(server_id, [])
        results = []
        for m in history[-points:]:
            entry = {"timestamp": m.timestamp}
            if metric == "cpu" and m.cpu:
                entry["value"] = m.cpu.usage_percent
            elif metric == "memory" and m.memory:
                entry["value"] = m.memory.usage_percent
            elif metric == "disk" and m.disks:
                entry["value"] = max(d.usage_percent for d in m.disks)
            else:
                entry["value"] = 0
            results.append(entry)
        return results

    def get_all_servers(self) -> List[Dict[str, Any]]:
        """Get summary of all servers."""
        result = []
        for sid, history in self._metrics.items():
            if not history:
                continue
            latest = history[-1]
            result.append({
                "id": latest.server_id,
                "online": latest.online,
                "timestamp": latest.timestamp,
                "cpu": latest.cpu.usage_percent if latest.cpu else None,
                "memory": latest.memory.usage_percent if latest.memory else None,
                "disk_max": max((d.usage_percent for d in latest.disks), default=0),
                "services_total": len(latest.services),
                "services_down": sum(1 for s in latest.services if s.status == "Stopped"),
            })
        return result

    def add_alert(self, alert: AlertRecord) -> None:
        """Record an alert and persist."""
        self._alerts.append(alert)
        if len(self._alerts) > 500:
            self._alerts = self._alerts[-500:]
        self._save_alerts()

    def get_alerts(self, limit: int = 50) -> List[AlertRecord]:
        """Get recent alerts, newest first."""
        return list(reversed(self._alerts[-limit:]))

    @property
    def thresholds(self) -> Dict[str, float]:
        return dict(self._thresholds)

    def update_thresholds(self, updates: Dict[str, float]) -> Dict[str, float]:
        """Update alert thresholds."""
        for key in ("cpu", "memory", "disk"):
            if key in updates:
                val = float(updates[key])
                if 0 < val <= 100:
                    self._thresholds[key] = val
        self._save_thresholds()
        return dict(self._thresholds)

    def _metrics_path(self) -> Path:
        return self.data_dir / "history.json"

    def _alerts_path(self) -> Path:
        return self.data_dir / "alerts.json"

    def _thresholds_path(self) -> Path:
        return self.data_dir / "thresholds.json"

    def _load(self) -> None:
        """Load persisted data from JSON files."""
        if self._metrics_path().exists():
            try:
                data = json.loads(self._metrics_path().read_text())
                for sid, records in data.items():
                    self._metrics[sid] = [ServerMetrics(**r) for r in records]
            except Exception:
                pass
        if self._alerts_path().exists():
            try:
                data = json.loads(self._alerts_path().read_text())
                self._alerts = [AlertRecord(**r) for r in data]
            except Exception:
                pass
        if self._thresholds_path().exists():
            try:
                data = json.loads(self._thresholds_path().read_text())
                self._thresholds.update(data)
            except Exception:
                pass

    def _save_metrics(self) -> None:
        data = {}
        for sid, history in self._metrics.items():
            data[sid] = [json.loads(m.model_dump_json()) for m in history]
        self._metrics_path().write_text(json.dumps(data, indent=2))

    def _save_alerts(self) -> None:
        data = [json.loads(a.model_dump_json()) for a in self._alerts]
        self._alerts_path().write_text(json.dumps(data, indent=2))

    def _save_thresholds(self) -> None:
        self._thresholds_path().write_text(json.dumps(self._thresholds, indent=2))

    def get_overview(self) -> Dict[str, Any]:
        """Compute aggregated KPI overview."""
        servers = self.get_all_servers()
        online = [s for s in servers if s["online"]]
        cpu_vals = [s["cpu"] for s in online if s["cpu"] is not None]
        mem_vals = [s["memory"] for s in online if s["memory"] is not None]
        disk_alert_count = sum(1 for s in servers if s.get("disk_max", 0) > self._thresholds["disk"])
        svc_down = sum(s.get("services_down", 0) for s in servers)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "servers_total": len(servers),
            "servers_online": len(online),
            "cpu_avg": round(sum(cpu_vals) / len(cpu_vals), 1) if cpu_vals else 0,
            "memory_avg": round(sum(mem_vals) / len(mem_vals), 1) if mem_vals else 0,
            "disk_alerts": disk_alert_count,
            "services_down": svc_down,
            "recent_alerts": len(self._alerts[-50:]),
        }


# Updated: 2026-09-07
