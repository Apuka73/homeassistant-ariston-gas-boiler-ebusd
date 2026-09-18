"""Közös ősosztály az integráció entitásaihoz."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AristonEbusCoordinator


class AristonEbusEntity(CoordinatorEntity[AristonEbusCoordinator]):
    """Minden entitás ugyanahhoz az egy eszközhöz (a kazánhoz) tartozik."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AristonEbusCoordinator, key: str) -> None:
        """Beállítja az egyedi azonosítót, a fordítási kulcsot és az eszközt."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        info = coordinator.data.info if coordinator.data else None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Ariston",
            model="eBUS (BridgeNet)",
            name=entry.title,
            sw_version=info.version if info else None,
            configuration_url=None,
        )
