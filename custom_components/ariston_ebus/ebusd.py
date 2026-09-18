"""Aszinkron kliens az ebusd TCP parancsfelületéhez.

Az ebusd alapértelmezetten a 8888-as TCP porton fogad parancsokat (ugyanazokat, amiket az
``ebusctl`` küld). Minden parancs egy sor, a válasz egy vagy több sor, amit egy üres sor zár.

A klienst egyetlen, újracsatlakozó kapcsolat valósítja meg zárral, mert az ebusd egyszerre
egy parancsot dolgoz fel kapcsolatonként.

Fordítás magyarra: a modul kizárólag OLVASÓ parancsokat küld (``read``, ``find``, ``info``),
írást szándékosan nem támogat.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 8888
#: Az ebusd „nincs tárolt érték” válasza, amikor egy üzenetet még sosem olvasott ki.
NO_DATA = "no data stored"


class EbusdError(Exception):
    """Az ebusd hibát adott vissza egy parancsra."""


class EbusdConnectionError(EbusdError):
    """Az ebusd nem érhető el."""


@dataclass(slots=True)
class EbusdInfo:
    """Az ``info`` parancs válaszának a számunkra érdekes mezői."""

    version: str | None = None
    device: str | None = None
    signal: bool = False
    symbol_rate: int | None = None
    reconnects: int | None = None


class EbusdClient:
    """Minimális, olvasásra szorítkozó ebusd kliens."""

    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = 20.0) -> None:
        """Beállítja a kapcsolat paramétereit (kapcsolódás csak az első parancsnál történik)."""
        self._host = host
        self._port = port
        self._timeout = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    @property
    def target(self) -> str:
        """A kapcsolat címe naplózáshoz és egyedi azonosítóhoz."""
        return f"{self._host}:{self._port}"

    async def async_close(self) -> None:
        """Lezárja a kapcsolatot."""
        async with self._lock:
            await self._close()

    async def _close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except (OSError, asyncio.TimeoutError):  # pragma: no cover - lezáráskor mindegy
                pass
        self._reader = None
        self._writer = None

    async def _connect(self) -> None:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=self._timeout
            )
        except (OSError, asyncio.TimeoutError) as err:
            raise EbusdConnectionError(f"nem sikerült csatlakozni ide: {self.target} ({err})") from err

    async def async_command(self, command: str) -> list[str]:
        """Elküld egy parancsot, és visszaadja a válaszsorokat (a záró üres sor nélkül)."""
        async with self._lock:
            for kiserlet in (1, 2):
                if self._writer is None:
                    await self._connect()
                try:
                    return await self._command(command)
                except (OSError, asyncio.TimeoutError) as err:
                    await self._close()
                    if kiserlet == 2:
                        raise EbusdConnectionError(f"{command!r}: {err}") from err
                    _LOGGER.debug("Újracsatlakozás %s után: %s", self.target, err)
            raise EbusdConnectionError(command)  # pragma: no cover - a ciklus mindig visszatér

    async def _command(self, command: str) -> list[str]:
        assert self._reader is not None and self._writer is not None
        self._writer.write(f"{command}\n".encode())
        await self._writer.drain()
        sorok: list[str] = []
        while True:
            nyers = await asyncio.wait_for(self._reader.readline(), timeout=self._timeout)
            if not nyers:
                raise OSError("az ebusd bontotta a kapcsolatot")
            sor = nyers.decode("utf-8", errors="replace").rstrip("\r\n")
            if sor == "":
                return sorok
            sorok.append(sor)

    # -- magas szintű parancsok ------------------------------------------------

    async def async_info(self) -> EbusdInfo:
        """Az ebusd állapota (verzió, adapter, jel, szimbólumsebesség)."""
        info = EbusdInfo()
        for sor in await self.async_command("info"):
            kulcs, _, ertek = sor.partition(":")
            kulcs = kulcs.strip().lower()
            ertek = ertek.strip()
            if kulcs == "version":
                info.version = ertek
            elif kulcs == "device":
                info.device = ertek
            elif kulcs == "signal":
                info.signal = ertek == "acquired"
            elif kulcs == "symbol rate":
                info.symbol_rate = _int_or_none(ertek)
            elif kulcs == "reconnects":
                info.reconnects = _int_or_none(ertek)
        return info

    async def async_read(self, circuit: str, name: str, max_age: int) -> str | None:
        """Egy üzenet kiolvasása.

        ``max_age`` másodperc: az ebusd ennél frissebb gyorsítótárazott értéket ad vissza,
        különben valódi buszolvasást végez. Ezzel szabályozzuk a busz terhelését.
        """
        valasz = await self.async_command(f"read -m {max_age} -c {circuit} {name}")
        if not valasz:
            return None
        elso = valasz[0]
        if elso.startswith("ERR"):
            if NO_DATA in elso:
                return None
            raise EbusdError(f"{circuit}/{name}: {elso}")
        if elso == NO_DATA:
            return None
        return elso

    async def async_find_values(self, circuit: str) -> dict[str, str]:
        """Egy kör összes ismert üzenete a gyorsítótárból (nem terheli a buszt).

        A válasz sorai ``kör név = érték`` alakúak.
        """
        ertekek: dict[str, str] = {}
        for sor in await self.async_command(f"find -c {circuit}"):
            bal, _, jobb = sor.partition(" = ")
            if not jobb:
                continue
            reszek = bal.split()
            if len(reszek) != 2:
                continue
            _kor, nev = reszek
            if jobb == NO_DATA:
                continue
            ertekek[nev] = jobb
        return ertekek

    async def async_circuits(self) -> set[str]:
        """Mely körök szerepelnek a betöltött ebusd konfigurációban."""
        korok: set[str] = set()
        for sor in await self.async_command("find -F circuit"):
            nev = sor.strip()
            if nev and nev != "ignored":
                korok.add(nev)
        return korok


def _int_or_none(ertek: str) -> int | None:
    try:
        return int(ertek.split()[0])
    except (ValueError, IndexError):
        return None
