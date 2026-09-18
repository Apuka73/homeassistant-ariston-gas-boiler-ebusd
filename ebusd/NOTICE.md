# Az ebusd konfiguráció eredete és a benne lévő módosítások

Ez a könyvtár **nem** a repó MIT licence alá tartozik.

## Eredet

Az `ariston.csv` a következő projekt **v2.6** verziójából származik:

* **[wrongisthenewright/ebusd-configuration-ariston-bridgenet](https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet)**
  — licenc: **GNU General Public License v3** (a teljes szöveg: `LICENSE`).

A pontos upstream commit, amire szinkronizálva van: [`UPSTREAM.md`](UPSTREAM.md).

Mivel a fájl módosított származékos mű, a GPL v3 feltételei szerint terjesztjük tovább.
A `mqtt-hassio.cfg` az [ebusd](https://github.com/john30/ebusd) projekt mintafájljának
módosított változata (szintén GPL v3).

## Amit ebben a könyvtárban módosítottunk

Az eredetihez képest **52 sor változott vagy került be** az `ariston.csv`-be. A módosítások
egy valódi telepítésen (Ariston Cares S System 24, kazán-only rendszer, rendszerszabályzó és
hőszivattyú nélkül) végzett méréseken alapulnak. Az eltérés `diff`-fel bármikor visszanézhető:

```bash
git clone https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet
diff ebusd-configuration-ariston-bridgenet/ariston.csv ariston.csv
```

### 1. Lekérdezési prioritások (38 üzenet) — a legfontosabb változás

Az eredeti CSV-ben a kazán üzenetei `r` típusúak: az ebusd **csak kérésre** olvassa ki őket, és
magától nem frissíti. Így a Home Assistant mindig elavult vagy hiányzó értéket kapna.
Minden használt üzenet **poll prioritást** kapott, a változékonyságához igazítva:

| Prioritás | Milyen gyakran | Mely üzenetek |
|---|---|---|
| `r1` | leggyakrabban | `flame_power_kw`, `flame_active`, `fan_speed`, `EWT_temp`, `boiler_pressure`, `diverter_valve`, `boiler_status_read` |
| `r2` | közepesen | `boiler_current_modulation` |
| `r3` | ritkán | üzemóra- és ciklusszámlálók (`hours_burner_on_CH`, `hours_pump_on`, `ignition_cycles`, `flame_lift_offs`, `diverter_cycles`, `boiler_fan_cycles`, `boiler_circulation_cycles`, `boiler_life_time`), `last_error` |
| `r9` | nagyon ritkán | beállítás jellegű értékek (`nominal_power`, `heat_max_power_pct`, `heat_min_power_pct`, `pump_*`, `boiler_type`, `pressure_monitoring_device`, `maintenance_*`, `config_version_counter`, `sensys/boiler_sw_version` stb.) |

> Az `--pollinterval=15` miatt ez 15 másodpercenként **legfeljebb egy** lekérdezést jelent, tehát
> a 2400 baudos busz nem telik meg. A prioritások nélkül viszont az integráció is lassabb lenne,
> mert mindent magának kellene kikényszerítenie.

### 2. A 10 mélységű hibanapló (9 új üzenet)

Az eredeti CSV csak a `last_error` bejegyzést ismeri. Felvettük az `error_slot_1` …
`error_slot_9` üzeneteket (`2002`/`0401`–`0409`), ugyanazzal a mezőszerkezettel. A szerkezet
forrása az [ysard/ebusd_configuration_chaffoteaux_bridgenet](https://github.com/ysard/ebusd_configuration_chaffoteaux_bridgenet)
projekt Chaffoteaux-konfigurációja — enélkül a hibanapló-entitás nem létezne.

### 3. `boiler_status`: topic-ütközés feloldása

Az eredetiben a lekérdezős és a broadcast változat **ugyanazt a nevet** viselte, ezért az ebusd
MQTT-n ugyanarra a topicra küldte mindkettőt: a zóna-mezők (`z1_heating`, `z2_heating`,
`z3_heating`) felváltva léteztek és tűntek el, a rájuk épülő sablonok hibára futottak.

Megoldás: a `boiler_status` **broadcast** (`b`) lett — így másodperceken belül frissül —, a
lekérdezős változat pedig külön néven, `boiler_status_read` (`r1`) került be.

> Erre épül az integráció gázbecslésének kapuzása: a gyorsan érkező állapot alapján nullázzuk a
> lángteljesítményt, amikor nem éghet láng.

### 4. `flame_power_kw` gyakoribb olvasása

`r2` → `r1`. Az eredeti ritmussal a láng kialvása után percekig a régi kW-érték maradt érvényben,
és a gázbecslés nem létező fogyasztást integrált — egy mért próbafűtésen a hiba **−8,6%** volt.

### 5. `boiler_current_modulation` broadcast változata kikommentezve

A `fe/2010/c404` broadcast változat dekódolása helyes, de ezen a rendszeren **sosem hordoz
adatot** (rendszerszabályzó nélkül nem küldi a kazán). Bent hagytuk megjegyzésként, hogy más
rendszeren ki lehessen próbálni; a lekérdezős `3c/2000/c404` változat az aktív.

Ugyanígy kikommentezve az `ignored/ign6` sor, amely egy másik broadcast üzenettel ütközött.

### 6. `energymgr` zónablokk-horgonyok (jelzés, nem javítás)

Az `energymgr/day_temp_settings` és az `energymgr/cooling_temps` definíciói a 6., illetve az
5. zónablokk közepére horgonyzódnak, miközben a mezőiket z1/z2/z3 értékeknek nevezik — ezért
**hibás értéket adnak**. A referenciarendszeren ez a kör nem létezik, ezért nem nyúltunk hozzá,
de jelezzük, mert más rendszeren félrevezető lehet.

### 7. `mqtt-hassio.cfg`: a `pct$` minta sorrendje

A `power` minta előbb illeszkedett, mint a `pct$`, ezért a `*_power_pct` mezők
`device_class: power` + `unit: pct` párral mentek ki, amit a Home Assistant eldob.
A `pct$` sor a `type_switch-number` lista elejére került.

## Szinkron az eredeti projekttel (2026-09-18)

A kiindulás az upstream **v2.6**, de azóta a projekt négy committel tovább lépett. Ezeket
átnéztük, és **méréssel ellenőriztük** a saját kazánon, mielőtt átvettük volna:

| Upstream változás | Mit tettünk |
|---|---|
| „changed Boiler power datatypes”: 7 regiszter `UCH` → `UIN` | **Részben átvéve.** Az öt teljesítmény-százalék (`6229`, `6329`, `6429`, `6529`, `6629`) válasza valóban **3 adatbájt** (`NN=03`), tehát ott a `UIN` a helyes — átvettük. A két szivattyú-PWM (`c928`, `ca28`) válasza viszont ezen a kazánon csak **2 adatbájt** (`NN=02`), amiből egy 2 bájtos `UIN` nem olvasható ki — ezért ott maradt a `UCH`. |
| „Addedd EM modulation Delta T” (`energymgr/em_delta_t`, `7b2b`) | **Átvéve**, de kazán-only rendszeren nem ellenőrizhető (a `0x18` cím nem válaszol). |
| Két „Update issue templates” commit | Nem érinti a konfigurációt. |

A mérés módja bárki által megismételhető:

```bash
echo "read -h 3c200002c928" | nc <EBUSD_GEP> 8888   # -> 020163  (NN=02: egy adatbájt)
echo "read -h 3c2000026329" | nc <EBUSD_GEP> 8888   # -> 03013d00 (NN=03: két adatbájt)
```

## Amit a forkokból megnéztünk, de nem vettünk át

Az eredeti projekt 18 forkja közül hétnek van saját fejlesztése. A kazán-only rendszerekre
nézve a legígéretesebb a [Patbonamy/ebusd-configuration-mira-c-green](https://github.com/Patbonamy/ebusd-configuration-mira-c-green)
(Chaffoteaux Mira C Green) volt: **78 kazán-köri üzenetet** definiál, köztük olyanokat, amik
nálunk hiányoznak — előremenő vízhőmérséklet (`6810`), zóna-alapjelek, fűtési görbe, szobahőmérséklet.

**Mind a 18 jelöltet kipróbáltuk a valódi buszon** (`read -h 3c200002<parancs>`), és
**egyik sem létezik** az Ariston Cares S System 24-en: a kazán mindegyikre „element not found”
választ ad, miközben az ismert regiszterek (`6910`, `6847`) helyes értéket adnak, a nem létező
eszköz (`0x18`) pedig időtúllépést. A Mira definíciói tehát **nem vihetők át** erre a kazánra —
ez is eredmény: nem kell keresni azt, ami nincs.

A [michalmie](https://github.com/michalmie/ebusd-configuration-ariston-bridgenet) fork
`dhw_boost` regisztere (`energymgr`, `1e22`) és a
[pouzak](https://github.com/pouzak/ebusd-configuration-ariston-bridgenet) fork hőszivattyús
kiegészítései (Nimbus R32 hibrid: kompresszorfrekvencia, előremenő/visszatérő HP-hőmérséklet,
elektromos fűtőbetét) **valódi, de ezen a rendszeren nem ellenőrizhető** bővítések — ezért nem
másoltuk be őket; akinek hibrid rendszere van, ezekben a forkokban megtalálja.

## Megjegyzés a Home Assistant integrációhoz

Ha az integrációt használod (és nem az MQTT-utat), a `mqtt-hassio.cfg`-re nincs szükség,
és az `--mqtt*` kapcsolók is elhagyhatók az ebusd indításából. Az `ariston.csv` viszont
**mindenképp kell** — abból tudja az ebusd, mit jelentenek a regiszterek.
