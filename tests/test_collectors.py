"""Tests for individual collectors in mock mode."""

import os
os.environ["MOCK_MODE"] = "1"

from monitor.collectors import get_collector


SERVER = {"id": "ws-prod-01", "hostname": "WS-PROD-01", "ip": "10.0.1.10", "role": "Prod", "os": "Windows Server 2022"}


class TestCPUCollector:
    def test_collect(self):
        c = get_collector("cpu")
        data = c.collect(SERVER)
        assert "usage_percent" in data
        assert 0 <= data["usage_percent"] <= 100
        assert data["core_count"] == 8

    def test_multiple_calls(self):
        c = get_collector("cpu")
        results = [c.collect(SERVER)["usage_percent"] for _ in range(10)]
        assert all(0 <= r <= 100 for r in results)


class TestMemoryCollector:
    def test_collect(self):
        c = get_collector("memory")
        data = c.collect(SERVER)
        assert data["total_gb"] == 32.0
        assert 0 <= data["usage_percent"] <= 100


class TestDiskCollector:
    def test_collect(self):
        c = get_collector("disk")
        data = c.collect(SERVER)
        assert "disks" in data
        assert len(data["disks"]) == 2
        for d in data["disks"]:
            assert 0 <= d["usage_percent"] <= 100

    def test_db_server(self):
        c = get_collector("disk")
        db_server = {"id": "ws-db-02", "hostname": "WS-DB-02"}
        data = c.collect(db_server)
        assert len(data["disks"]) == 3


class TestServiceCollector:
    def test_collect(self):
        c = get_collector("service")
        data = c.collect(SERVER)
        assert "services" in data
        assert len(data["services"]) > 0
        for s in data["services"]:
            assert s["status"] in ("Running", "Stopped", "Paused")


class TestNetworkCollector:
    def test_collect(self):
        c = get_collector("network")
        data = c.collect(SERVER)
        assert "network" in data
        assert len(data["network"]) >= 1
        n = data["network"][0]
        assert n["bytes_sent_per_sec"] >= 0


class TestProcessCollector:
    def test_collect(self):
        c = get_collector("process")
        data = c.collect(SERVER)
        assert "processes" in data
        assert len(data["processes"]) <= 5
        for p in data["processes"]:
            assert p["cpu_percent"] >= 0
            assert p["memory_mb"] >= 0


# Updated: 2026-09-07
