"""Tests for the DataStore."""

import os
os.environ["MOCK_MODE"] = "1"

from monitor.store import DataStore
from monitor.models import ServerMetrics, CPUData, MemoryData, DiskData, AlertRecord


class TestDataStore:
    def test_add_and_get_latest(self, store):
        m = ServerMetrics(
            server_id="test-srv",
            cpu=CPUData(usage_percent=50),
            memory=MemoryData(total_gb=32, used_gb=16, usage_percent=50, available_gb=16),
        )
        store.add_metrics(m)
        latest = store.get_latest("test-srv")
        assert latest is not None
        assert latest.cpu.usage_percent == 50

    def test_get_latest_empty(self, store):
        assert store.get_latest("nonexistent") is None

    def test_history_trim(self, tmp_data_dir):
        store = DataStore(data_dir=tmp_data_dir, max_history=5)
        for i in range(10):
            m = ServerMetrics(server_id="s1", cpu=CPUData(usage_percent=float(i)))
            store.add_metrics(m)
        history = store.get_history("s1", "cpu")
        assert len(history) == 5

    def test_get_history_cpu(self, store):
        m = ServerMetrics(server_id="s1", cpu=CPUData(usage_percent=42.0))
        store.add_metrics(m)
        h = store.get_history("s1", "cpu")
        assert len(h) == 1
        assert h[0]["value"] == 42.0

    def test_get_all_servers(self, store):
        m1 = ServerMetrics(server_id="s1", cpu=CPUData(usage_percent=30),
                           memory=MemoryData(total_gb=16, used_gb=8, usage_percent=50, available_gb=8))
        m2 = ServerMetrics(server_id="s2", cpu=CPUData(usage_percent=60),
                           memory=MemoryData(total_gb=32, used_gb=16, usage_percent=50, available_gb=16))
        store.add_metrics(m1)
        store.add_metrics(m2)
        servers = store.get_all_servers()
        assert len(servers) == 2

    def test_alerts(self, store):
        a = AlertRecord(id="a1", server_id="s1", metric="cpu", message="High", value=90, threshold=80)
        store.add_alert(a)
        alerts = store.get_alerts()
        assert len(alerts) == 1
        assert alerts[0].id == "a1"

    def test_thresholds(self, store):
        th = store.thresholds
        assert th["cpu"] == 80.0
        updated = store.update_thresholds({"cpu": 75, "memory": 90})
        assert updated["cpu"] == 75
        assert updated["memory"] == 90

    def test_overview(self, store):
        m = ServerMetrics(server_id="s1", cpu=CPUData(usage_percent=50),
                          memory=MemoryData(total_gb=16, used_gb=8, usage_percent=50, available_gb=8))
        store.add_metrics(m)
        ov = store.get_overview()
        assert ov["servers_total"] == 1
        assert ov["servers_online"] == 1

    def test_persistence(self, tmp_data_dir):
        store1 = DataStore(data_dir=tmp_data_dir)
        m = ServerMetrics(server_id="persist-test", cpu=CPUData(usage_percent=77))
        store1.add_metrics(m)
        # New store instance reads from same dir
        store2 = DataStore(data_dir=tmp_data_dir)
        latest = store2.get_latest("persist-test")
        assert latest is not None
        assert latest.cpu.usage_percent == 77


# Updated: 2026-09-07
