"""Diagnosztikai letöltés hibakereséshez (az ebusd címe nélkül)."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import AristonEbusCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """A koordinátor pillanatnyi állapota, személyes adat nélkül."""
    coordinator: AristonEbusCoordinator = hass.data[DOMAIN][entry.entry_id]
    adat = coordinator.data
    return {
        "options": dict(entry.options),
        "ebusd": {
            "version": adat.info.version if adat.info else None,
            "signal": adat.info.signal if adat.info else None,
            "symbol_rate": adat.info.symbol_rate if adat.info else None,
        },
        "values": adat.values,
        "derived": {
            "flame_power": adat.flame_power,
            "flame_power_gated": adat.flame_power_gated,
            "heat_energy": adat.heat_energy,
            "gas_total": adat.gas_total,
            "gas_factor": adat.gas_factor,
            "gas_factor_calibrated": adat.gas_factor_calibrated,
            "flame_lift_ratio": adat.flame_lift_ratio,
        },
        "errors": [e.as_dict() for e in adat.errors],
    }
