# Model bench report — gemma4-12b-ctx32768

- Date/time (UTC): 2026-11-23T14:10:13+00:00 → 2026-11-23T15:05:26+00:00
- Model: `gemma4:12b` via `ollama_chat` at `http://192.168.100.165:11434`
- Bench ctx: 32768 · harness (OpenKB): `79bae6d`

## Group: tool-call structure

**Score: 9/10**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 20.3 |  |
| t02-en-search | en | ✅ | structured | 2.1 |  |
| t03-ru-read | ru | ✅ | structured | 2.3 |  |
| t04-cyrillic-args | ru | ✅ | structured | 2.6 |  |
| t05-exact-args | en | ✅ | structured | 2.9 |  |
| t06-list | en | ✅ | structured | 2.2 |  |
| t07-no-tool | en | ✅ | none | 3.1 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 3.1 |  |
| t09-sequential | en | ❌ | structured/structured | 6.9 | path lacks 'backup' in [''] |
| t10-parallel | en | ✅ | structured | 4.0 |  |

## Group: OpenKB pipeline (fixture KB)

**Score: 1/6** · add: ok (2945.95 s)

| Question | Grounded | Latency s | Note |
|---|---|---|---|
| Какой порог тревоги по свободному месту на диске… | ❌ | 55.55 | no expected page cited |
| Сколько поколений бэкапов хранится?… | ❌ | 30.16 | no expected page cited |
| Когда запланирована миграция базы данных?… | ❌ | 55.1 | no expected page cited |
| Какой VLAN является серверным?… | ❌ | 45.42 | no expected page cited |
| Как новый сотрудник получает доступ?… | ❌ | 29.16 | no expected page cited |
| Какой пароль у роутера в серверной?… | ✅ | 95.87 |  |

