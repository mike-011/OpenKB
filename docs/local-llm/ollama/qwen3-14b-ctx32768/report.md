# Model bench report — qwen3-14b-ctx32768

- Date/time (UTC): 2026-11-23T18:17:02+00:00 → 2026-11-23T20:15:20+00:00
- Model: `qwen3:14b` via `ollama_chat` at `http://192.168.0.203:11434`
- Bench ctx: 32768 · harness (OpenKB): `a79a414`

## Group: tool-call structure

**Score: 13/14**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 29.9 |  |
| t02-en-search | en | ✅ | structured | 10.1 |  |
| t03-ru-read | ru | ✅ | structured | 15.2 |  |
| t04-cyrillic-args | ru | ✅ | structured | 26.1 |  |
| t05-exact-args | en | ✅ | structured | 20.7 |  |
| t06-list | en | ✅ | structured | 17.1 |  |
| t07-no-tool | en | ✅ | none | 30.8 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 102.0 |  |
| t09-sequential | en | ❌ | structured/structured | 46.7 | path lacks 'backup' in [''] |
| t10-parallel | en | ✅ | structured | 29.1 |  |
| t11-uk-read | uk | ✅ | structured | 13.1 |  |
| t12-pl-read-diacritics | pl | ✅ | structured | 20.5 |  |
| t13-uk-search | uk | ✅ | structured | 18.7 |  |
| t14-pl-no-tool | pl | ✅ | none | 23.6 | no-tool expected |

## Group: OpenKB pipeline (fixture KB) — faithfulness + answer correctness

**Score: 22/26** · add: ok (3125.72 s)

| Question | Lang | Cited | Facts | Latency s | Note |
|---|---|---|---|---|---|
| What is the free disk space alarm threshold?… | en | ✅ | ✅ | 107.0 | cited: ['server-setup.md'] |
| How many backup generations are kept?… | en | ✅ | ✅ | 135.51 | cited: ['backup-rotation.md'] |
| When is the database migration scheduled?… | en | ❌ | ✅ | 93.81 | no expected page cited |
| Which VLAN is the server VLAN?… | en | ✅ | ✅ | 115.65 | cited: ['network-vlan.md'] |
| How does a new employee get access?… | en | ✅ | ✅ | 108.12 | cited: ['onboarding.md'] |
| What is the router password in the server room?… | en | ✅ | ✅ | 181.29 |  |
| Какой порог тревоги по свободному месту на диске… | ru | ✅ | ✅ | 74.44 | cited: ['server-setup.md'] |
| Сколько поколений бэкапов хранится?… | ru | ✅ | ✅ | 190.75 | cited: ['backup-rotation.md'] |
| Когда запланирована миграция базы данных?… | ru | ✅ | ✅ | 91.71 | cited: ['db-migration-2026-11.md'] |
| Какой VLAN является серверным?… | ru | ✅ | ✅ | 134.31 | cited: ['network-vlan.md'] |
| Как новый сотрудник получает доступ?… | ru | ✅ | ✅ | 101.13 | cited: ['onboarding.md'] |
| Какой пароль у роутера в серверной?… | ru | ✅ | ✅ | 69.58 |  |
| Який поріг тривоги за вільним місцем на диску?… | uk | ✅ | ✅ | 181.57 | cited: ['server-setup.md'] |
| Скільки поколінь резервних копій зберігається?… | uk | ✅ | ✅ | 101.25 | cited: ['backup-rotation.md'] |
| Коли запланована міграція бази даних?… | uk | ❌ | ✅ | 93.09 | no expected page cited |
| Який VLAN є серверним?… | uk | ✅ | ✅ | 78.0 | cited: ['network-vlan.md'] |
| Як новий співробітник отримує доступ?… | uk | ❌ | ✅ | 208.18 | no expected page cited |
| Коли проводиться планове технічне обслуговування… | uk | ✅ | ✅ | 243.01 | cited: ['обслуговування-сервера.md'] |
| Який пароль від роутера в серверній?… | uk | ✅ | ✅ | 211.11 |  |
| Jaki jest próg alarmowy wolnego miejsca na dysku… | pl | ✅ | ✅ | 78.4 | cited: ['server-setup.md'] |
| Ile pokoleń kopii zapasowych jest przechowywanyc… | pl | ✅ | ✅ | 178.44 | cited: ['backup-rotation.md'] |
| Kiedy zaplanowana jest migracja bazy danych?… | pl | ✅ | ✅ | 158.93 | cited: ['db-migration-2026-11.md'] |
| Który VLAN jest serwerowy?… | pl | ✅ | ✅ | 207.95 | cited: ['network-vlan.md'] |
| Jak nowy pracownik uzyskuje dostęp?… | pl | ✅ | ✅ | 94.65 | cited: ['onboarding.md'] |
| Kiedy odbywa się konserwacja zapasowa?… | pl | ✅ | ❌ | 158.14 | cited: ['harmonogram-konserwacji.md'] | facts missing: ['pl-konserwacja-sat-0300'] |
| Jakie jest hasło do routera w serwerowni?… | pl | ✅ | ✅ | 166.48 |  |

## Group: context recall (fact retention — SCU / FActScore style)

**Retention: 9/10** — control facts surviving wiki generation (must live on a page, not just the index)

| Fact | Source | Retained | Found in |
|---|---|---|---|
| ip-monitor | server-setup.md | ❌ |  |
| disk-15 | server-setup.md | ✅ | wiki/concepts/disk-alarm-threshold.md, wiki/sources/server-setup.md, wiki/summaries/server-setup.md |
| backup-2-gen | backup-rotation.md | ✅ | wiki/concepts/data-retention-policies.md, wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-14-days | backup-rotation.md | ✅ | wiki/concepts/backup-rotation.md, wiki/concepts/data-retention-policies.md, wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-0200-warsaw | резервные-копии.md | ✅ | wiki/concepts/backup-maintenance-schedule.md, wiki/sources/резервные-копии.md, wiki/summaries/резервные-копии.md |
| migration-2026-11-30 | db-migration-2026-11.md | ✅ | wiki/concepts/database-migration.md, wiki/sources/db-migration-2026-11.md, wiki/summaries/db-migration-2026-11.md |
| vlan-100 | network-vlan.md | ✅ | wiki/concepts/network-architecture.md, wiki/concepts/network-segmentation.md, wiki/entities/vlan-100.md, wiki/sources/network-vlan.md, wiki/summaries/network-vlan.md |
| onboarding-itsm | onboarding.md | ✅ | wiki/sources/onboarding.md, wiki/summaries/onboarding.md |
| uk-service-friday-2300 | обслуговування-сервера.md | ✅ | wiki/concepts/planovoe-tehnichnoe-obsluzhuvannia.md, wiki/sources/обслуговування-сервера.md, wiki/summaries/обслуговування-сервера.md |
| pl-konserwacja-sat-0300 | harmonogram-konserwacji.md | ✅ | wiki/sources/harmonogram-konserwacji.md, wiki/summaries/harmonogram-konserwacji.md |

