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
    {
        "id": "t11-uk-read",
        "lang": "uk",
        "prompt": "Прочитай, будь ласка, файл pages/server-setup.md.",
        "expect_tool": "read_file",
        "args_contains": {"path": "server-setup.md"},
    },
    {
        "id": "t12-pl-read-diacritics",
        "lang": "pl",
        "prompt": (
            "Przeczytaj proszę plik pages/db-migration-2026-11.md — "
            "zwróć uwagę na cyfry i myślniki w nazwie."
        ),
        "expect_tool": "read_file",
        "args_contains": {"path": "pages/db-migration-2026-11.md"},
    },
    {
        "id": "t13-uk-search",
        "lang": "uk",
        "prompt": "Пошукай у вікі інформацію про резервні копії.",
        "expect_tool": "search",
        "args_contains": {"query": "резервн"},
    },
    {
        "id": "t14-pl-no-tool",
        "lang": "pl",
        "prompt": (
            "Jaka jest dziś pogoda w Katowicach? "
            "Odpowiedz bezpośrednio, dokumenty nie są potrzebne."
        ),
        "expect_tool": None,
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
    "обслуговування-сервера.md": (
        "# Обслуговування сервера\n\n"
        "Планове технічне обслуговування проводиться щопʼятниці о 23:00.\n"
    ),
    "harmonogram-konserwacji.md": (
        "# Harmonogram konserwacji\n\n"
        "Konserwacja zapasowa odbywa się w soboty o 03:00 czasu warszawskiego.\n"
    ),
}

