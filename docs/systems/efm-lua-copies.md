# EFM Lua copies

The EFM repository's `Cockpit/Scripts` directory keeps copies of some cockpit Lua
files. This mod's files are the ones DCS loads, so change them here and copy them
over. `tests/test_efm_lua_copies.py` fails when a copy falls behind.

IRADS motion is handled by the EFM. Cockpit FOV controls dispatch absolute endpoint
selections, which avoids the legacy intermediate zoom preset.
