"""Szenzor entitások: nyers ebusd regiszterek és a származtatott értékek."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BOILER_SENSORS,
    DOMAIN,
    ENERGYMGR_SENSORS,
    ERROR_DESCRIPTIONS_EN,
    ERROR_DESCRIPTIONS_HU,
    SENTINEL_TEMPERATURE,
    EbusEntity,
    normalize_option,
)
from .coordinator import AristonData, AristonEbusCoordinator
from .entity import AristonEbusEntity


@dataclass(frozen=True, kw_only=True)
class AristonSensorDescription(SensorEntityDescription):
    """Származtatott szenzor leírása."""

    value_fn: Callable[[AristonData], Any]
    attributes_fn: Callable[[AristonData, str], dict[str, Any]] | None = None


DERIVED_SENSORS: tuple[AristonSensorDescription, ...] = (
    AristonSensorDescription(
        key="flame_power_gated",
        translation_key="flame_power_gated",
        native_unit_of_measurement="kW",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fire",
        suggested_display_precision=1,
        value_fn=lambda adat: adat.flame_power_gated,
    ),
    AristonSensorDescription(
        key="heat_energy",
        translation_key="heat_energy",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:radiator",
        suggested_display_precision=2,
        value_fn=lambda adat: adat.heat_energy,
    ),
    AristonSensorDescription(
        key="gas_consumption",
        translation_key="gas_consumption",
        native_unit_of_measurement="m³",
        device_class=SensorDeviceClass.GAS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:meter-gas",
        suggested_display_precision=2,
        value_fn=lambda adat: adat.gas_total,
        attributes_fn=lambda adat, nyelv: {
            "gas_factor": adat.gas_factor,
            "calibrated": adat.gas_factor_calibrated,
        },
    ),
    AristonSensorDescription(
        key="gas_meter_estimate",
        translation_key="gas_meter_estimate",
        native_unit_of_measurement="m³",
        device_class=SensorDeviceClass.GAS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:meter-gas",
        suggested_display_precision=2,
        value_fn=lambda adat: adat.gas_meter_estimate,
    ),
    AristonSensorDescription(
        key="gas_since_reading",
        translation_key="gas_since_reading",
        native_unit_of_measurement="m³",
        icon="mdi:fire",
        value_fn=lambda adat: adat.gas_since_reading,
    ),
    AristonSensorDescription(
        key="flame_lift_ratio",
        translation_key="flame_lift_ratio",
        native_unit_of_measurement="‰",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-line-variant",
        suggested_display_precision=2,
        value_fn=lambda adat: adat.flame_lift_ratio,
    ),
    AristonSensorDescription(
        key="symbol_rate",
        translation_key="symbol_rate",
        native_unit_of_measurement="szimbólum/s",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:sine-wave",
        value_fn=lambda adat: adat.info.symbol_rate if adat.info else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Létrehozza a szenzorokat a katalógusból és a származtatott értékekből."""
    coordinator: AristonEbusCoordinator = hass.data[DOMAIN][entry.entry_id]
    ertekek = coordinator.data.values if coordinator.data else {}

    entitasok: list[SensorEntity] = []
    for leiras in BOILER_SENSORS + ENERGYMGR_SENSORS:
        # Csak azokat vesszük fel, amikre a rendszer valóban ad értéket: egy kazán-only
        # telepítésen a hőszivattyús és rendszerszabályzós regiszterek sosem válaszolnak.
        if f"{leiras.circuit}/{leiras.message}" in ertekek:
            entitasok.append(EbusRegisterSensor(coordinator, leiras))

    for leiras in DERIVED_SENSORS:
        if leiras.key in ("gas_consumption", "gas_meter_estimate", "gas_since_reading"):
            if not coordinator.gas_estimation:
                continue
        entitasok.append(AristonDerivedSensor(coordinator, leiras))

    if coordinator.error_log:
        entitasok.append(AristonErrorLogSensor(coordinator))

    async_add_entities(entitasok)


