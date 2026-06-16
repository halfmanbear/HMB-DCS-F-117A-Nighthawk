-- F-117A Center MFD — DLIR/FLIR symbology overlay
-- Draws on top of the TV feed.
-- Params driven by Displays.lua (SRCH_TRCK_MODE, MLAS_TOGGLE, WHOT_TOGGLE, BOST_TOGGLE)
--
-- Coordinate system: (0,0) = display centre.
-- ±0.5 reaches roughly the edge of the MFD screen.
-- Tune GAP/ARM/GW/GH and text positions below if sizes look wrong in-game.

local S   = 0.20    -- overall overlay scale
local LW  = 0.0018  -- line stroke width
local GAP = 0.03    -- crosshair centre gap radius
local ARM = 0.05    -- crosshair arm length (gap → tip)
local GW  = 0.04    -- tracking gate half-width
local GH  = 0.04    -- tracking gate half-height

-- ── Root element ────────────────────────────────────────────────────────────
-- Everything is a child of ROOT. Gated on mainpower so symbology disappears
-- with the rest of the avionics when power is off.
local ROOT              = CreateElement "ceSimple"
ROOT.name               = create_guid_string()
ROOT.init_pos           = {0, 0}
ROOT.element_params     = {"mainpower", "MFD_OVERLAY"}
ROOT.controllers        = {{"parameter_in_range", 0, 0.9, 1.1}, {"parameter_in_range", 1, 0.9, 1.1}}
ROOT.h_clip_relation    = h_clip_relations.COMPARE
ROOT.level              = MFD_LEVEL
ROOT.collimated         = false
ROOT.additive_alpha     = true
ROOT.blend_mode         = blend_mode.IBM_REGULAR_ADDITIVE_ALPHA
Add(ROOT)

-- ── Internal helpers ────────────────────────────────────────────────────────
local function mfdProps(obj, params, ctrls)
    obj.name            = obj.name or create_guid_string()
    obj.parent_element  = ROOT.name
    obj.h_clip_relation = h_clip_relations.COMPARE
    obj.level           = MFD_LEVEL
    obj.collimated      = false
    obj.additive_alpha  = true
    obj.blend_mode      = blend_mode.IBM_REGULAR_ADDITIVE_ALPHA
    if params then obj.element_params = params end
    if ctrls  then obj.controllers    = ctrls  end
    Add(obj)
    return obj
end

local function line(x1, y1, x2, y2, params, ctrls)
    local l          = CreateElement "ceSimpleLineObject"
    l.name           = create_guid_string()
    l.vertices       = {{x1, y1}, {x2, y2}}
    l.width          = LW
    l.material       = MFD_GREEN
    return mfdProps(l, params, ctrls)
end

local function text(str, x, y, sd, align, params, ctrls)
    local t          = CreateElement "ceStringPoly"
    t.name           = create_guid_string()
    t.init_pos       = {x, y}
    t.value          = str
    t.material       = MFD_FONT
    t.stringdefs     = sd    or MFD_SD_SM
    t.alignment      = align or "CenterCenter"
    return mfdProps(t, params, ctrls)
end

-- ── Targeting reticle ───────────────────────────────────────────────────────
-- Four-segment crosshair with open centre (no lines cross the aimpoint).
line((-GAP - ARM) * S,  0,             (-GAP) * S,         0)           -- left arm
line( GAP * S,          0,             (GAP + ARM) * S,    0)           -- right arm
line( 0,                GAP * S,        0,                (GAP + ARM) * S) -- top arm
line( 0,               (-GAP - ARM) * S, 0,               (-GAP) * S)     -- bottom arm

-- Small filled dot at the exact aimpoint
local dot             = CreateElement "ceMeshPoly"
dot.name              = create_guid_string()
dot.init_pos          = {0, 0}
dot.primitivetype     = "triangles"
dot.material          = MFD_GREEN
set_circle(dot, 0.004, 0, 360, 12)
mfdProps(dot)

