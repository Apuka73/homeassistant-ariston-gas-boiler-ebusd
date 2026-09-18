"""Tiszta számítási logika, Home Assistant nélkül.

Ez a modul szándékosan **nem importál Home Assistantot**: így egységtesztekkel közvetlenül
ellenőrizhető ugyanaz a kód, amit az integráció futás közben használ. A koordinátor ezeket a
függvényeket hívja, tehát a tesztek a valódi működést fedik le, nem egy másolatát.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .const import (
    MAX_GAS_FACTOR,
    MIN_CALIBRATION_ENERGY_KWH,
    MIN_GAS_FACTOR,
    SENTINEL_TEMPERATURE,
    STATUS_NO_FLAME,
    normalize_option,
)


def mezo(ertek: str | None, index: int) -> str | None:
    """Egy pontosvesszővel tagolt ebusd válasz adott mezője."""
    if ertek is None:
        return None
    mezok = ertek.split(";")
    if index >= len(mezok):
        return None
    kimenet = mezok[index].strip()
    return kimenet or None


def szamma(ertek: str | None) -> float | None:
    """Az ebusd válasz első mezőjét számmá alakítja, a szentinel értékek kiszűrésével.

    Bekötetlen érzékelőnél az Ariston 0x7FFF-et küld, amiből az ebusd 3276,7 °C-ot csinál.
    Ez nem mérés, hanem a „nincs érzékelő” jelzése, ezért ``None``-t adunk vissza.
    """
    m = mezo(ertek, 0)
    if m is None:
        return None
    try:
        szam = float(m)
    except ValueError:
        return None
    if abs(szam - SENTINEL_TEMPERATURE) < 0.05:
        return None
    return szam


def kapuzott_teljesitmeny(allapot: str | None, nyers: float | None) -> float | None:
    """A lángteljesítmény nullázása, ha a kazán állapota szerint nem éghet láng.

    A kazán állapotát broadcast üzenet hozza (másodpercek), a teljesítmény-regisztert viszont
    lekérdezés (percek). A láng kialvása után a beragadt kW-érték nem létező gázt integrálna.
    """
    if nyers is None:
        return None
    if allapot is not None and normalize_option(allapot) in STATUS_NO_FLAME:
        return 0.0
    return nyers


def trapez_novekmeny(
    elozo_teljesitmeny: float | None,
    uj_teljesitmeny: float,
    eltelt_mp: float,
    max_hezag_mp: float,
) -> float:
    """Két mérés közti energia (kWh) trapéz-módszerrel.

    ``max_hezag_mp``-nél hosszabb kimaradás után nulla a növekmény: ilyenkor nem tudjuk,
    mi történt közben (például leállt a Home Assistant vagy elveszett a buszjel), és inkább
    keveset számolunk, mint kitaláltat.
    """
    if elozo_teljesitmeny is None or eltelt_mp <= 0 or eltelt_mp > max_hezag_mp:
        return 0.0
    return (elozo_teljesitmeny + uj_teljesitmeny) / 2 * eltelt_mp / 3600


def hibanaplo_csuszas(regi: list[str], uj: list[str]) -> int:
    """Hány új bejegyzés került a kazán hibanaplójának elejére.

    A kazán léptetett, 10 mélységű naplót tart, és **nem tárol időbélyeget**. Ha a napló k
    bejegyzéssel lejjebb csúszott (``uj[k:] == regi[:len(uj)-k]``), akkor az első k bejegyzés új.
    Így az ugyanazzal a kóddal ismétlődő hibák is felismerhetők.
    """
    if not regi or not uj or uj == regi:
        return 0
    for k in range(1, len(uj)):
        if uj[k:] == regi[: len(uj) - k]:
            return k
    return len(uj)


@dataclass
class GazAllapot:
    """A gázbecslés tartós állapota.

    A ``bazis_*`` mezők miatt a szorzó megváltoztatása **nem értékeli át visszamenőleg** a
    fogyasztást: a már elszámolt gázmennyiség megmarad, és csak az ezután elégetett hő
    számolódik az új szorzóval. Enélkül a ``total_increasing`` szenzor ugrana — lefelé
    változó szorzónál a Home Assistant mérőóra-cserének hinné, és hamis fogyasztást könyvelne.
    """

    szorzo: float
    bazis_gaz: float = 0.0
    """Az eddig elszámolt gáz (m³) a legutóbbi szorzóváltás pillanatában."""

    bazis_energia: float = 0.0
    """A hőenergia (kWh) ugyanabban a pillanatban."""

    bemert: bool = False
    """Igaz, ha a szorzót valódi gázóra-leolvasásból mértük be."""


def gaz_mennyiseg(allapot: GazAllapot, energia: float) -> float:
    """Az összes elégetett gáz (m³) a bázispont óta érvényes szorzóval."""
    return round(allapot.bazis_gaz + max(energia - allapot.bazis_energia, 0.0) * allapot.szorzo, 3)


def uj_szorzo(allapot: GazAllapot, energia: float, szorzo: float) -> GazAllapot:
    """Szorzóváltás úgy, hogy a már elszámolt mennyiség ne változzon."""
    hatarolt = max(MIN_GAS_FACTOR, min(MAX_GAS_FACTOR, szorzo))
    return GazAllapot(
        szorzo=hatarolt,
        bazis_gaz=gaz_mennyiseg(allapot, energia),
        bazis_energia=energia,
        bemert=allapot.bemert,
    )


def kalibralt_szorzo(
    kezdo_allas: float, kezdo_energia: float, mostani_allas: float, mostani_energia: float
) -> float | None:
    """Gázóra-leolvasásokból számított m³/kWh szorzó, vagy ``None``, ha még nem megbízható.

    A kiinduló ponthoz viszonyítunk, nem az előző leolvasáshoz: így minden újabb leolvasás
    pontosít, és egy rövid, kevés fogyasztású időszak nem rontja el a szorzót.
    """
    d_gaz = mostani_allas - kezdo_allas
    d_energia = mostani_energia - kezdo_energia
    if d_energia < MIN_CALIBRATION_ENERGY_KWH or d_gaz <= 0:
        return None
    szorzo = round(d_gaz / d_energia, 4)
    if not MIN_GAS_FACTOR <= szorzo <= MAX_GAS_FACTOR:
        return None
    return szorzo


def langleszakadas_arany(leszakadas: float | None, gyujtas: float | None) -> float | None:
    """Hány lángleszakadás jut 1000 gyújtásra.

    Időbélyeg nélkül az abszolút szám keveset mond; a romló arány viszont árulkodó.
    """
    if leszakadas is None or not gyujtas:
        return None
    return round(leszakadas / gyujtas * 1000, 2)
