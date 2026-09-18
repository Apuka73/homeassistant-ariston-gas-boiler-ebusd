# Gázfogyasztás becslése

A házban a kazán az egyetlen gázfogyasztó, ezért a kazán által elégetett gáz a teljes
gázfogyasztás. Ez a szócikk azt foglalja össze, milyen buszadatból becsülhető, mennyire
pontosan, és hogyan működik a Home Assistantban futó becslés. Alapja a 2026-09-14-i
próbafűtés és egy közösségi forráskutatás (lásd [Források](forrasok.md)).

## Rövid válasz

* **Gázszámláló regiszter nincs.** Egyik ismert közösségi konfiguráció vagy visszafejtés
  sem dokumentál m³-es vagy kWh-s gáz- vagy energiaszámlálót a kazánban. Az Ariston NET felhő
  gázfogyasztás-kimutatása a felhőben vagy az átjáróban számol, busz-regiszterhez nem köthető;
  a költségszámítás regiszterei (`642b`, `652b`, `662b`, `682b`) az Energy Managerhez tartoznak,
  amely ezen a rendszeren nincs.
* **Van valós idejű teljesítményregiszter:** `0x4768` (wire `6847`), a kezelőegység
  szervizmenüjének 8.2.8 „Gas Power” pontja, UIN, /10, kW. Ennek időbeli integrálása a
  járható út — és a Home Assistant már így számol.

## A felhasználható regiszterek

| Wire | Regiszter | Jelentés | Skála | Ezen a kazánon | Megbízhatóság |
|---|---|---|---|---|---|
| `6847` | `0x4768` | pillanatnyi gázteljesítmény (8.2.8) | UIN /10 kW | **működik**: 9,5 → 9,4 kW fűtés közben, 0,0 láng nélkül; januári max. 14,6 kW = 24 kW × 61 % | igazolt (karbantartói összevetés + saját mérés) |
| `4013` | `0x1340` | ventilátor-fordulat (8.2.2) | UIN, rpm | működik: 3246 → 2343 rpm moduláció közben | igazolt |
| `c404` | `0x04c4` | gázmoduláció | UCH | **mindig 0** — a források szerint csak rendszerszabályzóval (Sensys/Cube) töltődik | nem használható |
| `4bd1` | `0xd14b` | égőórák, fűtés (8.1.0) | UIN, h (egyes források h/10) | 5096 → 5097 h | igazolt, a skála vitatott |
| `409d` | `0x9d40` | `flame_efficiency`? | UIN /10 % | nem vizsgált | spekulatív |
| `c104` | `0x04c1` | „flame power ?” | — | nem vizsgált | spekulatív |

A `6847`-ről a források vitatkoznak: az egyik közösségi CSV `dhw_flowmeter`-nek (liter)
nevezi, egy Chaffoteaux-tulajdonos kételkedett, a wrongisthenewright-konfiguráció karbantartója
viszont a kezelőegység menüjével vetette össze. Ezen a kazánon a mért értékek (láng nélkül 0,
fűtésben 9,5 kW, a beállított maximumnál 14,6 kW) a kW-os értelmezést támasztják alá.

**Nyitott kérdés:** a „Gas Power” a **bevitt gázteljesítmény** vagy a **leadott hő**. A
kalibráció (lásd lent) mindkét esetben helyes eredményt ad, de a kiinduló szorzó elméleti
értéke ettől függ.

## A Home Assistant becslés

Fájl: `/config/packages/gazfogyasztas.yaml`.

```
ebusd/boiler/flame_power_kw  ──►  sensor.kazan_langteljesitmeny (kW)
                                         │  integration, trapéz, max_sub_interval 1 perc
                                         ▼
                                  sensor.kazan_hoenergia (kWh)
                                         │  × input_number.gaz_kalibracio (0 → 0,118 m³/kWh)
                                         ▼
                                  sensor.gazfogyasztas (m³, Energia irányítópult)
```

* A szenzor a nyers MQTT topicra épül, nem a discovery entitásra (az entitásnevek a
  `mqtt-hassio.cfg` szerkesztésekor átneveződhetnek).
* Az `ebusd/global/running` LWT miatt az ebusd leállásakor a teljesítmény nem ragad be.
* Kontrollként a `sensor.kazan_egoorak` a kazán saját égőóra-számlálóját követi.
* **A `gaz_kalibracio` értéke 2026-09-14-én még 0**, vagyis a számítás az elméleti 0,118 m³/kWh
  szorzóval megy (1 m³ ≈ 9,4 kWh égéshő × ~90 % hatásfok).

