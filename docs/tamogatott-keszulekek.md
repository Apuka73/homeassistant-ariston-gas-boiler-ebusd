# Támogatott készülékek

Az integráció **egyetlen készüléken van ténylegesen validálva**. Ez a lap őszintén
szétválasztja, mi bizonyított, mi valószínű és mi ismeretlen — hogy senki ne abból induljon ki,
hogy „minden Ariston kazánnal működik”.

## Validálva (saját méréssel)

| Készülék | Rendszer | Mi működik | Mérés ideje |
|---|---|---|---|
| **Ariston Cares S System 24** (cikkszám 3301636BFV) | kazán-only: egyetlen busz-slave (`0x3c`), rendszerszabályzó és hőszivattyú nélkül, külső tároló | 29 entitás, köztük a teljes gázbecslés, a diagnosztika és a 10 mélységű hibanapló | 2026-08-16, 2026-09-14 (próbafűtés), 2026-09-18 |

Ezen a készüléken a következőket **mérés igazolja**, nem feltételezés:

* a `6847` regiszter a valós idejű lángteljesítmény (a mért 14,6 kW maximum pontosan a
  névleges 24 kW beállított 61%-os fűtési maximuma);
* a `boiler_life_time` **órákat** számol, nem percet (33 nap alatt napi 23,8 egység);
* a bekötetlen külső érzékelő 0x7FFF-et (3276,7 °C) küld;
* nyomáskapcsolós kazánon a `boiler_pressure` mindig 0,0 bar;
* a gázbecslés kapuzás nélkül −8,6% hibát okozott egy mért próbafűtésen.

## Valószínűleg működik, de nincs visszaigazolva

Ezek ugyanazt a BridgeNet protokollt és ugyanazt az `ariston.csv` alapot használják, tehát a
kazán-köri regiszterek jó eséllyel egyeznek:

* Ariston **Clas ONE / Genus One / ONE+** sorozat (a szervizmenü-hivatkozásaink is ezekből valók)
* Chaffoteaux és Elco BridgeNet-kazánok (ugyanaz a protokollcsalád)

Ha ilyened van, a legrosszabb, ami történhet: kevesebb entitás jön létre, mert a kazánod más
regisztereket ismer. **Az integráció csak olvas, tehát nem tud kárt okozni a készülékben.**

## Amiről tudjuk, hogy NEM vihető át

A [Chaffoteaux Mira C Green](https://github.com/Patbonamy/ebusd-configuration-mira-c-green)
konfigurációja 78 kazán-köri regisztert definiál, köztük olyanokat, amik nekünk hiányoznak
(előremenő vízhőmérséklet, zóna-alapjelek, fűtési görbe, szobahőmérséklet).
**Ezt 18 regiszterrel leteszteltük a valódi buszon: az Ariston Cares S System 24 egyiket sem
ismeri.** Tehát a „másik kazán CSV-jét bemásolom” megközelítés nem működik automatikusan.

## Hőszivattyús / hibrid rendszerek

A [pouzak fork](https://github.com/pouzak/ebusd-configuration-ariston-bridgenet) (Nimbus R32)
és az eredeti projekt definíciói lefedik a hőszivattyús köröket (kompresszorfrekvencia,
előremenő/visszatérő HP-hőmérséklet, elektromos fűtőbetét). Ezeket **nem tudtuk ellenőrizni**,
mert a tesztrendszerben nincs hőszivattyú. Az integráció automatikusan felveszi azokat az
entitásokat, amikre a te rendszered értéket ad, tehát hibrid rendszeren is érdemes kipróbálni.

## Hogyan jelents vissza egy új készüléket

Ha kipróbáltad más kazánnal, ez a három adat sokat segít (egy hibajegyben):

```bash
echo "info" | nc <EBUSD_GEP> 8888          # ebusd verzió, adapter, jel
echo "find -c boiler" | nc <EBUSD_GEP> 8888 # mely regiszterek adnak értéket
```

…és a kazán **adattábláján** szereplő pontos típus. Ezekből felvesszük a listára, és ha új,
működő regisztereket találtál, bekerülhetnek a konfigurációba is.
