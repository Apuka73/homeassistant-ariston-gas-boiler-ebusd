# Broadcast regisztertérkép

A [Ariston BridgeNet protokoll](ariston-bridgenet-protokoll.md) szócikkben leírt eljárással két mérésből
kinyert **264 regiszter**, laponként csoportosítva:

* **2026-08-16** — nyári állapot, 47 telegramtípusból 133 regiszter
* **2026-09-14** — próbafűtés közben, a nyers busznaplóból (3295 db `2010` és 102 db `2020` telegram)
  további **131 regiszter**, a *Mérés* oszlopban `09-14` jelöléssel. Döntő részük egyetlen
  `2020` paraméter-broadcast blokkból származik (16:38 UTC), amelyet valószínűleg a kazán
  kezelőpaneljének használata váltott ki.

A két mérés közös regiszterei mind azonos értéket adtak. A fűtés első ~12 percében a `2010`-es
szórt regiszterek közül egyedül a `0x9101` (z1_heat_request) változott (0 → 1); az azonosítatlan
`0x42`, `0x46`, `0x94`, `0x95`, `0x9c`, `0xf2` lapok értéke nem mozdult.

A *forrás* oszlop az azonosítás alapját jelöli:

* **igazolt** – az ebusd vagy az `ariston.csv` önállóan is ismeri, a dekódolt érték egyezik
* **levezetett** – a zóna-blokk mintából következik (lásd [Zóna-blokk szerkezet](zona-blokk-szerkezet.md))
* **részleges** – a zóna azonosítható, a paraméter nem
* **azonosítatlan** – nincs támpont

Összesítés: igazolt 20 · levezetett 129 · részleges 64 · azonosítatlan 51.

## Lap 0x10 — Hőmérsékletek (SIN /10 °C)

Értékhossz: **3 bájt**. Regiszterek: 1.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `7310` | `0x1073` | 32767 *(szentinel: nincs érzékelő)* | boiler ext_temp | igazolt | 08-16 |

## Lap 0x19 — Zónánkénti „fűtés folyamatban”

Értékhossz: **2 bájt**. Regiszterek: 6.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `0919` | `0x1909` | 0 | z1_fűtés folyamatban | levezetett | 08-16 |
| `0a19` | `0x190a` | 0 | z2_fűtés folyamatban | levezetett | 08-16 |
| `0b19` | `0x190b` | 0 | z3_fűtés folyamatban | levezetett | 08-16 |
| `0c19` | `0x190c` | 0 | z4_fűtés folyamatban | levezetett | 08-16 |
| `0d19` | `0x190d` | 0 | z5_fűtés folyamatban | levezetett | 08-16 |
| `0e19` | `0x190e` | 0 | z6_fűtés folyamatban | levezetett | 08-16 |

## Lap 0x20 — Rendszerszintű kapcsolók (azonosítatlan)

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `0120` | `0x2001` | 1 | — | azonosítatlan | 09-14 |
| `0220` | `0x2002` | 0 | — | azonosítatlan | 09-14 |
| `0520` | `0x2005` | 0 | — | azonosítatlan | 09-14 |
| `0b20` | `0x200b` | 1 | — | azonosítatlan | 09-14 |
| `0f20` | `0x200f` | 0 | — | azonosítatlan | 09-14 |

## Lap 0x23 — Rendszerszintű engedélyek

Értékhossz: **1 bájt**. Regiszterek: 2.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `0f23` | `0x230f` | 0 | energymgr/cooling_status | igazolt | 08-16 |
| `1023` | `0x2310` | 0 | energymgr/cooling_available | igazolt | 08-16 |

## Lap 0x26 — Hőmérséklet-küszöbök

Értékhossz: **2 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `6126` | `0x2661` | 600 → 60.0 °C ? | — | azonosítatlan | 09-14 |
| `6226` | `0x2662` | 100 → 10.0 °C ? | — | azonosítatlan | 09-14 |
| `6426` | `0x2664` | 50 → 5.0 °C | energymgr/antifreeze_temp | igazolt | 08-16 |
| `7426` | `0x2674` | 0 → 0.0 °C ? | — | azonosítatlan | 09-14 |
| `7d26` | `0x267d` | 600 → 60.0 °C ? | — | azonosítatlan | 09-14 |

