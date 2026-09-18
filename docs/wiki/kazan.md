# Kazán

| | |
|---|---|
| **Busz-cím** | slave `0x3c` (master `0x37` alatt) |
| **Névleges teljesítmény** | 24 kW |
| **Kazántípus** | `ext_tank_thermostat` — külső tároló termosztáttal |
| **Szoftververzió** | `22 00 02` |
| **Modulációs tartomány** | 5 – 61 % (max. beállítható: 64 %) |
| **Nyomásfelügyelet** | nyomáskapcsoló (`pressure_switch`) |
| **Gyújtási késleltetés** | 3 perc, `manual` típus |
| **Utókeringetés** | 3 perc |

A **kereskedelmi típusnév nem olvasható ki a buszról.** A BridgeNet nem támogatja a
szabványos eBUS eszközazonosítást (`0x0704` → `ERR: SYN received`), a gyári
sorozatszámot pedig a kazán csak busz-reset után szórja szét egyszer, `2031`
paranccsal. A használt `ariston.csv` konfiguráció fejléce „Ariston Genus One Hybrid
Net” rendszerre hivatkozik, ez azonban a konfiguráció célja, nem e példány
azonosítása.

## Azonosító válasz

A `2002` parancs `000000` azonosítóval a következő nyers választ adja:

```
>31 3c 2002 03 000000 01 <00 10 002200022a0107000100002020001000 a2 >00
```

A 16 bájtos válasz:

```
00 | 22 00 02 | 2a 01 07 00 01 00 00 20 20 00 10 00
│    │          └─ értelmezetlen (12 bájt)
│    └─ szoftververzió
└─ figyelmen kívül hagyva
```

Az `ariston.csv` az első bájtot átugorja (`IGN:1`), a következő hármat
szoftververzióként olvassa (`HEX:3`), a maradék **12 bájt értelmezetlen marad**.
Jelentésüket egyik ismert közösségi konfiguráció sem dokumentálja.

## Üzemi számlálók

2026-08-16-i állás:

| Számláló | Érték | Megjegyzés |
|---|---|---|
| `hours_burner_on_CH` | 5096 h | égő üzemideje fűtésben |
| `hours_burner_on_DHW` | **0 h** | a kazán soha nem termelt melegvizet |
| `hours_pump_on` | 5640 h | keringtetőszivattyú üzemideje |
| `ignition_cycles` | 9918 | gyújtási ciklusok |
| `boiler_circulation_cycles` | 7016 | |
| `boiler_fan_cycles` | 14237 | |
| `diverter_cycles` | 5289 | váltószelep-átállások |
| `flame_lift_offs` | 39 | lángleszakadások — lásd [Hibanapló](hibanaplo.md) |
| `boiler_life_time` | 31982 | **órában** számol, nem percben (lásd alább) |

### A `boiler_life_time` mértékegysége

Az `ariston.csv` percként definiálja, ami nem lehet helyes: 31 982 perc = 533 óra,
miközben csak az égő 5096 órát üzemelt. **Órában értelmezve** 31 982 h ≈ 3,65 év,
ami mellett az égő 16 %-os üzemidő-aránya reális egy fűtésre használt kazánnál.

**Méréssel igazolva (2026-08-16 → 2026-09-18):** a számláló 33 nap alatt 31 980-ról
32 768-ra nőtt, azaz **napi 23,8 egységgel** — ez óránként pontosan egy. A regiszter
tehát órákat számol; a repóban lévő CSV-ben ezt javítottuk.

## Fontos értelmezési tudnivalók

### A nyomásérték nem mérés

A `pressure_monitoring_device` regiszter értéke `pressure_switch`, azaz a kazánban
**nincs analóg nyomásérzékelő**, csak egy kapcsoló. A `boiler_pressure` regiszter
ezért állandóan `0.0`-t ad; ez nem 0 bar rendszernyomást jelent, hanem azt, hogy
nincs mit mérni. A `warning_pressure` = 0,6 bar a kapcsoló küszöbértéke.

### A külső hőmérséklet-érzékelő nincs bekötve

Az `ext_temp` regiszter értéke `32767`, ami a
[protokoll szentinel értéke](ariston-bridgenet-protokoll.md) az érvénytelen /
hiányzó érzékelőre. A felsőbb rétegekben ez 3276,7 °C-ként jelenik meg.
Következménye, hogy **időjáráskövető szabályozás nem tud működni**: a `0x4760`
hibrid előremenő alapjel a teljes 2026-os fűtési szezonban változatlanul 45,0 °C
volt (2026 augusztusában 50,0 °C).

## Üzemtörténet

A Home Assistant recorder hosszú távú statisztikájából (`flame_power_kw`):

