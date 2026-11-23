# Model bench report — mimo-v2.6-flash-ctx32768

- Date/time (UTC): 2026-11-23T15:49:56+00:00 → 2026-11-23T15:56:38+00:00
- Model: `mimo-v2.6-flash` via `openai` at `https://ollama.com`
- Bench ctx: 32768 · harness (OpenKB): `c3c0a8b`

## Group: tool-call structure

**Score: 13/14**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 0.9 |  |
| t02-en-search | en | ✅ | structured | 0.6 |  |
| t03-ru-read | ru | ✅ | structured | 0.6 |  |
| t04-cyrillic-args | ru | ✅ | structured | 0.9 |  |
| t05-exact-args | en | ✅ | structured | 0.8 |  |
| t06-list | en | ✅ | structured | 0.6 |  |
| t07-no-tool | en | ✅ | none | 0.4 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 0.7 |  |
| t09-sequential | en | ❌ | structured/structured | 1.3 | path lacks 'backup' in [''] |
| t10-parallel | en | ✅ | structured | 0.7 |  |
| t11-uk-read | uk | ✅ | structured | 0.9 |  |
| t12-pl-read-diacritics | pl | ✅ | structured | 0.7 |  |
| t13-uk-search | uk | ✅ | structured | 0.8 |  |
| t14-pl-no-tool | pl | ✅ | none | 1.5 | no-tool expected |

## Group: OpenKB pipeline (fixture KB) — faithfulness + answer correctness

**Score: 22/26** · add: ok (89.72 s)

| Question | Lang | Cited | Facts | Latency s | Note |
|---|---|---|---|---|---|
| What is the free disk space alarm threshold?… | en | ✅ | ✅ | 12.64 | cited: ['server-setup.md'] |
| How many backup generations are kept?… | en | ✅ | ✅ | 10.65 | cited: ['backup-rotation.md', 'резервные-копии.md'] |
| When is the database migration scheduled?… | en | ✅ | ✅ | 11.48 | cited: ['db-migration-2026-11.md'] |
| Which VLAN is the server VLAN?… | en | ✅ | ✅ | 9.47 | cited: ['network-vlan.md'] |
| How does a new employee get access?… | en | ✅ | ✅ | 12.31 | cited: ['onboarding.md'] |
| What is the router password in the server room?… | en | ✅ | ✅ | 8.54 |  |
| Какой порог тревоги по свободному месту на диске… | ru | ✅ | ✅ | 9.62 | cited: ['server-setup.md'] |
| Сколько поколений бэкапов хранится?… | ru | ❌ | ✅ | 11.64 | no expected page cited |
| Когда запланирована миграция базы данных?… | ru | ✅ | ✅ | 11.55 | cited: ['db-migration-2026-11.md'] |
| Какой VLAN является серверным?… | ru | ❌ | ✅ | 12.47 | no expected page cited |
| Как новый сотрудник получает доступ?… | ru | ✅ | ✅ | 12.58 | cited: ['onboarding.md'] |
| Какой пароль у роутера в серверной?… | ru | ✅ | ✅ | 12.5 |  |
| Який поріг тривоги за вільним місцем на диску?… | uk | ✅ | ✅ | 12.5 | cited: ['server-setup.md'] |
| Скільки поколінь резервних копій зберігається?… | uk | ✅ | ✅ | 11.45 | cited: ['backup-rotation.md'] |
| Коли запланована міграція бази даних?… | uk | ✅ | ✅ | 10.96 | cited: ['db-migration-2026-11.md'] |
| Який VLAN є серверним?… | uk | ✅ | ✅ | 9.6 | cited: ['network-vlan.md'] |
| Як новий співробітник отримує доступ?… | uk | ✅ | ✅ | 11.03 | cited: ['onboarding.md'] |
| Коли проводиться планове технічне обслуговування… | uk | ✅ | ✅ | 10.76 | cited: ['обслуговування-сервера.md'] |
| Який пароль від роутера в серверній?… | uk | ✅ | ✅ | 12.38 |  |
| Jaki jest próg alarmowy wolnego miejsca na dysku… | pl | ❌ | ✅ | 11.43 | no expected page cited |
| Ile pokoleń kopii zapasowych jest przechowywanyc… | pl | ❌ | ✅ | 11.31 | no expected page cited |
| Kiedy zaplanowana jest migracja bazy danych?… | pl | ✅ | ✅ | 11.98 | cited: ['db-migration-2026-11.md'] |
| Który VLAN jest serwerowy?… | pl | ✅ | ✅ | 10.19 | cited: ['network-vlan.md'] |
| Jak nowy pracownik uzyskuje dostęp?… | pl | ✅ | ✅ | 11.25 | cited: ['onboarding.md'] |
| Kiedy odbywa się konserwacja zapasowa?… | pl | ✅ | ✅ | 11.37 | cited: ['harmonogram-konserwacji.md'] |
| Jakie jest hasło do routera w serwerowni?… | pl | ✅ | ✅ | 12.77 |  |

## Group: context recall (fact retention — SCU / FActScore style)

**Retention: 9/10** — control facts surviving wiki generation (must live on a page, not just the index)

| Fact | Source | Retained | Found in |
|---|---|---|---|
| ip-monitor | server-setup.md | ❌ |  |
| disk-15 | server-setup.md | ✅ | wiki/concepts/alert-thresholds.md, wiki/concepts/monitoring.md, wiki/entities/monitoring-server.md, wiki/sources/server-setup.md, wiki/summaries/server-setup.md |
| backup-2-gen | backup-rotation.md | ✅ | wiki/concepts/backup-rotation.md, wiki/concepts/data-retention.md, wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-14-days | backup-rotation.md | ✅ | wiki/concepts/backup-rotation.md, wiki/concepts/data-retention.md, wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-0200-warsaw | резервные-копии.md | ✅ | wiki/concepts/backup-scheduling.md, wiki/sources/резервные-копии.md, wiki/summaries/резервные-копии.md |
| migration-2026-11-30 | db-migration-2026-11.md | ✅ | wiki/entities/db-migration-2026-11-30.md, wiki/sources/db-migration-2026-11.md, wiki/summaries/db-migration-2026-11.md |
| vlan-100 | network-vlan.md | ✅ | wiki/concepts/network-segmentation.md, wiki/concepts/vlan.md, wiki/sources/network-vlan.md, wiki/summaries/network-vlan.md |
| onboarding-itsm | onboarding.md | ✅ | wiki/concepts/access-management.md, wiki/concepts/employee-onboarding.md, wiki/concepts/itsm.md, wiki/concepts/planned-maintenance.md, wiki/sources/onboarding.md, wiki/summaries/onboarding.md |
| uk-service-friday-2300 | обслуговування-сервера.md | ✅ | wiki/concepts/planned-maintenance.md, wiki/sources/обслуговування-сервера.md, wiki/summaries/обслуговування-сервера.md |
| pl-konserwacja-sat-0300 | harmonogram-konserwacji.md | ✅ | wiki/sources/harmonogram-konserwacji.md |

