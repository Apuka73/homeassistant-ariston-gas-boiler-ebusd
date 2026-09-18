"""Állandók és az entitás-katalógus az Ariston eBUS integrációhoz.

A katalógus egy működő telepítés (Ariston Cares S System 24, kazán-only rendszer,
ebusd 26.1 + Elecrow eBUS Adapter Stick C6) tapasztalatai alapján készült: csak azok
az üzenetek szerepelnek benne, amelyek egy kazán-only rendszeren valóban értelmes
értéket adnak, a mértékegységekkel és eszközosztályokkal együtt.

A ``MAX_AGE_*`` értékek szabják meg, milyen gyakran kérhet az integráció VALÓDI
buszolvasást. Az ebusd a ``read -m <mp>`` parancsra a gyorsítótárból válaszol, ha az
érték ennél frissebb — így a lassan változó regiszterek nem terhelik a 2400 baudos buszt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

DOMAIN: Final = "ariston_ebus"

CONF_CIRCUIT_BOILER: Final = "boiler"
CONF_CIRCUIT_ENERGYMGR: Final = "energymgr"

CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_GAS_ESTIMATION: Final = "gas_estimation"
CONF_GAS_FACTOR: Final = "gas_factor"
CONF_ERROR_LOG: Final = "error_log"

DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_GAS_FACTOR: Final = 0.118
"""m³ gáz 1 kWh leadott hőre.

Elméleti kiindulás: 1 m³ földgáz ≈ 9,4 kWh égéshő, ebből egy kondenzációs kazán
radiátoros rendszerben ~90%-ot ad át, azaz 1 m³ ≈ 8,5 kWh → 1 / 8,5 ≈ 0,118.
A valódi szorzót a gázóra-leolvasás szolgáltatással lehet bemérni.
"""

MIN_GAS_FACTOR: Final = 0.05
MAX_GAS_FACTOR: Final = 0.2
MIN_CALIBRATION_ENERGY_KWH: Final = 20.0
"""Ennyi elégetett hő alatt a bemért szorzó még megbízhatatlan."""

MAX_AGE_FAST: Final = 30
MAX_AGE_NORMAL: Final = 300
MAX_AGE_SLOW: Final = 3600

ERROR_LOG_INTERVAL: Final = 600
"""A 10 mélységű hibanapló teljes kiolvasásának időköze (mp)."""

ERROR_LOG_MESSAGES: Final = ["last_error"] + [f"error_slot_{i}" for i in range(1, 10)]

SENTINEL_TEMPERATURE: Final = 3276.7
"""Bekötetlen érzékelő esetén az Ariston 0x7FFF-et küld, ebből az ebusd 3276,7 °C lesz."""

STATUS_NO_FLAME: Final = frozenset(
    {"standby", "circulating", "low_water_pressure", "no_flame"}
)
"""Ezekben az állapotokban biztosan nem ég láng.

