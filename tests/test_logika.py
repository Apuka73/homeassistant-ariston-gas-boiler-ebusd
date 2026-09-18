"""Egységtesztek a VALÓDI számítási logikára.

A tesztek a `custom_components/ariston_ebus/calculations.py` és `const.py` moduljait
importálják — ugyanazt a kódot, amit az integráció futás közben használ. Ezért ha a
koordinátor számítása elromlik, ezek a tesztek is elbuknak. (Korábban a tesztek a logika
másolatát ellenőrizték, ami pont ezt a védelmet nem adta meg.)

Home Assistant nem kell hozzá:

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import re
import sys
import types
import unittest
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]
INTEGRACIO = GYOKER / "custom_components" / "ariston_ebus"


def _betolt(nev: str) -> types.ModuleType:
    """Betölti az integráció egy moduljá­t Home Assistant nélkül.

    Az integráció `__init__.py`-ja importálná a Home Assistantot, ezért nem a csomagot
    töltjük be, hanem egy könnyű helyettesítő csomagot építünk, amiben a relatív importok
    (`from .const import ...`) is működnek.
    """
    if "ariston_ebus_teszt" not in sys.modules:
        csomag = types.ModuleType("ariston_ebus_teszt")
        csomag.__path__ = [str(INTEGRACIO)]
        sys.modules["ariston_ebus_teszt"] = csomag
    teljes = f"ariston_ebus_teszt.{nev}"
    if teljes not in sys.modules:
        spec = importlib.util.spec_from_file_location(teljes, INTEGRACIO / f"{nev}.py")
        modul = importlib.util.module_from_spec(spec)
        sys.modules[teljes] = modul
        spec.loader.exec_module(modul)
    return sys.modules[teljes]


const = _betolt("const")
szam = _betolt("calculations")


class HibanaploTeszt(unittest.TestCase):
    """A 10 mélységű, léptetett hibanapló csúszás-felismerése."""

    ALAP = ["5P1", "501", "5P2", "5P1", "5P3", "5P3", "5P3", "5P3", "501", "5P2"]

    def test_nincs_valtozas(self) -> None:
        """Változatlan napló: nincs új bejegyzés."""
        self.assertEqual(szam.hibanaplo_csuszas(self.ALAP, list(self.ALAP)), 0)

    def test_egy_uj_bejegyzes(self) -> None:
        """Egy új hiba: a napló eggyel lejjebb csúszik."""
        self.assertEqual(szam.hibanaplo_csuszas(self.ALAP, ["604"] + self.ALAP[:-1]), 1)

    def test_ket_uj_bejegyzes(self) -> None:
        """Két új hiba egyszerre."""
        self.assertEqual(szam.hibanaplo_csuszas(self.ALAP, ["604", "612"] + self.ALAP[:-2]), 2)

    def test_ismetlodo_kod_is_uj(self) -> None:
        """Ugyanaz a kód ismét — a csúszás miatt ez is új bejegyzésnek látszik.

        Ez a lényegi eset: enélkül az ismétlődő gyújtási hibák láthatatlanok lennének.
        """
        self.assertEqual(szam.hibanaplo_csuszas(self.ALAP, ["5P1"] + self.ALAP[:-1]), 1)

    def test_teljes_csere(self) -> None:
        """Ha semmi nem illeszkedik, minden bejegyzés újnak számít."""
        uj = ["101", "104", "108", "109", "309", "501", "502", "504", "604", "607"]
        self.assertEqual(szam.hibanaplo_csuszas(self.ALAP, uj), 10)

    def test_ures_elozmeny(self) -> None:
        """Első kiolvasáskor nincs mihez viszonyítani."""
        self.assertEqual(szam.hibanaplo_csuszas([], self.ALAP), 0)


class KapuzasTeszt(unittest.TestCase):
    """A lángteljesítmény kapuzása a kazán állapota alapján."""

    def test_keszenletben_nulla(self) -> None:
        """Készenlétben a beragadt kW-érték nem számít gázfogyasztásnak."""
        self.assertEqual(szam.kapuzott_teljesitmeny("standby", 7.6), 0.0)

    def test_keringetesben_nulla(self) -> None:
        """Utókeringetés alatt sem ég láng."""
        self.assertEqual(szam.kapuzott_teljesitmeny("circulating", 7.6), 0.0)

    def test_futesben_atmegy(self) -> None:
        """Fűtés közben a nyers érték érvényes."""
        self.assertEqual(szam.kapuzott_teljesitmeny("heating", 7.6), 7.6)

    def test_szokozos_allapot_is_illeszkedik(self) -> None:
        """Az ebusd szóközös értékeit is fel kell ismerni („no flame”)."""
        self.assertEqual(szam.kapuzott_teljesitmeny("no flame", 5.0), 0.0)

    def test_hianyzo_ertek(self) -> None:
        """Ha nincs teljesítményadat, nem találunk ki nullát sem."""
        self.assertIsNone(szam.kapuzott_teljesitmeny("heating", None))


class EnergiaTeszt(unittest.TestCase):
    """A hőenergia trapéz-integrálja."""

    def test_allando_teljesitmeny(self) -> None:
        """10 kW egy percen át = 10 × 60/3600 = 0,1667 kWh."""
        self.assertAlmostEqual(szam.trapez_novekmeny(10.0, 10.0, 60, 600), 10 / 60, places=6)

    def test_felfuto_el(self) -> None:
        """0-ról 10 kW-ra egy perc alatt: a trapéz az átlaggal (5 kW) számol."""
        self.assertAlmostEqual(szam.trapez_novekmeny(0.0, 10.0, 60, 600), 5 / 60, places=6)

    def test_teljes_ora_darabokban(self) -> None:
        """Hatvan egyperces lépés 10 kW-on összesen 10 kWh — ahogy a koordinátor is számol."""
        ossz = sum(szam.trapez_novekmeny(10.0, 10.0, 60, 600) for _ in range(60))
        self.assertAlmostEqual(ossz, 10.0, places=6)

    def test_hosszu_kimaradas_nem_szamol(self) -> None:
        """A megengedettnél hosszabb szünet után nem találunk ki fogyasztást."""
        self.assertEqual(szam.trapez_novekmeny(10.0, 10.0, 7200, 600), 0.0)

    def test_elso_meres_utan_nincs_novekmeny(self) -> None:
        """Előző érték nélkül (például HA-indulás, buszjel visszatérése) nincs mit integrálni."""
        self.assertEqual(szam.trapez_novekmeny(None, 10.0, 60, 600), 0.0)


class GazTeszt(unittest.TestCase):
    """A gázbecslés és a kalibráció."""

    def test_alap_szamitas(self) -> None:
        """100 kWh × 0,118 = 11,8 m³."""
        a = szam.GazAllapot(szorzo=0.118)
        self.assertAlmostEqual(szam.gaz_mennyiseg(a, 100.0), 11.8, places=3)

    def test_szorzovaltas_nem_ugrik(self) -> None:
        """Szorzóváltáskor a már elszámolt mennyiség nem változhat.

        Ez a `total_increasing` szenzor miatt kritikus: lefelé lépő értéket a Home Assistant
        mérőóra-cserének hinne, és hamis fogyasztást könyvelne el.
        """
        a = szam.GazAllapot(szorzo=0.118)
        elotte = szam.gaz_mennyiseg(a, 100.0)
        b = szam.uj_szorzo(a, 100.0, 0.09)  # lefelé módosítunk
        self.assertAlmostEqual(szam.gaz_mennyiseg(b, 100.0), elotte, places=3)

    def test_szorzovaltas_utan_uj_szorzoval_no(self) -> None:
        """A váltás után elégetett hő már az új szorzóval számol."""
        a = szam.uj_szorzo(szam.GazAllapot(szorzo=0.118), 100.0, 0.13)
        self.assertAlmostEqual(szam.gaz_mennyiseg(a, 200.0), 11.8 + 13.0, places=3)

    def test_monoton_novekedes(self) -> None:
        """Több szorzóváltás után sem csökkenhet az összeg."""
        a = szam.GazAllapot(szorzo=0.118)
        elozo, energia = 0.0, 0.0
        for szorzo in (0.13, 0.08, 0.2, 0.05):
            energia += 50
            a = szam.uj_szorzo(a, energia, szorzo)
            mostani = szam.gaz_mennyiseg(a, energia)
            self.assertGreaterEqual(mostani + 1e-9, elozo)
            elozo = mostani

    def test_szorzo_hatarolva(self) -> None:
        """A hihetetlen szorzót a tartomány szélére vágjuk."""
        a = szam.uj_szorzo(szam.GazAllapot(szorzo=0.118), 10.0, 99.0)
        self.assertEqual(a.szorzo, const.MAX_GAS_FACTOR)

    def test_kalibracio_keves_adatbol_nincs(self) -> None:
        """20 kWh alatt a bemérés még megbízhatatlan."""
        self.assertIsNone(szam.kalibralt_szorzo(1000.0, 0.0, 1001.0, 10.0))

    def test_kalibracio_eleg_adatbol(self) -> None:
        """100 kWh alatt 12 m³ fogyott → 0,12 m³/kWh."""
        self.assertAlmostEqual(szam.kalibralt_szorzo(1000.0, 0.0, 1012.0, 100.0), 0.12, places=4)

    def test_kalibracio_hihetetlen_erteket_eldob(self) -> None:
        """A tartományon kívüli eredményt nem vesszük át."""
        self.assertIsNone(szam.kalibralt_szorzo(1000.0, 0.0, 1100.0, 100.0))


class ErtekOlvasasTeszt(unittest.TestCase):
    """Az ebusd válaszok értelmezése."""

    def test_szentinel_kiszurve(self) -> None:
        """Bekötetlen érzékelőnél (0x7FFF → 3276,7 °C) nincs mérés."""
        self.assertIsNone(szam.szamma("3276.7"))

    def test_szam_beolvasas(self) -> None:
        """Rendes érték átmegy."""
        self.assertEqual(szam.szamma("21.9"), 21.9)

    def test_tobb_mezos_valasz(self) -> None:
        """A pontosvesszős válaszból a kért mező jön."""
        self.assertEqual(szam.mezo("standby;off;off;off", 0), "standby")
        self.assertEqual(szam.mezo("standby;off;on;off", 2), "on")
        self.assertIsNone(szam.mezo("standby", 3))

    def test_ertelmezhetetlen_ertek(self) -> None:
        """Szöveges válaszból nem csinálunk számot."""
        self.assertIsNone(szam.szamma("no data stored"))


class DiagnosztikaTeszt(unittest.TestCase):
    """Lángleszakadás-arány."""

    def test_arany(self) -> None:
        """39 leszakadás / 9920 gyújtás = 3,93 ‰ (a referenciarendszer értéke)."""
        self.assertAlmostEqual(szam.langleszakadas_arany(39, 9920), 3.93, places=2)

    def test_nulla_gyujtas(self) -> None:
        """Nulla gyújtásnál nincs értelmes arány (és nincs osztás nullával)."""
        self.assertIsNone(szam.langleszakadas_arany(5, 0))


class KatalogusTeszt(unittest.TestCase):
    """A katalógus belső ellentmondás-mentessége."""

    def test_egyedi_kulcsok(self) -> None:
        """Két entitásnak nem lehet ugyanaz a kulcsa (ütköznének az egyedi azonosítók)."""
        kulcsok = [e.key for e in const.BOILER_SENSORS + const.ENERGYMGR_SENSORS]
        kulcsok += [e.key for e in const.BOILER_BINARY_SENSORS]
        self.assertEqual(len(kulcsok), len(set(kulcsok)))

    def test_felsorolas_kulcsok_ervenyesek(self) -> None:
        """A Home Assistant a felsorolás-kulcsokban csak [a-z0-9_-] karaktereket enged."""
        minta = re.compile(r"^[a-z0-9]([a-z0-9_-]*[a-z0-9])?$")
        for ertek in const.BOILER_STATUS_OPTIONS + const.DIVERTER_VALVE_OPTIONS:
            self.assertRegex(ertek, minta, f"érvénytelen felsorolás-kulcs: {ertek}")

    def test_hibakod_szotarak_egyeznek(self) -> None:
        """A magyar és az angol hibakód-szótár ugyanazokat a kódokat ismeri."""
        self.assertEqual(set(const.ERROR_DESCRIPTIONS_HU), set(const.ERROR_DESCRIPTIONS_EN))

    def test_gazszorzo_hatarok(self) -> None:
        """Az alapértelmezett szorzó a megengedett tartományon belül van."""
        self.assertLessEqual(const.MIN_GAS_FACTOR, const.DEFAULT_GAS_FACTOR)
        self.assertLessEqual(const.DEFAULT_GAS_FACTOR, const.MAX_GAS_FACTOR)

    def test_forditasok_lefedik_a_katalogust(self) -> None:
        """Minden entitáskulcshoz van magyar és angol név."""
        import json

        alap = GYOKER / "custom_components" / "ariston_ebus"
        for fajl in ("strings.json", "translations/en.json", "translations/hu.json"):
            d = json.loads((alap / fajl).read_text(encoding="utf-8"))
            szenzorok = d["entity"]["sensor"]
            binarisok = d["entity"]["binary_sensor"]
            for e in const.BOILER_SENSORS + const.ENERGYMGR_SENSORS:
                self.assertIn(e.key, szenzorok, f"{fajl}: hiányzó fordítás — {e.key}")
            for e in const.BOILER_BINARY_SENSORS:
                self.assertIn(e.key, binarisok, f"{fajl}: hiányzó fordítás — {e.key}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
