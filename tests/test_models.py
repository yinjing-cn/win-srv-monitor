"""Tests for data models."""

import pytest
from monitor.models import (
    CPUData, MemoryData, DiskData, ServiceData,
    ProcessData, NetworkData, ServerMetrics, AlertRecord,
    OverviewResponse,
)


class TestCPUData:
    def test_valid(self):
        d = CPUData(usage_percent=45.0)
        assert d.usage_percent == 45.0
        assert d.core_count == 4

    def test_boundary_zero(self):
        d = CPUData(usage_percent=0)
        assert d.usage_percent == 0

    def test_boundary_hundred(self):
        d = CPUData(usage_percent=100)
        assert d.usage_percent == 100

    def test_invalid_negative(self):
        with pytest.raises(Exception):
            CPUData(usage_percent=-1)

    def test_invalid_over_100(self):
        with pytest.raises(Exception):
            CPUData(usage_percent=101)


class TestMemoryData:
    def test_valid(self):
        d = MemoryData(total_gb=32.0, used_gb=20.0, usage_percent=62.5, available_gb=12.0)
        assert d.total_gb == 32.0
        assert d.usage_percent == 62.5


class TestDiskData:
    def test_valid(self):
        d = DiskData(letter="C:", label="System", total_gb=500, used_gb=250, free_gb=250, usage_percent=50.0)
        assert d.letter == "C:"


class TestServiceData:
    def test_valid(self):
        d = ServiceData(name="W3SVC", display_name="Web Service", status="Running")
        assert d.status == "Running"
        assert d.start_type == "Automatic"


class TestProcessData:
    def test_valid(self):
        d = ProcessData(pid=1234, name="test.exe", cpu_percent=10.5, memory_mb=256)
        assert d.pid == 1234


class TestNetworkData:
    def test_valid(self):
        d = NetworkData(interface="eth0", bytes_sent_per_sec=1000, bytes_recv_per_sec=2000,
                        packets_sent_per_sec=10, packets_recv_per_sec=20)
        assert d.interface == "eth0"


class TestServerMetrics:
    def test_minimal(self):
        m = ServerMetrics(server_id="ws-prod-01")
        assert m.server_id == "ws-prod-01"
        assert m.online is True
        assert m.cpu is None

    def test_full(self):
        m = ServerMetrics(
            server_id="ws-db-02",
            cpu=CPUData(usage_percent=50),
            memory=MemoryData(total_gb=64, used_gb=32, usage_percent=50, available_gb=32),
            disks=[DiskData(letter="C:", total_gb=200, used_gb=100, free_gb=100, usage_percent=50)],
        )
        assert m.cpu.usage_percent == 50
        assert len(m.disks) == 1


class TestAlertRecord:
    def test_valid(self):
        a = AlertRecord(id="a1", server_id="ws-prod-01", metric="cpu", message="High CPU", value=90, threshold=80)
        assert a.severity == "warning"
        assert a.acknowledged is False


# Updated: 2026-09-07
