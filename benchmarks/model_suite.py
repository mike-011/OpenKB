"""OpenKB model comparison suite (#60).

One task set x one harness (OpenKB) x N models -> comparable results.

Groups
------
tools    -- raw tool-call structure against the model's native API
            (Ollama /api/chat or OpenAI-compatible /v1/chat/completions).
            Records HOW the tool call arrives: structured `tool_calls`,
            tool JSON emitted as plain text (the known small-model failure
            mode), or nothing.
pipeline -- the real ``openkb`` CLI on a fixed fixture KB: init -> add ->
            grounded queries + one unanswerable (fabrication check).

Usage
-----
    python benchmarks/model_suite.py \
        --model mimo-v2.6:9b --provider ollama_chat \
        --api-base http://192.168.0.203:11434 --ctx 32768 \
        --label mimo-v2.6-9b-ctx32768 --out docs/local-llm/ollama

Writes ``<out>/<label>/results.json`` and ``<out>/<label>/report.md`` with
UTC date/time and the harness git SHA pinned in both.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a wiki file by its path",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the wiki for a query",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files in a wiki directory",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
]

# Scenario fields: id, lang, prompt, expect_tool (None = expect no tool),
# args_contains {arg: substring} (optional), turns (optional multi-turn).
SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "t01-en-read",
        "lang": "en",
        "prompt": "Read the wiki file pages/server-setup.md for me.",
        "expect_tool": "read_file",
        "args_contains": {"path": "server-setup.md"},
    },
    {
        "id": "t02-en-search",
        "lang": "en",
        "prompt": "Search the wiki for the backup rotation policy.",
        "expect_tool": "search",
        "args_contains": {"query": "backup"},
    },
    {
        "id": "t03-ru-read",
        "lang": "ru",
        "prompt": "Прочитай, пожалуйста, файл pages/server-setup.md.",
        "expect_tool": "read_file",
        "args_contains": {"path": "server-setup.md"},
    },
    {
        "id": "t04-cyrillic-args",
        "lang": "ru",
        "prompt": "Открой файл pages/резервные-копии.md — страницу про резервные копии.",
        "expect_tool": "read_file",
        "args_contains": {"path": "резервные-копии.md"},
    },
    {
        "id": "t05-exact-args",
        "lang": "en",
        "prompt": (
            "Read exactly pages/db-migration-2026-11.md — mind the digits and dashes in the name."
        ),
        "expect_tool": "read_file",
        "args_contains": {"path": "pages/db-migration-2026-11.md"},
    },
    {
        "id": "t06-list",
        "lang": "en",
        "prompt": "What files are in the pages/ directory of the wiki?",
        "expect_tool": "list_directory",
        "args_contains": {"path": "pages"},
    },
    {
        "id": "t07-no-tool",
        "lang": "en",
        "prompt": "What is 2 + 2? Answer directly, no documents needed.",
        "expect_tool": None,
    },
    {
        "id": "t08-ru-search-cyrillic",
        "lang": "ru",
        "prompt": "Найди в вики информацию о политике резервного копирования.",
        "expect_tool": "search",
        "args_contains": {"query": "резервн"},
    },
    {
        "id": "t09-sequential",
        "lang": "en",
        "turns": [
            {"prompt": "Read pages/index.md.", "expect_tool": "read_file"},
            {
                "prompt": "Thanks. Now read the backup page too.",
                "expect_tool": "read_file",
                "args_contains": {"path": "backup"},
            },
        ],
    },
    {
        "id": "t10-parallel",
        "lang": "en",
        "prompt": "Read two files for me: pages/network-vlan.md and pages/onboarding.md.",
        "expect_tool": "read_file",
        "min_calls": 1,
    },
]

FIXTURES: dict[str, str] = {
    "server-setup.md": (
        "# Server setup\n\nThe monitoring server runs on 192.168.0.137.\n"
        "Disk alarm threshold is 15 GiB free.\n"
    ),
    "backup-rotation.md": (
        "# Backup rotation\n\nBackups keep 2 generations and expire after 14 days.\n"
    ),
    "резервные-копии.md": (
        "# Резервные копии\n\nРезервные копии делаются ежедневно в 02:00 по Варшаве.\n"
    ),
    "db-migration-2026-11.md": (
        "# DB migration\n\nThe database migration is scheduled for 2026-11-30.\n"
    ),
    "network-vlan.md": "# Network VLAN\n\nVLAN 100 is the server VLAN.\n",
    "onboarding.md": ("# Onboarding\n\nNew employees get access through an ITSM ticket.\n"),
}

PIPELINE_QUESTIONS: list[dict[str, Any]] = [
    {
        "q": "Какой порог тревоги по свободному месту на диске?",
        "expect_pages": ["server-setup.md"],
    },
    {
        "q": "Сколько поколений бэкапов хранится?",
        "expect_pages": ["backup-rotation.md", "резервные-копии.md"],
    },
    {
        "q": "Когда запланирована миграция базы данных?",
        "expect_pages": ["db-migration-2026-11.md"],
    },
    {
        "q": "Какой VLAN является серверным?",
        "expect_pages": ["network-vlan.md"],
    },
    {
        "q": "Как новый сотрудник получает доступ?",
        "expect_pages": ["onboarding.md"],
    },
    {
        "q": "Какой пароль у роутера в серверной?",
        "expect_pages": [],
        "unanswerable": True,
    },
]


def answer_cites(answer: str, expect_pages: list[str]) -> list[str]:
    """Return expected pages the answer grounds itself in.

    OpenKB answers cite wiki pages as ``[[summaries/<stem>]]``, not the raw
    filename — match on the bare file stem.
    """
    answer_l = answer.lower()
    stems = {p: (p[:-3] if p.endswith(".md") else p).lower() for p in expect_pages}
    return [p for p, stem in stems.items() if stem in answer_l]


REFUSAL_MARKERS = (
    "нет данных",
    "не указан",
    "не знаю",
    "нет информации",
    "не найдено",
    "no information",
    "not found",
    "i don't know",
    "не содержит",
    "в вики нет",
)


def _post_json(
    url: str,
    payload: dict[str, Any],
    timeout: float = 600.0,
    api_key: str | None = None,
) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def extract_calls(provider: str, data: dict[str, Any]) -> tuple[str, list[dict[str, Any]], str]:
    """Return (form, calls, content). form: structured|text-json|none."""
    if provider == "ollama_chat":
        msg = data.get("message", {})
        content = msg.get("content") or ""
        raw_calls = msg.get("tool_calls") or []
    else:
        msg = (data.get("choices") or [{}])[0].get("message", {})
        content = msg.get("content") or ""
        raw_calls = msg.get("tool_calls") or []

    calls: list[dict[str, Any]] = []
    for call in raw_calls:
        fn = call.get("function", {})
        args = fn.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except ValueError:
                pass
        calls.append({"name": fn.get("name", ""), "args": args})

    if calls:
        return "structured", calls, content

    text = content or ""
    # Text-JSON tool call: the known small-model failure mode — the model
    # writes the tool call into plain content instead of the tool_calls slot.
    if re.search(r'"\s*name\s*"\s*:\s*"(read_file|search|list_directory)"', text):
        return "text-json", [], text
    return "none", [], text


def judge_scenario(
    scenario: dict[str, Any], form: str, calls: list[dict[str, Any]]
) -> dict[str, Any]:
    expect_tool = scenario.get("expect_tool")
    if expect_tool is None:
        ok = form != "text-json" and not calls
        return {"pass": ok, "reason": "no-tool expected" if ok else "unexpected tool call"}

    matching = [c for c in calls if c["name"] == expect_tool]
    tool_ok = bool(matching)
    args_ok = True
    args_note = ""
    for arg, needle in (scenario.get("args_contains") or {}).items():
        values = [str(c["args"].get(arg, "")) for c in matching] if matching else [""]
        if not any(needle in v for v in values):
            args_ok = False
            args_note = f"{arg} lacks {needle!r} in {values}"
    min_calls = scenario.get("min_calls", 1)
    count_ok = len(calls) >= min_calls
    ok = form == "structured" and tool_ok and args_ok and count_ok
    reason = "" if ok else (args_note or f"form={form} tool_ok={tool_ok} calls={len(calls)}")
    return {"pass": ok, "reason": reason}


def run_tool_turn(
    api_base: str,
    provider: str,
    model: str,
    messages: list[dict[str, Any]],
    ctx: int,
    api_key: str | None = None,
) -> tuple[str, list[dict[str, Any]], str, float]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "tools": TOOLS,
        "stream": False,
    }
    if provider == "ollama_chat":
        url = api_base.rstrip("/") + "/api/chat"
        payload["options"] = {"num_ctx": ctx}
    else:
        url = api_base.rstrip("/") + "/v1/chat/completions"

    started = time.monotonic()
    data = _post_json(url, payload, api_key=api_key)
    latency = time.monotonic() - started
    form, calls, content = extract_calls(provider, data)
    return form, calls, content, latency


def run_tools_group(
    api_base: str, provider: str, model: str, ctx: int, api_key: str | None = None
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        turns = scenario.get("turns") or [
            {"prompt": scenario["prompt"], "expect_tool": scenario.get("expect_tool")}
        ]
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": "You are a wiki assistant with tools."}
        ]
        turn_rows: list[dict[str, Any]] = []
        for turn in turns:
            messages.append({"role": "user", "content": turn["prompt"]})
            form, calls, content, latency = run_tool_turn(
                api_base, provider, model, messages, ctx, api_key=api_key
            )
            turn_scenario = {**scenario, **turn}
            verdict = judge_scenario(turn_scenario, form, calls)
            turn_rows.append(
                {
                    "prompt": turn["prompt"],
                    "form": form,
                    "calls": calls,
                    "latency_s": round(latency, 2),
                    **verdict,
                }
            )
            messages.append({"role": "assistant", "content": content})
        passed = all(t["pass"] for t in turn_rows)
        rows.append(
            {
                "id": scenario["id"],
                "lang": scenario.get("lang", ""),
                "pass": passed,
                "turns": turn_rows,
            }
        )
    score = sum(1 for r in rows if r["pass"])
    return {"scenarios": rows, "score": score, "total": len(rows)}


def _run_cli(args: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    proc = subprocess.run(
        args, cwd=cwd, env=env, capture_output=True, text=True, timeout=3600, input="\n"
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def run_pipeline_group(api_base: str, provider: str, model: str, ctx: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="openkb-bench-") as tmp:
        kb = Path(tmp) / "kb"
        kb.mkdir()
        env = dict(os.environ)
        env["LLM_API_KEY"] = env.get("LLM_API_KEY", "bench-key")
        litellm_model = model
        if provider == "ollama_chat":
            env["OLLAMA_API_BASE"] = api_base.rstrip("/")
            litellm_model = f"ollama_chat/{model}"
        else:
            env["OPENAI_API_BASE"] = api_base.rstrip("/") + "/v1"
            litellm_model = f"openai/{model}"

        _, out = _run_cli(["openkb", "init", "-m", litellm_model, "-l", "ru"], kb, env)
        raw = kb / "raw"
        raw.mkdir(exist_ok=True)
        for name, text in FIXTURES.items():
            (raw / name).write_text(text)

        started = time.monotonic()
        _, add_out = _run_cli(["openkb", "add", "raw"], kb, env)
        add_latency = time.monotonic() - started
        add_ok = "added" in add_out.lower()

        queries: list[dict[str, Any]] = []
        for item in PIPELINE_QUESTIONS:
            started = time.monotonic()
            code, out = _run_cli(["openkb", "query", "--raw", item["q"]], kb, env)
            latency = time.monotonic() - started
            out_l = out.lower()
            if item.get("unanswerable"):
                fabricated = any(p.lower() in out_l for p in FIXTURES)
                refusal = any(m in out_l for m in REFUSAL_MARKERS)
                grounded = (not fabricated) or refusal
                note = "fabricated pages!" if fabricated and not refusal else ""
            else:
                cited = answer_cites(out, item["expect_pages"])
                grounded = bool(cited)
                note = f"cited: {cited}" if cited else "no expected page cited"
            queries.append(
                {
                    "q": item["q"],
                    "unanswerable": bool(item.get("unanswerable")),
                    "grounded": grounded,
                    "latency_s": round(latency, 2),
                    "note": note,
                    "answer_excerpt": out.strip()[-600:],
                }
            )

    score = sum(1 for q in queries if q["grounded"])
    return {
        "add_ok": add_ok,
        "add_latency_s": round(add_latency, 2),
        "add_log_excerpt": add_out.strip()[-300:],
        "queries": queries,
        "score": score,
        "total": len(queries),
    }


def harness_sha() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def render_report(results: dict[str, Any]) -> str:
    lines = [
        f"# Model bench report — {results['label']}",
        "",
        f"- Date/time (UTC): {results['started_utc']} → {results['finished_utc']}",
        f"- Model: `{results['model']}` via `{results['provider']}` at `{results['api_base']}`",
        f"- Bench ctx: {results['ctx']} · harness (OpenKB): `{results['harness_sha']}`",
        "",
    ]
    tools = results.get("groups", {}).get("tools")
    if tools:
        lines += [
            "## Group: tool-call structure",
            "",
            f"**Score: {tools['score']}/{tools['total']}**",
            "",
            "| Scenario | Lang | Pass | Form | Latency s | Note |",
            "|---|---|---|---|---|---|",
        ]
        for row in tools["scenarios"]:
            forms = "/".join(t["form"] for t in row["turns"])
            lat = sum(t["latency_s"] for t in row["turns"])
            notes = "; ".join(t["reason"] for t in row["turns"] if t["reason"])
            lines.append(
                f"| {row['id']} | {row['lang']} | {'✅' if row['pass'] else '❌'} "
                f"| {forms} | {lat:.1f} | {notes} |"
            )
        lines.append("")
    pipeline = results.get("groups", {}).get("pipeline")
    if pipeline:
        lines += [
            "## Group: OpenKB pipeline (fixture KB)",
            "",
            f"**Score: {pipeline['score']}/{pipeline['total']}** · "
            f"add: {'ok' if pipeline['add_ok'] else 'FAILED'} ({pipeline['add_latency_s']} s)",
            "",
            "| Question | Grounded | Latency s | Note |",
            "|---|---|---|---|",
        ]
        for q in pipeline["queries"]:
            lines.append(
                f"| {q['q'][:48]}… | {'✅' if q['grounded'] else '❌'} "
                f"| {q['latency_s']} | {q['note']} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="model tag for the provider")
    parser.add_argument("--provider", choices=["ollama_chat", "openai"], required=True)
    parser.add_argument("--api-base", required=True)
    parser.add_argument("--ctx", type=int, default=32768)
    parser.add_argument("--label", default=None, help="output dir name")
    parser.add_argument("--out", default="docs/local-llm")
    parser.add_argument("--groups", default="tools,pipeline")
    parser.add_argument(
        "--api-key-env",
        default=None,
        help="name of the env var holding the API key (cloud providers); "
        "the key never goes into code or logs",
    )
    args = parser.parse_args()

    label = args.label or f"{args.model.replace(':', '-')}-ctx{args.ctx}"
    api_key = os.environ.get(args.api_key_env) if args.api_key_env else None
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    groups: dict[str, Any] = {}
    wanted = {g.strip() for g in args.groups.split(",")}
    if "tools" in wanted:
        groups["tools"] = run_tools_group(
            args.api_base, args.provider, args.model, args.ctx, api_key=api_key
        )
    if "pipeline" in wanted:
        groups["pipeline"] = run_pipeline_group(args.api_base, args.provider, args.model, args.ctx)

    results = {
        "label": label,
        "model": args.model,
        "provider": args.provider,
        "api_base": args.api_base,
        "ctx": args.ctx,
        "harness_sha": harness_sha(),
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "groups": groups,
    }
    out_dir = Path(args.out) / label
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    (out_dir / "report.md").write_text(render_report(results))
    print(f"written: {out_dir}/results.json + report.md")
    for name, group in groups.items():
        print(f"  {name}: {group['score']}/{group['total']}")


if __name__ == "__main__":
    main()
