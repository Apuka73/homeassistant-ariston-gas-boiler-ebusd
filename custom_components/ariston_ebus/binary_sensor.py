"""Bináris szenzorok: láng, zóna-fűtésigény és az ebusd busz-jel."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BOILER_BINARY_SENSORS, DOMAIN, EbusEntity
from .coordinator import AristonEbusCoordinator
from .entity import AristonEbusEntity

ON_VALUES = {"on", "1", "true", "yes"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Létrehozza a bináris szenzorokat."""
    coordinator: AristonEbusCoordinator = hass.data[DOMAIN][entry.entry_id]
    ertekek = coordinator.data.values if coordinator.data else {}

    entitasok: list[BinarySensorEntity] = [
        EbusBinarySensor(coordinator, leiras)
        for leiras in BOILER_BINARY_SENSORS
        if f"{leiras.circuit}/{leiras.message}" in ertekek
    ]
    entitasok.append(EbusSignalSensor(coordinator))
    async_add_entities(entitasok)


class EbusBinarySensor(AristonEbusEntity, BinarySensorEntity):
    """Egy ebusd üzenet be/ki állapotú mezője."""

    def __init__(self, coordinator: AristonEbusCoordinator, leiras: EbusEntity) -> None:
        """Beállítja a katalógusból származó tulajdonságokat."""
        super().__init__(coordinator, leiras.key)
        self._leiras = leiras
        self._attr_icon = leiras.icon
        self._attr_entity_registry_enabled_default = leiras.enabled
        # A lángra szándékosan NINCS eszközosztály: a „heat" osztály „Forró / Normál" feliratot
        # adna, miközben itt az egyszerű be/ki a beszédes (ég-e a láng, vagy sem).

    @property
    def is_on(self) -> bool | None:
        """Igaz, ha a mező bekapcsolt állapotot jelez."""
        nyers = self.coordinator.data.values.get(
            f"{self._leiras.circuit}/{self._leiras.message}"
        )
        if nyers is None:
            return None
        mezok = nyers.split(";")
        if self._leiras.field_index >= len(mezok):
            return None
        return mezok[self._leiras.field_index].strip().lower() in ON_VALUES


class EbusSignalSensor(AristonEbusEntity, BinarySensorEntity):
    """Az ebusd látja-e az eBUS jelet.

    Ez a leghasznosabb hibajelző: ha elmegy, minden érték beragad, és a rájuk épülő
    számítások (például a gázbecslés) hamis adatot termelnének.
    """

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: AristonEbusCoordinator) -> None:
        """Létrehozza a jel-érzékelőt."""
        super().__init__(coordinator, "bus_signal")

    @property
    def is_on(self) -> bool | None:
        """Igaz, ha az ebusd jelet lát a buszon."""
        info = self.coordinator.data.info
        return None if info is None else info.signal
