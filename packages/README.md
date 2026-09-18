# Opcionális: a régi, MQTT-alapú megoldás

> **Ez a könyvtár NEM szükséges az integráció használatához.** Az integráció közvetlenül az
> ebusd TCP portjáról olvas, és ugyanezeket az értékeket adja, kényelmesebben.

Itt az a Home Assistant YAML megoldás található, amiből az integráció logikája született. Akkor
hasznos, ha nálad már működik az **ebusd → MQTT → Home Assistant** út, és nem akarsz áttérni,
vagy ha kíváncsi vagy, hogyan néz ki ugyanez sablonokkal.

## Fájlok

| Fájl | Mit ad |
|---|---|
| `gazfogyasztas.yaml` | A kapuzott lángteljesítmény, a Riemann-integrál (kWh), a gázbecslés (m³), és a gázóra-leolvasáshoz kötött automatikus kalibráció. |
| `egesi_diagnosztika.yaml` | Lángleszakadások, gyújtási ciklusok és a lángleszakadás-arány (‰) `state_class`-szal, hogy legyen hosszútávú statisztikájuk. |
| `hibanaplo.yaml` | A 10 mélységű hibanapló kiolvasása, csúszás-felismerés, magyar hibakód-szótár, és naplóbejegyzés új hibánál. |
| `scripts/ebusd_hibanaplo.py` | A hibanaplót egyben, frissen (`-m 0`) kiolvasó segédszkript, amit a `hibanaplo.yaml` `command_line` szenzora hív. |

## Használat

1. Másold a YAML fájlokat a Home Assistant `config/packages/` könyvtárába, és hivatkozd be őket
   a `configuration.yaml`-ban:

   ```yaml
   homeassistant:
     packages:
       gazfogyasztas: !include packages/gazfogyasztas.yaml
       egesi_diagnosztika: !include packages/egesi_diagnosztika.yaml
       hibanaplo: !include packages/hibanaplo.yaml
   ```

2. Másold a `scripts/ebusd_hibanaplo.py` fájlt a `config/scripts/` könyvtárba.

3. **Igazítsd az entitásneveket.** A fájlok a referenciarendszer MQTT discovery-ből származó
   entitásneveire hivatkoznak, például:

   ```
   sensor.heating_ebusd_boiler_ebusd_boiler_flame_lift_offs
   ```

   Nálad ezek a nevek majdnem biztosan mások lesznek — az ebusd `mqtt-hassio.cfg` mintái és a
   `--mqtttopic` érték alapján állnak elő. Nézd meg a Fejlesztői eszközök → Állapotok listában,
   és cseréld a hivatkozásokat.

4. A `hibanaplo.yaml` szkriptje az ebusd címét a fájl elején tartalmazza
   (`HOST, PORT = "127.0.0.1", 8888`) — írd át, ha az ebusd máshol fut.

## Miért egyszerűbb az integráció

* Nem kell MQTT bróker, discovery és `mqtt-hassio.cfg` hangolás.
* Az entitásnevek nem változnak meg a konfiguráció szerkesztésekor (a referenciarendszeren
  egyszer az összes kazán-entitás átnevezésre került, és minden sablon eltört).
* Az integráció csak azokat az entitásokat hozza létre, amikre a rendszered ad értéket —
  MQTT-vel a nem létező körök is megjelennek `ismeretlen` állapotban (a referenciarendszeren
  137 entitásból ~70 ilyen volt).
* A bekötetlen érzékelő szentinel értéke (3276,7 °C) és a nem válaszoló regiszterek kezelése
  be van építve.
