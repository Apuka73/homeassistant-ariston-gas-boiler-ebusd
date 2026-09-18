"""Adatgyűjtő koordinátor: ebusd lekérdezés, gázbecslés és hibanapló-követés."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    BOILER_BINARY_SENSORS,
    BOILER_SENSORS,
    CONF_CIRCUIT_BOILER,
    CONF_CIRCUIT_ENERGYMGR,
    DEFAULT_GAS_FACTOR,
    DOMAIN,
    ENERGYMGR_SENSORS,
    ERROR_LOG_INTERVAL,
    ERROR_LOG_MESSAGES,
    EbusEntity,
)
from .calculations import (
    GazAllapot,
    gaz_mennyiseg,
    hibanaplo_csuszas,
    kalibralt_szorzo,
    kapuzott_teljesitmeny,
    langleszakadas_arany,
    mezo,
    szamma,
    trapez_novekmeny,
    uj_szorzo,
)
from .ebusd import EbusdClient, EbusdError, EbusdInfo

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
MAX_INTEGRATION_GAP = timedelta(minutes=10)
"""Ennél hosszabb kimaradás után nem integrálunk: a láng állapota közben ismeretlen volt."""

MAX_READ_FAILURES = 2
"""Ennyi sikertelen olvasás után az üzenetet már csak a gyorsítótárból nézzük."""

READ_BACKOFF = timedelta(hours=6)
"""Ennyi idő múlva újra megpróbáljuk a nem válaszoló üzeneteket (hátha bővült a rendszer)."""

SAVE_INTERVAL = timedelta(minutes=5)
"""Ilyen sűrűn mentjük lemezre a hőenergiát és a kalibrációt."""


@dataclass
class ErrorEntry:
    """Egy hibanapló-bejegyzés."""

    code: str
    first_seen: str | None = None
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        """Szótárrá alakítja (tároláshoz és entitás-attribútumnak)."""
        return {"code": self.code, "first_seen": self.first_seen, "note": self.note}

    @classmethod
    def from_dict(cls, adat: dict[str, Any]) -> ErrorEntry:
        """Tárolt szótárból állítja vissza."""
        return cls(
            code=adat.get("code", ""),
            first_seen=adat.get("first_seen"),
            note=adat.get("note", ""),
        )


@dataclass
class AristonData:
    """A koordinátor egy körének eredménye."""

    values: dict[str, str] = field(default_factory=dict)
    """``kör/üzenet`` → nyers ebusd érték."""

    info: EbusdInfo | None = None
    flame_power: float | None = None
    flame_power_gated: float | None = None
    heat_energy: float = 0.0
    gas_total: float | None = None
    gas_meter_estimate: float | None = None
    gas_since_reading: float | None = None
    gas_factor: float = DEFAULT_GAS_FACTOR
    gas_factor_calibrated: bool = False
    flame_lift_ratio: float | None = None
    errors: list[ErrorEntry] = field(default_factory=list)
    errors_updated: datetime | None = None


class AristonEbusCoordinator(DataUpdateCoordinator[AristonData]):
    """Összefogja az ebusd lekérdezést, a származtatott értékeket és a tartós állapotot."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: EbusdClient,
        scan_interval: int,
        gas_estimation: bool,
        error_log: bool,
    ) -> None:
        """Létrehozza a koordinátort és a tartós tárolót."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )
        self.client = client
        self.gas_estimation = gas_estimation
        self.error_log = error_log
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self._state: dict[str, Any] = {}
        self._last_refresh: dict[str, datetime] = {}
        self._read_failures: dict[str, int] = {}
        self._skip_until: dict[str, datetime] = {}
        self._last_save: datetime | None = None
        self._last_power_time: datetime | None = None
        self._last_power: float | None = None
        self._errors: list[ErrorEntry] = []
        self._errors_updated: datetime | None = None
        self._circuits: set[str] = set()

    # -- tartós állapot --------------------------------------------------------

    async def async_load_state(self) -> None:
        """Betölti a korábbi hőenergiát, kalibrációt és hibanaplót."""
        self._state = await self._store.async_load() or {}
        self._migrate_state()
        self._errors = [ErrorEntry.from_dict(x) for x in self._state.get("errors", [])]
        if (idopont := self._state.get("errors_updated")) is not None:
            self._errors_updated = dt_util.parse_datetime(idopont)

    def _migrate_state(self) -> None:
        """Régi tárolt állapot átalakítása a bázispontos gázszámításra.

        A korai változat a gázmennyiséget mindig a teljes hőenergiából számolta, és a
        leolvasáshoz a hőenergiát tárolta (``ref_energy``). Az új séma a már elszámolt
        gázmennyiséget rögzíti, hogy a szorzó módosítása ne értékelje át visszamenőleg a
        fogyasztást. Frissítéskor ezt egyszer át kell számolni, különben a „Gázóra becsült
        állása” szenzor ismeretlenné válna.
        """
        if "ref_energy" in self._state and "ref_gas_total" not in self._state:
            szorzo = float(self._state.get("gas_factor") or DEFAULT_GAS_FACTOR)
            energia = float(self._state.get("heat_energy", 0.0))
            ref_energia = float(self._state.get("ref_energy") or 0.0)
            # A régi séma szerinti összeg a váltás pillanatában, hogy ne ugorjon a szenzor.
            self._state["gas_base_volume"] = round(energia * szorzo, 6)
            self._state["gas_base_energy"] = energia
            self._state["ref_gas_total"] = round(ref_energia * szorzo, 6)
            _LOGGER.debug("A gázbecslés tárolt állapota átalakítva a bázispontos sémára")

    async def _async_save_state(self) -> None:
        self._state["errors"] = [e.as_dict() for e in self._errors]
        self._state["errors_updated"] = (
            self._errors_updated.isoformat() if self._errors_updated else None
        )
        await self._store.async_save(self._state)

    def _gas_state(self) -> GazAllapot:
        """A gázbecslés állapota a tárolóból (szorzó + bázispont)."""
        return GazAllapot(
            szorzo=float(self._state.get("gas_factor") or DEFAULT_GAS_FACTOR),
            bazis_gaz=float(self._state.get("gas_base_volume", 0.0)),
            bazis_energia=float(self._state.get("gas_base_energy", 0.0)),
            bemert=bool(self._state.get("gas_factor_calibrated")),
        )

    def _store_gas_state(self, allapot: GazAllapot) -> None:
        self._state["gas_factor"] = allapot.szorzo
        self._state["gas_base_volume"] = allapot.bazis_gaz
        self._state["gas_base_energy"] = allapot.bazis_energia
        self._state["gas_factor_calibrated"] = allapot.bemert

    @property
    def gas_factor(self) -> float:
        """A jelenleg érvényes m³/kWh szorzó."""
        return self._gas_state().szorzo

    async def async_set_gas_factor(self, ertek: float) -> None:
        """Kézzel beállítja a gázszorzót — a már elszámolt gázmennyiség megmarad."""
        energia = float(self._state.get("heat_energy", 0.0))
        self._store_gas_state(uj_szorzo(self._gas_state(), energia, ertek))
        await self._async_save_state()
        await self.async_request_refresh()

    async def async_set_meter_reading(self, leolvasas: float) -> dict[str, Any]:
        """Valós gázóra-állás rögzítése; ha van elég adat, újraszámolja a szorzót.

        Az eljárás megegyezik a kézi Home Assistant-automatizálással, amiből származik: az első
        leolvasás rögzíti a kiinduló pontot, a későbbiek pedig a kiinduló ponttól mért gáz- és
        hőkülönbségből képzik a szorzót — így minden újabb leolvasás pontosít.

        A szorzó módosítása **nem értékeli át visszamenőleg** a fogyasztást (lásd
        :class:`~.calculations.GazAllapot`), különben a ``total_increasing`` szenzor ugrana.
        """
        energia = float(self._state.get("heat_energy", 0.0))
        allapot = self._gas_state()
        eredmeny: dict[str, Any] = {"calibrated": False}

        start_allas = self._state.get("start_reading")
        start_energia = self._state.get("start_energy")
        if start_allas is None:
            self._state["start_reading"] = leolvasas
            self._state["start_energy"] = energia
            self._state["start_time"] = dt_util.now().isoformat()
        else:
            szorzo = kalibralt_szorzo(
                float(start_allas), float(start_energia or 0.0), leolvasas, energia
            )
            if szorzo is not None:
                allapot = uj_szorzo(allapot, energia, szorzo)
                allapot.bemert = True
                eredmeny = {"calibrated": True, "factor": allapot.szorzo}
            else:
                _LOGGER.debug(
                    "A leolvasásból még nem számolható megbízható gázszorzó "
                    "(kevés elégetett hő vagy hihetetlen érték), a korábbi marad"
                )

        self._store_gas_state(allapot)
        self._state["ref_reading"] = leolvasas
        self._state["ref_gas_total"] = gaz_mennyiseg(allapot, energia)
        self._state["ref_time"] = dt_util.now().isoformat()
        await self._async_save_state()
        await self.async_request_refresh()
        return eredmeny

    # -- lekérdezés ------------------------------------------------------------

    async def _async_update_data(self) -> AristonData:
        try:
            if not self._circuits:
                self._circuits = await self.client.async_circuits()
            info = await self.client.async_info()
            await self._async_refresh_stale()
            ertekek = await self._async_collect_values()
        except EbusdError as err:
            raise UpdateFailed(str(err)) from err

        if self.error_log:
            # A hibanapló 10 külön olvasás, és a legritkábban használt adat. Ha bármelyik
            # elhasal, attól a kazán összes többi értéke még érvényes — ezért külön kezeljük,
            # és hiba esetén megtartjuk a korábbi naplót.
            try:
                await self._async_update_errors()
            except EbusdError as err:
                _LOGGER.debug("A hibanapló olvasása most nem sikerült: %s", err)

        adat = AristonData(values=ertekek, info=info)
        self._compute_flame(adat)
        await self._compute_gas(adat)
        self._compute_diagnostics(adat)
        adat.errors = list(self._errors)
        adat.errors_updated = self._errors_updated
        return adat

    async def _async_refresh_stale(self) -> None:
        """Valódi buszolvasást kér azokra az üzenetekre, amelyek gyorsítótára lejárt.

        Ami nem válaszol, azt megjegyezzük: egy kazán-only rendszeren a hőszivattyús és
        rendszerszabályzós regiszterek lekérdezése mind időtúllépésre fut (alapbeállításnál
        5 másodperc egyenként), ami feleslegesen lassítaná a kört és terhelné a buszt.
        Az ilyen üzenetek értékét ettől még megkapjuk, ha a kazán broadcastban közli őket.
        """
        most = dt_util.utcnow()
        for leiras in self._all_entities():
            if leiras.circuit not in self._circuits:
                continue
            kulcs = f"{leiras.circuit}/{leiras.message}"
            if (szunet := self._skip_until.get(kulcs)) is not None and most < szunet:
                continue
            utolso = self._last_refresh.get(kulcs)
            if utolso is not None and (most - utolso).total_seconds() < leiras.max_age:
                continue
            try:
                ertek = await self.client.async_read(leiras.circuit, leiras.message, leiras.max_age)
            except EbusdError as err:
                ertek = None
                _LOGGER.debug("%s nem olvasható: %s", kulcs, err)
            if ertek is None:
                self._read_failures[kulcs] = self._read_failures.get(kulcs, 0) + 1
                if self._read_failures[kulcs] >= MAX_READ_FAILURES:
                    self._skip_until[kulcs] = most + READ_BACKOFF
                    _LOGGER.debug(
                        "%s nem válaszol, %s-ig csak a gyorsítótárból olvasom",
                        kulcs,
                        self._skip_until[kulcs],
                    )
            else:
                self._read_failures.pop(kulcs, None)
            self._last_refresh[kulcs] = most

    async def _async_collect_values(self) -> dict[str, str]:
        ertekek: dict[str, str] = {}
        for kor in (CONF_CIRCUIT_BOILER, CONF_CIRCUIT_ENERGYMGR):
            if kor not in self._circuits:
                continue
            for nev, ertek in (await self.client.async_find_values(kor)).items():
                ertekek[f"{kor}/{nev}"] = ertek
        return ertekek

    def _all_entities(self) -> tuple[EbusEntity, ...]:
        return BOILER_SENSORS + BOILER_BINARY_SENSORS + ENERGYMGR_SENSORS

    # -- származtatott értékek -------------------------------------------------

    def _compute_flame(self, adat: AristonData) -> None:
        """Kapuzott lángteljesítmény és a hőenergia trapéz-integrálja.

        **Buszjel nélkül nem integrálunk.** Ha az ebusd elveszti a jelet, a gyorsítótárban
        bent marad az utolsó érték (például 8 kW és „fűtés”), és az integrátor órákon át nem
        létező gázt számolna. Ilyenkor inkább nincs érték, és az integrálás horgonya is
        törlődik, hogy a jel visszatérésekor ne keletkezzen egy óriási, hamis lépés.
        """
        adat.flame_power = szamma(adat.values.get(f"{CONF_CIRCUIT_BOILER}/flame_power_kw"))
        allapot = mezo(adat.values.get(f"{CONF_CIRCUIT_BOILER}/boiler_status"), 0)

        van_jel = adat.info is None or adat.info.signal
        if not van_jel:
            adat.flame_power = None
            adat.flame_power_gated = None
            self._last_power = None
            self._last_power_time = None
            adat.heat_energy = round(float(self._state.get("heat_energy", 0.0)), 3)
            return

        adat.flame_power_gated = kapuzott_teljesitmeny(allapot, adat.flame_power)

        energia = float(self._state.get("heat_energy", 0.0))
        most = dt_util.utcnow()
        teljesitmeny = adat.flame_power_gated
        if teljesitmeny is not None:
            eltelt = (most - self._last_power_time).total_seconds() if self._last_power_time else 0.0
            energia += trapez_novekmeny(
                self._last_power, teljesitmeny, eltelt, MAX_INTEGRATION_GAP.total_seconds()
            )
            self._last_power = teljesitmeny
            self._last_power_time = most
        self._state["heat_energy"] = round(energia, 6)
        adat.heat_energy = round(energia, 3)

    async def _compute_gas(self, adat: AristonData) -> None:
        """Gázfogyasztás és becsült gázóra-állás a hőenergiából."""
        allapot = self._gas_state()
        adat.gas_factor = allapot.szorzo
        adat.gas_factor_calibrated = allapot.bemert
        if not self.gas_estimation:
            return

        adat.gas_total = gaz_mennyiseg(allapot, adat.heat_energy)

        ref_allas = self._state.get("ref_reading")
        ref_gaz = self._state.get("ref_gas_total")
        if ref_allas is not None and ref_gaz is not None:
            # A leolvasás óta elfogyott mennyiséget is a bázispontos összegből képezzük,
            # így a szorzó módosítása ezt a két szenzort sem lépteti meg visszamenőleg.
            elfogyott = max(adat.gas_total - float(ref_gaz), 0.0)
            adat.gas_since_reading = round(elfogyott, 3)
            adat.gas_meter_estimate = round(float(ref_allas) + elfogyott, 3)

        # Az integrált energiát tartósan el kell menteni, különben HA-újraindításkor elvész.
        # Ötpercenként egy mentés bőven elég: ennyi kiesés a legnagyobb lángteljesítménynél is
        # csak tizedkilowattórákat jelent, a gyakori írás viszont fölöslegesen koptatná a lemezt.
        most = dt_util.utcnow()
        if self._last_save is None or (most - self._last_save) > SAVE_INTERVAL:
            self._last_save = most
            await self._async_save_state()

    def _compute_diagnostics(self, adat: AristonData) -> None:
        """Lángleszakadás arány: hány leszakadás jut 1000 gyújtásra."""
        adat.flame_lift_ratio = langleszakadas_arany(
            szamma(adat.values.get(f"{CONF_CIRCUIT_BOILER}/flame_lift_offs")),
            szamma(adat.values.get(f"{CONF_CIRCUIT_BOILER}/ignition_cycles")),
        )

    # -- hibanapló -------------------------------------------------------------

    async def _async_update_errors(self) -> None:
        """A 10 mélységű hibanapló kiolvasása és a csúszás felismerése.

        A kazán nem tárol időbélyeget a bejegyzésekhez. Ha a napló k bejegyzéssel lejjebb
        csúszott (``új[k:] == régi[:10-k]``), akkor az első k bejegyzés új, és megkapja a
        kiolvasás időpontját. Így az ugyanazzal a kóddal ismétlődő hibák is látszanak.
        """
        most = dt_util.now()
        if self._errors_updated is not None and (most - self._errors_updated) < timedelta(
            seconds=ERROR_LOG_INTERVAL
        ):
            return

        kodok: list[str] = []
        for nev in ERROR_LOG_MESSAGES:
            ertek = await self.client.async_read(CONF_CIRCUIT_BOILER, nev, 0)
            if ertek is None:
                return  # hiányos napló: inkább megtartjuk a korábbit
            kodok.append(ertek.split(";")[0].strip())

        regi = [e.code for e in self._errors]
        if not regi:
            self._errors = [
                ErrorEntry(code=k, first_seen=None, note="a nyilvántartás kezdete előtti")
                for k in kodok
            ]
        elif (csuszas := hibanaplo_csuszas(regi, kodok)) > 0:
            ujak = [ErrorEntry(code=k, first_seen=most.isoformat(), note="") for k in kodok[:csuszas]]
            self._errors = (ujak + self._errors)[: len(kodok)]

        self._errors_updated = most
        await self._async_save_state()
