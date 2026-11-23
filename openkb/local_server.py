"""Auto-detect a local OpenAI-compatible or Ollama LLM server.

Last-resort LLM ``api_base`` when nothing is configured explicitly: lets
`openkb` work out of the box against a local Ollama (e.g. the Lenovo PVE
box) without any env setup. Cloud users are unaffected — the probe only
runs when no api key and no base URL are configured at all.

Probes (localhost only, sub-second timeout):
- http://127.0.0.1:11434  (Ollama, /api/version)
- http://127.0.0.1:8081   (OpenAI-compatible facade, /v1/models)
- http://127.0.0.1:8080   (llama.cpp server default, /v1/models)
"""

from __future__ import annotations

import urllib.error
import urllib.request

PROBES: tuple[tuple[str, str], ...] = (
    ("http://127.0.0.1:11434", "/api/version"),
    ("http://127.0.0.1:8081", "/v1/models"),
    ("http://127.0.0.1:8080", "/v1/models"),
)

_PROBE_CACHE: dict[str, str | None] = {}


def detect_local_api_base(timeout: float = 0.5, use_cache: bool = True) -> str | None:
    """Return the first local LLM server base URL that answers 200, else None."""
    cache_key = f"t:{timeout}"
    if use_cache and cache_key in _PROBE_CACHE:
        return _PROBE_CACHE[cache_key]

    found: str | None = None
    for base, path in PROBES:
        try:
            with urllib.request.urlopen(base + path, timeout=timeout) as resp:
                if getattr(resp, "status", 200) == 200:
                    found = base
                    break
        except (urllib.error.URLError, OSError, ValueError):
            continue

    if use_cache:
        _PROBE_CACHE[cache_key] = found
    return found
