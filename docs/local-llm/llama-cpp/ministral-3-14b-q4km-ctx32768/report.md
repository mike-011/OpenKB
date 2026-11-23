# Model bench report — ministral-3-14b-q4km-ctx32768

- Date/time (UTC): 2026-11-23T12:46:22+00:00 → 2026-11-23T12:56:22+00:00
- Model: `ministral-3-14b-q4km` via `openai` at `http://192.168.0.203:8081`
- Bench ctx: 32768 · harness (OpenKB): `1d35428`

## Group: tool-call structure

**Score: 10/10**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 17.9 |  |
| t02-en-search | en | ✅ | structured | 0.9 |  |
| t03-ru-read | ru | ✅ | structured | 1.2 |  |
| t04-cyrillic-args | ru | ✅ | structured | 1.6 |  |
| t05-exact-args | en | ✅ | structured | 1.7 |  |
| t06-list | en | ✅ | structured | 0.9 |  |
| t07-no-tool | en | ✅ | none | 0.2 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 1.3 |  |
| t09-sequential | en | ✅ | structured/structured | 1.8 |  |
| t10-parallel | en | ✅ | structured | 2.1 |  |

## Group: OpenKB pipeline (fixture KB)

**Score: 1/6** · add: ok (399.81 s)

| Question | Grounded | Latency s | Note |
|---|---|---|---|
| Какой порог тревоги по свободному месту на диске… | ❌ | 28.79 | no expected page cited |
| Сколько поколений бэкапов хранится?… | ❌ | 19.43 | no expected page cited |
| Когда запланирована миграция базы данных?… | ❌ | 17.51 | no expected page cited |
| Какой VLAN является серверным?… | ❌ | 23.67 | no expected page cited |
| Как новый сотрудник получает доступ?… | ❌ | 43.79 | no expected page cited |
| Какой пароль у роутера в серверной?… | ✅ | 31.69 |  |

