# Model bench report — ministral-3-14b-q4km-ctx32768

- Date/time (UTC): 2026-11-23T12:57:01+00:00 → 2026-11-23T13:05:31+00:00
- Model: `ministral-3-14b-q4km` via `openai` at `http://192.168.0.203:8081`
- Bench ctx: 32768 · harness (OpenKB): `24c7af9`

## Group: tool-call structure

**Score: 10/10**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 1.5 |  |
| t02-en-search | en | ✅ | structured | 1.0 |  |
| t03-ru-read | ru | ✅ | structured | 1.3 |  |
| t04-cyrillic-args | ru | ✅ | structured | 1.7 |  |
| t05-exact-args | en | ✅ | structured | 1.9 |  |
| t06-list | en | ✅ | structured | 1.0 |  |
| t07-no-tool | en | ✅ | none | 0.2 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 1.4 |  |
| t09-sequential | en | ✅ | structured/structured | 2.0 |  |
| t10-parallel | en | ✅ | structured | 2.3 |  |

## Group: OpenKB pipeline (fixture KB)

**Score: 3/6** · add: ok (334.32 s)

| Question | Grounded | Latency s | Note |
|---|---|---|---|
| Какой порог тревоги по свободному месту на диске… | ❌ | 31.29 | no expected page cited |
| Сколько поколений бэкапов хранится?… | ❌ | 32.43 | no expected page cited |
| Когда запланирована миграция базы данных?… | ✅ | 20.14 | cited: ['db-migration-2026-11'] |
| Какой VLAN является серверным?… | ❌ | 26.65 | no expected page cited |
| Как новый сотрудник получает доступ?… | ✅ | 22.21 | cited: ['onboarding'] |
| Какой пароль у роутера в серверной?… | ✅ | 22.75 |  |

