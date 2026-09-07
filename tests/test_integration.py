"""Integration tests - end-to-end flow."""

import os
os.environ["MOCK_MODE"] = "1"

from monitor.config import AppConfig
from monitor.store import DataStore
from monitor.scheduler.jobs import run_collection_cycle


class TestEndToEnd:
    def test_full_cycle_then_api(self, config, store, client):
        """Run a collection cycle and verify API returns data."""
        run_collection_cycle(config, store)

        # Overview
        resp = client.get("/api/overview")
        data = resp.get_json()
        assert data["servers_total"] == 3
        assert data["servers_online"] == 3
        assert data["cpu_avg"] > 0

        # Servers
        resp = client.get("/api/servers")
        data = resp.get_json()
        assert len(data) == 3
        ids = {s["id"] for s in data}
        assert "ws-prod-01" in ids

        # Per-server metrics
        for sid in ["ws-prod-01", "ws-db-02", "ws-web-03"]:
            resp = client.get(f"/api/servers/{sid}/cpu")
            assert resp.status_code == 200

    def test_config_from_env(self):
        os.environ["MOCK_MODE"] = "1"
        os.environ["FLASK_PORT"] = "9999"
        cfg = AppConfig.from_env()
        assert cfg.mock_mode is True
        assert cfg.flask_port == 9999
        os.environ["FLASK_PORT"] = "5000"  # Reset

    def test_multiple_cycles_history(self, config, store, client):
        """Run multiple cycles and check history."""
        for _ in range(5):
            run_collection_cycle(config, store)

        history = store.get_history("ws-prod-01", "cpu")
        assert len(history) == 5


# Updated: 2026-09-07
