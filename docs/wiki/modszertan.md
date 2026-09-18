# Módszertan

Ez a szócikk azt írja le, hogyan születtek a wiki állításai, és hol húzódnak a
megbízhatóságuk határai. A mérések 2026-08-16-án készültek, egyetlen telepítésen.

## 1. A regiszterkészlet feltérképezése

Az `ariston.csv` 223 aktívan olvasható üzenetet definiál. Mindegyiket egyenként
lekérdeztük (`ebusctl read -m 0`), hibánál három próbálkozással. Eredmény: 38
válaszolt, 185 időtúllépésre vagy dekódolási hibára futott. A hibák eloszlása
körönként egyértelműen mutatta, hogy a nem válaszoló körök busz-címei nincsenek
jelen — lásd [Busz-topológia](busz-topologia.md).

## 2. A szórt telegramok szerkezetének levezetése

Az `ebusctl grab result all` 47 különböző telegramtípust adott, ebből 20 olyat,
amelyet az `ebusd` nem tudott azonosítani.

**Első lépés — a szerkezet felismerése.** Az `ariston.csv`-ben már azonosított
telegramok szolgáltak kontrollcsoportként. A `6047` azonosítójú üzenetről tudott
volt, hogy 50,0 °C-os alapjelet hordoz; a nyers bájtok (`6047 f40100`) ezt
`ID(2) + érték` felbontásban adták vissza, ami a többi telegramra is ráilleszthető
volt.

**Második lépés — az értékhossz meghatározása.** Az értékhossz nem uniform, ezért a
felbontás önmagában többértelmű. Első megközelítésben kényszer-megoldót írtunk: minden
telegramra felsorolta az összes olyan felbontást, amely pontosan kiadja a hosszmezőt,
majd laponként metszetet képzett. Ez túl megengedőnek bizonyult — a szabad keresés
értékbájtokat is azonosítóként értelmezett, és néhány lapra ellentmondásos (üres)
eredményt adott.

A végleges térkép ezért kézi levezetéssel készült, telegramonként, a már ismert lapok
hosszából kiindulva. **A helyessége mellett szól, hogy mind a 47 telegram pontosan
kiadja a saját hosszmezőjét — nincs maradék bájt és nincs többértelműség.** Téves
lap–hossz hozzárendelés mellett a telegramok többsége nem záródna le hibátlanul.

**Harmadik lépés — azonosítás.** A 133 kinyert regisztert három forrással vetettük
össze: az `ariston.csv` mintegy 250 ismert azonosítójával, az `ebusd` saját
dekódolásával, és egy külső regisztertérképpel (lásd [Források](forrasok.md)).

**2026-09-14 — kiegészítés.** A próbafűtés alatt az `ebusctl raw` üzenetszintű naplózás
minden szórt telegramot rögzített (3295 db `2010`, 102 db `2020`). A lap–értékhossz térkép
öt új lappal bővítve mind a 3397 telegramot felbontotta, egyetlen busz-ütközés miatt csonka
sor kivételével. Így 131 új regiszter került elő; a két mérés közös regiszterei mind azonos
értéket adtak.

## 3. Az azonosítások megbízhatósági szintjei

| Szint | 2026-08-16 | 2026-09-14 után | Alap |
|---|---|---|---|
| **Igazolt** | 20 | 20 | Az `ebusd` vagy a CSV önállóan is ismeri, és a dekódolt érték egyezik a független olvasással |
| **Levezetett** | 52 | 129 | A [zóna-blokk minta](zona-blokk-szerkezet.md) alapján, fizikailag ellenőrzött értéktartománnyal |
| **Részleges** | 26 | 64 | A zóna azonosítható, a paraméter nem |
| **Azonosítatlan** | 35 | 51 | Nincs támpont |

Az „igazolt” szint erős: például a `6047` → 50,0 °C, `6147` → 60,0 °C, `c04b` →
`standby`, `6996` → 19,0 °C mind egyezik azzal, amit az `ebusd` a saját, független
úton dekódolt.

A „levezetett” szint gyengébb, de nem spekulatív: a
[zóna-blokk ellenőrzés](zona-blokk-szerkezet.md) tizenhét paramétert vizsgált, és
mindegyik a saját jelentéséhez illő fizikai tartományba esett, két különböző
skálázási osztóval.

## 4. Amit nem lehetett megállapítani

* **A kazán kereskedelmi típusneve.** A BridgeNet nem támogatja a szabványos eBUS
  azonosítást, a sorozatszám pedig csak busz-reset után kerül a buszra. A reset a
  fűtésvezérlés újraindítását jelentené, ezért nem került rá sor.
* **A hibabejegyzések időpontja.** A kazán nem tárol időbélyeget — lásd
  [Hibanapló](hibanaplo.md).
* **35 regiszter jelentése.** Ezek a telepítésen végig 0-t vagy változatlan
  alapértéket adnak, mert nincs mögöttük bekötött hardver vagy aktív üzemállapot.
* **Az azonosító válasz 12 értelmezetlen bájtja** — lásd [Kazán](kazan.md).

## 5. Miért nem lehet visszamenőleg többet kinyerni

A `2026 januári–februári` fűtési szezonban az ismeretlen regiszterek feltehetően
beszédes értékeket vettek fel. Ez az adat azonban **nem maradt fenn**:

* az `ebusd`-nek nincs `--logfile` beállítása, csak szabványos kimenetre naplóz;
* a `grab` puffer memóriában él, és minden újraindításkor nullázódik;
* a Docker a konténer újralétrehozásakor törli az előző napló-fájlt;
* a Home Assistant recorder csak a **dekódolt** entitásokat őrzi — a szezonban
  mindössze hetet —, a nyers telegramokat nem.

A `37fe20(10|20)` mintára a rendszerben sehol nem található naplófájl: az ebusd ezeket a
telegramokat nem írja ki magától.

**Következmény:** a maradék 35 regiszter azonosításához a következő fűtési szezonban
kell rögzítést indítani. Erre kézenfekvő megoldás egy ütemezett
`ebusctl grab result all` pillanatkép, amely csak a megváltozott (regiszter, érték)
párokat naplózza. Melegvizes ciklusra nem lehet építeni: a kazán élettartama alatt
nulla órát üzemelt HMV-ben.

## 6. Reprodukálhatóság

A wiki adattáblái a mérési kimenetekből generáltak, nem kézzel átírtak. A nyers mérési
fájlok (`report.json`, `ebus_sweep.txt`, `grab_all.txt`, `grab_2020.txt`) **nem részei ennek
a repónak** — a bennük lévő adatok lényege a regisztertáblákban szerepel.

A mérés megismételhető: a regiszter-végigolvasás és a `grab` kiolvasás egyaránt
csak olvasási műveleteket használ, a rendszer beállításait nem érinti.

## Lásd még

* [Ariston BridgeNet protokoll](ariston-bridgenet-protokoll.md)
* [Források](forrasok.md)
