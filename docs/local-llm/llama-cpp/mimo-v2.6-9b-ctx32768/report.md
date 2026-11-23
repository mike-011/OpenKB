# Model bench report — mimo-v2.6-9b-ctx32768

- Date/time (UTC): 2026-11-23T16:19:16+00:00 → 2026-11-23T16:50:47+00:00
- Model: `mimo-v2.6-9b` via `openai` at `http://192.168.0.203:8081`
- Bench ctx: 32768 · harness (OpenKB): `02a4eb0`

## Group: tool-call structure

**Score: 13/14**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 15.4 |  |
| t02-en-search | en | ✅ | structured | 2.1 |  |
| t03-ru-read | ru | ✅ | structured | 1.1 |  |
| t04-cyrillic-args | ru | ✅ | structured | 1.6 |  |
| t05-exact-args | en | ✅ | structured | 1.4 |  |
| t06-list | en | ✅ | structured | 0.9 |  |
| t07-no-tool | en | ✅ | none | 0.4 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 1.7 |  |
| t09-sequential | en | ✅ | structured/structured | 3.7 |  |
| t10-parallel | en | ✅ | structured | 1.8 |  |
| t11-uk-read | uk | ✅ | structured | 1.9 |  |
| t12-pl-read-diacritics | pl | ✅ | structured | 1.5 |  |
| t13-uk-search | uk | ✅ | structured | 2.2 |  |
| t14-pl-no-tool | pl | ❌ | structured | 3.6 | unexpected tool call |

## Group: OpenKB pipeline (fixture KB) — faithfulness + answer correctness

**Score: 20/26** · add: ok (476.34 s)

| Question | Lang | Cited | Facts | Latency s | Note |
|---|---|---|---|---|---|
| What is the free disk space alarm threshold?… | en | ✅ | ✅ | 35.39 | cited: ['server-setup.md'] |
| How many backup generations are kept?… | en | ✅ | ✅ | 27.58 | cited: ['backup-rotation.md'] |
| When is the database migration scheduled?… | en | ❌ | ✅ | 34.88 | no expected page cited |
| Which VLAN is the server VLAN?… | en | ✅ | ✅ | 31.61 | cited: ['network-vlan.md'] |
| How does a new employee get access?… | en | ✅ | ✅ | 53.63 | cited: ['onboarding.md'] |
| What is the router password in the server room?… | en | ❌ | ✅ | 58.48 | fabricated pages! |
| Какой порог тревоги по свободному месту на диске… | ru | ✅ | ✅ | 21.79 | cited: ['server-setup.md'] |
| Сколько поколений бэкапов хранится?… | ru | ✅ | ✅ | 59.18 | cited: ['backup-rotation.md', 'резервные-копии.md'] |
| Когда запланирована миграция базы данных?… | ru | ❌ | ✅ | 37.84 | no expected page cited |
| Какой VLAN является серверным?… | ru | ✅ | ✅ | 40.92 | cited: ['network-vlan.md'] |
| Как новый сотрудник получает доступ?… | ru | ✅ | ✅ | 34.1 | cited: ['onboarding.md'] |
| Какой пароль у роутера в серверной?… | ru | ✅ | ✅ | 67.06 |  |
| Який поріг тривоги за вільним місцем на диску?… | uk | ✅ | ✅ | 35.01 | cited: ['server-setup.md'] |
| Скільки поколінь резервних копій зберігається?… | uk | ✅ | ✅ | 33.03 | cited: ['backup-rotation.md'] |
| Коли запланована міграція бази даних?… | uk | ❌ | ✅ | 71.75 | no expected page cited |
| Який VLAN є серверним?… | uk | ❌ | ✅ | 32.65 | no expected page cited |
| Як новий співробітник отримує доступ?… | uk | ✅ | ✅ | 61.42 | cited: ['onboarding.md'] |
| Коли проводиться планове технічне обслуговування… | uk | ❌ | ✅ | 100.01 | no expected page cited |
| Який пароль від роутера в серверній?… | uk | ✅ | ✅ | 213.15 |  |
| Jaki jest próg alarmowy wolnego miejsca na dysku… | pl | ✅ | ✅ | 43.93 | cited: ['server-setup.md'] |
| Ile pokoleń kopii zapasowych jest przechowywanyc… | pl | ✅ | ✅ | 42.8 | cited: ['backup-rotation.md'] |
| Kiedy zaplanowana jest migracja bazy danych?… | pl | ✅ | ✅ | 60.78 | cited: ['db-migration-2026-11.md'] |
| Który VLAN jest serwerowy?… | pl | ✅ | ✅ | 47.22 | cited: ['network-vlan.md'] |
| Jak nowy pracownik uzyskuje dostęp?… | pl | ✅ | ✅ | 31.83 | cited: ['onboarding.md'] |
| Kiedy odbywa się konserwacja zapasowa?… | pl | ✅ | ✅ | 53.94 | cited: ['harmonogram-konserwacji.md'] |
| Jakie jest hasło do routera w serwerowni?… | pl | ✅ | ✅ | 38.92 |  |

## Group: context recall (fact retention — SCU / FActScore style)

**Retention: 9/10** — control facts surviving wiki generation (must live on a page, not just the index)

| Fact | Source | Retained | Found in |
|---|---|---|---|
| ip-monitor | server-setup.md | ❌ |  |
| disk-15 | server-setup.md | ✅ | wiki/sources/server-setup.md, wiki/summaries/server-setup.md |
| backup-2-gen | backup-rotation.md | ✅ | wiki/concepts/backup-lifecycle.md, wiki/concepts/backup-retention.md, wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-14-days | backup-rotation.md | ✅ | wiki/concepts/backup-lifecycle.md, wiki/concepts/backup-retention.md, wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-0200-warsaw | резервные-копии.md | ✅ | wiki/concepts/backup-lifecycle.md, wiki/sources/резервные-копии.md, wiki/summaries/резервные-копии.md |
| migration-2026-11-30 | db-migration-2026-11.md | ✅ | wiki/concepts/db-migration.md, wiki/sources/db-migration-2026-11.md, wiki/summaries/db-migration-2026-11.md |
| vlan-100 | network-vlan.md | ✅ | wiki/concepts/network-vlan.md, wiki/sources/network-vlan.md, wiki/summaries/network-vlan.md |
| onboarding-itsm | onboarding.md | ✅ | wiki/concepts/onboarding.md, wiki/sources/onboarding.md, wiki/summaries/onboarding.md |
| uk-service-friday-2300 | обслуговування-сервера.md | ✅ | wiki/concepts/maintenance-window.md, wiki/concepts/server-maintenance.md, wiki/sources/обслуговування-сервера.md, wiki/summaries/обслуговування-сервера.md |
| pl-konserwacja-sat-0300 | harmonogram-konserwacji.md | ✅ | wiki/concepts/db-migration.md, wiki/sources/harmonogram-konserwacji.md, wiki/summaries/harmonogram-konserwacji.md |

