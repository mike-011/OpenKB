# FTS5 hybrid retrieval (keyword pre-filter)

Ported from runmanfm-bit/OpenKB (`feat/fts-hybrid-retrieval`, upstream PR #273).

## What it does

A SQLite FTS5 index over the wiki (`.openkb/fts.db`) acts as a retrieval
pre-filter for `query`/`chat`: instead of walking the whole table of
contents with LLM reads, a `search` tool call cuts irrelevant files at the
DB level in milliseconds (BM25 ranking, CJK-aware bigram query building in
`openkb/fts.py`), which lowers latency and token spend — notably for
flash-tier cloud models. The agent's tool set is now
`search, read_file, get_page_content, get_image`.

## CLI

- `openkb fts rebuild` — rebuild the index from scratch (reports files,
  rows, elapsed time).
- `openkb fts search <query> [--limit 8]` — BM25 keyword lookup with
  snippets; meant for debugging and quick manual lookup.

The index is created/refreshed automatically on demand (`ensure_index`);
`rebuild_index` forces a full resync.

## Rollback

Revert the squash commit for this change; the `fts.db` file is inert
without the code and can be deleted at any time.
