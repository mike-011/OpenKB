"""Tests for local LLM server auto-detect (#49) and its bundle wire."""

from __future__ import annotations

import urllib.error

import openkb.config as config
import openkb.local_server as ls


class _FakeResp:
    def __init__(self, status: int = 200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _clear_cache():
    ls._PROBE_CACHE.clear()


class TestDetectLocalApiBase:
    def test_first_answering_base_wins(self, monkeypatch):
        _clear_cache()
        monkeypatch.setattr(
            "openkb.local_server.urllib.request.urlopen",
            lambda url, timeout: _FakeResp(200),
        )
        assert ls.detect_local_api_base(use_cache=False) == "http://127.0.0.1:11434"

    def test_failures_are_skipped(self, monkeypatch):
        _clear_cache()
        seen: list[str] = []

        def fake(url, timeout):
            seen.append(url)
            if ":8080" in url:
                return _FakeResp(200)
            raise urllib.error.URLError("refused")

        monkeypatch.setattr("openkb.local_server.urllib.request.urlopen", fake)
        assert ls.detect_local_api_base(use_cache=False) == "http://127.0.0.1:8080"
        assert len(seen) == 3

    def test_none_when_nothing_answers(self, monkeypatch):
        _clear_cache()
        monkeypatch.setattr(
            "openkb.local_server.urllib.request.urlopen",
            lambda url, timeout: (_ for _ in ()).throw(urllib.error.URLError("nope")),
        )
        assert ls.detect_local_api_base(use_cache=False) is None


class TestBundleWire:
    def _isolate(self, monkeypatch, tmp_path):
        monkeypatch.setattr(config, "GLOBAL_CONFIG_DIR", tmp_path / "global")
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_BASE", raising=False)
        monkeypatch.delenv("LLM_API_BASE", raising=False)
        kb = tmp_path / "kb"
        (kb / ".openkb").mkdir(parents=True)
        return kb

    def test_detected_base_injected_when_nothing_configured(self, monkeypatch, tmp_path):
        kb = self._isolate(monkeypatch, tmp_path)
        monkeypatch.setattr(
            "openkb.local_server.detect_local_api_base",
            lambda: "http://127.0.0.1:11434",
        )
        bundle = config.resolve_credential_bundle(kb)
        assert bundle.base_url == "http://127.0.0.1:11434"

    def test_no_probe_when_key_configured(self, monkeypatch, tmp_path):
        kb = self._isolate(monkeypatch, tmp_path)
        monkeypatch.setenv("LLM_API_KEY", "sk-test")

        def explode():
            raise AssertionError("probe must not run when a key is set")

        monkeypatch.setattr("openkb.local_server.detect_local_api_base", explode)
        bundle = config.resolve_credential_bundle(kb)
        assert bundle.base_url is None

    def test_no_probe_when_base_configured(self, monkeypatch, tmp_path):
        kb = self._isolate(monkeypatch, tmp_path)
        monkeypatch.setenv("OPENAI_API_BASE", "https://cloud.example/v1")

        def explode():
            raise AssertionError("probe must not run when a base is set")

        monkeypatch.setattr("openkb.local_server.detect_local_api_base", explode)
        bundle = config.resolve_credential_bundle(kb)
        assert bundle.base_url == "https://cloud.example/v1"
