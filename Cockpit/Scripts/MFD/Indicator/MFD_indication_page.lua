-- F-117A Center MFD — DLIR/FLIR symbology overlay
-- Draws on top of the TV feed.
-- Params driven by Displays.lua (SRCH_TRCK_MODE, MLAS_TOGGLE, WHOT_TOGGLE, BOST_TOGGLE)
--
-- Coordinate system: (0,0) = display centre.
-- ±0.5 reaches roughly the edge of the MFD screen.
-- Tune GAP/ARM/GW/GH and text positions below if sizes look wrong in-game.

local S   = 0.20    -- overall overlay scale
local strokes=dofile(LockOn_Options.script_path.."display_strokes.lua")
local GAP = 0.03    -- crosshair centre gap radius
local ARM = 0.05    -- crosshair arm length (gap → tip)
local GW  = 0.04    -- tracking gate half-width
local GH  = 0.04    -- tracking gate half-height

-- ── Root element ────────────────────────────────────────────────────────────
-- Everything is a child of ROOT. Gated on mainpower so symbology disappears
-- with the rest of the avionics when power is off.
local ROOT              = CreateElement "ceSimple"
ROOT.name               = "F117_IRADS_SOURCE"
ROOT.init_pos           = {0, 0}
ROOT.element_params     = {"mainpower", "MFD_OVERLAY", "F117_IRADS_POWER"}
ROOT.controllers        = {{"parameter_in_range", 0, 0.9, 1.1}, {"parameter_in_range", 1, 0.9, 1.1}, {"parameter_in_range", 2, 0.9, 1.1}}
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
    local l = strokes.line({{x1,y1},{x2,y2}},1)
    l.name = create_guid_string()
    l.material       = MFD_GREEN
    return mfdProps(l, params, ctrls)
end

local function text(str, x, y, sd, align, params, ctrls)
    local t          = CreateElement "ceStringPoly"
    t.name           = create_guid_string()
    t.init_pos       = {x, y}
    t.value          = str
    t.material       = MFD_FONT
    local size = sd or MFD_SD_SM
    t.stringdefs     = {size[1]*1.3, size[1]*1.3*.65, size[1]*1.3*.13, size[4]}
    strokes.text(t)
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
local TK_P = {"F117_IRADS_LOCK_VALID"}
local TK_C = {{"parameter_in_range", 0, 0.9, 1.1}}
line(-GW * S,  GH * S,   GW * S,  GH * S,  TK_P, TK_C)   -- top
line(-GW * S, -GH * S,   GW * S, -GH * S,  TK_P, TK_C)   -- bottom
line(-GW * S, -GH * S,  -GW * S,  GH * S,  TK_P, TK_C)   -- left
line( GW * S, -GH * S,   GW * S,  GH * S,  TK_P, TK_C)   -- right

-- ── Mode text (bottom-left) ─────────────────────────────────────────────────
-- "SRCH" when mode 1, "TRCK" when mode 2.
text("SRCH", -0.070, -0.060, MFD_SD_XS, "LeftCenter",
    {"F117_IRADS_LOCK_VALID"}, {{"parameter_in_range", 0, -0.1, 0.1}})
text("POINT", -0.070, -0.060, MFD_SD_XS, "LeftCenter",
    {"F117_IRADS_LOCK_VALID"}, {{"parameter_in_range", 0, 0.9, 1.1}})

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
-- ARM is permission to lase; LASE requires a live native laser spot.
text("ARM",  0.070,  0.060, MFD_SD_XS, "RightCenter",
    {"F117_LASER_ARMED"}, {{"parameter_in_range", 0, 0.9, 1.1}})

text("LASE", 0.070, 0.045, MFD_SD_XS, "RightCenter",
    {"F117_LASER_FIRING"}, {{"parameter_in_range", 0, 0.9, 1.1}})

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

-- Actual EFM release-inhibit state, independent of decorative display modes.
local delivery_status = {
    [1]="MASTER SAFE", [2]="IRADS OFF", [3]="NO TARGET", [4]="NO STORE",
    [5]="LASER NOT READY", [6]="BAY CLOSED", [7]="NO SOLUTION",
    [8]="OUT OF RANGE", [9]="RELEASE READY", [10]="RELEASED",
    [11]="LAUNCH RETRY", [12]="ON GROUND", [13]="LAUNCH UNAVAILABLE", [14]="ALIGN TARGET"
}
for code,label in pairs(delivery_status) do
    text(label,0,0.040,MFD_SD_XS,"CenterCenter",{"F117_RELEASE_STATUS"},
        {{"parameter_in_range",0,code-0.1,code+0.1}})
end
text("M ARM",-0.070,0.045,MFD_SD_XS,"LeftCenter",{"F117_MASTER_ARM"},
    {{"parameter_in_range",0,0.9,1.1}})
local range=text("",0,-0.045,MFD_SD_XS,"CenterCenter",{"F117_IRADS_LOCK_RANGE","F117_IRADS_LOCK_VALID"},
    {{"text_using_parameter",0,0},{"parameter_in_range",1,0.9,1.1}})
range.formats={"RNG %.0f M"}
-- Flight time is predicted remaining time, not confirmed weapon impact/telemetry.
local flight=text("",0,-0.030,MFD_SD_XS,"CenterCenter",{"F117_STORE_FLIGHT_TIME"},
    {{"text_using_parameter",0,0},{"parameter_in_range",0,0.01,200.0}})
flight.formats={"EST TOF %.0f S"}

local station=text("",0,0.055,MFD_SD_XS,"CenterCenter",{"F117_WEAPON_STATION"},{{"text_using_parameter",0,0}})
station.formats={"STN %.0f"}

-- Estimated release limits in horizontal metres; RNG above is slant range.
local minimum=text("",-0.070,0.020,MFD_SD_XS,"LeftCenter",{"F117_RELEASE_MIN_RANGE","F117_RELEASE_CUE_VALID"},
    {{"text_using_parameter",0,0},{"parameter_in_range",1,0.9,1.1}})
minimum.formats={"MIN %.0f M"}
local maximum=text("",0.070,0.020,MFD_SD_XS,"RightCenter",{"F117_RELEASE_MAX_RANGE","F117_RELEASE_CUE_VALID"},
    {{"text_using_parameter",0,0},{"parameter_in_range",1,0.9,1.1}})
maximum.formats={"MAX %.0f M"}
