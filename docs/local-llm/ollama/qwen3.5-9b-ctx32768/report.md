# Model bench report — qwen3.5-9b-ctx32768

- Date/time (UTC): 2026-11-23T20:15:22+00:00 → 2026-11-23T20:58:27+00:00
- Model: `qwen3.5:9b` via `ollama_chat` at `http://192.168.0.203:11434`
- Bench ctx: 32768 · harness (OpenKB): `a79a414`

## Group: tool-call structure

**Score: 13/14**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 21.1 |  |
| t02-en-search | en | ✅ | structured | 4.1 |  |
| t03-ru-read | ru | ✅ | structured | 4.3 |  |
| t04-cyrillic-args | ru | ✅ | structured | 5.8 |  |
| t05-exact-args | en | ✅ | structured | 6.8 |  |
| t06-list | en | ✅ | structured | 7.7 |  |
| t07-no-tool | en | ✅ | none | 6.4 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 7.6 |  |
| t09-sequential | en | ❌ | structured/structured | 12.2 | path lacks 'backup' in [''] |
| t10-parallel | en | ✅ | structured | 12.7 |  |
| t11-uk-read | uk | ✅ | structured | 4.7 |  |
| t12-pl-read-diacritics | pl | ✅ | structured | 7.4 |  |
| t13-uk-search | uk | ✅ | structured | 12.8 |  |
| t14-pl-no-tool | pl | ✅ | none | 16.5 | no-tool expected |

## Group: OpenKB pipeline (fixture KB) — faithfulness + answer correctness

**Score: 7/26** · add: ok (1553.6 s)

| Question | Lang | Cited | Facts | Latency s | Note |
|---|---|---|---|---|---|
| What is the free disk space alarm threshold?… | en | ✅ | ✅ | 62.32 | cited: ['server-setup.md'] |
| How many backup generations are kept?… | en | ❌ | ✅ | 29.53 | no expected page cited |
| When is the database migration scheduled?… | en | ❌ | ❌ | 27.34 | no expected page cited | facts missing: ['migration-2026-11-30'] |
| Which VLAN is the server VLAN?… | en | ❌ | ✅ | 28.88 | no expected page cited |
| How does a new employee get access?… | en | ❌ | ❌ | 27.52 | no expected page cited | facts missing: ['onboarding-itsm'] |
| What is the router password in the server room?… | en | ✅ | ✅ | 57.51 |  |
| Какой порог тревоги по свободному месту на диске… | ru | ❌ | ❌ | 39.86 | no expected page cited | facts missing: ['disk-15'] |
| Сколько поколений бэкапов хранится?… | ru | ❌ | ❌ | 19.96 | no expected page cited | facts missing: ['backup-2-gen'] |
| Когда запланирована миграция базы данных?… | ru | ✅ | ✅ | 34.45 | cited: ['db-migration-2026-11.md'] |
| Какой VLAN является серверным?… | ru | ❌ | ❌ | 24.29 | no expected page cited | facts missing: ['vlan-100'] |
| Как новый сотрудник получает доступ?… | ru | ❌ | ✅ | 51.35 | no expected page cited |
| Какой пароль у роутера в серверной?… | ru | ✅ | ✅ | 47.26 |  |
| Який поріг тривоги за вільним місцем на диску?… | uk | ❌ | ✅ | 37.77 | no expected page cited |
| Скільки поколінь резервних копій зберігається?… | uk | ❌ | ✅ | 19.95 | no expected page cited |
| Коли запланована міграція бази даних?… | uk | ❌ | ✅ | 15.61 | no expected page cited |
| Який VLAN є серверним?… | uk | ❌ | ✅ | 27.02 | no expected page cited |
| Як новий співробітник отримує доступ?… | uk | ❌ | ❌ | 28.51 | no expected page cited | facts missing: ['onboarding-itsm'] |
| Коли проводиться планове технічне обслуговування… | uk | ❌ | ❌ | 26.09 | no expected page cited | facts missing: ['uk-service-friday-2300'] |
| Який пароль від роутера в серверній?… | uk | ✅ | ✅ | 70.22 |  |
| Jaki jest próg alarmowy wolnego miejsca na dysku… | pl | ❌ | ❌ | 29.79 | no expected page cited | facts missing: ['disk-15'] |
| Ile pokoleń kopii zapasowych jest przechowywanyc… | pl | ❌ | ❌ | 27.09 | no expected page cited | facts missing: ['backup-2-gen'] |
| Kiedy zaplanowana jest migracja bazy danych?… | pl | ❌ | ❌ | 34.38 | no expected page cited | facts missing: ['migration-2026-11-30'] |
| Który VLAN jest serwerowy?… | pl | ❌ | ✅ | 30.66 | no expected page cited |
| Jak nowy pracownik uzyskuje dostęp?… | pl | ✅ | ✅ | 52.4 | cited: ['onboarding.md'] |
| Kiedy odbywa się konserwacja zapasowa?… | pl | ❌ | ❌ | 25.17 | no expected page cited | facts missing: ['pl-konserwacja-sat-0300'] |
| Jakie jest hasło do routera w serwerowni?… | pl | ✅ | ✅ | 20.66 |  |

## Group: context recall (fact retention — SCU / FActScore style)

**Retention: 9/10** — control facts surviving wiki generation (must live on a page, not just the index)

| Fact | Source | Retained | Found in |
|---|---|---|---|
| ip-monitor | server-setup.md | ❌ |  |
| disk-15 | server-setup.md | ✅ | wiki/sources/server-setup.md |
| backup-2-gen | backup-rotation.md | ✅ | wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-14-days | backup-rotation.md | ✅ | wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-0200-warsaw | резервные-копии.md | ✅ | wiki/sources/резервные-копии.md, wiki/summaries/резервные-копии.md |
| migration-2026-11-30 | db-migration-2026-11.md | ✅ | wiki/log.md, wiki/sources/db-migration-2026-11.md, wiki/summaries/db-migration-2026-11.md |
| vlan-100 | network-vlan.md | ✅ | wiki/sources/network-vlan.md, wiki/summaries/network-vlan.md |
| onboarding-itsm | onboarding.md | ✅ | wiki/concepts/access-management.md, wiki/concepts/onboarding-workflow.md, wiki/sources/onboarding.md, wiki/summaries/onboarding.md |
| uk-service-friday-2300 | обслуговування-сервера.md | ✅ | wiki/sources/обслуговування-сервера.md |
| pl-konserwacja-sat-0300 | harmonogram-konserwacji.md | ✅ | wiki/sources/harmonogram-konserwacji.md |

