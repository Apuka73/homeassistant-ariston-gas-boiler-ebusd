# Ariston eBUS wiki

> **Mi ez és mi nem:** ez a könyvtár a kazán buszforgalmának **visszafejtési naplója** — méréseket,
> regisztertérképeket és módszertant tartalmaz. Nem az integráció használati útmutatója: ahhoz a repó
> [README](../../README.md) és az [entitáslista](../entitasok.md) való. A szócikkek egy konkrét
> telepítésen végzett méréseket írnak le, a Home Assistant-példák pedig a korábbi, MQTT-alapú
> megoldásból származnak (a repó integrációja ezeket már beépítve tartalmazza).


Egy konkrét Ariston kazán eBUS/BridgeNet kommunikációjának visszafejtése és
Home Assistant-integrációja. Az anyag a 2026-08-16-án végzett mérésekre és a
2026-09-14-i próbafűtés nyers busznaplójára épül; minden állítás megbízhatósági
szintje a [Módszertan](modszertan.md) szócikkben követhető.

## Áttekintés

A telepítés egy 24 kW-os Ariston kazánból, egy WiFi-s eBUS-illesztőből és egy
`ebusd` démonból áll, amely MQTT-n keresztül táplálja a Home Assistantot. A
vizsgálat kiindulópontja az volt, hogy a rendszerből mindössze négy érték jutott el
a Home Assistantba, miközben az `ebusd` folyamatosan naplózott „ismeretlen”
üzeneteket a buszról.

Fő eredmények:

* **38 regiszter** olvasható ki közvetlenül a kazánból; ezek most ciklikusan
  frissülnek. Korábban kettő volt lekérdezve.
* **185 regiszter nem válaszol** — nem hiba, hanem a telepítés adottsága: a
  konfiguráció hőszivattyús rendszerre készült, itt egyetlen busz-slave van.
* A korábban dekódolatlan szórt forgalom **szerkezetében teljesen felbontva** (a regiszterhatárok
  szintjén), az egyes regiszterek azonosítása viszont részben nyitott — 51 még azonosítatlan: 2026-08-16-án
  47 telegramtípus, 133 regiszter; a 2026-09-14-i próbafűtés 3397 szórt telegramjából
  további 131, összesen **264 regiszter**, a csonka (busz-ütközéses) sorok kivételével
  hibátlan felbontással.
* A próbafűtés **igazolta, hogy az 1. zóna a bekötött zóna**: egyedül ennek fűtési
  alapjele tér el (50,0 °C) a gyári 35,0 °C-tól.
* A szórt adatok nagy része a **be nem kötött 4–6. zóna** gyári alapértéke — ez
  magyarázza, miért tűnt zajnak.
* A kazán **10 mélységű hibanaplója** kiolvasva: mind a tíz bejegyzés égési hiba.

## Szócikkek

### Protokoll

* **[Ariston BridgeNet protokoll](ariston-bridgenet-protokoll.md)** — parancskódok,
  regisztercímzés, a szórt telegramok szerkezete, lap–értékhossz térkép
* **[Zóna-blokk szerkezet](zona-blokk-szerkezet.md)** — a regisztertérkép
  szervezőelve, amely a szórt forgalom nagy részét megnevezhetővé teszi

### Rendszer

* **[Busz-topológia](busz-topologia.md)** — eszközök, címek, busz-illesztő, terhelés
* **[Kazán](kazan.md)** — műszaki adatok, azonosítás, üzemi számlálók, üzemtörténet
* **[Hibanapló](hibanaplo.md)** — a 10 slotos hibanapló és értelmezése
* **[Gázfogyasztás becslése](gazfogyasztas-becsles.md)** — a `6847` gázteljesítmény-regiszter,
  a Home Assistant integrál, mért pontosság és javítási lehetőségek

### Adattáblák

* **[Olvasható regiszterek](olvashato-regiszterek.md)** — a 38 válaszoló regiszter
  mért értékkel, és a 185 nem válaszoló bontása
* **[Broadcast regisztertérkép](broadcast-regiszterterkep.md)** — mind a 264 kinyert
  regiszter laponként, megbízhatósági szinttel és a mérés dátumával

### Integráció

* **[ebusd konfiguráció](ebusd-konfiguracio.md)** — verziók, indítási paraméterek,
  CSV-módosítások, MQTT-leképezés
* **[Home Assistant integráció](home-assistant-integracio.md)** — entitások,
  template szenzorok, irányítópult, adatminőségi problémák

### Háttér

* **[Módszertan](modszertan.md)** — hogyan születtek az állítások, hol a határuk
* **[Források](forrasok.md)** — hivatkozások és korlátaik

## Nyitott kérdések

| Kérdés | Állapot |
|---|---|
| Az azonosítatlan regiszterek jelentése | A 2026-09-14-i próbafűtés első 12 percében a `0x42`, `0x46`, `0x94`, `0x95`, `0x9c`, `0xf2` lapok nem változtak; hosszabb fűtési üzem kell |
| Moduláció | Fűtés közben a `boiler_current_modulation` (`c404`) végig 0; a `flame_power_kw` (`6847`) viszont működik (9,5 kW), csak ritkán frissül |
| Gázfogyasztás | Gázszámláló regisztert egyik közösségi forrás sem ismer; a `flame_power_kw` időbeli integrálása a járható út (lásd [Kazán](kazan.md)) |
| `diverter_valve` jelentése | Fűtés közben is `dhw` — fordított vagy rendszerkazánnál mást jelent |
| A kazán kereskedelmi típusneve | A buszról nem kiolvasható (csak az adattábláról) |
| A hibabejegyzések időpontja | A kazán nem tárol időbélyeget |
| Az azonosító válasz 12 bájtja | Egyik közösségi forrás sem dokumentálja |
| ~~`boiler_life_time` mértékegysége~~ | **Megoldva:** méréssel igazolva órákat számol |

## Két gyakorlati megjegyzés

**A külső hőmérséklet-érzékelő nincs bekötve** (`ext_temp` = 32767 szentinel), ezért
időjáráskövető szabályozás nem tud működni. A hibrid előremenő alapjel a
2026-os fűtési szezonban végig változatlan volt (a nyári méréskor 45,0 °C, a szeptemberi
próbafűtéskor 50,0 °C — a kazán a saját, nem időjárásfüggő beállítását követi). Ez fűtéstechnikai, nem
szoftverkérdés.

**A rendszernyomás-érték nem mérés.** A kazánban nyomáskapcsoló van, nem analóg
érzékelő, ezért a `boiler_pressure` állandóan 0,0-t ad.