-- ── Tracking gate ───────────────────────────────────────────────────────────
-- Square box visible only when SRCH_TRCK_MODE == 2 (TRACK).
local TK_P = {"SRCH_TRCK_MODE"}
local TK_C = {{"parameter_in_range", 0, 1.9, 2.1}}
line(-GW * S,  GH * S,   GW * S,  GH * S,  TK_P, TK_C)   -- top
line(-GW * S, -GH * S,   GW * S, -GH * S,  TK_P, TK_C)   -- bottom
line(-GW * S, -GH * S,  -GW * S,  GH * S,  TK_P, TK_C)   -- left
line( GW * S, -GH * S,   GW * S,  GH * S,  TK_P, TK_C)   -- right

-- ── Mode text (bottom-left) ─────────────────────────────────────────────────
-- "SRCH" when mode 1, "TRCK" when mode 2.
text("SRCH", -0.070, -0.060, MFD_SD_XS, "LeftCenter",
    {"SRCH_TRCK_MODE"}, {{"parameter_in_range", 0, 0.9, 1.1}})
text("TRCK", -0.070, -0.060, MFD_SD_XS, "LeftCenter",
    {"SRCH_TRCK_MODE"}, {{"parameter_in_range", 0, 1.9, 2.1}})

-- ── IR polarity (top-left) ──────────────────────────────────────────────────
-- "W-HOT" when WHOT_TOGGLE == 1, "B-HOT" when 0.
text("W-HOT", -0.070,  0.060, MFD_SD_XS, "LeftCenter",
    {"WHOT_TOGGLE"}, {{"parameter_in_range", 0,  0.9, 1.1}})
text("B-HOT", -0.070,  0.060, MFD_SD_XS, "LeftCenter",
    {"WHOT_TOGGLE"}, {{"parameter_in_range", 0, -0.1, 0.1}})

-- ── CCRP profile readout (top-center) ───────────────────────────────────────
text("CCRP: GBU-31V1", 0.0, 0.070, MFD_SD_XS, "CenterCenter",
    {"F117_CCRP_PROFILE"}, {{"parameter_in_range", 0, -0.1, 0.1}})
text("CCRP: GBU-31V3", 0.0, 0.070, MFD_SD_XS, "CenterCenter",
    {"F117_CCRP_PROFILE"}, {{"parameter_in_range", 0, 0.9, 1.1}})
text("CCRP: GBU-32", 0.0, 0.070, MFD_SD_XS, "CenterCenter",
    {"F117_CCRP_PROFILE"}, {{"parameter_in_range", 0, 1.9, 2.1}})
text("CCRP: GBU-12", 0.0, 0.070, MFD_SD_XS, "CenterCenter",
    {"F117_CCRP_PROFILE"}, {{"parameter_in_range", 0, 2.9, 3.1}})
text("CCRP: GBU-27", 0.0, 0.070, MFD_SD_XS, "CenterCenter",
    {"F117_CCRP_PROFILE"}, {{"parameter_in_range", 0, 3.9, 4.1}})

-- ── Laser status (top-right) ────────────────────────────────────────────────
-- "LAS" when MLAS_TOGGLE == 1 (laser armed/firing).
text("LAS",  0.070,  0.060, MFD_SD_XS, "RightCenter",
    {"MLAS_TOGGLE"}, {{"parameter_in_range", 0, 0.9, 1.1}})

-- ── Boost indicator (bottom-right) ──────────────────────────────────────────
-- "BOST" when brightness boost is active.
text("BOST", 0.070, -0.060, MFD_SD_XS, "RightCenter",
    {"BOST_TOGGLE"}, {{"parameter_in_range", 0, 0.9, 1.1}})

-- ── Zoom level (bottom-center) ───────────────────────────────────────────────
-- WIDE=1.4×, MED=10×, NAR=80× — driven by IRADS_ZOOM (1/2/3).
text("WIDE", 0, -0.060, MFD_SD_XS, "CenterCenter",
    {"IRADS_ZOOM"}, {{"parameter_in_range", 0, 0.9, 1.1}})
text("MED",  0, -0.060, MFD_SD_XS, "CenterCenter",
    {"IRADS_ZOOM"}, {{"parameter_in_range", 0, 1.9, 2.1}})
text("NAR",  0, -0.060, MFD_SD_XS, "CenterCenter",
    {"IRADS_ZOOM"}, {{"parameter_in_range", 0, 2.9, 3.1}})
