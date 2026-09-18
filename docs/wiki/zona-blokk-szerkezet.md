# Zóna-blokk szerkezet

A **zóna-blokk** a [BridgeNet protokoll](ariston-bridgenet-protokoll.md)
regisztertérképének az a szervezőelve, hogy a fűtési zónák paraméterei egymást
követő **lapokon** ismétlődnek, laponként azonos alacsony-bájt kiosztással. A
felismerés teszi lehetővé, hogy a gyártói dokumentáció nélkül is megnevezhető legyen
a szórt forgalom nagy része.

## A megfigyelés

Az `ariston.csv` közösségi konfiguráció a `0x71`, `0x72` és `0x73` lapot az 1., 2. és
3. zóna hőmérséklet-paramétereiként nevezi meg, **azonos alacsony-bájt kiosztással**:

| Alacsony bájt | Paraméter |
|---|---|
| `60` | `heat_water_max_temp` |
| `61` | `heat_water_min_temp` |
| `62` | `day_temp` |
| `63` | `night_temp` |
| `64` | `heat_offset` |
| `65` | `heat_setpoint_temp_set` |
| `6a` | `heat_slope` |
| `70` | `cool_setpoint_temp_set` |
| `71` | `cool_water_max_temp` |
| `73` | `cool_water_min_temp` |
| `75` | `cool_offset` |
| `76` | `cool_slope` |
| `79` | `summer_winter_temp_thresh` |
| `7a` | `summer_winter_switch_delay_time` |

Ebből az a hipotézis adódik, hogy a `0x74`, `0x75` és `0x76` lap a 4., 5. és 6. zóna
ugyanezen blokkja.

## A hipotézis ellenőrzése

A hipotézis külső forrás nélkül is tesztelhető: ha a kiosztás helyes, a mért nyers
értékeknek a saját jelentésükhöz illő fizikai tartományba kell esniük. A `0x75` lapra
(feltételezett 5. zóna) ráillesztve:

| Alacsony bájt | Feltételezett jelentés | Nyers | Skálázva |
|---|---|---|---|
| `60` | `heat_water_max_temp` | 820 | **82,0 °C** |
| `61` | `heat_water_min_temp` | 350 | **35,0 °C** |
| `64` | `heat_offset` | 0 | 0,0 °C |
| `65` | `heat_setpoint_temp_set` | 350 | **35,0 °C** |
| `6a` | `heat_slope` | 130 | **1,30** |
| `70` | `cool_setpoint_temp_set` | 70 | 7,0 °C |
| `71` | `cool_water_max_temp` | 120 | **12,0 °C** |
| `73` | `cool_water_min_temp` | 70 | **7,0 °C** |
| `75` | `cool_offset` | 0 | 0,0 °C |
| `76` | `cool_slope` | 25 | **0,25** |
| `79`* | `summer_winter_temp_thresh` | 150 | **15,0 °C** |
| `7a`* | `summer_winter_switch_delay_time` | 30 | **30 perc** |

\* a `0x76` lapon megfigyelve.

Tizenkét egymástól független paraméter, mind értelmes értékkel: fűtési vízhőmérséklet
82/35 °C-os határok között, 1,30-as fűtési görbe, hűtési vízhőmérséklet 12/7 °C,
nyár–tél átkapcsolás 15 °C-nál 30 perces késleltetéssel. A skálázás sem uniform — a
hőmérsékletek `/10`, a meredekségek `/100` osztóval —, és mindkét családnál a
megfelelő osztóval jön ki értelmes szám. Ez a mintázat véletlen egybeesésként
rendkívül valószínűtlen.

## A zóna-blokk lapcsaládok

| Lapok | Tartalom | Zónák |
|---|---|---|
| `0x71` – `0x76` | hőmérséklet-paraméterek, görbék, offsetek | 1–6 |
| `0x79` – `0x7e` | termoreguláció (termosztát típus, szobahőm. befolyás, kérésmód) | 1–6 |
| `0x81` – `0x86` | tartomány-kapcsolók (fűtés/hűtés tartomány, nyár–tél automatika) | 1–6 |

