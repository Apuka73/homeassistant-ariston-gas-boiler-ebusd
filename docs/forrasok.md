# Források — honnan származnak az adatok, és mit fejtettünk meg mi

Ez a projekt **közösségi visszafejtésre** épül. Egyetlen felhasznált forrás sem gyártói
dokumentáció. Ez a fájl tételesen elkülöníti, mi származik mások munkájából, és mi az, amit a
saját méréseinkből állapítottunk meg.

## 1. Mások munkája

### Szoftver

| Projekt | Mit ad | Licenc |
|---|---|---|
| [john30/ebusd](https://github.com/john30/ebusd) | Maga az eBUS démon, ami a buszt olvassa. A fejlesztéskor 26.1. Enélkül semmi nem működne. | GPL v3 |
| [ebusd wiki – Hardware](https://github.com/john30/ebusd/wiki/6.-Hardware) | Az adapterek listája, bekötés, a busz-potenciométer beállítása. | — |

### BridgeNet regiszterek és konfigurációk

| Forrás | Mit vettünk át |
|---|---|
| [wrongisthenewright/ebusd-configuration-ariston-bridgenet](https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet) | **Az `ariston.csv` alapja (v2.6).** Innen származik a regiszterazonosítók és a zóna-elnevezések nagy része. GPL v3 — ezért van külön licenc az `ebusd/` mappában. |
| [kredow/ariston-ebus-prococol](https://github.com/kredow/ariston-ebus-prococol) | A PBSB-parancsok listája, valamint a `0x9101`–`0x9107` (`heat_request_z1`–`z7`), `0x9761`–`0x9767`, `0x190c` és `0x4776` azonosítása. |
| [ysard/ebusd_configuration_chaffoteaux_bridgenet](https://github.com/ysard/ebusd_configuration_chaffoteaux_bridgenet) | A `2001` parancs érték+min+max szerkezetének leírása, és a **10 mélységű hibanapló** (`0400`–`0409`) definíciója — a hibanapló-entitás enélkül nem létezne. |
| [komw/ariston-bus-bridgenet-ebusd](https://github.com/komw/ariston-bus-bridgenet-ebusd) | Eltérő elnevezések ugyanazokra az azonosítókra (keresztellenőrzésre használtuk). |
| [john30/ebusd – Discussion #880](https://github.com/john30/ebusd/discussions/880) | „Decoding strange broadcast messages for Ariston Ebus” — megerősíti az `xxfe2010` telegramok `(azonosító, érték)` páros szerkezetét. |
| [elektroda.com – Exploring Ariston BUS BridgeNet Protocol](https://www.elektroda.com/rtvforum/topic3415927.html) | Háttéranyag a protokoll általános felépítéséről. |

### A lángteljesítmény (gázbecslés) azonosítása

| Forrás | Mit ad |
|---|---|
| [wrongisthenewright #24](https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet/issues/24), [ysard #11](https://github.com/ysard/ebusd_configuration_chaffoteaux_bridgenet/issues/11) | A `6847` (`0x4768`) regiszter vitája: a karbantartó a kezelőegység szervizmenüjével vetette össze — valós idejű gázteljesítmény, kW/10. (A komw CSV ugyanezt `dhw_flowmeter`-nek nevezi, tévesen.) |
| [wrongisthenewright #20](https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet/issues/20), [#29](https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet/issues/29) | Megerősíti, hogy **gázfogyasztás-számláló regiszter nem létezik**; a költségszámítás az Energy Manager feladata, amely a legtöbb rendszeren nincs. |
| [Ariston Clas ONE R kézikönyv, 8. menü](https://library.ariston.co.uk/clas-one-r-installation-manual/65488087/40), [ONE+ szervizmenü](https://library.ariston.co.uk/one-series-installation-amp-service-manual/68650958/44) | A 8.2.8 „Gas Power, kW”, 8.2.2 ventilátor-fordulat, 8.3.1/8.3.2 előremenő/visszatérő hőmérséklet, 8.1.0/8.1.1 égőórák menüpontjai — ezekhez tudtuk kötni a regisztereket. |
| [HA community – Ariston group integration via ebusd #194](https://community.home-assistant.io/t/ariston-group-integration-via-ebusd/738887/194) | A `c404` moduláció csak rendszerszabályzós (Sensys/Cube) telepítésen ad értéket. |
| [fustom/python-ariston-api](https://github.com/fustom/python-ariston-api) | Az Ariston NET **felhős** API fogyasztási típusai — összehasonlításnak; a felhő a gázt szintén számolja, nem méri. |

## 2. Amit mi fejtettünk meg

Minden itt felsorolt megállapítás **saját mérésből** származik, egy valódi telepítésen
(Ariston Cares S System 24, kazán-only rendszer).

### 264 broadcast regiszter dekódolása

Az Ariston a buszon `xxfe2010` és `xxfe2020` típusú broadcast telegramokat küld, amelyek
`(regiszterazonosító, érték)` párokat hordoznak. Két mérésből fejtettük vissza őket:

| Mérés | Eredmény |
|---|---|
| **2026-08-16** (nyári állapot) | 47 telegramtípusból **133 regiszter** |
| **2026-09-14** (próbafűtés közben, nyers busznapló: 3295 db `2010` és 102 db `2020` telegram) | további **131 regiszter** |

A módszertan — hogyan különítettük el az „igazolt”, a „levezetett” és a „feltételezett”
azonosításokat — a wiki [Módszertan](wiki/modszertan.md) szócikkében van. A teljes
regisztertérkép: [Broadcast regisztertérkép](wiki/broadcast-regiszterterkep.md).

### A zóna-blokk szerkezet levezetése

Felismertük, hogy a zónánkénti értékek **fix lépésközű blokkokban** ismétlődnek, és ebből
levezethető olyan regiszterek jelentése is, amelyeket egyik közösségi forrás sem dokumentál.
Lásd: [Zóna-blokk szerkezet](wiki/zona-blokk-szerkezet.md).

### Javítások és kiegészítések az ebusd konfigurációban

Tételesen, `diff`-fel ellenőrizhetően: [`../ebusd/NOTICE.md`](../ebusd/NOTICE.md).

1. **Lekérdezési prioritások 38 üzenetre** — az eredeti CSV-ben az ebusd magától egyiket sem
   frissítette.
2. **A 10 mélységű hibanapló** 9 új üzenete (`error_slot_1`…`9`).
3. `boiler_status` topic-ütközés feloldása (broadcast + külön `boiler_status_read`).
4. `flame_power_kw` gyakoribb olvasása, ami a gázbecslést rontotta el.
5. `boiler_life_time` **mértékegysége percről órára** — méréssel igazolva (33 nap alatt
   31 980 → 32 768, azaz óránként egy).
6. `energymgr` zónablokk-horgonyok jelzése (hibás mezőnevek).
7. `mqtt-hassio.cfg`: a `pct$` minta rossz sorrendje.

### A gázbecslés eljárása

* **A kapuzás:** a kazán állapotát broadcast hozza (másodpercek), a teljesítményt lekérdezés
  (percek). A kettő időbeli eltérése miatt a láng kialvása után beragadt kW-érték nem létező
  gázt integrált. Méréssel igazolt hiba: a próbafűtésen a végén +0,5 kWh, az elején −0,75 kWh,
  összesen **−8,6%**. Megoldás: ha az állapot szerint nem éghet láng, a teljesítmény nulla.
* **A hitelesség ellenőrzése:** a mért maximum 14,6 kW pontosan a kazán névleges 24 kW-jának a
  beállított fűtési maximuma (61%): 24 × 0,61 = 14,64. Ez független megerősítés arra, hogy a
  `6847` regiszter tényleg a lángteljesítmény.
* **A kalibráció:** a fizikai gázóráról vett leolvasásokból, a kiinduló ponthoz viszonyítva
  számoljuk a m³/kWh szorzót — így minden újabb leolvasás pontosít.
  Részletek: [Gázfogyasztás-becslés](wiki/gazfogyasztas-becsles.md).

### A hibanapló időbélyegzése

A kazán a 10 bejegyzéshez **nem tárol időpontot** (a dátummezők `ff`-ek). Kidolgoztuk a
csúszás-alapú felismerést: ha a napló k bejegyzéssel lejjebb csúszott, az első k bejegyzés új,
és megkapja a kiolvasás időpontját — így az **ugyanazzal a kóddal ismétlődő** hibák is
láthatóvá válnak.

### A telepítés adottságai, amikre a kód épül

* A buszon **egyetlen valódi slave** van (`0x3c`, a kazán); az `energymgr` (0x18), `heatpump`
  (0x1e), `gateway` és `sensys` (0x75/0x23) körök **185 regisztere `read timeout`-ra fut**.
  Nem hiba — kazán-only telepítés. Ezért tanulja meg az integráció, mi nem válaszol.
* A **bekötetlen külső érzékelő** 0x7FFF-et küld (3276,7 °C) — ezt szűrni kell, különben
  hamis mérésként kerül az adatbázisba.
* A `boiler_pressure` **mindig 0,0 bar**, ha a kazánban nyomáskapcsoló van
  (`pressure_monitoring_device: pressure_switch`), nem analóg érzékelő.

## 2/b. A fork-ök átvizsgálása (2026-09-18)

Az eredeti projekt mind a **18 forkját** átnéztük; hétnek van saját fejlesztése. Amit tanultunk
belőlük, forrásmegjelöléssel:

| Fork | Mit ad | Mit tettünk vele |
|---|---|---|
| [Patbonamy – Mira C Green](https://github.com/Patbonamy/ebusd-configuration-mira-c-green) | 78 kazán-köri üzenet egy rendszerszabályzó nélküli Chaffoteaux kazánhoz (előremenő hőfok, zóna-alapjelek, fűtési görbe) | **18 jelöltet a valódi buszon teszteltünk** — egyik sem létezik az Ariston Cares S System 24-en. Nem vettük át, de dokumentáltuk (negatív eredmény is eredmény). |
| [michalmie](https://github.com/michalmie/ebusd-configuration-ariston-bridgenet) | `dhw_boost` regiszter (`energymgr/1e22`) | Valódi bővítés, de energiakezelő nélkül nem ellenőrizhető — nem vettük át, linkeljük. |
| [pouzak](https://github.com/pouzak/ebusd-configuration-ariston-bridgenet) | Nimbus R32 hibrid kiegészítés: hőszivattyú-hőmérsékletek, kompresszorfrekvencia, elektromos fűtőbetét, `32767=0` szentinel-kezelés a külső hőmérsékletre | A szentinel-kezelésük **független megerősítése** a mi 0x7FFF-megfigyelésünknek. A hőszivattyús rész nem ellenőrizhető nálunk. |
| [amonbts](https://github.com/amonbts/ebusd-configuration-ariston-bridgenet) | Saját hibakód-tábla, és a figyelmeztetés, hogy **a hibakódok számozása rendszerfüggő** | Átvettük **a figyelmeztetést** (lásd lent) — ez fontos korlát, amit eddig nem dokumentáltunk. |
| fvlaicu, lptr | Csak idézőjel- és szóköz-tisztítás a megjegyzésekben | Nincs mit átvenni. |
| duko1234 | Elco Aerotop (levegő-víz hőszivattyú) külön CSV | Más készülék. |

Ezen felül **szinkronizáltunk az eredeti projekt v2.6 utáni négy commitjával** — az adattípus-javítást
méréssel ellenőriztük, és csak azt a részét vettük át, ami ezen a kazánon helyes. Részletek:
[`../ebusd/NOTICE.md`](../ebusd/NOTICE.md).

> **Fontos korlát a hibakódokhoz** ([amonbts](https://github.com/amonbts/ebusd-configuration-ariston-bridgenet)
> megfigyelése, [ysard bruteforce-szkriptje](https://github.com/ysard/ebusd_configuration_chaffoteaux_bridgenet?tab=readme-ov-file#bruteforce-the-errors-to-discover-their-corresponding-codes)
> nyomán): a hibakódok **sorszámozása készülék- és rendszerfüggő**. A CSV-ben lévő
> „sorszám → hibakód” tábla erre a kazánra érvényes; más rendszeren ugyanaz a sorszám más hibát
> jelenthet. Ha a hibanapló értelmetlen kódokat ad, a hivatkozott szkripttel újra le lehet gyűjteni
> a saját készülék tábláját.

## 3. Ami máig ismeretlen

A broadcast forgalomból **kb. 35 regiszter azonosítatlan**: rendszeresen változnak, de nem
sikerült megfeleltetni őket semmilyen kezelőfelületi vagy szervizmenü-adatnak. A listájuk a
[Broadcast regisztertérkép](wiki/broadcast-regiszterterkep.md) „ismeretlen” soraiban van.

Két konkrét, sokakat érintő hiányosság:

* **Nincs olyan regiszter, amely a kazán kereskedelmi típusnevét vagy termékkódját adná vissza** —
  egyik forrás sem dokumentál ilyet, és mi sem találtunk.
* **Nincs gázfogyasztás-számláló**: a kazán nem mér gázt, csak teljesítményt jelent.

Ha a saját rendszereden azonosítasz valamit a listából, nyiss hibajegyet — a cél, hogy fogyjon.

## 4. A források korlátai

Egyik hivatkozott forrás sem gyártói dokumentáció; mind közösségi visszafejtés, gyakran
bizonytalanságot jelző elnevezésekkel (`temp_Z1?`, `heating in progress?`, `gas power?`).
Ez a projekt ezeket **nem kezeli azonos súlyúnak** a méréssel igazolt állításokkal: a
regisztertérkép minden sora jelöli, hogy igazolt, levezetett vagy feltételezett.
