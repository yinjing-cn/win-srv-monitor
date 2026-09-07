"""Tests for collector registry."""

import os
os.environ["MOCK_MODE"] = "1"

from monitor.collectors import (
    register_collector, get_collector, get_all_collectors,
    list_collector_names, BaseCollector, _REGISTRY,
)


class TestRegistry:
    def test_builtin_collectors_registered(self):
        names = list_collector_names()
        assert "cpu" in names
        assert "memory" in names
        assert "disk" in names
        assert "service" in names
        assert "network" in names
        assert "process" in names

    def test_get_collector(self):
        c = get_collector("cpu")
        assert c is not None
        assert isinstance(c, BaseCollector)

    def test_get_collector_unknown(self):
        c = get_collector("nonexistent")
        assert c is None

    def test_get_all_collectors(self):
        all_c = get_all_collectors()
        assert len(all_c) >= 6

    def test_register_custom_collector(self):
        @register_collector("test_custom")
        class TestCollector(BaseCollector):
            def collect(self, server):
                return {"test": 42}

        c = get_collector("test_custom")
        assert c is not None
        result = c.collect({"id": "test"})
        assert result["test"] == 42
        # Cleanup
        del _REGISTRY["test_custom"]

    def test_register_non_subclass_fails(self):
        import pytest
        with pytest.raises(TypeError):
            register_collector("bad")(type("Foo", (), {}))


# Updated: 2026-09-07
