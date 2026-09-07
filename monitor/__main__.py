"""CLI entry point - run with `python -m monitor`."""

import os
import sys
from monitor.config import AppConfig
from monitor.app import create_app


def main():
    """Start the monitoring dashboard server."""
    config = AppConfig.from_env()
    app = create_app(config)

    mode_str = "Mock Data" if config.mock_mode else "Live Collection"
    print(f"""
+======================================================+
|           Windows Server Monitor Dashboard            |
+======================================================+
|  Mode:     {mode_str:<43}|
|  Servers:  {len(config.servers):<43}|
|  Interval: {config.collect_interval}s{" " * 41}|
|  URL:      http://{config.flask_host}:{config.flask_port:<28}|
+======================================================+
""")
    app.run(
        host=config.flask_host,
        port=config.flask_port,
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()


# Updated: 2026-09-07
