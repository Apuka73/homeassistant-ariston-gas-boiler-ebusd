# Home Assistant integráció

Az [ebusd](ebusd-konfiguracio.md) MQTT Discovery útján hozza létre az entitásokat a
Home Assistantban. Ez a szócikk a 2026-08-16-i állapotot írja le.

## Entitások

| Forrás | Darab |
|---|---|
| `ebusd` MQTT Discovery | 123 |
| Template szenzorok (helyi) | 3 |

A 123 MQTT-entitás nem mind hordoz adatot: azok, amelyek nem létező busz-címekhez
tartozó körökhöz kötődnek (`energymgr`, `heatpump`, `gateway`), tartósan
elérhetetlenek — lásd [Busz-topológia](busz-topologia.md).

### Kiindulási állapot

A vizsgálat kezdetén mindössze **négy** érték jutott el a Home Assistantba:
`boiler_status`, `flame_power_kw`, `dhw_current_target_temp`, `hybrid_LWT_setpoint`.
Ennek oka, hogy az `ariston.csv`-ben csak két üzenetnek volt lekérdezési
prioritása, a többi regisztert az `ebusd` soha nem olvasta.

A lekérdezési prioritások beállítása után **38 regiszter** frissül ciklikusan.

## Template szenzorok

Fájl: a repóban [`../../packages/egesi_diagnosztika.yaml`](../../packages/egesi_diagnosztika.yaml),
a Home Assistantban a `config/packages/` könyvtárba másolva és a `configuration.yaml`
`packages:` blokkjába bekötve.

| Entitás | Állapotosztály | Érték (2026-08-16) |
|---|---|---|
| `sensor.kazan_langleszakadasok` | `total_increasing` | 39 |
| `sensor.kazan_gyujtasi_ciklusok` | `total_increasing` | 9918 |
| `sensor.kazan_langleszakadas_arany` | `measurement`, `‰` | 3,93 |

Létezésük oka kettős. Egyrészt az `ebusd` MQTT-leképezése nem ad `state_class`-t a
mértékegység nélküli számlálóknak, így azok nem kapnának hosszú távú statisztikát, és
a trendjük eltűnne a recorder takarításakor. Másrészt a lángleszakadások abszolút
száma önmagában nem értelmezhető — a gyújtási ciklusokhoz viszonyított arány az, ami
követhető mérőszám. Részletek: [Hibanapló](hibanaplo.md).

## Broadcastból kinyert entitások

A [zóna-blokk levezetés](zona-blokk-szerkezet.md) nyomán két meglévő broadcast-üzenet
mezőkkel bővült. Ezek nem terhelik a buszt: olyan telegramokat dekódolnak, amelyek
amúgy is folyamatosan érkeznek.

| Entitás | Regiszter | Érték |
|---|---|---|
| `…hybrid_lwt_setpoint_z1_computed_lwt` | `0x9761` | 50,0 °C |
| `…hybrid_lwt_setpoint_z2_computed_lwt` | `0x9762` | 35,0 °C |
| `…boiler_status_z1_heating` | `0x1909` | off |
| `…boiler_status_z2_heating` | `0x190a` | off |
| `…boiler_status_z3_heating` | `0x190b` | off |

A `0x9761` a fűtési görbéből számított előremenő alapjel az 1. zónára — a fűtés
hangolásának legbeszédesebb egyetlen értéke. A `0x190x` jelzők azt mutatják, melyik
zóna kért hőt (szemben a `boiler_status`-szal, amely csak a kazán állapotát adja).

## Példa irányítópult-felépítés

A mérésekhez készült egy Home Assistant irányítópult, aminek a szerkezete másnak is
kiindulás lehet. Kilenc szekció, fontossági sorrendben: pillanatnyi fogyasztás (kW és
átszámított m³/óra), fontos hőmérsékletek és a fűtésigény, gázbecslés és kalibráció,
égési diagnosztika (lángleszakadás-arány, trend), üzemidők és számlálók, a broadcast
fejtésből származó zóna-adatok, kazánkonfiguráció, az adapter és az ebusd állapota,
végül egy „adatminőség és korlátok" szekció a nem megbízható értékekről (nyomás,
külső hőmérséklet, moduláció, váltószelep) és a nem válaszoló körökről.

Az utolsó szekció tapasztalata általánosítható: **érdemes külön jelölni azokat az
értékeket, amelyekben a rendszer adottságai miatt nem lehet megbízni** — különben
később valaki (akár te magad) számolni kezd velük.

## Ismert adatminőségi problémák

| Entitás | Probléma |
|---|---|
| `…boiler_pressure` | A kazánban nincs analóg nyomásérzékelő, az érték állandó 0,0 — nem mérés. Lásd [Kazán](kazan.md). |
| `…ext_temp` | 3276,7 °C = a `32767` szentinel; a külső érzékelő nincs bekötve. |
| `…day_temp_settings_*` | A CSV rossz zóna-blokkra horgonyoz, az értékek nem értelmezhetők. |
| `…cooling_temps_*` | Ugyanaz. Lásd [Zóna-blokk szerkezet](zona-blokk-szerkezet.md). |
| `…circulation_time`, `…pump_current_modulation` | `ERR: invalid position in decode` — hibás meződefiníció a CSV-ben. |

## Gázfogyasztás

A `/config/packages/gazfogyasztas.yaml` csomag a `flame_power_kw` (`0x4768`) teljesítményből
integrálással számol hőenergiát (`sensor.kazan_hoenergia`) és gázfogyasztást
(`sensor.gazfogyasztas`, az Energia irányítópult gázforrása). Működését, a 2026-09-14-én
mért −8,6 %-os eltérést és a javítási lehetőségeket a
[Gázfogyasztás becslése](gazfogyasztas-becsles.md) szócikk tárgyalja.

## Lásd még

* [Gázfogyasztás becslése](gazfogyasztas-becsles.md)
* [ebusd konfiguráció](ebusd-konfiguracio.md)
* [Hibanapló](hibanaplo.md)
* [Zóna-blokk szerkezet](zona-blokk-szerkezet.md)
