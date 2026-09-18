# Források

## Szoftver

| Projekt | Leírás |
|---|---|
| [john30/ebusd](https://github.com/john30/ebusd) | Az eBUS démon. A használt verzió: 26.1.26.1. |
| [ebusd wiki – Hardware](https://github.com/john30/ebusd/wiki/6.-Hardware) | Busz-illesztők, potenciométer-beállítás. |

## BridgeNet konfigurációk és visszafejtés

| Forrás | Felhasználás |
|---|---|
| [wrongisthenewright/ebusd-configuration-ariston-bridgenet](https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet) | A telepítésen használt `ariston.csv` alapja (v2.6). Innen származik a regiszterazonosítók és a zóna-elnevezések nagy része. |
| [kredow/ariston-ebus-prococol](https://github.com/kredow/ariston-ebus-prococol) | A `ariston_register_map.csv` regisztertérkép. Innen származik a PBSB-parancsok listája, valamint a `0x9101`–`0x9107` (`heat_request_z1`–`z7`), `0x9761`–`0x9767`, `0x190c` és `0x4776` azonosítása. |
| [ysard/ebusd_configuration_chaffoteaux_bridgenet](https://github.com/ysard/ebusd_configuration_chaffoteaux_bridgenet) | Chaffoteaux Mira C Green konfiguráció. Innen származik a `2001` parancs érték+min+max szerkezetének leírása és a **10 mélységű hibanapló** (`0400`–`0409`) definíciója. |
| [john30/ebusd – Discussion #880](https://github.com/john30/ebusd/discussions/880) | „Decoding strange broadcast messages for Ariston Ebus”. Megerősíti a `xxfe2010` telegramok `(azonosító, érték)` páros szerkezetét. |
| [elektroda.com – Exploring Ariston BUS BridgeNet Protocol](https://www.elektroda.com/rtvforum/topic3415927.html) | Háttéranyag a protokoll általános felépítéséről. |

## Gázfogyasztás és teljesítmény (2026-09-14-i kutatás)

| Forrás | Felhasználás |
|---|---|
| [wrongisthenewright #24](https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet/issues/24), [ysard #11](https://github.com/ysard/ebusd_configuration_chaffoteaux_bridgenet/issues/11) | A `6847` (`0x4768`) regiszter vitája; a karbantartó a kezelőegység szervizmenüjével vetette össze: valós idejű gázteljesítmény, kW /10. A komw CSV ugyanezt `dhw_flowmeter`-nek nevezi. |
| [wrongisthenewright #20 – Add gas consumption](https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet/issues/20), [#29](https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet/issues/29) | Gázfogyasztás-számlálót nem ismernek; a költségszámítás (`642b` gázár, `652b`/`662b` áramár, `682b` arány) az Energy Manager feladata, amely ezen a rendszeren nincs. |
| [ysard #15](https://github.com/ysard/ebusd_configuration_chaffoteaux_bridgenet/issues/15), [ysard mira_c_green.csv](https://github.com/ysard/ebusd_configuration_chaffoteaux_bridgenet) | `0x46d7` = `dhw_comfort_mode_status` (2 = be); `0x46da` = 150 ott is azonosítatlan. |
| [kredow ariston_register_map.csv](https://github.com/kredow/ariston-ebus-prococol/blob/main/ariston_register_map.csv) | A 8.2.x szervizmenü-kódok; „gas power ?” és „flame power ?” jelöltek (`c104`). |
| [komw/ariston-bus-bridgenet-ebusd](https://github.com/komw/ariston-bus-bridgenet-ebusd) (CSV, [#12](https://github.com/komw/ariston-bus-bridgenet-ebusd/issues/12)) | Eltérő elnevezések ugyanazokra az azonosítókra. |
| [HA community – Ariston group integration via ebusd, #194](https://community.home-assistant.io/t/ariston-group-integration-via-ebusd/738887/194) | A `c404` moduláció csak rendszerszabályzós (Sensys/Cube) telepítésen ad értéket. |
| [Ariston Clas ONE R kézikönyv, 8. menü](https://library.ariston.co.uk/clas-one-r-installation-manual/65488087/40), [ONE+ sorozat szervizmenü](https://library.ariston.co.uk/one-series-installation-amp-service-manual/68650958/44) | A 8.2.8 „Gas Power, kW”, 8.2.2 ventilátor-fordulat, 8.3.1/8.3.2 előremenő/visszatérő hőmérséklet, 8.1.0/8.1.1 égőórák menüpontjai. |
| [fustom/python-ariston-api](https://github.com/fustom/python-ariston-api), [ariston-remotethermo-home-assistant-v3 #232](https://github.com/fustom/ariston-remotethermo-home-assistant-v3/issues/232) | Az Ariston NET felhő `CENTRAL_HEATING_GAS` / `DOMESTIC_HOT_WATER_GAS` fogyasztási típusai; a gáz egységét és árát a felhasználó adja meg — a számítás a felhőben/átjáróban történik, busz-regiszterhez nem köthető. |

## A források korlátai

Egyik hivatkozott forrás sem gyártói dokumentáció — mind közösségi visszafejtés
eredménye, gyakran bizonytalanságot jelző elnevezésekkel (`temp_Z1?`,
`heating in progress?`, `gas power?`). A wiki ezeket külön forrásként jelöli, és nem
kezeli azonos súlyúnak a mérésekkel igazolt állításokkal — lásd
[Módszertan](modszertan.md).

Egyik forrás sem dokumentál olyan regisztert, amely a kazán kereskedelmi típusnevét
vagy termékkódját adná vissza.

## Helyi mérési adatok

A wiki adattáblái 2026-08-16-án és 2026-09-14-én készült mérési kimenetekből generáltak:
a 223 olvasható regiszter végigolvasásából, az `ebusctl grab result all` kimenetéből
(47 telegramtípus), valamint a próbafűtés nyers busznaplójából.

**Ezek a nyers fájlok nem részei a repónak** — a belőlük kinyert eredmény a
[Broadcast regisztertérkép](broadcast-regiszterterkep.md) és az
[Olvasható regiszterek](olvashato-regiszterek.md) tábláiban van. A mérések
megismételhetők; a módszer a [Módszertan](modszertan.md) szócikkben.

## Lásd még

* [Módszertan](modszertan.md)
* [Ariston BridgeNet protokoll](ariston-bridgenet-protokoll.md)
