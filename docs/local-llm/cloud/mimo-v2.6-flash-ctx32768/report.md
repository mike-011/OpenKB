# Model bench report — mimo-v2.6-flash-ctx32768

- Date/time (UTC): 2026-11-23T12:57:44+00:00 → 2026-11-23T13:00:33+00:00
- Model: `mimo-v2.6-flash` via `openai` at `https://ollama.com`
- Bench ctx: 32768 · harness (OpenKB): `1d35428`

## Group: tool-call structure

**Score: 9/10**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 0.6 |  |
| t02-en-search | en | ✅ | structured | 1.0 |  |
| t03-ru-read | ru | ✅ | structured | 1.0 |  |
| t04-cyrillic-args | ru | ✅ | structured | 0.6 |  |
| t05-exact-args | en | ✅ | structured | 0.7 |  |
| t06-list | en | ✅ | structured | 0.6 |  |
| t07-no-tool | en | ✅ | none | 0.7 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 0.9 |  |
| t09-sequential | en | ❌ | structured/structured | 1.8 | path lacks 'backup' in [''] |
| t10-parallel | en | ✅ | structured | 0.8 |  |

## Group: OpenKB pipeline (fixture KB)

**Score: 6/6** · add: ok (86.05 s)

| Question | Grounded | Latency s | Note |
|---|---|---|---|
| Какой порог тревоги по свободному месту на диске… | ✅ | 9.99 | cited: ['server-setup.md'] |
| Сколько поколений бэкапов хранится?… | ✅ | 11.66 | cited: ['backup-rotation.md', 'резервные-копии.md'] |
| Когда запланирована миграция базы данных?… | ✅ | 12.65 | cited: ['db-migration-2026-11.md'] |
| Какой VLAN является серверным?… | ✅ | 10.55 | cited: ['network-vlan.md'] |
| Как новый сотрудник получает доступ?… | ✅ | 12.2 | cited: ['onboarding.md'] |
| Какой пароль у роутера в серверной?… | ✅ | 11.87 |  |

