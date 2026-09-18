#!/usr/bin/env python3
"""A kazán 10 mélységű hibanaplójának egyben, frissen (-m 0) kiolvasása az ebusd TCP portján.

Kimenet (JSON): {"ok": true, "kodok": ["5P1-1 failed ignition", ...], "rovid": "5P1,501,..."}
A 0. elem a legfrissebb bejegyzés. A kazán nem tárol időbélyeget (a dátummezők ff-ek).
"""
import json, socket, sys

HOST, PORT = "127.0.0.1", 8888
NEVEK = ["last_error"] + [f"error_slot_{i}" for i in range(1, 10)]

def olvas(sock, fajl, nev):
    sock.sendall(f"read -m 0 -c boiler {nev}\n".encode())
    sorok = []
    while True:
        sor = fajl.readline()
        if not sor:
            raise ConnectionError("ebusd bontotta a kapcsolatot")
        sor = sor.rstrip("\n")
        if sor == "":
            break
        sorok.append(sor)
    valasz = sorok[0] if sorok else ""
    if valasz.startswith("ERR"):
        raise ValueError(f"{nev}: {valasz}")
    return valasz.split(";")[0].strip()

def main():
    try:
        with socket.create_connection((HOST, PORT), timeout=20) as sock:
            fajl = sock.makefile("r", encoding="utf-8", errors="replace")
            kodok = [olvas(sock, fajl, n) for n in NEVEK]
        print(json.dumps({"ok": True, "kodok": kodok, "rovid": ",".join(k.split("-")[0] for k in kodok)}, ensure_ascii=False))
    except Exception as ex:  # noqa: BLE001
        print(json.dumps({"ok": False, "hiba": str(ex), "kodok": [], "rovid": ""}, ensure_ascii=False))

if __name__ == "__main__":
    main()
