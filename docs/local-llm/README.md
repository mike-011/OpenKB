# Local LLM bench reports

Сравнение локальных моделей на одинаковых задачах OpenKB (suite: `benchmarks/`,
методика и сценарии — `benchmarks/README.md`). Один каталог на модель:
`{runtime}/{model}-ctx{N}` (ctx = единый контекст прогона для сравнимости;
фактический потолок модели указан в отчёте). Внутри: `report.md` (дата/время UTC,
версии, показатели) и `results.json` (сырые данные).

## Leaderboard

| Model | Runtime | Tools (10) | Pipeline (6) | Notes | Report |
|---|---|---|---|---|---|
| mimo-v2.6-flash | Ollama Cloud | 9/10 | 6/6 | эталон (решение #41) | [report](cloud/mimo-v2.6-flash-ctx32768/report.md) |
| mimo-v2.6-9b | llama.cpp | **10/10** | **6/6** | лучший; перенос из Ollama (#70) | [report](llama-cpp/mimo-v2.6-9b-ctx32768/report.md) |
| ministral-3-14b-q4km | llama.cpp | 10/10 | 3/6 | быстрый; факты верны 5/6, цитаты 3/6 | [report](llama-cpp/ministral-3-14b-q4km-ctx32768/report.md) |
| _заполняется по мере прогонов_ | | | | | |

Строки добавляются по мере прогонов; каждый прогон — отдельный тикет,
отчёт дублируется комментарием в тикет.
