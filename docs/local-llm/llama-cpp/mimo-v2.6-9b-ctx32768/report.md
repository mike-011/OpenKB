# Model bench report — mimo-v2.6-9b-ctx32768

- Date/time (UTC): 2026-11-23T13:51:33+00:00 → 2026-11-23T13:59:39+00:00
- Model: `mimo-v2.6-9b` via `openai` at `http://192.168.100.165:8081`
- Bench ctx: 32768 · harness (OpenKB): `ca28d77`

## Group: tool-call structure

**Score: 10/10**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 1.8 |  |
| t02-en-search | en | ✅ | structured | 1.7 |  |
| t03-ru-read | ru | ✅ | structured | 1.0 |  |
| t04-cyrillic-args | ru | ✅ | structured | 1.2 |  |
| t05-exact-args | en | ✅ | structured | 1.4 |  |
| t06-list | en | ✅ | structured | 1.0 |  |
| t07-no-tool | en | ✅ | none | 0.4 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 1.6 |  |
| t09-sequential | en | ✅ | structured/structured | 2.1 |  |
| t10-parallel | en | ✅ | structured | 2.0 |  |

## Group: OpenKB pipeline (fixture KB)

**Score: 6/6** · add: ok (203.72 s)

| Question | Grounded | Latency s | Note |
|---|---|---|---|
| Какой порог тревоги по свободному месту на диске… | ✅ | 27.89 | cited: ['server-setup.md'] |
| Сколько поколений бэкапов хранится?… | ✅ | 20.58 | cited: ['backup-rotation.md'] |
| Когда запланирована миграция базы данных?… | ✅ | 33.48 | cited: ['db-migration-2026-11.md'] |
| Какой VLAN является серверным?… | ✅ | 13.63 | cited: ['network-vlan.md'] |
| Как новый сотрудник получает доступ?… | ✅ | 28.14 | cited: ['onboarding.md'] |
| Какой пароль у роутера в серверной?… | ✅ | 138.17 |  |

