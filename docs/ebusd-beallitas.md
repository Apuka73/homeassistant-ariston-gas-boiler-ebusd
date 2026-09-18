# Az ebusd beállítása Ariston kazánhoz

Ez a leírás végigvezet azon, hogyan jut el a kazán az eBUS-tól a Home Assistantig. Az
integráció ennek a láncnak csak az utolsó szeme: **működő ebusd nélkül nem tud mit olvasni.**

```
Ariston kazán ──eBUS (2 ér, 2400 baud)── adapter ──WiFi/USB── ebusd ──TCP 8888── Home Assistant
```

## 1. Hardver: az eBUS adapter

A fejlesztés és a tesztelés ezzel az adapterrel készült:

**[Elecrow eBUS Adapter Stick C6](https://www.elecrow.com/ebus-adapter-stick-c6.html)**

* ESP32-C6 alapú, **WiFi**-n csatlakozik — nem kell a kazán mellé számítógép.
* Az ebusd **„enhanced”** protokollját beszéli (gyorsabb és megbízhatóbb, mint a soros emuláció).
* Saját firmware-t futtat, amit az ebusd tud frissíteni (az `info` parancs kiírja, ha van újabb).

Bármelyik, az ebusd által támogatott adapter megfelel — az összes lehetőség és a bekötés
részletei: [ebusd wiki – Hardware](https://github.com/john30/ebusd/wiki/6.-Hardware).

### Bekötés

Az eBUS **kétvezetékes, polaritásfüggetlen** busz, a kazán sorkapcsán jellemzően a
szobatermosztát csatlakozója (`T`, `TA`, `BUS` jelölés). Az adapter a buszról kapja a
tápfeszültséget (kb. 24 V), külön táp nem kell.

> ⚠️ A kazán bontása előtt **áramtalaníts**. Ha nem vagy biztos a sorkapocs azonosításában,
> kérj szakembert. Az eBUS kisfeszültségű, de a kazán belsejében 230 V is van.

## 2. ebusd konfiguráció

A [john30/ebusd](https://github.com/john30/ebusd) démont Dockerből a legegyszerűbb futtatni.
A repóban van egy kitöltendő minta: [`../ebusd/docker-compose.example.yaml`](../ebusd/docker-compose.example.yaml),
és hozzá a [`../.env.example`](../.env.example).

A referenciarendszeren futó indítás (a lényeges kapcsolókkal):

```
ebusd
  --device=ens:<ADAPTER_IP>:9999   # „ens:” = enhanced protokoll hálózaton
  --configpath=/config             # a SAJÁT CSV-nk, nem a letöltött alapértelmezett
  --scanconfig=off                 # ne próbáljon automatikusan konfigurációt választani
  --pollinterval=15                # 15 másodpercenként egy lekérdezés megy ki a buszra
  --receivetimeout=5000            # lassú kazánnál kell a hosszabb türelem
  --latency=20000                  # WiFi-s adapternél elengedhetetlen
  --sendretries=10 --acquireretries=5 --acquiretimeout=20
```

### Miért `--scanconfig=off`?

Az automatikus felismerés az Ariston rendszereken rendszerint nem találja el a megfelelő
konfigurációt. Megbízhatóbb kézzel megadni a CSV-t, és pontosan tudni, mi van betöltve.

### A CSV konfiguráció

A repó [`../ebusd/ariston.csv`](../ebusd/ariston.csv) fájlja használható közvetlenül. Ez a
[wrongisthenewright/ebusd-configuration-ariston-bridgenet](https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet)
v2.6 **módosított** változata; a négy javítás leírása: [`../ebusd/NOTICE.md`](../ebusd/NOTICE.md).
A fájl GPL v3 licencű.

Másold a `--configpath` által mutatott könyvtárba, és indítsd újra az ebusd-t.

## 3. Ellenőrzés az ebusd oldalán

Mielőtt a Home Assistanthoz nyúlnál, győződj meg róla, hogy az ebusd lát a buszra:

```bash
# a démon állapota
echo "info" | nc <EBUSD_GEP> 8888
```

Amit látni akarsz:

```
version: ebusd 26.1.26.1
device: <ADAPTER_IP>:9999, TCP, enhanced, firmware 1.1[6819].1[6819]
signal: acquired          <-- EZ a lényeg
symbol rate: 57
```

Ha `signal: no signal`, akkor a bekötéssel vagy az adapterrel van baj — a Home Assistant
ezen nem segít.

Ezután nézd meg, mit tud a kazán köre:

```bash
echo "find -c boiler" | nc <EBUSD_GEP> 8888
```

Egy kazán-only rendszeren ~50 üzenetből jellemzően **37 ad értéket**, a többi
`no data stored` marad. Ez normális.

## 4. Mit várj a saját rendszereden

A referenciarendszer **kazán-only**: egyetlen valódi slave van a buszon (`0x3c`, a kazán).
Ilyenkor:

* Az `ariston.csv` `energymgr` (0x18), `heatpump` (0x1e), `gateway` és `sensys` (0x75/0x23)
  köreinek lekérdezése **időtúllépésre fut** — ez a telepítés adottsága, nem hiba.
  (A referenciarendszeren 185 regiszter fut így.) Az integráció ezt megjegyzi, és nem
  próbálja újra 6 órán át.
* Ezekből a körökből mégis lehet értéked, ha a kazán **broadcastban** közli őket (például a
  melegvíz céhőmérséklete vagy az előremenő alapjel).
* Ha van rendszerszabályzód (Sensys, Cube) vagy hőszivattyúd, jóval több regisztered lesz —
  és az integráció automatikusan felveszi azokat, amikre érkezik érték.

## 5. Gyakori problémák

| Tünet | Ok és megoldás |
|---|---|
| A külső hőmérséklet 3276,7 °C | Nincs bekötve külső érzékelő; a kazán 0x7FFF-et küld. Az integráció ezt kiszűri (az entitás `ismeretlen` lesz). Időjáráskövetés ilyenkor nem tud működni. |
| A víznyomás mindig 0,0 bar | A kazánban nyomás*kapcsoló* van, nem analóg érzékelő (ellenőrizd a „Nyomásfigyelő eszköz” entitást: `pressure_switch`). Valódi nyomást csak a manométer mutat. |
| A lángteljesítmény a láng kialvása után is nagy | A regiszter lekérdezése percekig késhet. Az integráció ezért **nullára kapuzza** a teljesítményt, ha a kazán állapota szerint nem éghet láng. Ha a nyers értéket látod ilyennek, az rendben van — a „Lángteljesítmény” (kapuzott) entitást használd. |
| Nagyon lassú lekérdezés | Növeld a `--latency` értéket (WiFi-s adapternél 20000 bevált), és hagyd magasabban a `--pollinterval`-t. |
| `signal: no signal` | Bekötés, adapter, vagy a busz potenciométerének beállítása — lásd az ebusd hardver-wikit. |

## 6. MQTT (opcionális, nem szükséges)

Az integrációhoz **nem kell MQTT**. Ha mégis MQTT-n keresztül szeretnéd használni a kazánt
(például mert már így működik nálad), a repó [`../packages/`](../packages/) könyvtárában
megtalálod a megfelelő Home Assistant YAML csomagokat, és az [`../ebusd/mqtt-hassio.cfg`](../ebusd/mqtt-hassio.cfg)
fájlt a discovery-hez. A kettő párhuzamosan is futhat, de akkor duplán kapod az entitásokat.