| Hónap | Adatot tartalmazó órák | Ebből lánggal | Max. lángteljesítmény |
|---|---|---|---|
| 2026-01 | 221 | 137 | 14,6 kW |
| 2026-02 | 263 | 115 | 14,6 kW |
| 2026-03 – 2026-08 | 261 | **0** | — |

A kazán 2026 februárja óta nem gyújtott be. Mivel melegvizet sem termel
(`hours_burner_on_DHW` = 0), a fűtési szezonon kívül teljesen inaktív.

A megfigyelt 14,6 kW maximum egyben a névleges teljesítmény és a százalékos
skálázás keresztellenőrzése: 24 kW × 61 % = 14,64 kW.

### 2026-09-14 — próbafűtés

A kazán (a készülék adattáblája szerint **Ariston Cares S System 24**, cikkszám
3301636BFV) hét hónap állás után először kapott fűtési igényt.

| Idő (helyi) | Esemény |
|---|---|
| 18:29:38 | a fűtéskapcsoló relé bekapcsol; `0x9101` (z1_heat_request) 0 → 1 |
| 18:29:40 | `boiler_status`: `standby` → `heating`, z1 fűtés folyamatban |
| 18:29:50 | keringetési ciklus +1 (szivattyú indul) |
| 18:29:58 | **`5P1-1 failed ignition`** — az első gyújtási kísérlet sikertelen (`2004` hiba-broadcast, jelző `02`; 18:30:14-től `00`) |
| 18:31:56 | **láng aktív** (második kísérletre gyújtott) |
| 18:32–18:35 | ventilátor 3232 → 2475 → 2343 rpm (moduláció lefelé), visszatérő víz 22,2 → 38,2 °C |

* A sikertelen első gyújtás hosszú állás után tipikus (levegő a gázvezetékben); a kijelzőn
  hibakód nem maradt, a manométer 1,5 bart mutatott. Az `energymgr/error` mező a sikeres
  gyújtás után is percekig ismételten `5P1`-et szórt — ez a bent ragadt utolsó kód, nem új hiba.
* **Lángteljesítmény:** a `flame_power_kw` (`0x4768`, wire `6847`, UIN /10 kW — a kezelő
  szervizmenüjének 8.2.8 „Gas Power” pontja) **működik**: 18:36:44-kor 9,5 kW, 18:43-kor
  9,4 kW. Az `ebusd` azonban `r2` prioritással ritkán kérdezte le, ezért a gyújtás után csak
  ~5 perccel jelent meg, és a láng kialvása után percekig a régi értéket mutatta. Még aznap
  este `r1`-re állítva, a Home Assistantban pedig a kazánállapottal kapuzva — lásd
  Gázfogyasztás becslése.
* **Fűtés közben használhatatlannak bizonyult regiszterek:** a `boiler_current_modulation`
  (`0x04c4`, wire `c404`) végig 0, miközben a ventilátor modulál és a lángteljesítmény
  9,5 kW; a közösségi források szerint ezt a kazán csak valódi rendszerszabályzó
  (Sensys/Cube) jelenlétében tölti ki. A `diverter_valve` végig `dhw`-t jelez, pedig a
  `diverter_cycles` számláló a fűtés alatt eggyel nőtt — a regiszter értelmezése hibás.
* **Számlálók a fűtés után** (16:00 → 18:53): `ignition_cycles` 9918 → 9919 (egyetlen
  sikeres gyújtás, a sikertelen kísérlet nem számolódik), `flame_lift_offs` 39 → 39
  (nem volt lángleszakadás), `boiler_fan_cycles` +1, `diverter_cycles` +1. A
  `boiler_life_time` egy óra alatt eggyel nőtt — összhangban a hosszabb távú méréssel, amely
  szerint a számláló órákat számol.
* A busz a fűtés alatt nyugodt maradt: kapcsolatvesztés nem volt; az ütközéses
  (`SYN received`) lekérdezési hibák 5 percenként 2–5-ről 8–12-re nőttek a sűrűbb szórt
  forgalom miatt. A hiba idején megjelent a `2004` szórt parancs (`37 fe 2004 05 3005 xx 00 00 3c`):
  ez az `energymgr/error` üzenet. 18:29:58–18:30:10 között `02` jelzővel, utána `00`-val, és
  a kazán a sikeres gyújtás után is 2 percenként ismétli — ezért látszik az `5P1` még percekkel
  később is az MQTT-ben.
* A lángteljesítményből számolt gázfogyasztás pontosságát lásd:
  [Gázfogyasztás becslése](gazfogyasztas-becsles.md).
* Az előremenő alapjel fix 50,0 °C (lásd [Zóna-blokk szerkezet](zona-blokk-szerkezet.md)).

## Lásd még

* [Busz-topológia](busz-topologia.md)
* [Hibanapló](hibanaplo.md)
* [Olvasható regiszterek](olvashato-regiszterek.md)
