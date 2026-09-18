# Entitások

Az integráció **csak azokat az entitásokat hozza létre, amelyekre a rendszered valóban ad
értéket**. A lenti táblázatok jelölik, mi mit jelent, és hogy alapból létrejön-e.

A referenciarendszer (Ariston Cares S System 24, kazán-only) **29 entitást** kapott.

## A kazán működése

| Entitás | Mértékegység | Forrás (ebusd üzenet) | Megjegyzés |
|---|---|---|---|
| Kazán állapota | – | `boiler/boiler_status` (1. mező) | Felsorolás: készenlét, fűtés, melegvíz fűtése, tárolótöltés, keringetés, kézi teszt, komfort, gázkör légtelenítés, önkalibráció, alacsony víznyomás, nincs láng. **Broadcast üzenet**, másodperceken belül frissül. |
| Láng | be/ki | `boiler/flame_active` | Ég-e éppen a láng. |
| Lángteljesítmény | kW | számított | A nyers érték **nullára kapuzva**, ha a kazán állapota szerint nem éghet láng. Erre épül a gázbecslés. |
| Lángteljesítmény (nyers) | kW | `boiler/flame_power_kw` | A kazán által jelentett pillanatnyi égőteljesítmény (kW/10 felbontás). Összehasonlításnak hasznos. |
| Moduláció | % | `boiler/boiler_current_modulation` | Az égő pillanatnyi modulációja. |
| Ventilátor fordulatszám | rpm | `boiler/fan_speed` | |
| Visszatérő víz hőmérséklete | °C | `boiler/EWT_temp` | A kazánba **visszatérő** fűtővíz hőmérséklete (az eredeti CSV megjegyzése szerint „heating return temperature”; az EWT az *entering water temperature* rövidítése). Előremenő hőmérsékletet ez a rendszer nem ad. |
| Külső hőmérséklet | °C | `boiler/ext_temp` | **Csak akkor jön létre, ha van bekötött külső érzékelő.** Bekötetlen érzékelőnél a kazán 0x7FFF-et küld (3276,7 °C); ezt az integráció kiszűri, és az entitás `ismeretlen` marad. |
| Víznyomás | bar | `boiler/boiler_pressure` | **Figyelem:** ha a kazánban nyomás*kapcsoló* van (lásd „Nyomásfigyelő eszköz”), ez az érték mindig 0,0 — valódi nyomást csak a manométer mutat. |
| Váltószelep | fűtés/melegvíz | `boiler/diverter_valve` | Diagnosztikai. |
| 1–3. zóna fűtésigény | be/ki | `boiler/boiler_status` (2–4. mező) | A 2. és 3. zóna alapból ki van kapcsolva. |

## Gáz és energia

| Entitás | Mértékegység | Hogyan készül |
|---|---|---|
| Leadott hőenergia | kWh | A kapuzott lángteljesítmény trapéz-integrálja. HA-újraindítást túlél (tárolt érték). |
| Gázfogyasztás | m³ | hőenergia × kalibrációs szorzó. `device_class: gas`, beköthető az Energia irányítópultba. |
| Gázóra becsült állása | m³ | utolsó rögzített leolvasás + azóta elfogyott gáz. **Csak akkor egyezik a fizikai órával, ha a kazán az egyetlen gázfogyasztó.** |
| Gázfogyasztás a leolvasás óta | m³ | Az utolsó leolvasás óta elfogyott mennyiség. |
| Gáz kalibrációs szorzó | m³/kWh | Állítható szám (0,05–0,2). A `set_gas_meter_reading` szolgáltatás méri be. |

## Diagnosztika

| Entitás | Mértékegység | Forrás | Mire jó |
|---|---|---|---|
| Égőórák (fűtés) | h | `boiler/hours_burner_on_CH` | Független ellenőrzés a gázbecsléshez: ha a kettő tartósan elszalad egymástól, valami elromlott. |
| Égőórák (melegvíz) | h | `boiler/hours_burner_on_DHW` | Kombi kazánnál értelmes; rendszerkazánnál külső tárolóval jellemzően 0. |
| Szivattyú üzemórák | h | `boiler/hours_pump_on` | |
| Gyújtási ciklusok | – | `boiler/ignition_cycles` | |
| Lángleszakadások | – | `boiler/flame_lift_offs` | |
| **Lángleszakadás arány** | ‰ | számított | leszakadások / gyújtások × 1000. **Ez a tényleges mérőszám:** időbélyeg nélkül csak az arány romlása árulkodó. A referenciarendszeren 3,93‰. |
| Hibanapló | hibakód | `boiler/last_error` + `error_slot_1…9` | Lásd lent. |
| eBUS jel | kapcsolat | ebusd `info` | Ha elmegy, minden érték beragad. |
| Busz szimbólumsebesség | szimbólum/s | ebusd `info` | Alapból kikapcsolva. |
| Ventilátor / keringetési / váltószelep ciklusok, üzemidő | – | `boiler/*_cycles`, `boiler_life_time` | Alapból kikapcsolva. |

