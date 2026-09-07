"""Tests for API endpoints."""

import os
import json
os.environ["MOCK_MODE"] = "1"

from monitor.config import AppConfig
from monitor.store import DataStore
from monitor.models import ServerMetrics, CPUData, MemoryData, DiskData, ServiceData, AlertRecord
from monitor.api.routes import init_api


class TestOverviewAPI:
    def test_overview_empty(self, client, store):
        resp = client.get("/api/overview")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "servers_total" in data

    def test_overview_with_data(self, client, store, app):
        # Populate store
        _populate_store(store)
        resp = client.get("/api/overview")
        data = resp.get_json()
        assert data["servers_total"] == 3
        assert data["servers_online"] == 3


class TestServersAPI:
    def test_servers_empty(self, client):
        resp = client.get("/api/servers")
        assert resp.status_code == 200

    def test_servers_with_data(self, client, store):
        _populate_store(store)
        resp = client.get("/api/servers")
        data = resp.get_json()
        assert len(data) == 3


class TestServerMetricsAPI:
    def test_cpu(self, client, store):
        _populate_store(store)
        resp = client.get("/api/servers/ws-prod-01/cpu")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["server_id"] == "ws-prod-01"
        assert data["latest"] is not None

    def test_memory(self, client, store):
        _populate_store(store)
        resp = client.get("/api/servers/ws-db-02/memory")
        assert resp.status_code == 200

    def test_disk(self, client, store):
        _populate_store(store)
        resp = client.get("/api/servers/ws-web-03/disk")
        assert resp.status_code == 200

    def test_services(self, client, store):
        _populate_store(store)
        resp = client.get("/api/servers/ws-prod-01/services")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["services"]) > 0

    def test_processes(self, client, store):
        _populate_store(store)
        resp = client.get("/api/servers/ws-prod-01/processes")
        assert resp.status_code == 200

    def test_network(self, client, store):
        _populate_store(store)
        resp = client.get("/api/servers/ws-prod-01/network")
        assert resp.status_code == 200


class TestAlertsAPI:
    def test_alerts_empty(self, client):
        resp = client.get("/api/alerts")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_thresholds_get(self, client):
        resp = client.get("/api/alerts/threshold")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "cpu" in data

    def test_thresholds_post(self, client, store):
        resp = client.post("/api/alerts/threshold",
                           data=json.dumps({"cpu": 75, "memory": 90}),
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["cpu"] == 75


class TestDashboard:
    def test_homepage(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Windows Server Monitor" in resp.data


def _populate_store(store):
    """Helper to fill store with sample data."""
    for sid in ["ws-prod-01", "ws-db-02", "ws-web-03"]:
        m = ServerMetrics(
            server_id=sid,
            cpu=CPUData(usage_percent=50.0),
            memory=MemoryData(total_gb=32, used_gb=16, usage_percent=50, available_gb=16),
            disks=[DiskData(letter="C:", total_gb=200, used_gb=100, free_gb=100, usage_percent=50)],
            services=[ServiceData(name="W3SVC", display_name="Web Service", status="Running")],
        )
        store.add_metrics(m)


# Updated: 2026-09-07
