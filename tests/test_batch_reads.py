"""Behavioral tests for batch multi-file reads and wiki catalog pre-load.

Ported feature (pes-innovation-lab/SLM-Wiki e3a1195) shipped with only a
tool-count/name assertion; these pin the actual behavior.
"""

from __future__ import annotations

from openkb.agent.query import _read_wiki_section, build_query_agent
from openkb.agent.tools import read_wiki_files


class TestReadWikiFiles:
    def test_concatenates_with_path_headers(self, tmp_path):
        wiki = tmp_path / "wiki"
        (wiki / "summaries").mkdir(parents=True)
        (wiki / "summaries" / "a.md").write_text("Alpha body", encoding="utf-8")
        (wiki / "summaries" / "b.md").write_text("Beta body", encoding="utf-8")

        out = read_wiki_files(["summaries/a.md", "summaries/b.md"], str(wiki))

        assert "Alpha body" in out
        assert "Beta body" in out
        assert "=== summaries/a.md ===" in out
        assert "=== summaries/b.md ===" in out

    def test_order_is_preserved(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "first.md").write_text("one", encoding="utf-8")
        (wiki / "second.md").write_text("two", encoding="utf-8")

        out = read_wiki_files(["second.md", "first.md"], str(wiki))

        assert out.index("=== second.md ===") < out.index("=== first.md ===")


class TestReadWikiSection:
    def test_reads_existing_section(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("Catalog line", encoding="utf-8")

        assert _read_wiki_section(str(wiki), "index.md") == "Catalog line"

    def test_missing_section_placeholder(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        assert "(tags.md not found)" == _read_wiki_section(str(wiki), "tags.md")


class TestCatalogPreload:
    def test_query_agent_prompt_contains_catalog(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("paper-one: short doc", encoding="utf-8")
        (wiki / "tags.md").write_text("#tag/infra", encoding="utf-8")

        agent = build_query_agent(str(wiki), "gpt-4o-mini")

        assert "paper-one: short doc" in agent.instructions
        assert "#tag/infra" in agent.instructions
