# Az `ariston.csv` eredete — pontos hivatkozás

Ez a fájl rögzíti, **melyik upstream állapotból** származik az itteni konfiguráció, hogy a
származás auditálható legyen, és a későbbi frissítés egy paranccsal megnézhető.

| | |
|---|---|
| **Upstream projekt** | https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet |
| **Licenc** | GNU GPL v3 (lásd `LICENSE` ebben a mappában) |
| **Kiindulási címke** | `v2.6` (commit `1169e7c`) |
| **Szinkronizálva eddig** | commit `f2c9a63` — „changed Boiler power datatypes” (2026-03-23) |
| **Utolsó ellenőrzés** | 2026-09-18 |

A `v2.6` utáni upstream változásokat átnéztük és méréssel ellenőriztük; hogy mit vettünk át és
mit nem, az a [`NOTICE.md`](NOTICE.md) „Szinkron az eredeti projekttel” szakaszában van.

## Mi változott azóta az upstreamben?

```bash
git clone https://github.com/wrongisthenewright/ebusd-configuration-ariston-bridgenet upstream
cd upstream
git log --oneline f2c9a63..origin/main          # a szinkron óta született commitok
git diff f2c9a63:ariston.csv origin/main:ariston.csv
```

## Mi az eltérésünk az upstreamtől?

```bash
git show f2c9a63:ariston.csv > /tmp/upstream.csv
diff /tmp/upstream.csv ariston.csv
```

A `diff` jelenleg **107 eltérő sort** ad (a ~610-ből): lekérdezési prioritások, a 10 mélységű
hibanapló, a `boiler_status` szétválasztása, a `boiler_life_time` mértékegysége és néhány
megjegyzés. Mindegyik indoklása a [`NOTICE.md`](NOTICE.md)-ben.
