"""Scheduled job definitions and alert evaluation."""

from __future__ import annotations
import uuid
import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from monitor.config import AppConfig
from monitor.store import DataStore
from monitor.collectors import get_all_collectors
from monitor.models import (
    ServerMetrics, CPUData, MemoryData, DiskData,
    ServiceData, ProcessData, NetworkData, AlertRecord,
)

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


def start_scheduler(app_config: AppConfig, store: DataStore) -> BackgroundScheduler:
    """Start the background scheduler for periodic collection."""
    global _scheduler
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        run_collection_cycle,
        "interval",
        seconds=app_config.collect_interval,
        args=[app_config, store],
        id="collect_metrics",
        name="Collect server metrics",
        max_instances=1,
    )
    _scheduler.start()
    logger.info("Scheduler started (interval=%ds, mock=%s)",
                app_config.collect_interval, app_config.mock_mode)
    run_collection_cycle(app_config, store)
    return _scheduler


def stop_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    _scheduler = None


def run_collection_cycle(config: AppConfig, store: DataStore) -> None:
    """Execute one collection cycle across all servers and collectors."""
    collectors = get_all_collectors()
    logger.debug("Running collection cycle with %d collectors", len(collectors))

    for server in config.servers:
        sid = server["id"]
        cpu_data = None
        mem_data = None
        disks_data = []
        services_data = []
        processes_data = []
        network_data = []

        if "cpu" in collectors:
            raw = collectors["cpu"].collect(server)
            cpu_data = CPUData(**raw)

        if "memory" in collectors:
            raw = collectors["memory"].collect(server)
            mem_data = MemoryData(**raw)

        if "disk" in collectors:
            raw = collectors["disk"].collect(server)
            disks_data = [DiskData(**d) for d in raw.get("disks", [])]

        if "service" in collectors:
            raw = collectors["service"].collect(server)
            services_data = [ServiceData(**s) for s in raw.get("services", [])]

        if "process" in collectors:
            raw = collectors["process"].collect(server)
            processes_data = [ProcessData(**p) for p in raw.get("processes", [])]

        if "network" in collectors:
            raw = collectors["network"].collect(server)
            network_data = [NetworkData(**n) for n in raw.get("network", [])]

        metrics = ServerMetrics(
            server_id=sid,
            timestamp=datetime.utcnow().isoformat(),
            online=True,
            cpu=cpu_data,
            memory=mem_data,
            disks=disks_data,
            services=services_data,
            processes=processes_data,
            network=network_data,
        )
        store.add_metrics(metrics)
        logger.debug("Collected metrics for %s", sid)
        _evaluate_alerts(metrics, config, store)


def _evaluate_alerts(metrics: ServerMetrics, config: AppConfig, store: DataStore) -> None:
    """Check metrics against thresholds and create alerts."""
    th = store.thresholds

    if metrics.cpu and metrics.cpu.usage_percent > th["cpu"]:
        cpu_th = th["cpu"]
        store.add_alert(AlertRecord(
            id=str(uuid.uuid4())[:8],
            server_id=metrics.server_id,
            severity="warning" if metrics.cpu.usage_percent < 90 else "critical",
            metric="cpu",
            message=f"CPU usage {metrics.cpu.usage_percent}% exceeds threshold {cpu_th}%",
            value=metrics.cpu.usage_percent,
            threshold=th["cpu"],
        ))

    if metrics.memory and metrics.memory.usage_percent > th["memory"]:
        mem_th = th["memory"]
        store.add_alert(AlertRecord(
            id=str(uuid.uuid4())[:8],
            server_id=metrics.server_id,
            severity="warning" if metrics.memory.usage_percent < 95 else "critical",
            metric="memory",
            message=f"Memory usage {metrics.memory.usage_percent}% exceeds threshold {mem_th}%",
            value=metrics.memory.usage_percent,
            threshold=th["memory"],
        ))

    for d in metrics.disks:
        if d.usage_percent > th["disk"]:
            disk_th = th["disk"]
            store.add_alert(AlertRecord(
                id=str(uuid.uuid4())[:8],
                server_id=metrics.server_id,
                severity="warning" if d.usage_percent < 95 else "critical",
                metric="disk",
                message=f"Disk {d.letter} ({d.label}) usage {d.usage_percent}% exceeds {disk_th}%",
                value=d.usage_percent,
                threshold=th["disk"],
            ))

    for svc in metrics.services:
        if svc.status == "Stopped" and svc.start_type == "Automatic":
            store.add_alert(AlertRecord(
                id=str(uuid.uuid4())[:8],
                server_id=metrics.server_id,
                severity="critical",
                metric="service",
                message=f"Service '{svc.display_name}' ({svc.name}) is Stopped",
                value=0,
                threshold=0,
            ))


# Updated: 2026-09-07
