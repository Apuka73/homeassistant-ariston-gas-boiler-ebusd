"""Ariston eBUS (ebusd) integráció.

Közvetlenül az ebusd TCP parancsfelületéről olvas, MQTT nélkül. Csak olvas: az integráció
egyetlen íróparancsot sem küld a buszra.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import (
    ATTR_READING,
    CONF_ERROR_LOG,
    CONF_GAS_ESTIMATION,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SERVICE_SET_METER_READING,
)
from .coordinator import AristonEbusCoordinator
from .ebusd import DEFAULT_PORT, EbusdClient, EbusdError

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.NUMBER, Platform.SENSOR]

SZOLGALTATAS_SEMA = vol.Schema(
    {
        # Célzásnál (target) a HA listaként adja át az eszközazonosítót, közvetlen
        # hívásnál egyetlen karakterláncként — mindkettőt elfogadjuk.
        vol.Required("device_id"): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(ATTR_READING): vol.All(vol.Coerce(float), vol.Range(min=0)),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Beállítja az integrációt egy ebusd példányhoz."""
    kliens = EbusdClient(entry.data[CONF_HOST], entry.data.get(CONF_PORT, DEFAULT_PORT))
    coordinator = AristonEbusCoordinator(
        hass,
        entry,
        kliens,
        scan_interval=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        gas_estimation=entry.options.get(CONF_GAS_ESTIMATION, True),
        error_log=entry.options.get(CONF_ERROR_LOG, True),
    )
    await coordinator.async_load_state()

    try:
        await coordinator.async_config_entry_first_refresh()
    except EbusdError as err:  # pragma: no cover - a koordinátor UpdateFailed-et dob
        await kliens.async_close()
        raise ConfigEntryNotReady(str(err)) from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    _async_register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Eltávolítja az integrációt."""
    sikeres = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if sikeres:
        coordinator: AristonEbusCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.async_close()
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SET_METER_READING)
    return sikeres


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """A beállítások módosítása után újratölti az integrációt."""
    await hass.config_entries.async_reload(entry.entry_id)


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    """Regisztrálja a gázóra-leolvasás szolgáltatást (egyszer)."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_METER_READING):
        return

    async def _async_set_meter_reading(call: ServiceCall) -> None:
        """A fizikai gázóra állásának rögzítése és a szorzó bemérése."""
        nyilvantartas = dr.async_get(hass)
        for eszkoz_azonosito in call.data["device_id"]:
            eszkoz = nyilvantartas.async_get(eszkoz_azonosito)
            if eszkoz is None:
                raise ServiceValidationError(f"ismeretlen eszköz: {eszkoz_azonosito}")
            for bejegyzes_id in eszkoz.config_entries:
                coordinator = hass.data.get(DOMAIN, {}).get(bejegyzes_id)
                if coordinator is not None:
                    await coordinator.async_set_meter_reading(call.data[ATTR_READING])
                    return
        raise ServiceValidationError("az eszközhöz nem tartozik Ariston eBUS integráció")

    hass.services.async_register(
        DOMAIN, SERVICE_SET_METER_READING, _async_set_meter_reading, schema=SZOLGALTATAS_SEMA
    )
