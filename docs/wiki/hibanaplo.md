# Hibanapló

A [kazán](kazan.md) tíz mélységű, körkörös hibanaplót tart nyilván. A napló a
`2002` paranccsal olvasható, a `0400`–`0409` azonosítókkal; a `0400` a legfrissebb
bejegyzés.

## Kiolvasás

Az `ariston.csv` alapból csak a `0400` slotot definiálja (`boiler/last_error`
néven). A további kilenc slot definícióját a
[Chaffoteaux-konfiguráció](forrasok.md) alapján adtuk hozzá `error_slot_1` …
`error_slot_9` néven:

```
docker exec ebusd-ariston ebusctl read -m 0 -c boiler error_slot_3
```

## A 2026-08-16-i kiolvasás eredménye

| Slot | Azonosító | Kód | Jelentés |
|---|---|---|---|
| 0 (utolsó) | `0400` | `501` | Nincs láng |
| 1 | `0401` | `5P2` | 2 sikertelen gyújtás |
| 2 | `0402` | `5P1` | 1 sikertelen gyújtás |
| 3 | `0403` | `5P3` | Lángleszakadás |
| 4 | `0404` | `5P3` | Lángleszakadás |
| 5 | `0405` | `5P3` | Lángleszakadás |
| 6 | `0406` | `5P3` | Lángleszakadás |
| 7 | `0407` | `501` | Nincs láng |
| 8 | `0408` | `5P2` | 2 sikertelen gyújtás |
| 9 | `0409` | `5P3` | Lángleszakadás |

Megoszlás: **lángleszakadás 5×, sikertelen gyújtás 3×, nincs láng 2×.**

A napló teljes mélységében **kizárólag égési és gyújtási hiba** szerepel. Egyetlen
nyomás-, keringetési, túlmelegedési vagy érzékelőhiba sincs köztük.

## A bejegyzések nem tartalmaznak időbélyeget

Az `ariston.csv` definíciója év, hónap, nap és idő mezőket is olvas, ezek azonban
üresen térnek vissza. A nyers válaszból kiderül, hogy nem dekódolási hibáról van szó:

```
>31 3c 2002 02 0400 b5 <00 0b 2d 00 0000 ffffffffff 0100 06 >00
                            │  │  │      └─ év/hó/nap/idő = ff (nincs beállítva)
                            │  │  └─ zóna: 0
                            │  └─ hibakód 0x2d = 45 → „501 – Nincs láng”
                            └─ 11 bájtos válasz
```

A dátummezők helyén literálisan `ff` áll. **A kazán nem tárol időbélyeget a
hibákhoz**, így a bejegyzések nem datálhatók. Felső korlát a mérés idejéből adódik: a
2026-08-16-i kiolvasáskor a kazán hónapok óta nem üzemelt, tehát az akkor látott
bejegyzések mind korábbiak. A 2026-09-14-i próbafűtés sikertelen első gyújtása (`5P1`)
viszont új bejegyzést eredményezett — ez jól mutatja, hogy a napló csúszásából
utólag is megállapítható, mikor keletkezett egy hiba.

A válasz utolsó két bájtja (`01 00`) mindkét megvizsgált slotnál azonos volt;
jelentése ismeretlen.

## Diagnosztikai mérőszám

Időbélyeg hiányában az abszolút számláló nem értelmezhető: 39 lángleszakadás lehet
egy régi, már lezárt időszak maradványa is. A **1000 gyújtásra jutó lángleszakadás**
viszont trendként követhető:

```
flame_lift_offs / ignition_cycles × 1000  =  39 / 9918 × 1000  =  3,93 ‰
```

Ez a mérőszám a [Home Assistant integrációban](home-assistant-integracio.md)
`sensor.kazan_langleszakadas_arany` néven van kivezetve, `measurement`
állapotosztállyal, így hosszú távú statisztikát kap. Emelkedése aktív problémára
utal; stagnálása arra, hogy a meglévő 39 esemény múltbeli.

## Értelmezés

A hibakódok jelentése az `_templates.csv` értéklistája szerint:

* **5P3 – lángleszakadás**: a láng elszakad az égőfejtől
* **5P1 / 5P2 – sikertelen gyújtás**: egy, illetve két gyújtási kísérlet meghiúsult
* **501 – nincs láng**: a lángőr nem érzékel lángot

Mindhárom az égési folyamat köré csoportosul. A tíz bejegyzés egyöntetűsége
mintázatra utal, nem szórványos meghibásodásokra; a konkrét ok megállapítása
égéselemzést és a gázoldali beállítás ellenőrzését igényli, ami szakember feladata.

## Lásd még

* [Kazán](kazan.md)
* [Home Assistant integráció](home-assistant-integracio.md)
* [Források](forrasok.md)
