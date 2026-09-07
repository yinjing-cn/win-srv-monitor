"""REST API route handlers."""

from __future__ import annotations
from flask import Blueprint, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")

_store = None
_config = None


def init_api(store, config):
    """Inject store and config into the blueprint module."""
    global _store, _config
    _store = store
    _config = config


@api_bp.route("/overview")
def overview():
    """GET /api/overview - Aggregated KPI summary."""
    return jsonify(_store.get_overview())


@api_bp.route("/servers")
def servers():
    """GET /api/servers - List all monitored servers."""
    data = _store.get_all_servers()
    server_info = {s["id"]: s for s in _config.servers}
    result = []
    for s in data:
        info = server_info.get(s["id"], {})
        result.append({**s, **{k: info[k] for k in ("hostname", "ip", "role", "os") if k in info}})
    return jsonify(result)


@api_bp.route("/servers/<server_id>/cpu")
def server_cpu(server_id):
    """GET /api/servers/<id>/cpu - CPU time series."""
    history = _store.get_history(server_id, "cpu")
    latest = _store.get_latest(server_id)
    return jsonify({
        "server_id": server_id,
        "latest": latest.cpu.model_dump() if latest and latest.cpu else None,
        "history": history,
    })


@api_bp.route("/servers/<server_id>/memory")
def server_memory(server_id):
    """GET /api/servers/<id>/memory - Memory time series."""
    history = _store.get_history(server_id, "memory")
    latest = _store.get_latest(server_id)
    return jsonify({
        "server_id": server_id,
        "latest": latest.memory.model_dump() if latest and latest.memory else None,
        "history": history,
    })


@api_bp.route("/servers/<server_id>/disk")
def server_disk(server_id):
    """GET /api/servers/<id>/disk - Disk time series."""
    history = _store.get_history(server_id, "disk")
    latest = _store.get_latest(server_id)
    return jsonify({
        "server_id": server_id,
        "latest": [d.model_dump() for d in latest.disks] if latest else [],
        "history": history,
    })


@api_bp.route("/servers/<server_id>/services")
def server_services(server_id):
    """GET /api/servers/<id>/services - Windows service statuses."""
    latest = _store.get_latest(server_id)
    return jsonify({
        "server_id": server_id,
        "services": [s.model_dump() for s in latest.services] if latest else [],
    })


@api_bp.route("/servers/<server_id>/processes")
def server_processes(server_id):
    """GET /api/servers/<id>/processes - Top processes."""
    latest = _store.get_latest(server_id)
    return jsonify({
        "server_id": server_id,
        "processes": [p.model_dump() for p in latest.processes] if latest else [],
    })


@api_bp.route("/servers/<server_id>/network")
def server_network(server_id):
    """GET /api/servers/<id>/network - Network interface stats."""
    latest = _store.get_latest(server_id)
    return jsonify({
        "server_id": server_id,
        "network": [n.model_dump() for n in latest.network] if latest else [],
    })


@api_bp.route("/alerts")
def alerts():
    """GET /api/alerts - Alert history."""
    limit = request.args.get("limit", 50, type=int)
    alert_list = _store.get_alerts(limit=limit)
    return jsonify([a.model_dump() for a in alert_list])


@api_bp.route("/alerts/threshold", methods=["GET", "POST"])
def thresholds():
    """GET/POST /api/alerts/threshold - View or update alert thresholds."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        updated = _store.update_thresholds(data)
        return jsonify(updated)
    return jsonify(_store.thresholds)


# Updated: 2026-09-07