class EbusRegisterSensor(AristonEbusEntity, SensorEntity):
    """Egy ebusd üzenetből képzett szenzor."""

    def __init__(self, coordinator: AristonEbusCoordinator, leiras: EbusEntity) -> None:
        """Átveszi a katalógusban megadott mértékegységet és eszközosztályt."""
        super().__init__(coordinator, leiras.key)
        self._leiras = leiras
        self._attr_native_unit_of_measurement = leiras.unit
        self._attr_device_class = leiras.device_class
        self._attr_state_class = leiras.state_class
        self._attr_icon = leiras.icon
        self._attr_entity_registry_enabled_default = leiras.enabled
        if leiras.diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if leiras.options:
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = leiras.options
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = None
        elif leiras.numeric:
            # A számlálók és fordulatszámok egészek, a mért mennyiségek egy tizedesig érdekesek.
            if leiras.state_class == "total_increasing" or leiras.unit in (None, "rpm", "%", "min"):
                self._attr_suggested_display_precision = 0
            else:
                self._attr_suggested_display_precision = 1

    @property
    def native_value(self) -> Any:
        """A regiszter aktuális értéke."""
        nyers = self.coordinator.data.values.get(
            f"{self._leiras.circuit}/{self._leiras.message}"
        )
        if nyers is None:
            return None
        mezok = nyers.split(";")
        if self._leiras.field_index >= len(mezok):
            return None
        ertek = mezok[self._leiras.field_index].strip()
        if not ertek:
            return None
        if self._leiras.options:
            kulcs = normalize_option(ertek)
            return kulcs if kulcs in self._leiras.options else None
        if not self._leiras.numeric:
            return ertek
        try:
            szam = float(ertek)
        except ValueError:
            return None
        # Bekötetlen érzékelőnél az Ariston 0x7FFF-et küld (3276,7 °C) — ez nem mérés.
        if abs(szam - SENTINEL_TEMPERATURE) < 0.05:
            return None
        return szam


class AristonDerivedSensor(AristonEbusEntity, SensorEntity):
    """Számított szenzor (kapuzott teljesítmény, hőenergia, gáz, diagnosztika)."""

    entity_description: AristonSensorDescription

    def __init__(
        self, coordinator: AristonEbusCoordinator, leiras: AristonSensorDescription
    ) -> None:
        """Beállítja a leírást."""
        super().__init__(coordinator, leiras.key)
        self.entity_description = leiras

    @property
    def native_value(self) -> Any:
        """A számított érték."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Kiegészítő adatok (pl. a gázszorzó)."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(
            self.coordinator.data, self.hass.config.language
        )


class AristonErrorLogSensor(AristonEbusEntity, SensorEntity):
    """A kazán 10 mélységű hibanaplója.

    Az állapot a legfrissebb bejegyzés kódja, az attribútumokban pedig a teljes napló
    szerepel: kód, magyarázat, és az az időpont, amikor az integráció ELŐSZÖR látta.
    A kazán maga nem tárol időbélyeget a bejegyzésekhez.
    """

    _attr_icon = "mdi:clipboard-alert-outline"

    def __init__(self, coordinator: AristonEbusCoordinator) -> None:
        """Létrehozza a hibanapló szenzort."""
        super().__init__(coordinator, "error_log")

    @property
    def native_value(self) -> str | None:
        """A legfrissebb hibanapló-bejegyzés kódja."""
        bejegyzesek = self.coordinator.data.errors
        if not bejegyzesek:
            return None
        return bejegyzesek[0].code.split("-")[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """A teljes napló és az utolsó ellenőrzés ideje."""
        szotar = (
            ERROR_DESCRIPTIONS_HU
            if self.hass.config.language == "hu"
            else ERROR_DESCRIPTIONS_EN
        )
        bejegyzesek = []
        for e in self.coordinator.data.errors:
            kod = e.code.split("-")[0]
            leiras = szotar.get(kod)
            if leiras is None:
                # Az ebusd saját (angol) szövege a tartalék, ha nincs a szótárunkban.
                leiras = e.code.split("-", 1)[1] if "-" in e.code else e.code
            bejegyzesek.append(
                {
                    "code": kod,
                    "raw": e.code,
                    "description": leiras,
                    "first_seen": e.first_seen,
                    "note": e.note,
                }
            )
        frissitve = self.coordinator.data.errors_updated
        return {
            "entries": bejegyzesek,
            "last_checked": frissitve.isoformat() if frissitve else None,
        }
