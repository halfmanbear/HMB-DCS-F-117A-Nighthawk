# Changelog

Newest first. Entries marked **EFM** need the matching EFM build.

## 4 November 2026

- Overwing vapour is one whole cloud covering the inner wings, faded in by
  `OpacityOverPower` rather than built up slice by slice.
- **Blender source for the exterior:** `blender_files/f-117-nighthawk-exterior.blend`
  is one scene that exports the whole exterior model, including the 25 damage-cell
  collision sections, which are hidden while editing. `tools/check_edm_export.py`
  compares an export with the model at git HEAD.

## 3 November 2026

- **HUD/IRADS cursor and 10 mrad lock box** (EFM). The EFM publishes the IRADS view
  direction as `F117_IRADS_LOS_*`.
- **Exhaust:** each platypus slot feeds four nozzles for a flat heat haze and smoke
  sheet, plus a night glow that follows rpm with a 6 s lag (draw arguments 1002, 1003).
- **Liveries:** all nine now texture the full airframe. `tools/sync_livery_materials.py`
  and `tests/test_liveries.py` keep them in step with the model.
- **Engines and start** (EFM): two separately modelled engines, start air from the APU,
  air cart or crossbleed, a 15 % light-off and 54 % starter cut-out, and EGT, fuel flow
  and oil pressure matched to TO 1F-117A-1. New ground power and air cart commands.
- **Cold start is dark:** the battery gates everything and the APU, ground power or an
  engine generator powers the displays. They boot in sequence with illustrative
  self-test screens, and attitude and heading slew to the true values.
- **Weapons:** all 14 pylon stores release and every one was confirmed in DCS.
  The four Su-25T-derived missions are replaced by five Nevada night lessons and a
  Nevada quick start.
- **Displays:** left VSD, centre IRADS and right MAP defaults, a DEP main menu,
  CMDI VSD/HSD/MAP formats and a mission route on the map. The flight model
  performance constants were refitted.

## 2 November 2026

- **Stock JDAMs:** GBU-31(V)1/B, GBU-31(V)3/B and GBU-32(V)2/B replace the mod's own
  copies, so missions using `GBU31_JDAM`, `GBU31_V3B_JDAM` or `GBU32_JDAM` need
  re-arming. Release is confirmed in DCS.
- OCIP III CMDI configuration, and `tools/fm_bench` to score the EFM against the manual.

## 28 to 30 October 2026

- **IRADS designation** (EFM): terrain-validated point lock, Master Arm, Weapon Station
  Next/Previous, automatic laser illumination (code 1688) and CCRP release through the
  EFM. The v11 terrain lock is confirmed in DCS.
- **Release gates:** guided weapons use their own release window, with ALIGN TARGET
  and OUT OF RANGE messages. JDAM range comes from each weapon's launch tables.
- **Controls:** Weapon Release is Right Alt+Space; plain Space is Weapon Fire again.
- **Displays:** Ctrl+Shift+E toggles left EO/VSD, and a Harris-style moving map with
  chart backend sits on the centre screen (Ctrl+Shift+[ ] range, Ctrl+Shift+M
  orientation). The chart backend still needs an in-DCS check.
- OCIP HUD, VSD and HSD pages, autothrottle (CAS HOLD) and PAARS.
