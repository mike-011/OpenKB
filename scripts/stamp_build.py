#!/usr/bin/env python3
"""Stamp a build with the ``YYYYMMDD-HHMM-NNN`` version format (#81).

Run at image build time (see the Dockerfile/compose build). Responsibilities:

1. compute the stamp (UTC date-time + per-day counter);
2. persist the counter (``.build-counter``, local build-host state, gitignored);
3. write ``openkb/_build_stamp`` + ``openkb/_build_channel`` next to the
   package (baked into the image);
4. print the stamp on stdout (``docker build`` ARG/ENV wiring).

Usage:
    python scripts/stamp_build.py [--channel dev|stable] [--counter-file PATH]
                                  [--out PATH] [--dry-run]

Counter semantics: NNN = which build of the day on this build host, 000 =
first. The counter file stores ``<date> <count>`` and resets when the date
changes. Channel defaults to ``dev`` (Mike: all our builds are dev builds);
``stable`` is stamped only for explicit release builds.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from openkb.version import make_stamp, utc_now  # noqa: E402


def next_counter(counter_file: Path, today: str) -> int:
    """Increment (or reset) the per-day build counter stored in counter_file."""
    count = 0
    if counter_file.is_file():
        stored_date, _, stored_count = counter_file.read_text().strip().partition(" ")
        if stored_date == today and stored_count.isdigit():
            count = int(stored_count)
    counter_file.write_text(f"{today} {count + 1}\n")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counter-file", type=Path, default=REPO_ROOT / ".build-counter")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "openkb" / "_build_stamp")
    parser.add_argument("--channel", choices=("dev", "stable"), default="dev")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    now = utc_now()
    today = now.strftime("%Y%m%d")
    counter = next_counter(args.counter_file, today)
    stamp = make_stamp(now, counter)

    if not args.dry_run:
        args.out.write_text(stamp + "\n")
        args.out.with_name("_build_channel").write_text(args.channel + "\n")
    print(f"{stamp} {args.channel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
