# Változásnapló

A verziószámozás a [szemantikus verziózást](https://semver.org/lang/hu/) követi.

## [0.1.0] — 2026-09-18

Első nyilvános kiadás. Az integráció **kizárólag olvas**: egyetlen íróparancsot sem küld a buszra.

### Amit tud

* **Kazán működése:** állapot (készenlét / fűtés / melegvíz / keringetés…), láng, moduláció,
  ventilátor-fordulat, visszatérő vízhőmérséklet, víznyomás, váltószelep, zóna-fűtésigény.
* **Gázfogyasztás-becslés:** a lángteljesítmény trapéz-integrálja adja a leadott hőt (kWh),
  abból egy kalibrálható szorzóval a gáztérfogat (m³). A `set_gas_meter_reading` szolgáltatással
  a fizikai gázóráról bemérhető a szorzó.
* **Diagnosztika:** égőórák, gyújtási ciklusok, lángleszakadások, és a lángleszakadás-arány (‰).
* **Hibanapló:** a kazán 10 mélységű naplója magyar magyarázattal, és azzal az időponttal,
  amikor egy bejegyzés először megjelent (a kazán maga nem tárol időbélyeget).
* **Busz állapota:** az eBUS jel megléte — ha elmegy, minden érték beragadna.

### Fontos megoldások

* **Kapuzott lángteljesítmény:** a kazán gyors broadcast állapota alapján a teljesítmény nulla,
  amikor nem éghet láng. E nélkül a beragadt kW-érték nem létező gázt integrálna (mért hiba: −8,6%).
* **Buszjel-védelem:** jelvesztéskor az integrálás megáll és a horgony törlődik, így a jel
  visszatérésekor sem keletkezik hamis lépés.
* **Bázispontos gázszámítás:** a kalibrációs szorzó módosítása nem értékeli át visszamenőleg a
  fogyasztást, így a `total_increasing` szenzor nem ugrik (lefelé lépő értéket a Home Assistant
  mérőóra-cserének hinne).
* **Adaptív lekérdezés:** ami nem válaszol, azt az integráció megjegyzi, és 6 órán át csak a
  gyorsítótárból nézi — kazán-only rendszeren 185 regiszter fut időtúllépésre.
* **Bekötetlen érzékelő felismerése:** a 0x7FFF (3276,7 °C) szentinel nem kerül be mérésként.

### Az ebusd konfigurációban

A mellékelt `ariston.csv` az upstream v2.6-ból indul, és 107 sorban tér el tőle: lekérdezési
prioritások 38 üzenetre, a 10 mélységű hibanapló, a `boiler_status` szétválasztása, és a
`boiler_life_time` mértékegységének javítása (**óra**, nem perc — méréssel igazolva).
Részletek: [`ebusd/NOTICE.md`](ebusd/NOTICE.md).

### Ismert korlátok

* Csak **Ariston Cares S System 24**-en van validálva
  ([`docs/tamogatott-keszulekek.md`](docs/tamogatott-keszulekek.md)).
* A gázbecslés **csak a kazán** fogyasztását fedi; más gázfogyasztó (tűzhely, gázbojler) nem
  szerepel benne.
* A hibakódok sorszámozása készülékfüggő; más kazánon a szöveges magyarázat eltérhet.
* Vezérlés nincs (célhőmérséklet-állítás, be/ki kapcsolás) — szándékosan.
