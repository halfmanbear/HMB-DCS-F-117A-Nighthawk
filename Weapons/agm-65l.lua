local function find_core_agm65l()
  local wt = weapons_table and weapons_table.weapons and weapons_table.weapons.missiles
  if not wt then
    if env and env.warning then env.warning("[AGM65L] weapons_table.missiles not ready; using fallback.", true) end
    return nil
  end
  local core = wt["AGM_65L"]
  if not core then
    if env and env.warning then env.warning("[AGM65L] Core 'AGM_65L' not found in missiles table; using fallback.", true) end
    return nil
  end
  return core
end

local CORE = find_core_agm65l()

local DEFAULT_CX_PIL = 1.7 / 4096   -- ≈ 0.000415   :contentReference[oaicite:1]{index=1}
local FALLBACK_ATTR  = {wsType_Weapon,wsType_Missile,wsType_AS_Missile,AGM_65E} -- enum last
local FALLBACK_W     = 292.0
local FALLBACK_MODEL = "agm-65l"

declare_loadout({
  category    = CAT_MISSILES,
  CLSID       = "AGM_65_L",
  attribute   = (CORE and CORE.wsTypeOfWeapon) or FALLBACK_ATTR,
  Count       = 1,
  Cx_pil      = DEFAULT_CX_PIL,
  Picture     = "agm65.png",
  displayName = _("AGM-65E2/L - Maverick E2/L (Laser Guided ASM)"),
  Weight      = (CORE and (CORE.M or CORE.mass)) or FALLBACK_W,
  Elements    = { { ShapeName = (CORE and CORE.model) or FALLBACK_MODEL } },
})