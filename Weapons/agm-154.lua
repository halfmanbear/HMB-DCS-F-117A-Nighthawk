local function find_core_agm154()
  local wt = weapons_table and weapons_table.weapons and weapons_table.weapons.missiles
  if not wt then
    if env and env.warning then env.warning("[AGM154] weapons_table.missiles not ready; using fallback.", true) end
    return nil
  end
  local core = wt["AGM_154"]
  if not core then
    if env and env.warning then env.warning("[AGM154] Core 'AGM_154' not found in missiles table; using fallback.", true) end
    return nil
  end
  return core
end

local CORE = find_core_agm154()

local DEFAULT_CX_PIL = 0.0018   -- ≈ 0.000415   :contentReference[oaicite:1]{index=1}
local FALLBACK_ATTR  = {wsType_Weapon, wsType_Missile, wsType_AS_Missile, 132} -- enum last
local FALLBACK_W     = 485.0
local FALLBACK_MODEL = "agm-154"

declare_loadout({
  category    = CAT_MISSILES,
  CLSID       = "AGM_154_C_JSOW",
  attribute   = (CORE and CORE.wsTypeOfWeapon) or FALLBACK_ATTR,
  Count       = 1,
  Cx_pil      = DEFAULT_CX_PIL,
  Picture     = "AGM154.png",
  displayName = _("AGM-154C - JSOW Unitary BROACH"),
  Weight      = (CORE and (CORE.M or CORE.mass)) or FALLBACK_W,
  Elements    = { { ShapeName = (CORE and CORE.model) or FALLBACK_MODEL } },
})