PIPELINE_QUESTIONS: list[dict[str, Any]] = [
    # --- en ---
    {
        "q": "What is the free disk space alarm threshold?",
        "lang": "en",
        "expect_pages": ["server-setup.md"],
        "expect_facts": ["disk-15"],
    },
    {
        "q": "How many backup generations are kept?",
        "lang": "en",
        "expect_pages": ["backup-rotation.md", "резервные-копии.md"],
        "expect_facts": ["backup-2-gen"],
    },
    {
        "q": "When is the database migration scheduled?",
        "lang": "en",
        "expect_pages": ["db-migration-2026-11.md"],
        "expect_facts": ["migration-2026-11-30"],
    },
    {
        "q": "Which VLAN is the server VLAN?",
        "lang": "en",
        "expect_pages": ["network-vlan.md"],
        "expect_facts": ["vlan-100"],
    },
    {
        "q": "How does a new employee get access?",
        "lang": "en",
        "expect_pages": ["onboarding.md"],
        "expect_facts": ["onboarding-itsm"],
    },
    {
        "q": "What is the router password in the server room?",
        "lang": "en",
        "expect_pages": [],
        "unanswerable": True,
    },
    # --- ru ---
    {
        "q": "Какой порог тревоги по свободному месту на диске?",
        "lang": "ru",
        "expect_pages": ["server-setup.md"],
        "expect_facts": ["disk-15"],
    },
    {
        "q": "Сколько поколений бэкапов хранится?",
        "lang": "ru",
        "expect_pages": ["backup-rotation.md", "резервные-копии.md"],
        "expect_facts": ["backup-2-gen"],
    },
    {
        "q": "Когда запланирована миграция базы данных?",
        "lang": "ru",
        "expect_pages": ["db-migration-2026-11.md"],
        "expect_facts": ["migration-2026-11-30"],
    },
    {
        "q": "Какой VLAN является серверным?",
        "lang": "ru",
        "expect_pages": ["network-vlan.md"],
        "expect_facts": ["vlan-100"],
    },
    {
        "q": "Как новый сотрудник получает доступ?",
        "lang": "ru",
        "expect_pages": ["onboarding.md"],
        "expect_facts": ["onboarding-itsm"],
    },
    {
        "q": "Какой пароль у роутера в серверной?",
        "lang": "ru",
        "expect_pages": [],
        "unanswerable": True,
    },
    # --- uk ---
    {
        "q": "Який поріг тривоги за вільним місцем на диску?",
        "lang": "uk",
        "expect_pages": ["server-setup.md"],
        "expect_facts": ["disk-15"],
    },
    {
        "q": "Скільки поколінь резервних копій зберігається?",
        "lang": "uk",
        "expect_pages": ["backup-rotation.md", "резервные-копии.md"],
        "expect_facts": ["backup-2-gen"],
    },
    {
        "q": "Коли запланована міграція бази даних?",
        "lang": "uk",
        "expect_pages": ["db-migration-2026-11.md"],
        "expect_facts": ["migration-2026-11-30"],
    },
    {
        "q": "Який VLAN є серверним?",
        "lang": "uk",
        "expect_pages": ["network-vlan.md"],
        "expect_facts": ["vlan-100"],
    },
    {
        "q": "Як новий співробітник отримує доступ?",
        "lang": "uk",
        "expect_pages": ["onboarding.md"],
        "expect_facts": ["onboarding-itsm"],
    },
    {
        "q": "Коли проводиться планове технічне обслуговування сервера?",
        "lang": "uk",
        "expect_pages": ["обслуговування-сервера.md"],
        "expect_facts": ["uk-service-friday-2300"],
    },
    {
        "q": "Який пароль від роутера в серверній?",
        "lang": "uk",
        "expect_pages": [],
        "unanswerable": True,
    },
    # --- pl ---
    {
        "q": "Jaki jest próg alarmowy wolnego miejsca na dysku?",
        "lang": "pl",
        "expect_pages": ["server-setup.md"],
        "expect_facts": ["disk-15"],
    },
    {
        "q": "Ile pokoleń kopii zapasowych jest przechowywanych?",
        "lang": "pl",
        "expect_pages": ["backup-rotation.md", "резервные-копии.md"],
        "expect_facts": ["backup-2-gen"],
    },
    {
        "q": "Kiedy zaplanowana jest migracja bazy danych?",
        "lang": "pl",
        "expect_pages": ["db-migration-2026-11.md"],
        "expect_facts": ["migration-2026-11-30"],
    },
    {
        "q": "Który VLAN jest serwerowy?",
        "lang": "pl",
        "expect_pages": ["network-vlan.md"],
        "expect_facts": ["vlan-100"],
    },
    {
        "q": "Jak nowy pracownik uzyskuje dostęp?",
        "lang": "pl",
        "expect_pages": ["onboarding.md"],
        "expect_facts": ["onboarding-itsm"],
    },
    {
        "q": "Kiedy odbywa się konserwacja zapasowa?",
        "lang": "pl",
        "expect_pages": ["harmonogram-konserwacji.md"],
        "expect_facts": ["pl-konserwacja-sat-0300"],
    },
    {
        "q": "Jakie jest hasło do routera w serwerowni?",
        "lang": "pl",
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

# Control facts for the context-recall (fact retention) group — one entry per
# atomic fact (Summarization Content Units / FActScore style). ``needles`` are
# alternates: a fact matches when ONE needle's tokens all occur in the SAME
# sentence. Word needles match by prefix (>=2 chars), numbers/times exactly.
FACTS: list[dict[str, Any]] = [
    {"id": "ip-monitor", "src": "server-setup.md", "needles": [["192.168.0.137"]]},
    {"id": "disk-15", "src": "server-setup.md", "needles": [["15", "gib"]]},
    {
        "id": "backup-2-gen",
        "src": "backup-rotation.md",
        "needles": [["2", "поколен"], ["2", "generation"], ["2", "pokole"], ["2", "поколін"]],
    },
    {
        "id": "backup-14-days",
        "src": "backup-rotation.md",
        "needles": [["14", "дн"], ["14", "day"], ["14", "dni"], ["14", "dnia"]],
    },
    {
        "id": "backup-0200-warsaw",
        "src": "резервные-копии.md",
        "needles": [["2:00", "варшав"], ["2:00", "warsaw"], ["2:00", "warszaw"]],
    },
    {
        "id": "migration-2026-11-30",
        "src": "db-migration-2026-11.md",
        "needles": [["2026", "11", "30"]],
    },
    {"id": "vlan-100", "src": "network-vlan.md", "needles": [["vlan", "100"]]},
    {"id": "onboarding-itsm", "src": "onboarding.md", "needles": [["itsm"]]},
    {
        "id": "uk-service-friday-2300",
        "src": "обслуговування-сервера.md",
        "needles": [["23:00", "п'ятниц"], ["23:00", "friday"], ["23:00", "piątek"]],
    },
    {
        "id": "pl-konserwacja-sat-0300",
        "src": "harmonogram-konserwacji.md",
        "needles": [["3:00", "sobot"], ["3:00", "saturday"], ["3:00", "субот"]],
    },
]

MONTHS: dict[str, str] = {
    "января": "1",
    "февраля": "2",
    "марта": "3",
    "апреля": "4",
    "мая": "5",
    "июня": "6",
    "июля": "7",
    "августа": "8",
    "сентября": "9",
    "октября": "10",
    "ноября": "11",
    "декабря": "12",
    "січня": "1",
    "лютого": "2",
    "березня": "3",
    "квітня": "4",
    "травня": "5",
    "червня": "6",
    "липня": "7",
    "серпня": "8",
    "вересня": "9",
    "жовтня": "10",
    "листопада": "11",
    "грудня": "12",
    "stycznia": "1",
    "lutego": "2",
    "marca": "3",
    "kwietnia": "4",
    "maja": "5",
    "czerwca": "6",
    "lipca": "7",
    "sierpnia": "8",
    "września": "9",
    "października": "10",
    "listopada": "11",
    "grudnia": "12",
    "january": "1",
    "february": "2",
    "march": "3",
    "april": "4",
    "june": "6",
    "july": "7",
    "august": "8",
    "september": "9",
    "october": "10",
    "november": "11",
    "december": "12",
    "may": "5",
}

UNIT_SYNONYMS: dict[str, str] = {
    "gb": "gib",
    "гб": "gib",
    "гіб": "gib",
    "gigabytes": "gib",
    "gigabyte": "gib",
    "гigabytes": "gib",
    "гігабайт": "gib",
    "гігабайти": "gib",
    "гigabyte": "gib",
}


def normalize_tokens(text: str) -> list[str]:
    """NFKC + lowercase + canonical units/dates/times -> comparable tokens."""
    import unicodedata

    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("’", "'").replace("`", "'").replace("ʼ", "'")
    text = re.sub(r"\b(\d{1,2}):(\d{2})\b", lambda m: f" {int(m.group(1))}:{m.group(2)} ", text)
    text = re.sub(r"\b(\d{4})-(\d{2})-(\d{2})\b", r" \1 \2 \3 ", text)
    for name, num in MONTHS.items():
        text = re.sub(rf"\b{name}\b", f" {num} ", text)
    tokens = re.findall(r"[a-zа-яіїєґё']+|\d+(?::\d+)?", text)
    return [UNIT_SYNONYMS[t] if t in UNIT_SYNONYMS else t for t in tokens]


def needle_matches(tokens: list[str], needle: list[str]) -> bool:
    for part in needle:
        if part.isdigit() or ":" in part:
            if part not in tokens:
                return False
        elif not any(part in t for t in tokens):
            return False
    return True


def fact_in_text(text: str, needles: list[list[str]]) -> bool:
    """A fact matches when one needle sits inside ONE sentence (token window)."""
    for sentence in re.split(r"(?<=[.!?…])\s+|\n+", text):
        tokens = normalize_tokens(sentence)
        for needle in needles:
            if needle_matches(tokens, needle):
                return True
    return False


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


def run_pipeline_group(
    api_base: str, provider: str, model: str, ctx: int, with_queries: bool = True
) -> dict[str, Any]:
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

        # Context recall (fact retention): every control fact must survive wiki
        # generation and live on a real page (not just the index).
        wiki_texts: list[tuple[str, str]] = []
        for path in sorted(kb.rglob("*.md")):
            if "raw" in path.parts or path.name == "index.md":
                continue
            wiki_texts.append((str(path.relative_to(kb)), path.read_text()))
        recall_rows: list[dict[str, Any]] = []
        for fact in FACTS:
            hits = [name for name, text in wiki_texts if fact_in_text(text, fact["needles"])]
            recall_rows.append(
                {"id": fact["id"], "src": fact["src"], "retained": bool(hits), "found_in": hits}
            )
        recall = {
            "facts": recall_rows,
            "score": sum(1 for r in recall_rows if r["retained"]),
            "total": len(recall_rows),
        }

        queries: list[dict[str, Any]] = []
        for item in PIPELINE_QUESTIONS if with_queries else []:
            started = time.monotonic()
            code, out = _run_cli(["openkb", "query", "--raw", item["q"]], kb, env)
            latency = time.monotonic() - started
            out_l = out.lower()
            if item.get("unanswerable"):
                fabricated = any(p.lower() in out_l for p in FIXTURES)
                refusal = any(m in out_l for m in REFUSAL_MARKERS)
                grounded = (not fabricated) or refusal
                correct = True
                note = "fabricated pages!" if fabricated and not refusal else ""
            else:
                cited = answer_cites(out, item["expect_pages"])
                grounded = bool(cited)
                wanted = [f for f in FACTS if f["id"] in (item.get("expect_facts") or [])]
                missing = [f["id"] for f in wanted if not fact_in_text(out, f["needles"])]
                correct = not missing
                note = f"cited: {cited}" if grounded else "no expected page cited"
                if missing:
                    note += f" | facts missing: {missing}"
            ok = grounded and correct
            queries.append(
                {
                    "q": item["q"],
                    "lang": item.get("lang", ""),
                    "unanswerable": bool(item.get("unanswerable")),
                    "grounded": grounded,
                    "correct": correct,
                    "pass": ok,
                    "latency_s": round(latency, 2),
                    "note": note,
                    "answer_excerpt": out.strip()[-600:],
                }
            )

    score = sum(1 for q in queries if q["pass"])
    return {
        "add_ok": add_ok,
        "add_latency_s": round(add_latency, 2),
        "add_log_excerpt": add_out.strip()[-300:],
        "queries": queries,
        "score": score,
        "total": len(queries),
        "context_recall": recall,
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
            "## Group: OpenKB pipeline (fixture KB) — faithfulness + answer correctness",
            "",
            f"**Score: {pipeline['score']}/{pipeline['total']}** · "
            f"add: {'ok' if pipeline['add_ok'] else 'FAILED'} ({pipeline['add_latency_s']} s)",
            "",
            "| Question | Lang | Cited | Facts | Latency s | Note |",
            "|---|---|---|---|---|---|",
        ]
        for q in pipeline["queries"]:
            lines.append(
                f"| {q['q'][:48]}… | {q.get('lang', '')} "
                f"| {'✅' if q['grounded'] else '❌'} | {'✅' if q['correct'] else '❌'} "
                f"| {q['latency_s']} | {q['note']} |"
            )
        lines.append("")
    recall = results.get("groups", {}).get("context_recall")
    if recall:
        lines += [
            "## Group: context recall (fact retention — SCU / FActScore style)",
            "",
            f"**Retention: {recall['score']}/{recall['total']}** — control facts "
            "surviving wiki generation (must live on a page, not just the index)",
            "",
            "| Fact | Source | Retained | Found in |",
            "|---|---|---|---|",
        ]
        for f in recall["facts"]:
            lines.append(
                f"| {f['id']} | {f['src']} | {'✅' if f['retained'] else '❌'} "
                f"| {', '.join(f['found_in'])} |"
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
    parser.add_argument("--groups", default="tools,pipeline,context-recall")
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
    if "pipeline" in wanted or "context-recall" in wanted:
        pipe = run_pipeline_group(
            args.api_base,
            args.provider,
            args.model,
            args.ctx,
            with_queries="pipeline" in wanted,
        )
        if "pipeline" in wanted:
            groups["pipeline"] = pipe
        if "context-recall" in wanted:
            groups["context_recall"] = pipe["context_recall"]

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
