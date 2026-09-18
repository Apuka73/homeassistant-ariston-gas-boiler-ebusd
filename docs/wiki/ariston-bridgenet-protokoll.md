# Ariston BridgeNet protokoll

| | |
|---|---|
| **Típus** | Alkalmazásrétegi kiterjesztés eBUS fölött |
| **Gyártó** | Ariston Group (Ariston, Chaffoteaux, Elco) |
| **Fizikai réteg** | eBUS (0–24 V, 2400 baud, félduplex, két eres) |
| **Címzési modell** | Regiszteres (virtuális memóriatérkép) |
| **Bájtsorrend** | Little-endian |
| **Dokumentáltság** | Nincs nyilvános gyártói specifikáció; közösségi visszafejtés |

A **BridgeNet** az Ariston Group fűtéstechnikai eszközeinek belső kommunikációs
protokollja. Az eBUS szabvány fizikai és adatkapcsolati rétegére épül, de saját
alkalmazásréteget definiál: a szabványos eBUS szolgáltatás-orientált üzenetei helyett
az eszközök **regisztereket** olvasnak és írnak, mintha közös memóriatérképet
osztanának meg.

A protokoll gyártói dokumentációja nem nyilvános. Az itt leírtak a
[Módszertan](modszertan.md) szócikkben részletezett mérésekből származnak, és egy
konkrét telepítésen ellenőrzöttek — lásd [Busz-topológia](busz-topologia.md).

## Parancskódok

A BridgeNet az eBUS PBSB (primary/secondary command byte) mezőjében saját
parancskódokat használ:

| PBSB | Irány | Jelentés |
|---|---|---|
| `2000` | kérés | Egyetlen regiszter közvetlen olvasása |
| `2001` | kérés | Regiszter olvasása aktuális értékkel **és** a megengedett min/max korláttal |
| `2002` | kérés | Azonosítás, illetve indexelt rekordok (pl. hibanapló) olvasása |
| `200e`, `200f` | szórás | Válasz `2000` kérésre, illetve broadcast egyetlen regiszterről |
| `2010` | szórás | Broadcast több regiszter értékéről |
| `2020` | szórás | Broadcast paraméterírásról (több regiszter) |
| `2031` | szórás | Sorozatszámok szórása, illetve busz-reset |
| `203b` | szórás | Azonosítatlan, rendszeres rövid üzenet |

Ritkábban előfordul még a `2050`, `2051`, `2071` és `2073`.

A `2001` visszatérési formátuma külön figyelmet érdemel: a válasz a hosszjelző után
az aktuális értéket, majd a megengedett minimumot és maximumot tartalmazza. Ez
gyakran egyértelműsíti egy ismeretlen regiszter mértékegységét és skálázását
anélkül, hogy a rendszer beállításához hozzá kellene nyúlni.

## Regisztercímzés

Egy regisztert kétbájtos azonosító jelöl. A buszon **little-endian** sorrendben
utazik, ezért a logikai regisztercím és a vezetéken látott bájtpár egymás fordítottja:

```
logikai regiszter:  0x4760
vezetéken (wire):   60 47
```

Az `ebusd` CSV-konfigurációjában az azonosító mindig a **vezetéki** sorrendben
szerepel (`6047`).

A magas bájt gyakorlatilag **lapszámként** viselkedik: azonos lapon lévő regiszterek
egy funkcionális családba tartoznak, azonos adattípussal és azonos értékhosszal. Az
alacsony bájt a lapon belüli index. Ez a felépítés teszi lehetővé a
[zóna-blokk levezetést](zona-blokk-szerkezet.md).

## A szórt telegramok szerkezete

A `2010` és `2020` parancsú szórt üzenetek felépítése egyetlen szabállyal leírható:
a fejléc után **(regiszter-azonosító, érték)** párok ismétlődnek a hosszmező által
megadott végéig.

```
QQ  fe  20 10  NN  [ ID_lo ID_hi <érték> ]*
│   │   │      │     │     │      └─ little-endian, hossza a laptól függ
│   │   │      │     └─────┴─ regiszterazonosító (2 bájt)
│   │   │      └─ adathossz bájtban
│   │   └─ parancs
│   └─ cél: broadcast
└─ forrás (master)
```

**Az értékhossz nem uniform**: laponként állandó, de lapok között eltér. Ez azt
jelenti, hogy egy telegram helyes felbontásához ismerni kell az érintett lapok
hosszát; enélkül a bájtfolyam többértelmű.

### Példa

```
37 fe 2010 0f  6047 f40100  6197 f40100  6297 5e0100
```

