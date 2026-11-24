# Local LLM bench reports

Сравнение локальных моделей на одинаковых задачах OpenKB (suite: `benchmarks/`,
методика и сценарии — `benchmarks/README.md`). Один каталог на модель:
`{runtime}/{model}-ctx{N}` (ctx = единый контекст прогона для сравнимости;
фактический потолок модели указан в отчёте). Внутри: `report.md` (дата/время UTC,
версии, показатели) и `results.json` (сырые данные).

## Leaderboard

### Итог марафона (тулы / ответы / retention)

- ☁️ mimo-v2.6-flash — 13/14 · 22/26 · 9/10 (эталон)
- 🟢 qwen3-14b — 13/14 · 22/26 · 9/10 — на уровне облака!
- ⚡ mimo-v2.6-9b (llama.cpp) — 13/14 · 20/26 · 9/10 — лидер локальных
- ⚡ ministral — 14/14 · 10/26 · 9/10 — идеальные тулы
- 🟡 gemma4-12b — 13/14 · 9/26 · 9/10
- 🟡 qwen3.5-9b — 13/14 · 7/26 · 9/10

| Model | Runtime | Tools (14) | Pipeline (26) | Retention (10) | Notes | Report |
|---|---|---|---|---|---|---|
| _матрица v2 (EN/RU/UK/PL) — перепрогон 2026-11-23_ | | | | | | |
| mimo-v2.6-flash | cloud (Ollama Cloud) | 13 | 22 | 9 | эталон скорости/качества | [report](cloud/mimo-v2.6-flash-ctx32768/report.md) |
| ministral-3-14b-q4km | llama.cpp | 14 | 10 | 9 | идеальные тулы, слабые цитаты | [report](llama-cpp/ministral-3-14b-q4km-ctx32768/report.md) |
| mimo-v2.6-9b | llama.cpp | 13 | 20 | 9 | лидер среди локальных | [report](llama-cpp/mimo-v2.6-9b-ctx32768/report.md) |
| gemma4-12b | Ollama | 13 | 9 | 9 | факты верны, цитаты пропускает | [report](ollama/gemma4-12b-ctx32768/report.md) |
| qwen3-14b | Ollama | 13 | 22 | 9 | второй после облака по ответам | [report](ollama/qwen3-14b-ctx32768/report.md) |
| qwen3.5-9b | Ollama | 13 | 7 | 9 | тулы ок, ответы слабые | [report](ollama/qwen3.5-9b-ctx32768/report.md) |

Старые результаты v1 (одна RU/EN-матрица) пережиты; все модели перегоняются
под 4 языка + context-recall (см. benchmarks/README.md).

Строки добавляются по мере прогонов; каждый прогон — отдельный тикет,
отчёт дублируется комментарием в тикет.
