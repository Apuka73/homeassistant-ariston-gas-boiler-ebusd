"""Beállítási folyamat: az ebusd címének megadása és ellenőrzése."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .const import (
    CONF_CIRCUIT_BOILER,
    CONF_ERROR_LOG,
    CONF_GAS_ESTIMATION,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .ebusd import DEFAULT_PORT, EbusdClient, EbusdError

LEPES_SEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
    }
)


async def _async_ellenoriz(host: str, port: int) -> tuple[str | None, str]:
    """Kapcsolódik az ebusd-hez; visszaadja a hibakulcsot és a felajánlott nevet."""
    kliens = EbusdClient(host, port)
    try:
        info = await kliens.async_info()
        if info.version is None:
            return "invalid_response", ""
        korok = await kliens.async_circuits()
        if CONF_CIRCUIT_BOILER not in korok:
            return "no_boiler", ""
        return None, "Ariston kazán"
    except EbusdError:
        return "cannot_connect", ""
    finally:
        await kliens.async_close()


class AristonEbusConfigFlow(ConfigFlow, domain=DOMAIN):
    """Az integráció hozzáadása a felületről."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Bekéri az ebusd címét, és kipróbálja a kapcsolatot."""
        hibak: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()
            hiba, nev = await _async_ellenoriz(host, port)
            if hiba is None:
                return self.async_create_entry(title=nev, data={CONF_HOST: host, CONF_PORT: port})
            hibak["base"] = hiba
        return self.async_show_form(step_id="user", data_schema=LEPES_SEMA, errors=hibak)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Az ebusd címének módosítása a meglévő entitások megtartásával.

        Erre azért van szükség, mert az integrációt az ebusd címe azonosítja: DHCP-s
        hálózaton az IP-cím megváltozhat, és enélkül új eszközként kellene felvenni,
        ami elveszítené az eddigi előzményt és a gázbecslés állapotát.
        """
        bejegyzes = self._get_reconfigure_entry()
        hibak: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            hiba, _nev = await _async_ellenoriz(host, port)
            if hiba is None:
                uj_azonosito = f"{host}:{port}"
                # Az azonosító maga a cím, ezért címváltáskor az is változik. Csak azt kell
                # kizárni, hogy egy MÁSIK bejegyzés már ezt az ebusd-t használja.
                utkozes = any(
                    e.unique_id == uj_azonosito and e.entry_id != bejegyzes.entry_id
                    for e in self._async_current_entries()
                )
                if utkozes:
                    return self.async_abort(reason="masik_ebusd")
                return self.async_update_reload_and_abort(
                    bejegyzes,
                    unique_id=uj_azonosito,
                    data_updates={CONF_HOST: host, CONF_PORT: port},
                )
            hibak["base"] = hiba
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=bejegyzes.data[CONF_HOST]): str,
                    vol.Optional(
                        CONF_PORT, default=bejegyzes.data.get(CONF_PORT, DEFAULT_PORT)
                    ): vol.Coerce(int),
                }
            ),
            errors=hibak,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AristonEbusOptionsFlow:
        """Beállítások (lekérdezési ütem, gázbecslés, hibanapló)."""
        return AristonEbusOptionsFlow()


class AristonEbusOptionsFlow(OptionsFlow):
    """A telepítés után módosítható beállítások."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Megjeleníti és elmenti a beállításokat."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        beallitasok = self.config_entry.options
        sema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=beallitasok.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=600)),
                vol.Optional(
                    CONF_GAS_ESTIMATION,
                    default=beallitasok.get(CONF_GAS_ESTIMATION, True),
                ): bool,
                vol.Optional(
                    CONF_ERROR_LOG, default=beallitasok.get(CONF_ERROR_LOG, True)
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=sema)