A lángteljesítményt ezekben nullára kapuzzuk: a kazán állapotát broadcast üzenet hozza
másodpercek alatt, a teljesítmény-regiszter olvasása viszont percekig késhet, és a beragadt
kW-érték nem létező gázfogyasztást integrálna.
"""

BOILER_STATUS_OPTIONS: Final = [
    "standby",
    "heating",
    "heating_hot_water",
    "water_tank",
    "circulating",
    "manual_test",
    "comfort",
    "gas_circuit_deaeration",
    "auto_calibration",
    "low_water_pressure",
    "no_flame",
]

DIVERTER_VALVE_OPTIONS: Final = ["heating", "dhw"]


def normalize_option(ertek: str) -> str:
    """Az ebusd szóközös értékeit felsorolás-kulccsá alakítja (pl. „water tank” → water_tank).

    A Home Assistant a felsorolás (enum) kulcsokban csak [a-z0-9-_] karaktereket enged meg.
    """
    return ertek.strip().lower().replace(" ", "_")


@dataclass(frozen=True, slots=True)
class EbusEntity:
    """Egy ebusd üzenetből képzett entitás leírása."""

    key: str
    """Az entitás azonosítója (egyben a fordítási kulcs)."""

    message: str
    """Az ebusd üzenet neve."""

    circuit: str = CONF_CIRCUIT_BOILER
    field_index: int = 0
    """Több mezős üzenetnél a mező sorszáma a pontosvesszővel tagolt válaszban."""

    max_age: int = MAX_AGE_NORMAL
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    icon: str | None = None
    diagnostic: bool = False
    enabled: bool = True
    options: list[str] | None = None
    numeric: bool = True


# --- Kazán kör -----------------------------------------------------------------
# A sorrend a dashboardon megszokott logikát követi: működés → teljesítmény → számlálók → beállítások.

BOILER_SENSORS: Final[tuple[EbusEntity, ...]] = (
    EbusEntity(
        key="boiler_status",
        message="boiler_status",
        max_age=MAX_AGE_FAST,
        icon="mdi:water-boiler",
        options=BOILER_STATUS_OPTIONS,
        numeric=False,
    ),
    EbusEntity(
        key="flame_power",
        message="flame_power_kw",
        max_age=MAX_AGE_FAST,
        unit="kW",
        device_class="power",
        state_class="measurement",
        icon="mdi:fire",
    ),
    EbusEntity(
        key="modulation",
        message="boiler_current_modulation",
        max_age=MAX_AGE_FAST,
        unit="%",
        state_class="measurement",
        icon="mdi:percent",
    ),
    EbusEntity(
        key="fan_speed",
        message="fan_speed",
        max_age=MAX_AGE_FAST,
        unit="rpm",
        state_class="measurement",
        icon="mdi:fan",
    ),
    EbusEntity(
        key="return_temperature",
        message="EWT_temp",
        max_age=MAX_AGE_FAST,
        unit="°C",
        device_class="temperature",
        state_class="measurement",
    ),
    EbusEntity(
        key="outside_temperature",
        message="ext_temp",
        max_age=MAX_AGE_FAST,
        unit="°C",
        device_class="temperature",
        state_class="measurement",
    ),
    EbusEntity(
        key="boiler_pressure",
        message="boiler_pressure",
        max_age=MAX_AGE_NORMAL,
        unit="bar",
        device_class="pressure",
        state_class="measurement",
        icon="mdi:gauge",
    ),
    EbusEntity(
        key="burner_hours_heating",
        message="hours_burner_on_CH",
        unit="h",
        state_class="total_increasing",
        icon="mdi:timer-outline",
    ),
    EbusEntity(
        key="burner_hours_water",
        message="hours_burner_on_DHW",
        unit="h",
        state_class="total_increasing",
        icon="mdi:timer-outline",
    ),
    EbusEntity(
        key="pump_hours",
        message="hours_pump_on",
        unit="h",
        state_class="total_increasing",
        icon="mdi:timer-outline",
        diagnostic=True,
    ),
    EbusEntity(
        key="ignition_cycles",
        message="ignition_cycles",
        state_class="total_increasing",
        icon="mdi:counter",
    ),
    EbusEntity(
        key="flame_lift_offs",
        message="flame_lift_offs",
        state_class="total_increasing",
        icon="mdi:fire-alert",
    ),
    EbusEntity(
        key="fan_cycles",
        message="boiler_fan_cycles",
        state_class="total_increasing",
        icon="mdi:counter",
        diagnostic=True,
        enabled=False,
    ),
    EbusEntity(
        key="circulation_cycles",
        message="boiler_circulation_cycles",
        state_class="total_increasing",
        icon="mdi:counter",
        diagnostic=True,
        enabled=False,
    ),
    EbusEntity(
        key="diverter_cycles",
        message="diverter_cycles",
        state_class="total_increasing",
        icon="mdi:counter",
        diagnostic=True,
        enabled=False,
    ),
    EbusEntity(
        key="operating_hours",
        message="boiler_life_time",
        unit="h",
        state_class="total_increasing",
        icon="mdi:clock-outline",
        diagnostic=True,
        enabled=False,
    ),
    EbusEntity(
        key="diverter_valve",
        message="diverter_valve",
        max_age=MAX_AGE_FAST,
        icon="mdi:valve",
        options=DIVERTER_VALVE_OPTIONS,
        numeric=False,
        diagnostic=True,
    ),
    # --- beállítások (lassan vagy sosem változnak) ---
    EbusEntity(
        key="nominal_power",
        message="nominal_power",
        max_age=MAX_AGE_SLOW,
        unit="kW",
        device_class="power",
        icon="mdi:fire-circle",
        diagnostic=True,
    ),
    EbusEntity(
        key="heating_max_power",
        message="heat_max_power_pct",
        max_age=MAX_AGE_SLOW,
        unit="%",
        icon="mdi:speedometer",
        diagnostic=True,
    ),
    EbusEntity(
        key="heating_min_power",
        message="heat_min_power_pct",
        max_age=MAX_AGE_SLOW,
        unit="%",
        icon="mdi:speedometer-slow",
        diagnostic=True,
    ),
    EbusEntity(
        key="water_max_power",
        message="dhw_max_power_pct",
        max_age=MAX_AGE_SLOW,
        unit="%",
        icon="mdi:speedometer",
        diagnostic=True,
        enabled=False,
    ),
    EbusEntity(
        key="boiler_type",
        message="boiler_type",
        max_age=MAX_AGE_SLOW,
        numeric=False,
        icon="mdi:information-outline",
        diagnostic=True,
        enabled=False,
    ),
    EbusEntity(
        key="pressure_device",
        message="pressure_monitoring_device",
        max_age=MAX_AGE_SLOW,
        numeric=False,
        icon="mdi:information-outline",
        diagnostic=True,
        enabled=False,
    ),
    EbusEntity(
        key="pump_operation",
        message="pump_operation",
        max_age=MAX_AGE_SLOW,
        numeric=False,
        icon="mdi:pump",
        diagnostic=True,
        enabled=False,
    ),
    EbusEntity(
        key="post_circulation",
        message="heat_post_circulation",
        max_age=MAX_AGE_SLOW,
        unit="min",
        icon="mdi:timer-sand",
        diagnostic=True,
        enabled=False,
    ),
)

BOILER_BINARY_SENSORS: Final[tuple[EbusEntity, ...]] = (
    EbusEntity(
        key="flame",
        message="flame_active",
        max_age=MAX_AGE_FAST,
        icon="mdi:fire",
        numeric=False,
    ),
    EbusEntity(
        key="zone1_heating",
        message="boiler_status",
        field_index=1,
        max_age=MAX_AGE_FAST,
        numeric=False,
    ),
    EbusEntity(
        key="zone2_heating",
        message="boiler_status",
        field_index=2,
        max_age=MAX_AGE_FAST,
        numeric=False,
        enabled=False,
    ),
    EbusEntity(
        key="zone3_heating",
        message="boiler_status",
        field_index=3,
        max_age=MAX_AGE_FAST,
        numeric=False,
        enabled=False,
    ),
)

# --- Energiakezelő kör ---------------------------------------------------------
# Kazán-only rendszeren ezek a lekérdezések időtúllépésre futnak, de a broadcast
# üzenetekből az ebusd mégis eltárol értéket, ezért a gyorsítótárból olvassuk őket.

ENERGYMGR_SENSORS: Final[tuple[EbusEntity, ...]] = (
    EbusEntity(
        key="dhw_target_temperature",
        message="dhw_current_target_temp",
        circuit=CONF_CIRCUIT_ENERGYMGR,
        max_age=MAX_AGE_NORMAL,
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        icon="mdi:water-thermometer",
    ),
    EbusEntity(
        key="flow_setpoint",
        message="hybrid_LWT_setpoint",
        circuit=CONF_CIRCUIT_ENERGYMGR,
        max_age=MAX_AGE_NORMAL,
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        icon="mdi:thermometer-water",
    ),
)

# --- Hibakódok -----------------------------------------------------------------
# A kazán a naplóbejegyzésekhez NEM tárol időpontot, csak a kódot. A magyar magyarázatok
# az Ariston szervizkézikönyvekből és a közösségi visszafejtésekből származnak.

ERROR_DESCRIPTIONS_HU: Final[dict[str, str]] = {
    "101": "Primer kör túlmelegedés",
    "104": "Elégtelen keringetés",
    "108": "Feltöltés szükséges (alacsony víznyomás)",
    "109": "Alacsony víznyomás",
    "309": "Gázszelep vagy gázrelé hiba",
    "501": "Nincs láng — a lángőr nem érzékel lángot",
    "502": "Láng zárt gázszelepnél",
    "504": "Lángleválás",
    "604": "Alacsony ventilátor-fordulat",
    "607": "Nyomáskapcsoló zárva álló ventilátornál",
    "612": "Ventilátor hiba",
    "5P1": "Első gyújtási kísérlet sikertelen",
    "5P2": "Második gyújtási kísérlet is sikertelen",
    "5P3": "Lángleválás működés közben",
    "5P4": "Lángleválás",
    "5P6": "Nincs láng",
}

ERROR_DESCRIPTIONS_EN: Final[dict[str, str]] = {
    "101": "Primary circuit overheating",
    "104": "Insufficient circulation",
    "108": "Refill required (low water pressure)",
    "109": "Low water pressure",
    "309": "Gas valve or gas relay fault",
    "501": "No flame detected",
    "502": "Flame detected with closed gas valve",
    "504": "Flame lift",
    "604": "Fan speed too low",
    "607": "Pressure switch closed with fan stopped",
    "612": "Fan fault",
    "5P1": "First ignition attempt failed",
    "5P2": "Second ignition attempt failed",
    "5P3": "Flame lift during operation",
    "5P4": "Flame lift",
    "5P6": "No flame",
}

SERVICE_SET_METER_READING: Final = "set_gas_meter_reading"
ATTR_READING: Final = "reading"
