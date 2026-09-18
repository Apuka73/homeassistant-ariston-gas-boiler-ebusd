# Busz-topológia

A vizsgált telepítés eBUS-hálózatának felépítése, 2026-08-16-i állapot szerint.

## Eszközök a buszon

| Cím | Szerep | Eszköz |
|---|---|---|
| `0x31` | master | `ebusd` (saját cím) |
| `0x36` | slave | `ebusd` (saját cím) |
| `0x37` | master | rendszervezérlő (a szórt forgalom forrása) |
| `0x3c` | slave | **a kazán** |

A `0x37` master és a `0x3c` slave ugyanahhoz az eszközhöz tartozik (`#18` sorszámmal).
Egy korábbi mérésben `0x01` címen egy további master is látszott (`masters: 3`), amely
később eltűnt (`masters: 2`); ennek oka nem tisztázott.

## Következmény: egyetlen elérhető slave

**A buszon egyetlen olyan slave van, amely aktív olvasásra válaszol: a `0x3c`.**

Az `ariston.csv` közösségi konfiguráció ennél lényegesen gazdagabb rendszerre készült
(hibrid, hőszivattyús telepítés Sensys kezelővel és gateway-jel), és olyan
busz-címeket szólít meg, amelyek itt nincsenek jelen:

| Kör | Cél cím | Definiált olvasható üzenet | Eredmény |
|---|---|---|---|
| `boiler` | `0x3c` | 39 | 37 válaszol |
| `energymgr` | `0x18` | 126 | mind időtúllépés |
| `heatpump` | `0x1e` | 46 | mind időtúllépés |
| `gateway` | — | 7 | mind időtúllépés |
| `sensys` | `0x3c`, `0x18`, `0x1e`, `0x23`, `0x75` | 5 | 1 válaszol (`0x3c`) |

Ez nem hibajelenség, hanem a telepítés adottsága: **kazán-only rendszer,
hőszivattyú, külön energiamenedzser és gateway nélkül.** A 185 sikertelen olvasás
teljes listája az [Olvasható regiszterek](olvashato-regiszterek.md) szócikkben.

Fontos megkülönböztetés: az `energymgr` kör *aktív olvasásra* nem válaszol, néhány
értéke viszont **szórásként megérkezik** a `0x37` mastertől — például
`dhw_current_target_temp`, `hybrid_LWT_setpoint`, `dhw_info_3`. A körnév tehát nem
egy fizikailag jelen lévő eszközt jelöl, hanem a közösségi konfiguráció logikai
csoportosítását.

## Busz-illesztő

| | |
|---|---|
| Cím | `<ADAPTER_IP>:9999` |
| Csatlakozás | TCP (WiFi–eBUS illesztő) |
| Protokoll | enhanced |
| Firmware | `1.1[6704].1[6704]` |

A `--latency=20000` és a megemelt újrapróbálkozás-számok (`--sendretries=10`,
`--acquireretries=5`) a WiFi-s köztes réteg miatt szükségesek: az útvonal
`ebusd → WiFi → illesztő → busz → illesztő → WiFi → ebusd`, ami a szigorú eBUS
időzítéshez képest jelentős késleltetést ad.

## Buszterhelés

Mért értékek nyugalmi állapotban:

| | |
|---|---|
| Szimbólumsebesség | 34–110 /s |
| Maximum | 156–165 /s |
| Szimbólum-késleltetés | 0–69 ms |
| Újracsatlakozás | 0 |

A busz alapterhelését a `0x37` master folyamatos szórása adja: a
[Broadcast regisztertérkép](broadcast-regiszterterkep.md) 47 telegramtípusa
másodperces–percenkénti ismétlődéssel.

Alkalmi `ERR: SYN received` és `arbitration won in invalid state` hibák előfordulnak
az aktív olvasásoknál. Ezek átmenetiek, az `ebusd` újrapróbálkozik.

## Lásd még

* [Kazán](kazan.md)
* [ebusd konfiguráció](ebusd-konfiguracio.md)
* [Olvasható regiszterek](olvashato-regiszterek.md)