## Lap 0x27 — Időzítések

Értékhossz: **1 bájt**. Regiszterek: 2.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `da27` | `0x27da` | 3 | — | azonosítatlan | 08-16 |
| `db27` | `0x27db` | 3 | — | azonosítatlan | 08-16 |

## Lap 0x28 — Üzemmód-választók

Értékhossz: **1 bájt**. Regiszterek: 1.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `c028` | `0x28c0` | 2 | energymgr/dhw_comfort_mode | igazolt | 08-16 |

## Lap 0x2a — Bemenetek jelentése

Értékhossz: **1 bájt**. Regiszterek: 3.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `ca2a` | `0x2aca` | 6 | — | azonosítatlan | 08-16 |
| `d02a` | `0x2ad0` | 2 | — | azonosítatlan | 09-14 |
| `d12a` | `0x2ad1` | 0 | — | azonosítatlan | 09-14 |

## Lap 0x2b — Költségek és offsetek

Értékhossz: **2 bájt**. Regiszterek: 3.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `602b` | `0x2b60` | 960 | — | azonosítatlan | 09-14 |
| `712b` | `0x2b71` | 28860 | — | azonosítatlan | 08-16 |
| `7e2b` | `0x2b7e` | 256 | — | azonosítatlan | 08-16 |

## Lap 0x42 — Azonosítatlan számláló

Értékhossz: **2 bájt**. Regiszterek: 1.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `d742` | `0x42d7` | 0 | — | azonosítatlan | 08-16 |

## Lap 0x46 — Üzemi értékek (hőszivattyú/kazán)

Értékhossz: **2 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `d346` | `0x46d3` | 0 | — | azonosítatlan | 08-16 |
| `d746` | `0x46d7` | 2 | `dhw_comfort_mode_status`? (2 = be) — a ysard Chaffoteaux-konfiguráció szerint, itt nem igazolt | azonosítatlan | 08-16 |
| `da46` | `0x46da` | 150 | — | azonosítatlan | 08-16 |
| `dc46` | `0x46dc` | 75 | — | azonosítatlan | 08-16 |
| `de46` | `0x46de` | 75 | — | azonosítatlan | 08-16 |

## Lap 0x47 — Teljesítmény és alapjelek

Értékhossz: **3 bájt**. Regiszterek: 3.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `6047` | `0x4760` | 500 → 50.0 °C | energymgr hybrid_LWT_setpoint | igazolt | 08-16 |
| `6147` | `0x4761` | 600 → 60.0 °C | energymgr dhw_current_target_temp | igazolt | 08-16 |
| `7647` | `0x4776` | 32767 *(szentinel: nincs érzékelő)* | energymgr/ext_temp | igazolt | 08-16 |

## Lap 0x4b — Állapot-enumok

Értékhossz: **2 bájt**. Regiszterek: 1.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `c04b` | `0x4bc0` | 1 | boiler boiler_status | igazolt | 08-16 |

## Lap 0x71 — Zóna 1 – hőmérséklet-paraméterek