* `0f` = 15 adatbájt
* `6047` → regiszter `0x4760`, érték `f40100` = 500 → **50,0 °C** (hibrid előremenő alapjel)
* `6197` → regiszter `0x9761`, érték 500 → **50,0 °C** (1. zóna számított alapjele)
* `6297` → regiszter `0x9762`, érték 350 → **35,0 °C** (2. zóna, minimumon)

Vegyes hosszúságú példa:

```
37 fe 2010 0d  7647 ff7f00  d194 0000  d294 0000
```

* `7647` → `0x4776`, 3 bájtos érték `ff7f00` = **32767**
* `d194`, `d294` → `0x94d1`, `0x94d2`, 2 bájtos értékek

### Szentinel érték

A `32767` (`0x7FFF`) érték **nem mérés**, hanem „nincs érzékelő / érvénytelen”
jelzés. Egy `/10` skálázású hőmérséklet-mezőben ez 3276,7 °C-ként jelenik meg a
felsőbb rétegekben — ez a jellegzetes nyoma egy be nem kötött érzékelőnek.

## Lap–értékhossz térkép

A 2026-08-16-i mérésen megfigyelt 47 telegramból levezetett és azokon
maradéktalanul ellenőrzött hozzárendelés, a 2026-09-14-i próbafűtés nyers busznaplójával
kiegészítve (új lapok: `0x20`, `0x72`, `0x73`, `0x7a`, `0x7b`). A bővített táblával a
3397 szórt telegramból egy kivételével mind maradéktalanul felbontható volt; a kivétel egy
busz-ütközés miatt csonka sor.

| Értékhossz | Lapok |
|---|---|
| **1 bájt** | `0x19`¹, `0x20`, `0x23`, `0x27`, `0x28`, `0x2a`, `0x79`, `0x7a`, `0x7b`, `0x7c`, `0x7d`, `0x7e`, `0x81`, `0x82`, `0x83`, `0x84`, `0x85`, `0x86` |
| **2 bájt** | `0x19`¹, `0x26`, `0x2b`, `0x42`, `0x46`, `0x4b`, `0x71`, `0x72`, `0x73`, `0x74`, `0x75`, `0x76`, `0x91`, `0x94`, `0x95`, `0x9c`, `0xf2` |
| **3 bájt** | `0x10`, `0x47`, `0x96`, `0x97` |

¹ A `0x19` lap a `2010`-es telegramokban 2 bájtos értékkel jelenik meg.

A nyers naplóban busz-ütközéskor (`ERR: SYN received`) csonka telegramok is előfordulnak.
Ezek formailag felbonthatók, de értelmetlen, `0x00` lapú „regisztereket” adnak
(pl. `0000`, `0b00`, `9100`) — ilyen lap valós telegramban nem fordul elő, ezért a
dekódolásnál el kell dobni őket.

A 3 bájtos lapok esetében a felsőbb rétegek (és az `ebusd` CSV-je) tipikusan csak az
első két bájtot értelmezik `SIN`-ként; a harmadik bájt a megfigyelt esetekben mindig
`0x00` volt. Numerikusan a két értelmezés azonos eredményt ad, a bájtszámlálás
szempontjából viszont a 3 bájt a helyes.

## Az ismeretlen mezők átugrása

Mivel egy telegram több regisztert hordoz, egy dekóder az elsőt azonosítja
mintaillesztéssel, a többit pedig pozíció alapján. Az `ebusd` CSV-jében ehhez az
`IGN:n` mezőtípus használatos: az érték kiolvasása után `IGN:3` egyszerre nyeli le az
érték maradék bájtját és a következő kétbájtos azonosítót.

```
b,boiler,boiler_status,…,fe,2010,c04b,boilerstatus,,UCH,<értéklista>,,,,,IGN:3,,,,z1_heating,,BCD,0=off;1=on,…
```

Ez a konstrukció a `0x4b` lapon (2 bájtos érték, `UCH` 1 bájtot olvas) pontosan
illeszkedik: 1 bájt érték + `IGN:3` (1 maradék bájt + 2 azonosító bájt) + következő
érték.

## Nem támogatott szabványos szolgáltatások

A szabványos eBUS eszközazonosítás (`0x0704`) **nem működik**: a lekérdezés
`ERR: SYN received` hibával tér vissza. A BridgeNet eszközök helyette a `2002`
parancsot használják, illetve a sorozatszámukat a `2031` paranccsal szórják szét —
utóbbit tipikusan csak busz-reset vagy bekapcsolás után, egyszer.

## Lásd még

* [Broadcast regisztertérkép](broadcast-regiszterterkep.md)
* [Zóna-blokk szerkezet](zona-blokk-szerkezet.md)
* [Busz-topológia](busz-topologia.md)
* [Módszertan](modszertan.md)
* [Források](forrasok.md)
