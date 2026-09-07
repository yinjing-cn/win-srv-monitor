"""Pydantic data models for metrics, alerts, and server state."""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CPUData(BaseModel):
    """CPU usage snapshot."""
    usage_percent: float = Field(ge=0, le=100)
    core_count: int = Field(default=4, ge=1)
    load_1m: float = Field(default=0.0, ge=0)
    load_5m: float = Field(default=0.0, ge=0)
    load_15m: float = Field(default=0.0, ge=0)


class MemoryData(BaseModel):
    """Memory usage snapshot."""
    total_gb: float = Field(gt=0)
    used_gb: float = Field(ge=0)
    usage_percent: float = Field(ge=0, le=100)
    available_gb: float = Field(ge=0)


class DiskData(BaseModel):
    """Single disk partition snapshot."""
    letter: str
    label: str = ""
    total_gb: float = Field(gt=0)
    used_gb: float = Field(ge=0)
    free_gb: float = Field(ge=0)
    usage_percent: float = Field(ge=0, le=100)


class ServiceData(BaseModel):
    """Windows service status."""
    name: str
    display_name: str
    status: str  # Running, Stopped, Paused
    start_type: str = "Automatic"


class ProcessData(BaseModel):
    """Process resource usage."""
    pid: int = Field(ge=0)
    name: str
    cpu_percent: float = Field(ge=0)
    memory_mb: float = Field(ge=0)


class NetworkData(BaseModel):
    """Network interface statistics."""
    interface: str
    bytes_sent_per_sec: float = Field(ge=0)
    bytes_recv_per_sec: float = Field(ge=0)
    packets_sent_per_sec: float = Field(ge=0)
    packets_recv_per_sec: float = Field(ge=0)


class ServerMetrics(BaseModel):
    """Complete metrics snapshot for a single server."""
    server_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    online: bool = True
    cpu: Optional[CPUData] = None
    memory: Optional[MemoryData] = None
    disks: List[DiskData] = Field(default_factory=list)
    services: List[ServiceData] = Field(default_factory=list)
    processes: List[ProcessData] = Field(default_factory=list)
    network: List[NetworkData] = Field(default_factory=list)


class AlertRecord(BaseModel):
    """A single alert event."""
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    server_id: str
    severity: str = "warning"
    metric: str
    message: str
    value: float = 0.0
    threshold: float = 0.0
    acknowledged: bool = False


class OverviewResponse(BaseModel):
    """Aggregated overview KPIs."""
    timestamp: str
    servers_total: int
    servers_online: int
    cpu_avg: float
    memory_avg: float
    disk_alerts: int
    services_down: int
    recent_alerts: int


# Updated: 2026-09-07
