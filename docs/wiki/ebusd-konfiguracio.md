# ebusd konfiguráció

| | |
|---|---|
| **Verzió** | ebusd 26.1.26.1 |
| **Konténer** | `ebusd-ariston` |
| **Image** | `john30/ebusd:latest` (címke: `26.1-amd64`, amd64) |
| **Image digest** | `sha256:59bf92661bd49900ec64d6bb994556ee8f4f06c036f640163908439b684bc066` |
| **Image build** | 2026-02-10 |
| **Compose** | a Home Assistant melletti `docker-compose.yaml`, `ebusd` szolgáltatás |
| **Konfigkönyvtár** | a gazdagépen tetszőleges könyvtár, a konténerben `/config` |

Az [ebusd](https://github.com/john30/ebusd) nyílt forráskódú démon, amely eBUS
hálózatot olvas és az adatokat MQTT-n, illetve saját TCP-parancsinterfészen
(`ebusctl`, 8888-as port) teszi elérhetővé.

## Indítási paraméterek

```
ebusd
  --mqtthost=<MQTT_BROKER_IP> --mqttport=1883 --mqttuser=<MQTT_FELHASZNALO> --mqttpass=<MQTT_JELSZO>
  --mqttjson --mqttretain --mqttint=/config/mqtt-hassio.cfg --mqtttopic=ebusd
  --configpath=/config --scanconfig=off
  --device=ens:<ADAPTER_IP>:9999
  --receivetimeout=5000 --latency=20000 --pollinterval=15
  --sendretries=10 --acquireretries=5 --acquiretimeout=20
```

Kiemelendő beállítások:

* `--scanconfig=off` — az `ebusd` nem próbál automatikusan konfigurációt betölteni a
  buszon talált eszközök alapján; kizárólag a helyi CSV érvényes. A BridgeNet
  amúgy sem támogatja a szabványos azonosítást.
* `--latency=20000` és a megemelt újrapróbálkozások — a WiFi-s busz-illesztő
  késleltetése miatt szükségesek (lásd [Busz-topológia](busz-topologia.md)).
* `--mqttretain` — az értékek retained üzenetként kerülnek ki, így egy Home
  Assistant-újraindítás után azonnal rendelkezésre állnak, nem kell megvárni a
  következő lekérdezési kört.
* `--pollinterval=15` — 15 másodpercenként **egy** lekérdezés megy ki a buszra; ezen
  osztozik az összes lekérdezett üzenet a prioritása arányában (mért gyakorlati érték:
  16 mp/lekérdezés).

## Konfigurációs CSV

Alap: [wrongisthenewright/ebusd-configuration-ariston-bridgenet](forrasok.md)
**v2.6** (commit `1169e7c`, 2025-02-18). Az upstream azóta négy committel előrébb
jár; ezek jórészt a `*_power_pct` regiszterek `UCH` → `UIN` adattípus-javításai és
egy új `em_delta_t` üzenet — a helyi módosítások miatt nincsenek átvéve.

A CSV 352 üzenetet definiál (a hibanapló-bővítés után 361-et). Ebből
[223 olvasható aktívan](olvashato-regiszterek.md), a többi szórásra várakozó vagy
írható üzenet.

### Helyi módosítások

| Módosítás | Hatás |
|---|---|
| Lekérdezési prioritás 36 soron | 2 → **38** lekérdezett üzenet |
| `boiler_status` (`c04b`) bővítése | + zónánkénti „fűtés folyamatban” mezők |
| `hybrid_LWT_setpoint` (`6047`) bővítése | + zónánkénti számított előremenő alapjel |
| `error_slot_1` … `error_slot_9` (`0401`–`0409`) | 10 mélységű [hibanapló](hibanaplo.md) |
| 2026-09-14: a lekérdezéses `boiler_status` (`r1`, `2000/c04b`) átnevezve `boiler_status_read`-re | a broadcast és a lekérdezés nem ír többé ugyanarra az MQTT-témára; megszűntek a `z1/z2/z3_heating` template-hibák |
| 2026-09-14: `flame_power_kw` (`6847`) `r2` → `r1` | a lángteljesítmény kb. 5 helyett kb. 3 percenként frissül — lásd [Gázfogyasztás becslése](gazfogyasztas-becsles.md) |

A módosítások tételes listája és az eredetihez képesti eltérés: [`../../ebusd/NOTICE.md`](../../ebusd/NOTICE.md).

### Lekérdezési prioritások

Az `ebusd` a prioritással fordítottan arányos gyakorisággal kérdez le:

| Prioritás | Regiszterek | Tipikus frissülés |
|---|---|---|
| `r1` | nyomás, visszatérő hőm., láng, ventilátor, váltószelep, kazánállapot, lángteljesítmény (2026-09-14 óta) | ~3–4 perc |
| `r2` | kazánmoduláció | ~5–6 perc |
| `r3` | üzemórák, ciklusszámlálók, utolsó hiba | ~10 perc |
| `r9` | statikus konfiguráció (teljesítményhatárok, PWM, típusok) | ~30 perc |

Egy teljes első kör az indulás után nagyjából 10 perc.

## MQTT-integráció (`mqtt-hassio.cfg`)

Az `ebusd` a Home Assistant MQTT Discovery formátumában publikál. A leképezést a
`mqtt-hassio.cfg` írja le: mezőtípus, név és mértékegység alapján dönt az entitás
típusáról, eszközosztályáról és állapotosztályáról.

### Javítás: a `pct` mezők leképezése

A `type_switch-number` lista sorrendfüggő, és a `power` minta megelőzte a `pct$`
mintát. Emiatt minden `*_power_pct` nevű mező `device_class: power` és
`unit_of_measurement: pct` párral került ki, amit a Home Assistant érvénytelenként
eldob — az öt érintett entitás egyáltalán nem jött létre. A `pump_max_pwm` (szintén
`pct`, de a nevében nincs „power”) helyesen működött, ez vezetett a hiba
felismeréséhez.

Megoldás: a `pct$` sor a lista elejére került.

```
type_switch-number =
    sensor,,measurement, = pct$        ← ide került
    sensor,temperature,measurement = temp|,°C$
    …
```

### Szűrés: hibanapló-slotok

A `filter-non-name = ^error_slot_` sor megakadályozza, hogy a kilenc hozzáadott
hibanapló-slot entitásokat hozzon létre a Home Assistantban. A napló így
`ebusctl`-lel bármikor olvasható, de nem terheli az entitáslistát.

### Meg nem oldott korlát

A mértékegység nélküli számlálók (`flame_lift_offs`, `ignition_cycles`,
`*_cycles`) nem kapnak `state_class`-t, ezért nincs hosszú távú statisztikájuk. A
`type_switch-number` listát nem sikerült úgy bővíteni, hogy ezekre illeszkedjen (sem
`*lift_offs,$`, sem `lift_offs,$` mintával). A hiányt a Home Assistant oldalán,
template szenzorokkal pótoltuk — lásd
[Home Assistant integráció](home-assistant-integracio.md).

A módosítás leírása: [`../../ebusd/NOTICE.md`](../../ebusd/NOTICE.md).

## Hasznos parancsok

```
docker exec ebusd-ariston ebusctl info                 # verzió, busz, lekérdezés
docker exec ebusd-ariston ebusctl find -c boiler       # ismert értékek
docker exec ebusd-ariston ebusctl read -m 0 -c boiler <név>   # friss olvasás
docker exec ebusd-ariston ebusctl grab result all      # látott telegramok
docker exec ebusd-ariston ebusctl raw                  # nyers naplózás ki/be
docker exec ebusd-ariston ebusctl log bus debug        # naplószint futásidőben
```

A `ebusctl hex` (tetszőleges telegram küldése) **nincs engedélyezve**; bekapcsolása
`--enablehex` kapcsolót igényelne, ami tetszőleges buszírást is megnyitna.

## Lásd még

* [Busz-topológia](busz-topologia.md)
* [Home Assistant integráció](home-assistant-integracio.md)
* [Módszertan](modszertan.md)