## Pontosság — a 2026-09-14-i próbafűtés

| | Érték |
|---|---|
| Láng | 18:31:56 – 18:51:38 (19,7 perc, egyetlen gyújtás, lángleszakadás nélkül) |
| Mért teljesítmény | 9,5 kW (18:36:44), 9,4 kW (18:43:08) |
| Becsült valós energia | 3,105 kWh ≈ 0,366 m³ |
| HA integrál | 2,837 kWh = 0,335 m³ |
| **Eltérés** | **−0,268 kWh (−8,6 %)** |

Az eltérés oka a lekérdezési ütem. A `flame_power_kw` `r2` prioritású, az `ebusd` kb.
6 percenként olvassa, és csak értékváltozáskor publikál:

| Él | Mi történt | Hatás |
|---|---|---|
| gyújtás | a láng 18:31:56-kor gyulladt, az első nem nulla érték 18:36:44-kor jött | ~4,8 perc kimarad (≈ −0,75 kWh) |
| leállás | a kazán 18:51:38-kor állt le, a 0,0 kW 18:54:54-kor jött | ~3,3 perc fantomégés (≈ +0,5 kWh) |

A két hiba ellentétes előjelű, de nem oltja ki egymást. Ciklusonként ±0,5–0,8 kWh a
bizonytalanság: hosszú téli égéseknél ez néhány százalék, sok rövid ciklusnál viszont a
fogyasztás jelentős része lehet.

## Javítási lehetőségek

1. **Sűrűbb lekérdezés — bevezetve 2026-09-14.** A `flame_power_kw` sora `r2` helyett `r1`
  . A lekérdezési ütemet az `ebusd`
   `--pollinterval=15` beállítása korlátozza: 15 másodpercenként **egy** lekérdezés megy ki,
   amelyen a 38 lekérdezett üzenet a prioritásuk arányában osztozik. A próbafűtés nyers
   forgalmában 20 perc alatt az `r1` `fan_speed` 6-szor (≈ 3,3 percenként), az `r2`
   `flame_power_kw` 4-szer (≈ 5 percenként) ment ki. Az `r1` besorolás után mérve (19:15–19:35,
   20 perc) a `flame_power_kw` 7-szer, a `fan_speed` szintén 7-szer ment ki: a teljesítmény
   **2,9 percenként** frissül — a korábbi kb. kétszerese, de nem percre pontos. A 67
   lekérdezésből 11 busz-ütközés miatt sikertelen volt, a `flame_power_kw`-t egyik sem érintette.
   Tovább gyorsítani csak a `pollinterval` csökkentésével lehet (több busz-forgalom, több
   ütközés), vagy más üzenetek prioritásának lejjebb vételével.
2. **Azonnali leállásjel — bevezetve 2026-09-14.** A csomag új `sensor.kazan_allapot`
   szenzora a `boiler_status` szórt üzenetből jön, és a `heating` → `standby` váltást
   másodperceken belül jelzi. A `sensor.kazan_langteljesitmeny_kapuzott` `standby`,
   `circulating`, `low_water_pressure` és `no_flame` állapotban 0 kW-ot ad, egyébként a nyers
   értéket; a `kazan_hoenergia` integrál ezt összegzi. Ezzel a leállás utáni fantomégés a
   lekérdezési ütemtől függetlenül megszűnik. A gyújtás utáni kimaradás megmarad, de az
   átlagos késés ~2,5 percről ~1,5 percre csökken. (Az integrál forrásának cseréje
   Home Assistant-újraindítást igényel, mert az `integration` platformnak nincs
   újratöltése; a felgyűlt érték megmarad.)
3. **Kalibráció a fizikai gázórához.** Egy fűtött hónap gázóra-különbségét elosztva a
   `kazan_hoenergia` különbségével a rendszerszintű hibák (szorzó, hatásfok, a lekérdezési
   él-hibák átlaga) egyszerre kiesnek.
4. **Tartalék becslés.** Ha a `6847` kiesne: a `4013` fordulat és a `6847` kW párosaiból
   saját rpm → kW görbe illeszthető; hivatalos görbe nincs.
5. **Kipróbálandó regiszterek** lánggal és láng nélkül `2000`-es olvasással: `409d`, `c104`,
   `6547`.

## Lásd még

* [Kazán](kazan.md) — a próbafűtés idővonala és számlálói
* [ebusd konfiguráció](ebusd-konfiguracio.md) — lekérdezési prioritások
* [Home Assistant integráció](home-assistant-integracio.md)
* [Források](forrasok.md)
