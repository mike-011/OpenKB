"""Build versioning (#81) — single source for release + build stamp.

Release: the installed package version (``openkb.__version__``, e.g.
``0.5.0rc1`` / ``0.0.0+unknown`` fallback).

Build stamp: ``YYYYMMDD-HHMM-NNN`` where NNN is the build's sequence number
per day (000 = first build of the day). Resolution order:

1. ``OPENKB_BUILD_STAMP`` environment variable (set at image build);
2. ``openkb/_build_stamp`` file (baked next to the package at build time);
3. ``"dev"`` fallback for source checkouts.

The stamp is informational only — nothing functional depends on its shape
beyond the format regex used by tests and ``scripts/stamp_build.py``.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

STAMP_RE = re.compile(r"^\d{8}-\d{4}-\d{3}$")

_ENV_VAR = "OPENKB_BUILD_STAMP"
_STAMP_FILE = Path(__file__).with_name("_build_stamp")
_CHANNEL_FILE = Path(__file__).with_name("_build_channel")


def make_stamp(now: datetime, counter: int) -> str:
    """Format a build stamp: UTC date-time + per-day build counter."""
    if not 0 <= counter <= 999:
        raise ValueError(f"build counter out of range: {counter}")
    return f"{now.strftime('%Y%m%d-%H%M')}-{counter:03d}"


def build_stamp() -> str:
    """Return the build stamp (env override -> baked file -> ``dev``)."""
    env = os.environ.get(_ENV_VAR, "").strip()
    if env:
        return env
    try:
        baked = _STAMP_FILE.read_text().strip()
    except OSError:
        return "dev"
    return baked or "dev"


def is_release_stamp(stamp: str) -> bool:
    """True when the stamp matches the build format (not a fallback)."""
    return bool(STAMP_RE.match(stamp))


def channel() -> str:
    """Channel marker — ``dev`` by default (Mike: all our builds are dev
    builds for now), ``stable`` only when a build explicitly stamps it via
    ``OPENKB_BUILD_CHANNEL=stable`` or the baked ``_build_channel`` file."""
    env = os.environ.get("OPENKB_BUILD_CHANNEL", "").strip()
    if env:
        return env
    try:
        baked = _CHANNEL_FILE.read_text().strip()
    except OSError:
        return "dev"
    return baked or "dev"


def release() -> str:
    """Installed package version (release line, e.g. ``0.5.0rc1``)."""
    from openkb import __version__

    return __version__


def version_info() -> dict[str, str]:
    """Machine-readable version payload for the REST API and diagnostics.

    ``version`` is the upstream SemVer release (hatch-vcs from git tags),
    ``build`` the build number stamp, ``channel`` the dev/stable marker,
    ``train`` the composite display line.
    """
    return {
        "version": release(),
        "build": build_stamp(),
        "channel": channel(),
        "train": version_string(),
    }


def version_string() -> str:
    """Composite display line («train») for GUI/TUI surfaces."""
    return f"v{release()} · {build_stamp()} · {channel()}"


def utc_now() -> datetime:
    """Build-time clock (UTC) — kept here so the format tests stay honest."""
    return datetime.now(timezone.utc)
