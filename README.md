# F-117A Nighthawk for DCS

Community Discord: https://discord.gg/qj6wz48jAn

This mod is a substantial rework and fork of [WatchBambi/DCS-F-117](https://github.com/WatchBambi/DCS-F-117).

The External Flight Model used by this mod is also a substantial rework and fork of [WatchBambi/DCS-F-117-EFM](https://github.com/WatchBambi/DCS-F-117-EFM).

- Current EFM source code and related work: [halfmanbear/HMB-DCS-F-117A-EFM](https://github.com/halfmanbear/HMB-DCS-F-117A-EFM)

## Install

Download the latest `.zip` from Releases and extract it to:

```text
Saved Games/DCS/Mods/aircraft/F-117-NightHawk
```

If you still use the older Open Beta folder structure, install it to the corresponding `Saved Games/DCS.openbeta/Mods/aircraft/` path instead.

## First setup in DCS

Before flying, open the Controls menu for `F-117-NightHawk`, then use the `Adjust Controls` dropdown and configure the bindings under `F-117A Essential System Controls`.

At minimum, bind or verify these commands:

- `Air-To-Ground Mode` - required to employ munitions
- `Electro-Optical System On/Off` - required to enable the targeting MFD in Air-To-Ground mode
- `IRADS FOV - Narrow` / `IRADS FOV - Wide` (or the `IRADS FOV (Wide / Medium / Narrow)` axis)
- `Weapon Release` - for automatic bomb bay door opening on release, do not bind `Weapon Fire`
- `Bomb Bay Door Toggle` - manual bay door override
- `IRADS Laser Arm/Safe` - arms the EFM laser for laser-guided munitions
- `Drag Chute` - recommended for shorter-field landings
- `Refueling Hatch`
- `Tail Hook` - optional

### IRADS input migration

After updating, rebind any saved controls that used the old custom zoom IDs or
stock laser / sensor axes. Use `Throttle Designator Controller` directions and
`Depress / Slew Stop` to slew and designate; use `IRADS Designation Clear` to clear.
`TDC Slew Horizontal` and `TDC Slew Vertical` now route directly to the EFM IRADS
sensor. The zoom axis uses -1 = wide, 0 = medium and +1 = narrow, with hysteresis.
The unsupported `Target Box Size` axis has been removed. `DLIR MFD Overlay Toggle`
is available for keyboard and joystick assignment.

Cockpit Lua development copies are maintained in the EFM repository's
`Cockpit/Scripts` directory and deployed to the same paths in this mod. IRADS
motion and zoom are handled by the EFM; cockpit Lua does not redispatch them.

## Included content

This package currently includes:

- Multiple liveries
- Quick start and single missions
- Custom pylon loadouts for Maverick and JSOW stores; JDAMs use the stock DCS weapons
- Cockpit lighting and basic aircraft systems scripts

## Credits

- Initial development, EFM, EDMs, and base mod project: `@JinxxDCS`, `@WatchBambi`
- Latest development, fixes, improvements, and new features: `HalfManBear (HMB)`

## Legal / Attribution

Please keep attribution to the upstream projects when redistributing or further forking this work:

- Original Mod fork base: [WatchBambi/DCS-F-117](https://github.com/WatchBambi/DCS-F-117)
- Original EFM fork base:[WatchBambi/DCS-F-117-EFM](https://github.com/WatchBambi/DCS-F-117-EFM).