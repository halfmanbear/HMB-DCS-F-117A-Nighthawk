local function find_core_agm65d()
  local wt = weapons_table and weapons_table.weapons and weapons_table.weapons.missiles
  if not wt then
    if env and env.warning then env.warning("[AGM65D] weapons_table.missiles not ready; using fallback.", true) end
    return nil
  end
  local core = wt["AGM_65D"]
  if not core then
    if env and env.warning then env.warning("[AGM65D] Core 'AGM_65D' not found in missiles table; using fallback.", true) end
    return nil
  end
  return core
end

local CORE = find_core_agm65d()

local DEFAULT_CX_PIL = 1.7 / 4096   -- ≈ 0.000415   :contentReference[oaicite:1]{index=1}
local FALLBACK_ATTR  = {wsType_Weapon,wsType_Missile,wsType_AS_Missile,AGM_65D} -- enum last
local FALLBACK_W     = 218.0
local FALLBACK_MODEL = "agm-65d"

declare_loadout({
  category    = CAT_MISSILES,
  CLSID       = "AGM_65_D",
  attribute   = (CORE and CORE.wsTypeOfWeapon) or FALLBACK_ATTR,
  Count       = 1,
  Cx_pil      = DEFAULT_CX_PIL,
  Picture     = "agm65.png",
  displayName = _("AGM-65D - Maverick D (IIR ASM)"),
  Weight      = (CORE and (CORE.M or CORE.mass)) or FALLBACK_W,
  Elements    = { { ShapeName = (CORE and CORE.model) or FALLBACK_MODEL } },
})