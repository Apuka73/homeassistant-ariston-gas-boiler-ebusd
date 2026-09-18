# Közvetlenül olvasható regiszterek

A `0x2000`/`0x2002` parancsokkal aktívan lekérdezhető regiszterek. A 2026-08-16-i
teljes végigolvasás (223 definiált olvasható üzenet) eredménye:
**38 válaszolt**, 185 időtúllépésre vagy hibára futott.

A hibára futók oka körönként a [Busz-topológia](busz-topologia.md) szócikkben olvasható:

| Kör | Hibás olvasás |
|---|---|
| `energymgr` | 126 |
| `heatpump` | 46 |
| `gateway` | 7 |
| `sensys` | 4 |
| `boiler` | 2 |

## A válaszoló regiszterek

| Kör | Regiszter | Mért érték | Mértékegység |
|---|---|---|---|
| `boiler` | `EWT_temp` | 23.3 | °C |
| `boiler` | `boiler_circulation_cycles` | 7016 |  |
| `boiler` | `boiler_current_modulation` | 0 | pct |
| `boiler` | `boiler_fan_cycles` | 14237 |  |
| `boiler` | `boiler_life_time` | 31980 | óra \* |
| `boiler` | `boiler_pressure` | 0.0 | bar |
| `boiler` | `boiler_status` | standby |  |
| `boiler` | `boiler_type` | ext_tank_thermostat |  |
| `boiler` | `config_version_counter` | 1 |  |
| `boiler` | `dhw_max_power_pct` | 76 | pct |
| `boiler` | `diverter_cycles` | 5289 |  |
| `boiler` | `diverter_valve` | dhw |  |
| `boiler` | `fan_speed` | 0 | rpm |
| `boiler` | `flame_active` | off |  |
| `boiler` | `flame_lift_offs` | 39 |  |
| `boiler` | `flame_power_kw` | 0.0 | kW |
| `boiler` | `heat_max_adj_power_pct` | 64 | pct |
| `boiler` | `heat_max_power_pct` | 61 | pct |
| `boiler` | `heat_min_power_pct` | 5 | pct |
| `boiler` | `heat_post_circulation` | 3 | perc |
| `boiler` | `hours_burner_on_CH` | 5096 | h |
| `boiler` | `hours_burner_on_DHW` | 0 | h |
| `boiler` | `hours_pump_on` | 5640 | h |
| `boiler` | `hybrid_integration` | off |  |
| `boiler` | `ignition_cycles` | 9918 |  |
| `boiler` | `ignition_delay` | 3 | perc |
| `boiler` | `ignition_delay_type` | manual |  |
| `boiler` | `last_error` | 501-No flame;0;-;-;-;-:- |  |
| `boiler` | `maintenance_months` | 0 | hónap |
| `boiler` | `maintenance_warnings_enabled` | off |  |
| `boiler` | `nominal_power` | 24 | kW |
| `boiler` | `pressure_monitoring_device` | pressure_switch |  |
| `boiler` | `pump_max_pwm` | 99 | pct |
| `boiler` | `pump_min_pwm` | 40 | pct |
| `boiler` | `pump_operation` | modulating |  |
| `boiler` | `slow_ignition_power_pct` | 57 | pct |
| `boiler` | `warning_pressure` | 0.6 | bar |
| `sensys` | `boiler_sw_version` | 22 00 02 |  |

\* Az `ariston.csv` eredetileg percet mond, de mérés szerint a számláló órákat számol —
lásd [Kazán](kazan.md). A táblázat értéke a 2026-08-16-i kiolvasásból való; a
[Kazán](kazan.md) szócikk 31 982-es értéke két nappal későbbi mérésből származik.
