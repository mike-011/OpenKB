"""Tests for build versioning (#81): stamp format, counter, resolution."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

import openkb.version as ver


class TestMakeStamp:
    def test_format(self):
        stamp = ver.make_stamp(datetime(2026, 11, 23, 17, 45, tzinfo=timezone.utc), 0)
        assert stamp == "20261123-1745-000"
        assert ver.is_release_stamp(stamp)

    def test_counter_width(self):
        assert (
            ver.make_stamp(datetime(2026, 11, 23, 0, 0, tzinfo=timezone.utc), 7)
            == "20261123-0000-007"
        )

    def test_counter_out_of_range(self):
        with pytest.raises(ValueError):
            ver.make_stamp(datetime(2026, 11, 23, 0, 0, tzinfo=timezone.utc), 1000)


class TestBuildStampResolution:
    def test_env_override_wins(self, monkeypatch, tmp_path: Path):
        monkeypatch.setenv("OPENKB_BUILD_STAMP", "20261123-1745-003")
        assert ver.build_stamp() == "20261123-1745-003"

    def test_fallback_dev(self, monkeypatch):
        monkeypatch.delenv("OPENKB_BUILD_STAMP", raising=False)
        monkeypatch.setattr(ver, "_STAMP_FILE", Path("/nonexistent/_build_stamp"))
        assert ver.build_stamp() == "dev"
        assert not ver.is_release_stamp("dev")


class TestVersionPayload:
    def test_info_shape(self, monkeypatch):
        monkeypatch.setenv("OPENKB_BUILD_STAMP", "20261123-1745-000")
        info = ver.version_info()
        assert set(info) == {"version", "build", "channel", "train"}
        assert info["build"] == "20261123-1745-000"
        assert info["channel"] == "stable"
        assert info["train"].endswith("· 20261123-1745-000 · stable")
        assert ver.version_string() == info["train"]

    def test_channel_dev_without_stamp(self, monkeypatch):
        monkeypatch.delenv("OPENKB_BUILD_STAMP", raising=False)
        monkeypatch.setattr(ver, "_STAMP_FILE", Path("/nonexistent/_build_stamp"))
        assert ver.channel() == "dev"


class TestCounterFile:
    def test_increments_and_resets_by_day(self, tmp_path: Path):
        import importlib.util

        script = Path(__file__).resolve().parent.parent / "scripts" / "stamp_build.py"
        spec = importlib.util.spec_from_file_location("stamp_build", script)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        counter = tmp_path / ".build-counter"
        assert mod.next_counter(counter, "20261123") == 0
        assert mod.next_counter(counter, "20261123") == 1
        assert mod.next_counter(counter, "20261123") == 2
        assert mod.next_counter(counter, "20261124") == 0