## Beállítás jellegű (ritkán változó) értékek

Ezek óránként frissülnek, és a kazán gyári/szerelői beállításait mutatják:
névleges teljesítmény (kW), fűtési maximum és minimum teljesítmény (%), melegvíz maximum
teljesítmény (%), kazán típusa, nyomásfigyelő eszköz, szivattyú működése, utókeringetés (perc).
Egy részük alapból ki van kapcsolva — az entitáslistában bekapcsolható.

## Hibanapló

A kazán **10 mélységű, léptetett** hibanaplót tart: a legfrissebb a `last_error`, alatta
`error_slot_1` … `error_slot_9`. **A bejegyzésekhez a kazán NEM tárol időpontot** (a dátummezők
`ff`-ek).

Az integráció 10 percenként kiolvassa mind a 10 bejegyzést, és összeveti az előzővel: ha a napló
k bejegyzéssel lejjebb csúszott (`új[k:] == régi[:10−k]`), akkor az első k bejegyzés új, és
megkapja a kiolvasás időpontját. Így az **ugyanazzal a kóddal ismétlődő** hibák is látszanak.

Az entitás állapota a legfrissebb bejegyzés kódja; az attribútumokban a teljes napló:

```yaml
entries:
  - code: "5P1"
    raw: "5P1-1 failed ignition"
    description: "Első gyújtási kísérlet sikertelen"
    first_seen: "2026-09-14T18:30:03+02:00"   # vagy null, ha a nyilvántartás kezdete előtti
    note: ""
last_checked: "2026-09-18T02:30:56+02:00"
```

### Ismert hibakódok

| Kód | Jelentés |
|---|---|
| 101 | Primer kör túlmelegedés |
| 104 | Elégtelen keringetés |
| 108 | Feltöltés szükséges (alacsony víznyomás) |
| 109 | Alacsony víznyomás |
| 309 | Gázszelep vagy gázrelé hiba |
| 501 | Nincs láng — a lángőr nem érzékel lángot |
| 502 | Láng zárt gázszelepnél |
| 504 | Lángleválás |
| 604 | Alacsony ventilátor-fordulat |
| 607 | Nyomáskapcsoló zárva álló ventilátornál |
| 612 | Ventilátor hiba |
| 5P1 | Első gyújtási kísérlet sikertelen |
| 5P2 | Második gyújtási kísérlet is sikertelen |
| 5P3 | Lángleválás működés közben |
| 5P4 | Lángleválás |
| 5P6 | Nincs láng |

Ismeretlen kódnál az ebusd saját (angol) szövege jelenik meg. Ha új kóddal találkozol,
nyiss hibajegyet, és felvesszük.

> ⚠️ **A hibakódok sorszámozása készülékfüggő.** A kazán a naplóban sorszámot tárol, amit az
> `ariston.csv` fordít szöveggé — ez a tábla erre a kazánra van bemérve. Másik készüléken ugyanaz
> a sorszám más hibát jelenthet, tehát ha a napló értelmetlen kódokat mutat, ne a kazánt hibáztasd:
> a táblát kell újragyűjteni
> ([ysard bruteforce-szkriptje](https://github.com/ysard/ebusd_configuration_chaffoteaux_bridgenet?tab=readme-ov-file#bruteforce-the-errors-to-discover-their-corresponding-codes)).

## Melegvíz / zónák (energiakezelő kör)

Rendszerszabályzó (Sensys, Cube) vagy energiakezelő nélküli rendszeren ezek a regiszterek
**nem kérdezhetők le**, de a kazán egy részüket broadcastban közli, ezért mégis lehet értékük:

| Entitás | Forrás |
|---|---|
| Melegvíz céhőmérséklet | `energymgr/dhw_current_target_temp` |
| Előremenő alapjel | `energymgr/hybrid_LWT_setpoint` |

## Amit NEM ad ez az integráció

* **Vezérlést.** Az integráció kizárólag olvas. Célhőmérséklet-állítás, be-/kikapcsolás nincs.
* **Valódi víznyomást** nyomáskapcsolós kazánon (lásd fent).
* **Gázmérő-adatot.** A kazán nem mér gázt; a gázfogyasztás számított becslés.
* **Kazán-típusnevet.** Egyik ismert regiszter sem adja vissza a kereskedelmi típusnevet.

## Ismeretlen regiszterek

A broadcast forgalomból eddig 264 regiszter jelentése ismert, de **kb. 35 máig azonosítatlan**
— ezek olyan értékek, amelyek rendszeresen változnak, de nem sikerült megfeleltetni őket
semmilyen kezelőfelületi adatnak. A részletes lista és a dekódolás módszertana:
[`wiki/`](wiki/) (magyar szócikkek, a mérési adatokkal együtt).

Ha a saját rendszereden azonosítasz közülük valamit, nyiss hibajegyet — a cél, hogy a lista fogyjon.