Értékhossz: **2 bájt**. Regiszterek: 18.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `6071` | `0x7160` | 820 → 82.0 °C | z1_heat_water_max_temp | levezetett | 09-14 |
| `6171` | `0x7161` | 350 → 35.0 °C | z1_heat_water_min_temp | levezetett | 09-14 |
| `6271` | `0x7162` | 190 → 19.0 °C | energymgr/z1_day_temp | igazolt | 08-16 |
| `6371` | `0x7163` | 160 → 16.0 °C | z1_night_temp | levezetett | 09-14 |
| `6471` | `0x7164` | 0 → 0.0 °C | z1_heat_offset | levezetett | 09-14 |
| `6571` | `0x7165` | 500 → 50.0 °C | z1_heat_setpoint_temp_set | levezetett | 09-14 |
| `6671` | `0x7166` | 820 → 82.0 °C | z1 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6771` | `0x7167` | 300 → 30.0 °C | z1 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6c71` | `0x716c` | 50 → 5.0 °C | z1 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7071` | `0x7170` | 70 → 7.0 °C | z1_cool_setpoint_temp_set | levezetett | 09-14 |
| `7171` | `0x7171` | 120 → 12.0 °C | z1_cool_water_max_temp | levezetett | 09-14 |
| `7271` | `0x7172` | 120 → 12.0 °C | z1 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7371` | `0x7173` | 70 → 7.0 °C | z1_cool_water_min_temp | levezetett | 09-14 |
| `7471` | `0x7174` | 70 → 7.0 °C | z1 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7571` | `0x7175` | 0 → 0.0 °C | z1_cool_offset | levezetett | 09-14 |
| `7671` | `0x7176` | 25 → 0.25 | z1_cool_slope | levezetett | 09-14 |
| `7971` | `0x7179` | 150 → 15.0 °C | z1_summer_winter_temp_thresh | levezetett | 09-14 |
| `7a71` | `0x717a` | 30 → 30 perc | z1_summer_winter_switch_delay_time | levezetett | 09-14 |

## Lap 0x72 — Zóna 2 – hőmérséklet-paraméterek

Értékhossz: **2 bájt**. Regiszterek: 19.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `6072` | `0x7260` | 820 → 82.0 °C | z2_heat_water_max_temp | levezetett | 09-14 |
| `6172` | `0x7261` | 350 → 35.0 °C | z2_heat_water_min_temp | levezetett | 09-14 |
| `6272` | `0x7262` | 190 → 19.0 °C | z2_day_temp | levezetett | 09-14 |
| `6372` | `0x7263` | 160 → 16.0 °C | z2_night_temp | levezetett | 09-14 |
| `6472` | `0x7264` | 0 → 0.0 °C | z2_heat_offset | levezetett | 09-14 |
| `6572` | `0x7265` | 350 → 35.0 °C | z2_heat_setpoint_temp_set | levezetett | 09-14 |
| `6672` | `0x7266` | 820 → 82.0 °C | z2 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6772` | `0x7267` | 300 → 30.0 °C | z2 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6972` | `0x7269` | 300 → 30.0 °C | z2 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6a72` | `0x726a` | 130 → 1.30 | z2_heat_slope | levezetett | 09-14 |
| `6b72` | `0x726b` | 350 → 35.0 °C | z2 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6c72` | `0x726c` | 50 → 5.0 °C | z2 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7072` | `0x7270` | 70 → 7.0 °C | z2_cool_setpoint_temp_set | levezetett | 09-14 |
| `7172` | `0x7271` | 120 → 12.0 °C | z2_cool_water_max_temp | levezetett | 09-14 |
| `7272` | `0x7272` | 120 → 12.0 °C | z2 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7372` | `0x7273` | 70 → 7.0 °C | z2_cool_water_min_temp | levezetett | 09-14 |
| `7472` | `0x7274` | 70 → 7.0 °C | z2 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7572` | `0x7275` | 0 → 0.0 °C | z2_cool_offset | levezetett | 09-14 |
| `7672` | `0x7276` | 25 → 0.25 | z2_cool_slope | levezetett | 09-14 |

## Lap 0x73 — Zóna 3 – hőmérséklet-paraméterek

