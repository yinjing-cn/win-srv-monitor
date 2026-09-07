"""Flask application factory."""

from __future__ import annotations
import logging
from flask import Flask, render_template

from monitor.config import AppConfig
from monitor.store import DataStore
from monitor.api import api_bp
from monitor.api.routes import init_api
from monitor.scheduler import start_scheduler

logger = logging.getLogger(__name__)


def create_app(config: AppConfig | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Application configuration. If None, loaded from environment.

    Returns:
        Configured Flask application instance.
    """
    if config is None:
        config = AppConfig.from_env()

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["APP_CONFIG"] = config

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    store = DataStore(data_dir=config.data_dir, max_history=config.history_points)
    app.config["STORE"] = store

    init_api(store, config)
    app.register_blueprint(api_bp)

    @app.route("/")
    def dashboard():
        mock_mode = config.mock_mode
        return render_template("dashboard.html", mock_mode=mock_mode)

    if not app.config.get("TESTING"):
        start_scheduler(config, store)

    logger.info("App created (mock=%s, servers=%d, interval=%ds)",
                config.mock_mode, len(config.servers), config.collect_interval)
    return app


# Updated: 2026-09-07
