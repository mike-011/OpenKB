# Model bench report — ministral-3-14b-q4km-ctx32768

- Date/time (UTC): 2026-11-23T15:51:02+00:00 → 2026-11-23T16:09:15+00:00
- Model: `ministral-3-14b-q4km` via `openai` at `http://192.168.0.203:8081`
- Bench ctx: 32768 · harness (OpenKB): `9328525`

## Group: tool-call structure

**Score: 14/14**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 10.8 |  |
| t02-en-search | en | ✅ | structured | 0.8 |  |
| t03-ru-read | ru | ✅ | structured | 1.0 |  |
| t04-cyrillic-args | ru | ✅ | structured | 1.3 |  |
| t05-exact-args | en | ✅ | structured | 1.4 |  |
| t06-list | en | ✅ | structured | 0.8 |  |
| t07-no-tool | en | ✅ | none | 0.2 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 1.1 |  |
| t09-sequential | en | ✅ | structured/structured | 2.2 |  |
| t10-parallel | en | ✅ | structured | 1.7 |  |
| t11-uk-read | uk | ✅ | structured | 0.9 |  |
| t12-pl-read-diacritics | pl | ✅ | structured | 1.5 |  |
| t13-uk-search | uk | ✅ | structured | 0.9 |  |
| t14-pl-no-tool | pl | ✅ | none | 2.9 | no-tool expected |

## Group: OpenKB pipeline (fixture KB) — faithfulness + answer correctness

**Score: 10/26** · add: ok (394.91 s)

| Question | Lang | Cited | Facts | Latency s | Note |
|---|---|---|---|---|---|
| What is the free disk space alarm threshold?… | en | ✅ | ✅ | 24.63 | cited: ['server-setup.md'] |
| How many backup generations are kept?… | en | ❌ | ✅ | 12.0 | no expected page cited |
| When is the database migration scheduled?… | en | ✅ | ✅ | 14.14 | cited: ['db-migration-2026-11.md'] |
| Which VLAN is the server VLAN?… | en | ✅ | ✅ | 16.46 | cited: ['network-vlan.md'] |
| How does a new employee get access?… | en | ✅ | ✅ | 16.34 | cited: ['onboarding.md'] |
| What is the router password in the server room?… | en | ✅ | ✅ | 13.54 |  |
| Какой порог тревоги по свободному месту на диске… | ru | ❌ | ✅ | 19.14 | no expected page cited |
| Сколько поколений бэкапов хранится?… | ru | ❌ | ❌ | 17.62 | no expected page cited | facts missing: ['backup-2-gen'] |
| Когда запланирована миграция базы данных?… | ru | ❌ | ✅ | 17.9 | no expected page cited |
| Какой VLAN является серверным?… | ru | ❌ | ✅ | 15.16 | no expected page cited |
| Как новый сотрудник получает доступ?… | ru | ❌ | ✅ | 40.01 | no expected page cited |
| Какой пароль у роутера в серверной?… | ru | ✅ | ✅ | 30.06 |  |
| Який поріг тривоги за вільним місцем на диску?… | uk | ❌ | ✅ | 16.9 | no expected page cited |
| Скільки поколінь резервних копій зберігається?… | uk | ✅ | ❌ | 28.23 | cited: ['backup-rotation.md'] | facts missing: ['backup-2-gen'] |
| Коли запланована міграція бази даних?… | uk | ✅ | ✅ | 15.99 | cited: ['db-migration-2026-11.md'] |
| Який VLAN є серверним?… | uk | ❌ | ✅ | 15.49 | no expected page cited |
| Як новий співробітник отримує доступ?… | uk | ❌ | ✅ | 55.22 | no expected page cited |
| Коли проводиться планове технічне обслуговування… | uk | ❌ | ✅ | 12.96 | no expected page cited |
| Який пароль від роутера в серверній?… | uk | ✅ | ✅ | 73.56 |  |
| Jaki jest próg alarmowy wolnego miejsca na dysku… | pl | ✅ | ✅ | 16.26 | cited: ['server-setup.md'] |
| Ile pokoleń kopii zapasowych jest przechowywanyc… | pl | ✅ | ❌ | 31.92 | cited: ['backup-rotation.md'] | facts missing: ['backup-2-gen'] |
| Kiedy zaplanowana jest migracja bazy danych?… | pl | ❌ | ✅ | 19.18 | no expected page cited |
| Który VLAN jest serwerowy?… | pl | ❌ | ✅ | 63.88 | no expected page cited |
| Jak nowy pracownik uzyskuje dostęp?… | pl | ❌ | ✅ | 36.7 | no expected page cited |
| Kiedy odbywa się konserwacja zapasowa?… | pl | ❌ | ❌ | 13.34 | no expected page cited | facts missing: ['pl-konserwacja-sat-0300'] |
| Jakie jest hasło do routera w serwerowni?… | pl | ✅ | ✅ | 28.32 |  |

## Group: context recall (fact retention — SCU / FActScore style)

**Retention: 9/10** — control facts surviving wiki generation (must live on a page, not just the index)

| Fact | Source | Retained | Found in |
|---|---|---|---|
| ip-monitor | server-setup.md | ❌ |  |
| disk-15 | server-setup.md | ✅ | wiki/sources/server-setup.md, wiki/summaries/server-setup.md |
| backup-2-gen | backup-rotation.md | ✅ | wiki/sources/backup-rotation.md |
| backup-14-days | backup-rotation.md | ✅ | wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-0200-warsaw | резервные-копии.md | ✅ | wiki/sources/резервные-копии.md, wiki/summaries/резервные-копии.md |
| migration-2026-11-30 | db-migration-2026-11.md | ✅ | wiki/sources/db-migration-2026-11.md, wiki/summaries/db-migration-2026-11.md |
| vlan-100 | network-vlan.md | ✅ | wiki/sources/network-vlan.md, wiki/summaries/network-vlan.md |
| onboarding-itsm | onboarding.md | ✅ | wiki/sources/onboarding.md, wiki/summaries/onboarding.md |
| uk-service-friday-2300 | обслуговування-сервера.md | ✅ | wiki/sources/обслуговування-сервера.md, wiki/summaries/обслуговування-сервера.md |
| pl-konserwacja-sat-0300 | harmonogram-konserwacji.md | ✅ | wiki/sources/harmonogram-konserwacji.md |

