"""Harness self-tests for benchmarks/model_suite.py (#60)."""

from __future__ import annotations

import json

from benchmarks import model_suite as ms


def _ollama_response(content: str = "", calls=None) -> dict:
    return {"message": {"content": content, "tool_calls": calls or []}}


def _openai_response(content: str = "", calls=None) -> dict:
    return {"choices": [{"message": {"content": content, "tool_calls": calls or []}}]}


class TestExtractCalls:
    def test_structured_ollama(self):
        data = _ollama_response(
            calls=[{"function": {"name": "read_file", "arguments": {"path": "a.md"}}}]
        )
        form, calls, _ = ms.extract_calls("ollama_chat", data)
        assert form == "structured"
        assert calls == [{"name": "read_file", "args": {"path": "a.md"}}]

    def test_structured_openai_json_string_args(self):
        data = _openai_response(
            calls=[
                {
                    "function": {
                        "name": "search",
                        "arguments": json.dumps({"query": "backup"}),
                    }
                }
            ]
        )
        form, calls, _ = ms.extract_calls("openai", data)
        assert form == "structured"
        assert calls[0]["args"] == {"query": "backup"}

    def test_text_json_tool_call_detected(self):
        data = _ollama_response(content='{"name": "read_file", "arguments": {}}')
        form, calls, _ = ms.extract_calls("ollama_chat", data)
        assert form == "text-json"
        assert calls == []

    def test_plain_answer_is_none(self):
        data = _openai_response(content="2 + 2 = 4")
        form, calls, _ = ms.extract_calls("openai", data)
        assert form == "none"


class TestJudgeScenario:
    def test_correct_tool_and_args_pass(self):
        scenario = {"expect_tool": "read_file", "args_contains": {"path": "server-setup.md"}}
        verdict = ms.judge_scenario(
            scenario,
            "structured",
            [{"name": "read_file", "args": {"path": "pages/server-setup.md"}}],
        )
        assert verdict["pass"]

    def test_wrong_args_fail(self):
        scenario = {"expect_tool": "read_file", "args_contains": {"path": "резервные"}}
        verdict = ms.judge_scenario(
            scenario, "structured", [{"name": "read_file", "args": {"path": "pages/other.md"}}]
        )
        assert not verdict["pass"]

    def test_text_json_never_passes(self):
        scenario = {"expect_tool": "read_file", "args_contains": {}}
        assert not ms.judge_scenario(scenario, "text-json", [])["pass"]

    def test_no_tool_expected(self):
        assert ms.judge_scenario({"expect_tool": None}, "none", [])["pass"]
        assert not ms.judge_scenario(
            {"expect_tool": None}, "structured", [{"name": "search", "args": {}}]
        )["pass"]

    def test_min_calls_for_parallel(self):
        scenario = {"expect_tool": "read_file", "min_calls": 2}
        one = [{"name": "read_file", "args": {"path": "pages/a.md"}}]
        assert not ms.judge_scenario(scenario, "structured", one)["pass"]
        two = one + [{"name": "read_file", "args": {"path": "pages/b.md"}}]
        assert ms.judge_scenario(scenario, "structured", two)["pass"]


class TestAnswerCites:
    def test_wiki_link_stem_citation_counts(self):
        answer = "Хранится два поколения, см. [[summaries/backup-rotation]]."
        assert ms.answer_cites(answer, ["backup-rotation.md"]) == ["backup-rotation.md"]

    def test_raw_filename_citation_counts(self):
        answer = "See pages/server-setup.md for the threshold."
        assert ms.answer_cites(answer, ["server-setup.md"]) == ["server-setup.md"]

    def test_no_citation(self):
        assert ms.answer_cites("just prose", ["server-setup.md"]) == []


class TestNormalizeFacts:
    def test_units_dates_times_canonical(self):
        toks = ms.normalize_tokens(
            "Порог 15 ГБ; миграция 30 ноября 2026; резерв в 02:00 по Варшаве"
        )
        assert "15" in toks and "gib" in toks
        assert "2:00" in toks
        assert "30" in toks and "11" in toks and "2026" in toks

    def test_fact_matches_same_sentence(self):
        text = "Порог тревоги — 15 GiB свободного места. Другое предложение."
        fact = next(f for f in ms.FACTS if f["id"] == "disk-15")
        assert ms.fact_in_text(text, fact["needles"])

    def test_fact_split_across_sentences_fails(self):
        text = "Порог тревоги — 15. В другом предложении говорится про GiB."
        fact = next(f for f in ms.FACTS if f["id"] == "disk-15")
        assert not ms.fact_in_text(text, fact["needles"])

    def test_uk_compound_token_fact(self):
        text = "Планове технічне обслуговування проводиться щопʼятниці о 23:00."
        fact = next(f for f in ms.FACTS if f["id"] == "uk-service-friday-2300")
        assert ms.fact_in_text(text, fact["needles"])

    def test_date_written_out_matches_iso_fact(self):
        text = "Миграция назначена на 30 ноября 2026 года."
        fact = next(f for f in ms.FACTS if f["id"] == "migration-2026-11-30")
        assert ms.fact_in_text(text, fact["needles"])

    def test_pl_diacritics_fact(self):
        text = "Konserwacja zapasowa odbywa się w soboty o 03:00 czasu warszawskiego."
        fact = next(f for f in ms.FACTS if f["id"] == "pl-konserwacja-sat-0300")
        assert ms.fact_in_text(text, fact["needles"])


class TestReport:
    def test_report_pins_dates_and_scores(self):
        results = {
            "label": "demo-ctx32768",
            "model": "demo:1b",
            "provider": "ollama_chat",
            "api_base": "http://x",
            "ctx": 32768,
            "harness_sha": "abc1234",
            "started_utc": "2026-11-23T10:00:00+00:00",
            "finished_utc": "2026-11-23T10:05:00+00:00",
            "groups": {
                "tools": {
                    "score": 1,
                    "total": 1,
                    "scenarios": [
                        {
                            "id": "t01",
                            "lang": "en",
                            "pass": True,
                            "turns": [
                                {
                                    "form": "structured",
                                    "latency_s": 1.0,
                                    "pass": True,
                                    "reason": "",
                                }
                            ],
                        }
                    ],
                },
                "pipeline": {
                    "score": 1,
                    "total": 1,
                    "add_ok": True,
                    "add_latency_s": 2.0,
                    "queries": [
                        {
                            "q": "demo?",
                            "lang": "en",
                            "grounded": True,
                            "correct": True,
                            "pass": True,
                            "latency_s": 3.0,
                            "note": "",
                        }
                    ],
                },
                "context_recall": {
                    "score": 1,
                    "total": 2,
                    "facts": [
                        {
                            "id": "disk-15",
                            "src": "server-setup.md",
                            "retained": True,
                            "found_in": ["pages/x.md"],
                        },
                        {
                            "id": "vlan-100",
                            "src": "network-vlan.md",
                            "retained": False,
                            "found_in": [],
                        },
                    ],
                },
            },
        }
        report = ms.render_report(results)
        assert "2026-11-23T10:00:00" in report
        assert "abc1234" in report
        assert "1/1" in report
        assert "| t01 |" in report
        assert "Retention: 1/2" in report