Értékhossz: **2 bájt**. Regiszterek: 21.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `6073` | `0x7360` | 820 → 82.0 °C | z3_heat_water_max_temp | levezetett | 09-14 |
| `6173` | `0x7361` | 350 → 35.0 °C | z3_heat_water_min_temp | levezetett | 09-14 |
| `6273` | `0x7362` | 190 → 19.0 °C | z3_day_temp | levezetett | 09-14 |
| `6373` | `0x7363` | 160 → 16.0 °C | z3_night_temp | levezetett | 09-14 |
| `6473` | `0x7364` | 0 → 0.0 °C | z3_heat_offset | levezetett | 09-14 |
| `6573` | `0x7365` | 350 → 35.0 °C | z3_heat_setpoint_temp_set | levezetett | 09-14 |
| `6673` | `0x7366` | 820 → 82.0 °C | z3 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6773` | `0x7367` | 300 → 30.0 °C | z3 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6973` | `0x7369` | 300 → 30.0 °C | z3 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6a73` | `0x736a` | 130 → 1.30 | z3_heat_slope | levezetett | 09-14 |
| `6b73` | `0x736b` | 350 → 35.0 °C | z3 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6c73` | `0x736c` | 50 → 5.0 °C | z3 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7073` | `0x7370` | 70 → 7.0 °C | z3_cool_setpoint_temp_set | levezetett | 09-14 |
| `7173` | `0x7371` | 120 → 12.0 °C | z3_cool_water_max_temp | levezetett | 09-14 |
| `7273` | `0x7372` | 120 → 12.0 °C | z3 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7373` | `0x7373` | 70 → 7.0 °C | z3_cool_water_min_temp | levezetett | 09-14 |
| `7473` | `0x7374` | 70 → 7.0 °C | z3 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7573` | `0x7375` | 0 → 0.0 °C | z3_cool_offset | levezetett | 09-14 |
| `7673` | `0x7376` | 25 → 0.25 | z3_cool_slope | levezetett | 09-14 |
| `7973` | `0x7379` | 150 → 15.0 °C | z3_summer_winter_temp_thresh | levezetett | 09-14 |
| `7a73` | `0x737a` | 30 → 30 perc | z3_summer_winter_switch_delay_time | levezetett | 09-14 |

## Lap 0x74 — Zóna 4 – hőmérséklet-paraméterek

Értékhossz: **2 bájt**. Regiszterek: 21.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `6074` | `0x7460` | 820 → 82.0 °C | z4_heat_water_max_temp | levezetett | 09-14 |
| `6174` | `0x7461` | 350 → 35.0 °C | z4_heat_water_min_temp | levezetett | 09-14 |
| `6274` | `0x7462` | 190 → 19.0 °C | z4_day_temp | levezetett | 09-14 |
| `6374` | `0x7463` | 160 → 16.0 °C | z4_night_temp | levezetett | 09-14 |
| `6474` | `0x7464` | 0 → 0.0 °C | z4_heat_offset | levezetett | 09-14 |
| `6574` | `0x7465` | 350 → 35.0 °C | z4_heat_setpoint_temp_set | levezetett | 09-14 |
| `6674` | `0x7466` | 820 → 82.0 °C | z4 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6774` | `0x7467` | 300 → 30.0 °C | z4 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6974` | `0x7469` | 300 → 30.0 °C | z4 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6a74` | `0x746a` | 130 → 1.30 | z4_heat_slope | levezetett | 09-14 |
| `6b74` | `0x746b` | 350 → 35.0 °C | z4 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `6c74` | `0x746c` | 50 → 5.0 °C | z4 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7074` | `0x7470` | 70 → 7.0 °C | z4_cool_setpoint_temp_set | levezetett | 08-16 |
| `7174` | `0x7471` | 120 → 12.0 °C | z4_cool_water_max_temp | levezetett | 08-16 |
| `7274` | `0x7472` | 120 → 12.0 °C | z4 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `7374` | `0x7473` | 70 → 7.0 °C | z4_cool_water_min_temp | levezetett | 08-16 |
| `7474` | `0x7474` | 70 → 7.0 °C | z4 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `7574` | `0x7475` | 0 → 0.0 °C | z4_cool_offset | levezetett | 08-16 |
| `7674` | `0x7476` | 25 → 0.25 | z4_cool_slope | levezetett | 08-16 |
| `7974` | `0x7479` | 150 → 15.0 °C | z4_summer_winter_temp_thresh | levezetett | 09-14 |
| `7a74` | `0x747a` | 30 → 30 perc | z4_summer_winter_switch_delay_time | levezetett | 09-14 |

## Lap 0x75 — Zóna 5 – hőmérséklet-paraméterek

Értékhossz: **2 bájt**. Regiszterek: 21.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `6075` | `0x7560` | 820 → 82.0 °C | z5_heat_water_max_temp | levezetett | 08-16 |
| `6175` | `0x7561` | 350 → 35.0 °C | z5_heat_water_min_temp | levezetett | 08-16 |
| `6275` | `0x7562` | 190 → 19.0 °C | z5_day_temp | levezetett | 09-14 |
| `6375` | `0x7563` | 160 → 16.0 °C | z5_night_temp | levezetett | 09-14 |
| `6475` | `0x7564` | 0 → 0.0 °C | z5_heat_offset | levezetett | 08-16 |
| `6575` | `0x7565` | 350 → 35.0 °C | z5_heat_setpoint_temp_set | levezetett | 08-16 |
| `6675` | `0x7566` | 820 → 82.0 °C | z5 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `6775` | `0x7567` | 300 → 30.0 °C | z5 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `6975` | `0x7569` | 300 → 30.0 °C | z5 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `6a75` | `0x756a` | 130 → 1.30 | energymgr/cooling_temps † | levezetett | 08-16 |
| `6b75` | `0x756b` | 350 → 35.0 °C | z5 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `6c75` | `0x756c` | 50 → 5.0 °C | z5 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `7075` | `0x7570` | 70 → 7.0 °C | z5_cool_setpoint_temp_set | levezetett | 08-16 |
| `7175` | `0x7571` | 120 → 12.0 °C | z5_cool_water_max_temp | levezetett | 08-16 |
| `7275` | `0x7572` | 120 → 12.0 °C | z5 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `7375` | `0x7573` | 70 → 7.0 °C | z5_cool_water_min_temp | levezetett | 08-16 |
| `7475` | `0x7574` | 70 → 7.0 °C | z5 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `7575` | `0x7575` | 0 → 0.0 °C | z5_cool_offset | levezetett | 08-16 |
| `7675` | `0x7576` | 25 → 0.25 | z5_cool_slope | levezetett | 08-16 |
| `7975` | `0x7579` | 150 → 15.0 °C | z5_summer_winter_temp_thresh | levezetett | 09-14 |
| `7a75` | `0x757a` | 30 → 30 perc | z5_summer_winter_switch_delay_time | levezetett | 09-14 |

## Lap 0x76 — Zóna 6 – hőmérséklet-paraméterek

Értékhossz: **2 bájt**. Regiszterek: 21.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `6076` | `0x7660` | 820 → 82.0 °C | z6_heat_water_max_temp | levezetett | 08-16 |
| `6176` | `0x7661` | 350 → 35.0 °C | energymgr/day_temp_settings † | levezetett | 08-16 |
| `6276` | `0x7662` | 190 → 19.0 °C | z6_day_temp | levezetett | 09-14 |
| `6376` | `0x7663` | 160 → 16.0 °C | z6_night_temp | levezetett | 08-16 |
| `6476` | `0x7664` | 0 → 0.0 °C | z6_heat_offset | levezetett | 08-16 |
| `6576` | `0x7665` | 350 → 35.0 °C | z6_heat_setpoint_temp_set | levezetett | 08-16 |
| `6676` | `0x7666` | 820 → 82.0 °C | z6 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `6776` | `0x7667` | 300 → 30.0 °C | z6 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `6976` | `0x7669` | 300 → 30.0 °C | z6 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `6a76` | `0x766a` | 130 → 1.30 | z6_heat_slope | levezetett | 08-16 |
| `6b76` | `0x766b` | 350 → 35.0 °C | z6 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `6c76` | `0x766c` | 50 → 5.0 °C | z6 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `7076` | `0x7670` | 70 → 7.0 °C | z6_cool_setpoint_temp_set | levezetett | 08-16 |
| `7176` | `0x7671` | 120 → 12.0 °C | z6_cool_water_max_temp | levezetett | 09-14 |
| `7276` | `0x7672` | 120 → 12.0 °C | z6 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `7376` | `0x7673` | 70 → 7.0 °C | z6_cool_water_min_temp | levezetett | 09-14 |
| `7476` | `0x7674` | 70 → 7.0 °C | z6 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `7576` | `0x7675` | 0 → 0.0 °C | z6_cool_offset | levezetett | 08-16 |
| `7676` | `0x7676` | 25 → 0.25 | z6_cool_slope | levezetett | 08-16 |
| `7976` | `0x7679` | 150 → 15.0 °C | z6_summer_winter_temp_thresh | levezetett | 08-16 |
| `7a76` | `0x767a` | 30 → 30 perc | z6_summer_winter_switch_delay_time | levezetett | 08-16 |

## Lap 0x79 — Zóna 1 – termoreguláció

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `c079` | `0x79c0` | 1 | z1_heat_therm_type_selection | levezetett | 09-14 |
| `c279` | `0x79c2` | 10 | z1_heat_room_temp_infl | levezetett | 09-14 |
| `c679` | `0x79c6` | 3 | z1 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `c979` | `0x79c9` | 6 | z1 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `ce79` | `0x79ce` | 0 | energymgr/z1_heat_request_mode | igazolt | 08-16 |

## Lap 0x7a — Zóna 2 – termoreguláció

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `c07a` | `0x7ac0` | 1 | z2_heat_therm_type_selection | levezetett | 09-14 |
| `c27a` | `0x7ac2` | 10 | z2_heat_room_temp_infl | levezetett | 09-14 |
| `c67a` | `0x7ac6` | 3 | z2 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `c97a` | `0x7ac9` | 6 | z2 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `ce7a` | `0x7ace` | 0 | z2_heat_request_mode | levezetett | 09-14 |

## Lap 0x7b — Zóna 3 – termoreguláció

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `c07b` | `0x7bc0` | 1 | z3_heat_therm_type_selection | levezetett | 09-14 |
| `c27b` | `0x7bc2` | 10 | z3_heat_room_temp_infl | levezetett | 09-14 |
| `c67b` | `0x7bc6` | 3 | z3 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `c97b` | `0x7bc9` | 6 | z3 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `ce7b` | `0x7bce` | 0 | z3_heat_request_mode | levezetett | 09-14 |

## Lap 0x7c — Zóna 4 – termoreguláció

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `c07c` | `0x7cc0` | 1 | z4_heat_therm_type_selection | levezetett | 08-16 |
| `c27c` | `0x7cc2` | 10 | z4_heat_room_temp_infl | levezetett | 08-16 |
| `c67c` | `0x7cc6` | 3 | z4 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `c97c` | `0x7cc9` | 6 | z4 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `ce7c` | `0x7cce` | 0 | z4_heat_request_mode | levezetett | 09-14 |

## Lap 0x7d — Zóna 5 – termoreguláció

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `c07d` | `0x7dc0` | 1 | z5_heat_therm_type_selection | levezetett | 08-16 |
| `c27d` | `0x7dc2` | 10 | z5_heat_room_temp_infl | levezetett | 08-16 |
| `c67d` | `0x7dc6` | 3 | z5 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `c97d` | `0x7dc9` | 6 | z5 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `ce7d` | `0x7dce` | 0 | z5_heat_request_mode | levezetett | 09-14 |

## Lap 0x7e — Zóna 6 – termoreguláció

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `c07e` | `0x7ec0` | 1 | z6_heat_therm_type_selection | levezetett | 09-14 |
| `c27e` | `0x7ec2` | 10 | z6_heat_room_temp_infl | levezetett | 09-14 |
| `c67e` | `0x7ec6` | 3 | z6 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `c97e` | `0x7ec9` | 6 | z6 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |
| `ce7e` | `0x7ece` | 0 | z6_heat_request_mode | levezetett | 08-16 |

## Lap 0x81 — Zóna 1 – tartomány-kapcsolók

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `0081` | `0x8100` | 1 | z1_heat_temp_range | levezetett | 09-14 |
| `0281` | `0x8102` | 1 | z1 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `0681` | `0x8106` | 0 | z1_cool_temp_range | levezetett | 09-14 |
| `0781` | `0x8107` | 0 | energymgr/z1_summer_winter_auto_switch | igazolt | 08-16 |
| `0881` | `0x8108` | 0 | z1 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |

## Lap 0x82 — Zóna 2 – tartomány-kapcsolók

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `0082` | `0x8200` | 1 | z2_heat_temp_range | levezetett | 09-14 |
| `0282` | `0x8202` | 1 | z2 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `0682` | `0x8206` | 0 | z2_cool_temp_range | levezetett | 09-14 |
| `0782` | `0x8207` | 0 | z2_summer_winter_auto_switch | levezetett | 09-14 |
| `0882` | `0x8208` | 0 | z2 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |

## Lap 0x83 — Zóna 3 – tartomány-kapcsolók

Értékhossz: **1 bájt**. Regiszterek: 4.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `0083` | `0x8300` | 1 | z3_heat_temp_range | levezetett | 09-14 |
| `0283` | `0x8302` | 1 | z3 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `0683` | `0x8306` | 0 | z3_cool_temp_range | levezetett | 09-14 |
| `0883` | `0x8308` | 0 | z3 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |

## Lap 0x84 — Zóna 4 – tartomány-kapcsolók

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `0084` | `0x8400` | 1 | z4_heat_temp_range | levezetett | 08-16 |
| `0284` | `0x8402` | 1 | z4 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `0684` | `0x8406` | 0 | z4_cool_temp_range | levezetett | 08-16 |
| `0784` | `0x8407` | 0 | z4_summer_winter_auto_switch | levezetett | 09-14 |
| `0884` | `0x8408` | 0 | z4 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |

## Lap 0x85 — Zóna 5 – tartomány-kapcsolók

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `0085` | `0x8500` | 1 | z5_heat_temp_range | levezetett | 08-16 |
| `0285` | `0x8502` | 1 | z5 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `0685` | `0x8506` | 0 | z5_cool_temp_range | levezetett | 08-16 |
| `0785` | `0x8507` | 0 | z5_summer_winter_auto_switch | levezetett | 09-14 |
| `0885` | `0x8508` | 0 | z5 zóna-blokk, ismeretlen paraméter | részleges | 09-14 |

## Lap 0x86 — Zóna 6 – tartomány-kapcsolók

Értékhossz: **1 bájt**. Regiszterek: 5.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `0086` | `0x8600` | 1 | z6_heat_temp_range | levezetett | 09-14 |
| `0286` | `0x8602` | 1 | z6 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |
| `0686` | `0x8606` | 0 | z6_cool_temp_range | levezetett | 08-16 |
| `0786` | `0x8607` | 0 | z6_summer_winter_auto_switch | levezetett | 09-14 |
| `0886` | `0x8608` | 0 | z6 zóna-blokk, ismeretlen paraméter | részleges | 08-16 |

## Lap 0x91 — Zónánkénti fűtésigény

Értékhossz: **2 bájt**. Regiszterek: 6.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `0191` | `0x9101` | 0 | energymgr/z1_heat_request | igazolt | 08-16 |
| `0291` | `0x9102` | 0 | energymgr/z2_heat_request | igazolt | 08-16 |
| `0391` | `0x9103` | 0 | energymgr/z3_heat_request | igazolt | 08-16 |
| `0491` | `0x9104` | 0 | z4_heat_request | levezetett | 08-16 |
| `0591` | `0x9105` | 0 | z5_heat_request | levezetett | 08-16 |
| `0691` | `0x9106` | 0 | z6_heat_request | levezetett | 08-16 |

## Lap 0x94 — Zónánkénti azonosítatlan mód

Értékhossz: **2 bájt**. Regiszterek: 18.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `c194` | `0x94c1` | 2 | — | azonosítatlan | 08-16 |
| `c294` | `0x94c2` | 2 | — | azonosítatlan | 08-16 |
| `c394` | `0x94c3` | 2 | — | azonosítatlan | 08-16 |
| `c494` | `0x94c4` | 2 | — | azonosítatlan | 08-16 |
| `c594` | `0x94c5` | 2 | — | azonosítatlan | 08-16 |
| `c694` | `0x94c6` | 2 | — | azonosítatlan | 08-16 |
| `d194` | `0x94d1` | 0 | — | azonosítatlan | 08-16 |
| `d294` | `0x94d2` | 0 | — | azonosítatlan | 08-16 |
| `d394` | `0x94d3` | 0 | — | azonosítatlan | 09-14 |
| `d494` | `0x94d4` | 0 | — | azonosítatlan | 09-14 |
| `d594` | `0x94d5` | 0 | — | azonosítatlan | 09-14 |
| `d694` | `0x94d6` | 0 | — | azonosítatlan | 09-14 |
| `d994` | `0x94d9` | 0 | — | azonosítatlan | 08-16 |
| `da94` | `0x94da` | 0 | — | azonosítatlan | 08-16 |
| `db94` | `0x94db` | 0 | — | azonosítatlan | 08-16 |
| `dc94` | `0x94dc` | 0 | — | azonosítatlan | 08-16 |
| `dd94` | `0x94dd` | 0 | — | azonosítatlan | 08-16 |
| `de94` | `0x94de` | 0 | — | azonosítatlan | 08-16 |

## Lap 0x95 — Zónánkénti azonosítatlan

Értékhossz: **2 bájt**. Regiszterek: 6.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `d995` | `0x95d9` | 0 | — | azonosítatlan | 08-16 |
| `da95` | `0x95da` | 0 | — | azonosítatlan | 08-16 |
| `db95` | `0x95db` | 0 | — | azonosítatlan | 08-16 |
| `dc95` | `0x95dc` | 0 | — | azonosítatlan | 08-16 |
| `dd95` | `0x95dd` | 0 | — | azonosítatlan | 08-16 |
| `de95` | `0x95de` | 0 | — | azonosítatlan | 08-16 |

## Lap 0x96 — Zónánkénti szoba-alapjel

Értékhossz: **3 bájt**. Regiszterek: 6.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `6996` | `0x9669` | 190 → 19.0 °C | energymgr/z1_setpoint_temp | igazolt | 08-16 |
| `6a96` | `0x966a` | 190 → 19.0 °C | energymgr/z2_setpoint_temp | igazolt | 08-16 |
| `6b96` | `0x966b` | 190 → 19.0 °C | energymgr/z3_setpoint_temp | igazolt | 08-16 |
| `6c96` | `0x966c` | 190 → 19.0 °C | z4_szoba-alapjel | levezetett | 08-16 |
| `6d96` | `0x966d` | 190 → 19.0 °C | z5_szoba-alapjel | levezetett | 08-16 |
| `6e96` | `0x966e` | 190 → 19.0 °C | z6_szoba-alapjel | levezetett | 08-16 |

## Lap 0x97 — Zónánkénti számított előremenő alapjel

Értékhossz: **3 bájt**. Regiszterek: 6.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `6197` | `0x9761` | 500 → 50.0 °C | z1_számított előremenő alapjel | levezetett | 08-16 |
| `6297` | `0x9762` | 350 → 35.0 °C | z2_számított előremenő alapjel | levezetett | 08-16 |
| `6397` | `0x9763` | 350 → 35.0 °C | z3_számított előremenő alapjel | levezetett | 08-16 |
| `6497` | `0x9764` | 350 → 35.0 °C | z4_számított előremenő alapjel | levezetett | 08-16 |
| `6597` | `0x9765` | 350 → 35.0 °C | z5_számított előremenő alapjel | levezetett | 08-16 |
| `6697` | `0x9766` | 350 → 35.0 °C | z6_számított előremenő alapjel | levezetett | 08-16 |

## Lap 0x9c — Gateway / rendszer

Értékhossz: **2 bájt**. Regiszterek: 1.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `cf9c` | `0x9ccf` | 0 | — | azonosítatlan | 08-16 |

## Lap 0xf2 — Azonosítatlan kis számlálók

Értékhossz: **2 bájt**. Regiszterek: 3.

| Wire | Regiszter | Érték | Azonosítás | Forrás | Mérés |
|---|---|---|---|---|---|
| `d1f2` | `0xf2d1` | 7 | — | azonosítatlan | 08-16 |
| `d2f2` | `0xf2d2` | 4 | — | azonosítatlan | 08-16 |
| `d3f2` | `0xf2d3` | 1 | — | azonosítatlan | 08-16 |

† Az `ebusd` konfiguráció így nevezi, de a CSV-ben ez a definíció **rossz zónablokkra
horgonyzódik**, ezért a belőle képzett entitás hibás értéket adna — lásd
[Zóna-blokk szerkezet](zona-blokk-szerkezet.md). A regiszter jelentése a blokk-mintából
levezetett, nem az ebusd-definícióval igazolt.
