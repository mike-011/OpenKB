# Model bench report — gemma4-12b-ctx32768

- Date/time (UTC): 2026-11-23T17:00:50+00:00 → 2026-11-23T18:17:00+00:00
- Model: `gemma4:12b` via `ollama_chat` at `http://192.168.0.203:11434`
- Bench ctx: 32768 · harness (OpenKB): `02a4eb0`

## Group: tool-call structure

**Score: 13/14**

| Scenario | Lang | Pass | Form | Latency s | Note |
|---|---|---|---|---|---|
| t01-en-read | en | ✅ | structured | 20.9 |  |
| t02-en-search | en | ✅ | structured | 2.4 |  |
| t03-ru-read | ru | ✅ | structured | 2.4 |  |
| t04-cyrillic-args | ru | ✅ | structured | 2.8 |  |
| t05-exact-args | en | ✅ | structured | 2.9 |  |
| t06-list | en | ✅ | structured | 2.2 |  |
| t07-no-tool | en | ✅ | none | 3.5 | no-tool expected |
| t08-ru-search-cyrillic | ru | ✅ | structured | 2.6 |  |
| t09-sequential | en | ❌ | structured/structured | 5.0 | path lacks 'backup' in [''] |
| t10-parallel | en | ✅ | structured | 3.6 |  |
| t11-uk-read | uk | ✅ | structured | 2.4 |  |
| t12-pl-read-diacritics | pl | ✅ | structured | 4.1 |  |
| t13-uk-search | uk | ✅ | structured | 2.4 |  |
| t14-pl-no-tool | pl | ✅ | none | 14.5 | no-tool expected |

## Group: OpenKB pipeline (fixture KB) — faithfulness + answer correctness

**Score: 9/26** · add: ok (3456.71 s)

| Question | Lang | Cited | Facts | Latency s | Note |
|---|---|---|---|---|---|
| What is the free disk space alarm threshold?… | en | ❌ | ❌ | 53.19 | no expected page cited | facts missing: ['disk-15'] |
| How many backup generations are kept?… | en | ✅ | ✅ | 57.55 | cited: ['backup-rotation.md'] |
| When is the database migration scheduled?… | en | ❌ | ✅ | 25.68 | no expected page cited |
| Which VLAN is the server VLAN?… | en | ❌ | ✅ | 39.88 | no expected page cited |
| How does a new employee get access?… | en | ✅ | ✅ | 65.76 | cited: ['onboarding.md'] |
| What is the router password in the server room?… | en | ✅ | ✅ | 38.8 |  |
| Какой порог тревоги по свободному месту на диске… | ru | ❌ | ❌ | 29.48 | no expected page cited | facts missing: ['disk-15'] |
| Сколько поколений бэкапов хранится?… | ru | ❌ | ✅ | 28.55 | no expected page cited |
| Когда запланирована миграция базы данных?… | ru | ❌ | ✅ | 47.02 | no expected page cited |
| Какой VLAN является серверным?… | ru | ❌ | ✅ | 14.76 | no expected page cited |
| Как новый сотрудник получает доступ?… | ru | ✅ | ✅ | 47.9 | cited: ['onboarding.md'] |
| Какой пароль у роутера в серверной?… | ru | ✅ | ✅ | 56.9 |  |
| Який поріг тривоги за вільним місцем на диску?… | uk | ❌ | ✅ | 25.17 | no expected page cited |
| Скільки поколінь резервних копій зберігається?… | uk | ❌ | ✅ | 23.22 | no expected page cited |
| Коли запланована міграція бази даних?… | uk | ❌ | ✅ | 33.96 | no expected page cited |
| Який VLAN є серверним?… | uk | ❌ | ✅ | 36.66 | no expected page cited |
| Як новий співробітник отримує доступ?… | uk | ✅ | ✅ | 51.45 | cited: ['onboarding.md'] |
| Коли проводиться планове технічне обслуговування… | uk | ❌ | ❌ | 28.42 | no expected page cited | facts missing: ['uk-service-friday-2300'] |
| Який пароль від роутера в серверній?… | uk | ✅ | ✅ | 51.05 |  |
| Jaki jest próg alarmowy wolnego miejsca na dysku… | pl | ❌ | ✅ | 37.77 | no expected page cited |
| Ile pokoleń kopii zapasowych jest przechowywanyc… | pl | ❌ | ✅ | 32.85 | no expected page cited |
| Kiedy zaplanowana jest migracja bazy danych?… | pl | ❌ | ✅ | 33.42 | no expected page cited |
| Który VLAN jest serwerowy?… | pl | ❌ | ✅ | 23.27 | no expected page cited |
| Jak nowy pracownik uzyskuje dostęp?… | pl | ✅ | ✅ | 37.56 | cited: ['onboarding.md'] |
| Kiedy odbywa się konserwacja zapasowa?… | pl | ❌ | ✅ | 62.3 | no expected page cited |
| Jakie jest hasło do routera w serwerowni?… | pl | ✅ | ✅ | 53.9 |  |

## Group: context recall (fact retention — SCU / FActScore style)

**Retention: 9/10** — control facts surviving wiki generation (must live on a page, not just the index)

| Fact | Source | Retained | Found in |
|---|---|---|---|
| ip-monitor | server-setup.md | ❌ |  |
| disk-15 | server-setup.md | ✅ | wiki/concepts/server_infrastructure.md, wiki/sources/server-setup.md |
| backup-2-gen | backup-rotation.md | ✅ | wiki/concepts/data_retention.md, wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-14-days | backup-rotation.md | ✅ | wiki/concepts/data_retention.md, wiki/sources/backup-rotation.md, wiki/summaries/backup-rotation.md |
| backup-0200-warsaw | резервные-копии.md | ✅ | wiki/sources/резервные-копии.md, wiki/summaries/резервные-копии.md |
| migration-2026-11-30 | db-migration-2026-11.md | ✅ | wiki/sources/db-migration-2026-11.md, wiki/summaries/db-migration-2026-11.md |
| vlan-100 | network-vlan.md | ✅ | wiki/concepts/vlan.md, wiki/sources/network-vlan.md, wiki/summaries/network-vlan.md |
| onboarding-itsm | onboarding.md | ✅ | wiki/concepts/access_management.md, wiki/concepts/itsm.md, wiki/sources/onboarding.md, wiki/summaries/onboarding.md |
| uk-service-friday-2300 | обслуговування-сервера.md | ✅ | wiki/sources/обслуговування-сервера.md |
| pl-konserwacja-sat-0300 | harmonogram-konserwacji.md | ✅ | wiki/sources/harmonogram-konserwacji.md |

