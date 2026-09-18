"""A gázbecslés kalibrációs szorzója állítható számként."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_GAS_FACTOR, MIN_GAS_FACTOR
from .coordinator import AristonEbusCoordinator
from .entity import AristonEbusEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Létrehozza a kalibrációs szorzót, ha a gázbecslés be van kapcsolva."""
    coordinator: AristonEbusCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.gas_estimation:
        async_add_entities([GasFactorNumber(coordinator)])


class GasFactorNumber(AristonEbusEntity, NumberEntity):
    """Hány m³ gáz esik 1 kWh leadott hőre.

    Kézzel is állítható, de a pontos értéket a gázóra-leolvasás szolgáltatás méri be.
    """

    _attr_native_min_value = MIN_GAS_FACTOR
    _attr_native_max_value = MAX_GAS_FACTOR
    _attr_native_step = 0.001
    _attr_native_unit_of_measurement = "m³/kWh"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:tune-variant"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: AristonEbusCoordinator) -> None:
        """Létrehozza a szorzó-beállítót."""
        super().__init__(coordinator, "gas_factor")

    @property
    def native_value(self) -> float:
        """Az érvényes szorzó."""
        return self.coordinator.gas_factor

    async def async_set_native_value(self, value: float) -> None:
        """Új szorzó beállítása."""
        await self.coordinator.async_set_gas_factor(value)