## Lapon belül indexelt családok

Más családoknál nem a lap, hanem az **alacsony bájt** indexeli a zónát: egyetlen
lapon belül 6–7 egymást követő regiszter tartozik a zónákhoz.

| Lap | Kezdő alacsony bájt | Jelentés |
|---|---|---|
| `0x91` | `01` | zónánkénti fűtésigény (`heat_request`) |
| `0x96` | `69` | zónánkénti szoba-alapjel (`setpoint_temp`) |
| `0x97` | `61` | zónánkénti számított előremenő alapjel |
| `0x19` | `09` | zónánkénti „fűtés folyamatban” |
| `0x94` | `c1`, `d9` | zónánkénti azonosítatlan módok (két külön futam) |
| `0x95` | `d9` | zónánkénti azonosítatlan |

A `0x91` lap esetében a külső regisztertérkép (lásd [Források](forrasok.md))
**hét** zónát dokumentál (`0x9101`–`0x9107`); a többinél hatot lehetett megfigyelni.

## Következmény: két hibás CSV-definíció

A zóna-blokk szerkezet ismeretében kiderül, hogy az `ariston.csv` két többmezős
broadcast-definíciója rossz helyre horgonyzódik:

| Üzenet | Horgony | Valójában |
|---|---|---|
| `energymgr/day_temp_settings` | `6176` | a **6. zóna** blokkjának közepe |
| `energymgr/cooling_temps` | `6a75` | az **5. zóna** blokkjának közepe |

Mindkettő úgy van megírva, mintha egy telegram az 1–3. zóna értékeit sorolná fel.
A `day_temp_settings` „z1_day_temp” mezője ezért 0,0 °C-ot ad, miközben a valódi
1. zóna nappali alapjele a `6271` regiszterben **19,0 °C**. Az ezekből származó
Home Assistant entitások értéke nem értelmezhető.

## Gyakorlati jelentőség ezen a telepítésen

A vizsgált rendszeren egyetlen zóna van bekötve. A szórt forgalom nagy része ezért a
**4–6. zóna gyári alapértéke**, amely soha nem változik. A zóna-blokk levezetés
gyakorlati haszna nem az, hogy ezeket az értékeket használhatóvá teszi, hanem hogy
megmagyarázza, miért zajszerű a forgalom nagy része, és így elkülöníti tőle azt a
néhány regisztert, amely valóban informatív.

### Az 1. zóna azonosítása (2026-09-14)

A próbafűtés közben érkezett `2020` paraméter-blokk először tartalmazta az 1–3. zóna
(`0x71`–`0x73`) teljes hőmérséklet-blokkját. A hat zóna paraméterei egyetlen ponton
térnek el egymástól:

| Paraméter | Z1 | Z2–Z6 |
|---|---|---|
| `heat_setpoint_temp_set` (`65`) | **50,0 °C** | 35,0 °C |
| `heat_water_max_temp` / `min` (`60`/`61`) | 82,0 / 35,0 °C | 82,0 / 35,0 °C |
| `night_temp` (`63`) | 16,0 °C | 16,0 °C |
| `summer_winter_temp_thresh` / `delay` (`79`/`7a`) | 15,0 °C / 30 perc | ugyanaz |

Az 1. zóna 50,0 °C-os fűtési alapjele pontosan egyezik a `0x9761` számított előremenő
alapjellel és a `0x4760` hibrid előremenő alapjellel (50,0 °C), a többi zónáé a minimumon
(35,0 °C) áll. Ez független megerősítése annak, hogy **az 1. zóna a bekötött zóna**, és hogy
a kazán — külső érzékelő híján — fix 50 °C-os előremenő alapjellel fűt.

A `heat_slope` (`6a`) az 1. zónára ebben a blokkban nem érkezett meg; a 2–6. zónáé 1,30.

## Lásd még

* [Ariston BridgeNet protokoll](ariston-bridgenet-protokoll.md)
* [Broadcast regisztertérkép](broadcast-regiszterterkep.md)
* [Home Assistant integráció](home-assistant-integracio.md)
