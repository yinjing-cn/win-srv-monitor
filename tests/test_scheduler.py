"""Tests for the scheduler module."""

import os
os.environ["MOCK_MODE"] = "1"

from monitor.config import AppConfig
from monitor.store import DataStore
from monitor.scheduler.jobs import run_collection_cycle, _evaluate_alerts
from monitor.models import ServerMetrics, CPUData, MemoryData, DiskData, ServiceData


class TestCollectionCycle:
    def test_cycle_populates_store(self, config, store):
        run_collection_cycle(config, store)
        for server in config.servers:
            latest = store.get_latest(server["id"])
            assert latest is not None
            assert latest.cpu is not None
            assert latest.memory is not None

    def test_cycle_multiple_runs(self, config, store):
        run_collection_cycle(config, store)
        run_collection_cycle(config, store)
        history = store.get_history("ws-prod-01", "cpu")
        assert len(history) == 2


class TestAlertEvaluation:
    def test_cpu_alert(self, config, store):
        m = ServerMetrics(
            server_id="ws-prod-01",
            cpu=CPUData(usage_percent=95.0),
        )
        _evaluate_alerts(m, config, store)
        alerts = store.get_alerts()
        assert len(alerts) >= 1
        assert any(a.metric == "cpu" for a in alerts)

    def test_memory_alert(self, config, store):
        m = ServerMetrics(
            server_id="ws-db-02",
            memory=MemoryData(total_gb=64, used_gb=58, usage_percent=90, available_gb=6),
        )
        _evaluate_alerts(m, config, store)
        alerts = store.get_alerts()
        assert any(a.metric == "memory" for a in alerts)

    def test_disk_alert(self, config, store):
        m = ServerMetrics(
            server_id="ws-web-03",
            disks=[DiskData(letter="D:", label="Data", total_gb=500, used_gb=460, free_gb=40, usage_percent=92)],
        )
        _evaluate_alerts(m, config, store)
        alerts = store.get_alerts()
        assert any(a.metric == "disk" for a in alerts)

    def test_service_alert(self, config, store):
        m = ServerMetrics(
            server_id="ws-prod-01",
            services=[ServiceData(name="MSSQLSERVER", display_name="SQL Server", status="Stopped", start_type="Automatic")],
        )
        _evaluate_alerts(m, config, store)
        alerts = store.get_alerts()
        assert any(a.metric == "service" for a in alerts)

    def test_no_alert_below_threshold(self, config, store):
        m = ServerMetrics(
            server_id="ws-prod-01",
            cpu=CPUData(usage_percent=30.0),
            memory=MemoryData(total_gb=32, used_gb=10, usage_percent=31, available_gb=22),
        )
        _evaluate_alerts(m, config, store)
        alerts = store.get_alerts()
        assert len(alerts) == 0


# Updated: 2026-09-07
