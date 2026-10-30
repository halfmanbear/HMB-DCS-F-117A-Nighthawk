dofile(LockOn_Options.script_path.."HUD/Indicator/HUD_def.lua")

----
local HUD_BASE                                 = CreateElement "ceSimple"
HUD_BASE.name                                  = create_guid_string()
HUD_BASE.init_pos                        = {0, -0.2, 0}   -- raise to keep symbology above HUD glass bottom clip (was -1.17343 → -0.9 → -0.5 → -0.2; tune toward 0 if still low)
HUD_BASE.element_params     = {"mainpower"}             
HUD_BASE.controllers        = {{"parameter_in_range" ,0,0.9,1.1} }
AddHudElement(HUD_BASE)



local HUDMounter          = CreateElement "ceSimple"
HUDMounter.name           = create_guid_string()
HUDMounter.init_rot       = {0, 0, 15}
HUDMounter.parent_element = HUD_BASE.name
AddHudElement(HUDMounter)

local nextWP           = CreateElement "ceMeshPoly"
nextWP.name            = create_guid_string()
nextWP.init_rot        = {90}
nextWP.parent_element  = HUDMounter.name
--nextWP.h_clip_relation = h_clip_relations.REWRITE_LEVEL
nextWP.material        = MakeMaterial(nil, {0, 255, 0, 255})
nextWP.element_params  = {"currentPhase", "nextWPRange", "nextWPType", "nextWPHUDAz", "nextWPHUDEl", "rollRad", "HUDBrightness"}
nextWP.controllers     = {{"parameter_in_range", 0, 6.9, 8.9}, {"parameter_in_range", 1, 0, 999}, {ctrl.inRange, 2, 1.9, 3.1}, {"move_up_down_using_parameter", 3, .6465}, {"move_left_right_using_parameter", 4, .6465}, {"rotate_using_parameter", 5, 1}, {ctrl.opacity, 6}}
set_circle(nextWP, 6 / 230, 4 / 230, 180, 8)
AddHudElement(nextWP)

local nextWPClampLine           = CreateElement "ceSimpleLineObject"
nextWPClampLine.name            = create_guid_string()
nextWPClampLine.parent_element  = HUDMounter.name
nextWPClampLine.init_rot        = {90}
nextWPClampLine.vertices        = {{0}, {0}}
nextWPClampLine.width           = 2 / 230 / 2
--nextWPClampLine.h_clip_relation = h_clip_relations.REWRITE_LEVEL
nextWPClampLine.material        = MakeMaterial(nil, {0, 255, 0, 255})
nextWPClampLine.element_params  = {"currentPhase", "nextWPHUDClamped", "nextWPType", "nextWPHUDAz", "nextWPHUDEl", "nextWPHUDAzUnclamped", "nextWPHUDElUnclamped", "HUDBrightness"}
nextWPClampLine.controllers     = {{"parameter_in_range", 0, 6.9, 8.9}, {"parameter_compare_with_number", 1, 1}, {ctrl.inRange, 2, 1.9, 3.1}, {"line_object_set_point_using_parameters", 0, 4, 3, .6465, .6465}, {"line_object_set_point_using_parameters", 1, 6, 5, .6465, .6465}, {ctrl.opacity, 7}}
AddHudElement(nextWPClampLine)

addHUDSimple("Next_WP_Offset_Text", nil, {-90}, nextWP, nil, nil, {"nextWPHUDClamped", "rollRad"}, {{ctrl.compareNum, 0, 1}, {ctrl.rotate, 1, -1}})
addHUDTextParam(nil, {0, -12.5 / 230}, "Next_WP_Offset_Text", hcr.rw, nil, nil, nil, "nextWPHUDClampText", nil, nil, strdefs.std)


----
local SID          = CreateElement "ceSimple"
SID.name           = create_guid_string()
SID.init_pos       = {0, -1.2}
SID.parent_element = HUD_BASE.name
SID.element_params = {"currentPhase", "AoA"} -- , "landingMode"}
SID.controllers    = {{"parameter_in_range", 0, 6.9, 8.9}, {"parameter_in_range", 1, -999, 14}} --, {ctrl.moveY, 2, .205}} Will add when the whole HUD moves with VelVec.
AddHudElement(SID)

add_text_hud_param(-.2, 0, "nextWPName", "HUDBrightness", "%s", SID, HUD_strdefs_text, "F-117_Font_green", "LeftCenter")

local wpRangeO10          = add_text_hud_param(.2, 0, "nextWPRange", "HUDBrightness", "R%0.0f", SID, HUD_strdefs_text, "F-117_Font_green", "LeftCenter")
wpRangeO10.element_params = {"nextWPRange", "HUDBrightness"}
wpRangeO10.controllers    = {{"parameter_in_range", 0, 9.9, 999}, {"text_using_parameter", 0}, {"opacity_using_parameter", 1}}
local wpRangeU10          = add_text_hud_param(.2, 0, "nextWPRange", "HUDBrightness", "R%0.1f", SID, HUD_strdefs_text, "F-117_Font_green", "LeftCenter")
wpRangeU10.element_params = {"nextWPRange", "HUDBrightness"}
wpRangeU10.controllers    = {{"parameter_in_range", 0, 0, 9.9}, {"text_using_parameter", 0}, {"opacity_using_parameter", 1}}



local nav_mode_ind                                          = add_text_hud("NAV", -0.69, -0.7, HUD_BASE , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
nav_mode_ind.element_params                  = {"masterMode"}
nav_mode_ind.controllers                     = {{"parameter_in_range" ,0,0.9,1.1} }

local bvr_mode_ind                                          = add_text_hud("BVR", -0.69, -0.7, HUD_BASE , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
bvr_mode_ind.element_params                  = {"masterMode"}
bvr_mode_ind.controllers                     = {{"parameter_in_range" ,0,1.9,2.1} }

local vs_mode_ind                                          = add_text_hud("VS", -0.69, -0.7, HUD_BASE , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
vs_mode_ind.element_params                  = {"masterMode"}
vs_mode_ind.controllers                     = {{"parameter_in_range" ,0,2.9,3.1} }

local bore_mode_ind                                 = add_text_hud("BORE", -0.69, -0.7, HUD_BASE , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
bore_mode_ind.element_params                  = {"masterMode"}
bore_mode_ind.controllers                     = {{"parameter_in_range" ,0,3.9,4.1} }

local HMDMode_ind                                         = add_text_hud("HMD", -0.69, -0.7, HUD_BASE , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
HMDMode_ind.element_params                  = {"masterMode"}
HMDMode_ind.controllers                     = {{"parameter_in_range" ,0,7.9,8.1} }

local lngt_mode_ind                                 = add_text_hud("LNGT", -0.69, -0.7, HUD_BASE , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
lngt_mode_ind.element_params                  = {"masterMode"}
lngt_mode_ind.controllers                     = {{"parameter_in_range" ,0,5.9,6.1} }


local Left_Side_Indication_base          = CreateElement "ceSimple"
Left_Side_Indication_base.name           = create_guid_string()
Left_Side_Indication_base.init_pos       = {-0.033, -0.15}
Left_Side_Indication_base.parent_element = HUD_BASE.name
AddHudElement(Left_Side_Indication_base)


--Auto throttle on/off indicator
local Auto_throttle_ind                           = add_text_hud("AT", -0.71, -0.04, Left_Side_Indication_base , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
Auto_throttle_ind.element_params          = {"AUTOTHROTTLE_ONOFF"}
Auto_throttle_ind.controllers             = {{"parameter_in_range" ,0,0.9,1.1} }
--Auto throttle mode 12 AoA

local Auto_throttle_mode12                          = add_text_hud("12", -0.65, -0.04, Left_Side_Indication_base , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
Auto_throttle_mode12.element_params  = {"AUTOTHROTTLE_MODE"}
Auto_throttle_mode12.controllers     = {{"parameter_in_range" ,0,0.4,0.6} }
--Auto throttle mode 14 AoA

local Auto_throttle_mode14                          = add_text_hud("14", -0.65, -0.04, Left_Side_Indication_base , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
Auto_throttle_mode14.element_params  = {"AUTOTHROTTLE_MODE"}
Auto_throttle_mode14.controllers     = {{"parameter_in_range" ,0,0.9,1.1} }


local Alfa_indicator         = add_text_hud_param(-0.63, 0.255, "AoA","HUDBrightness", "%0.0f", Left_Side_Indication_base, HUD_strdefs_digit, "F-117_Font_green")

local alfa_text                 =  add_text_hud("@", -0.71, 0.255, Left_Side_Indication_base , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")

local G_indicator                 = add_text_hud_param(-0.63, 0.18, "CUR_G","HUDBrightness", "%0.1f", Left_Side_Indication_base, HUD_strdefs_digit, "F-117_Font_green")

local G_text                         = add_text_hud("G", -0.71, 0.18, Left_Side_Indication_base , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")

-- Ground Speed
add_text_hud("GS", -0.71, 0.05, Left_Side_Indication_base, "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
local GS_indicator           = add_text_hud_param(-0.63, 0.05, "GS_HUD", "HUDBrightness", "%0.0f", Left_Side_Indication_base, HUD_strdefs_digit, "F-117_Font_green")

-- CAS
local KIAS_indicator         = add_text_hud_param(-0.63, -0.1, "CURR_IAS","HUDBrightness", "%0.0f", Left_Side_Indication_base, HUD_strdefs_digit, "F-117_Font_green")

local Mach_indicator                                 = CreateElement "ceStringPoly"
Mach_indicator.name                                 = create_guid_string()
Mach_indicator.parent_element                = Left_Side_Indication_base.name
Mach_indicator.material                                = fonts["F-117_Font_green"]
Mach_indicator.init_pos                         = {-0.67, -0.4}
Mach_indicator.alignment                         = "LeftCenter"
Mach_indicator.stringdefs                         = HUD_strdefs_digit
Mach_indicator.formats                                 = {"%0.0f","%s"}
Mach_indicator.element_params                 = {"machDecimals","HUDBrightness"}
Mach_indicator.controllers                         = {{"text_using_parameter",0,0},{"parameter_in_range" ,0, 3, 99.5},{"opacity_using_parameter", 1}}
AddHudElement(Mach_indicator)

local M_text                        = add_text_hud("M", -0.76, -0.4, Left_Side_Indication_base , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")

local MachComma                        = add_text_hud(".", -0.011, 0, Mach_indicator , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")

local Mach_indicator2                                 = CreateElement "ceStringPoly"
Mach_indicator2.name                                 = create_guid_string()
Mach_indicator2.parent_element                = Left_Side_Indication_base.name
Mach_indicator2.material                        = fonts["F-117_Font_green"]
Mach_indicator2.init_pos                         = {-0.718, -0.4}
Mach_indicator2.alignment                         = "LeftCenter"
Mach_indicator2.stringdefs                         = HUD_strdefs_digit
Mach_indicator2.formats                         = {"%0.2f","%s"}
Mach_indicator2.element_params                 = {"machWhole","HUDBrightness"}
Mach_indicator2.controllers                 = {{"text_using_parameter",0,0},{"parameter_in_range" ,0, 0.995, 3},{"opacity_using_parameter", 1}}
AddHudElement(Mach_indicator2)

----
local HUD_PITCH                                                 = CreateElement "ceSimple"
HUD_PITCH.name                                                  = create_guid_string()
HUD_PITCH.init_pos                                                = {0, 0}
HUD_PITCH.init_rot                                                = {0, 0, 15}
HUD_PITCH.parent_element                                = HUD_BASE.name
HUD_PITCH.element_params                                 = {"ROLL_HUD","PITCH_HUD"}
HUD_PITCH.controllers                                        = {{"rotate_using_parameter" ,0, 1.00},{"move_up_down_using_parameter",1, -0.6465}}
AddHudElement(HUD_PITCH)

local HorizonLineHUD                                         = CreateElement "ceSimple"
HorizonLineHUD.name                                                = create_guid_string()
HorizonLineHUD.init_pos                                        = {0, 0, 0}
HorizonLineHUD.parent_element                        = HUD_PITCH.name
AddHudElement(HorizonLineHUD)

-- Horizon line (procedural – left and right wings with centre gap for FPM symbol)
addHUDSimpleLine(nil, {0, 0}, nil, HUD_PITCH.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter", 0}}, 0.002, {{0.05, 0}, {1.8, 0}})
addHUDSimpleLine(nil, {0, 0}, nil, HUD_PITCH.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter", 0}}, 0.002, {{-1.8, 0}, {-0.05, 0}})

local AltitudeKeepingBoxes                                         = Hud_Horizon_Line(HUD_HORIZON, 1086, 1786, 2218, 2022, 1)
AltitudeKeepingBoxes.name                                        = create_guid_string()
AltitudeKeepingBoxes.init_pos                                = {0, -0.067, 0}
AltitudeKeepingBoxes.parent_element                        = HUD_PITCH.name
AltitudeKeepingBoxes.element_params                        = {"HUDBrightness", "ALT_HOLD"}
AltitudeKeepingBoxes.controllers                        = {{"opacity_using_parameter" ,0} ,{"parameter_in_range" ,1,0.9,1.1} }        
AddHudElement(AltitudeKeepingBoxes)

local TakeOffLinesVV                                         = Hud_Horizon_Line(HUD_HORIZON, 1148, 349, 2156, 906, 1)
TakeOffLinesVV.name                                                = create_guid_string()
TakeOffLinesVV.init_pos                                        = {0, 0.1605, 0}
TakeOffLinesVV.parent_element                        = HUD_PITCH.name
TakeOffLinesVV.element_params                        = {"CURRENT_PHASE_CO","CURRENT_PHASE_PAL","CURRENT_PHASE_STATIONARY","CURRENT_PHASE_TD","CURRENT_PHASE_LR","landingMode","HUDBrightness"}
TakeOffLinesVV.controllers                                = {{"parameter_in_range" ,0,-0.1,0.1},{"parameter_in_range" ,1,-0.1,0.1},{"parameter_in_range" ,2,-0.1,0.1},{"parameter_in_range" ,3,-0.1,0.1},{"parameter_in_range" ,4,-0.1,0.1},{"parameter_in_range" ,5,-0.1,0.1},{"opacity_using_parameter" ,6} }        
AddHudElement(TakeOffLinesVV)


-- ── Velocity Vector / FPM symbol (procedural) ──────────────────────────────
-- Container: moves with velocity vector, gated on ground phases and out-of-bounds limits
local VelocityVectorHUD = addHUDSimple(nil, {0, -0.0212}, nil, HUD_BASE.name, nil, nil,
    {"VELVEC_HUD_Y","VELVEC_HUD_X","CURRENT_PHASE_STATIONARY","CURRENT_PHASE_PARKED",
     "CURRENT_PHASE_TAXI","CURRENT_PHASE_TGR","CURRENT_PHASE_ROT","CURRENT_PHASE_LO",
     "CURRENT_PHASE_TD","CURRENT_PHASE_LR","VV_LimitedLower","VV_LimitedUpper","HUDBrightness"},
    {{"move_up_down_using_parameter",0,0.6465},{"move_left_right_using_parameter",1,0.6465},
     {"parameter_in_range",2,-0.1,0.1},{"parameter_in_range",3,-0.1,0.1},
     {"parameter_in_range",4,-0.1,0.1},{"parameter_in_range",5,-0.1,0.1},
     {"parameter_in_range",6,-0.1,0.1},{"parameter_in_range",7,-0.1,0.1},
     {"parameter_in_range",8,-0.1,0.1},{"parameter_in_range",9,-0.1,0.1},
     {"parameter_in_range",10,-0.1,0.1},{"parameter_in_range",11,-0.1,0.1},
     {"opacity_using_parameter",12}})

-- FPM circle ring
addHUDCircle(nil, {0,0}, nil, VelocityVectorHUD.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.030, 0.024, 360, 32)

-- FPM arms: left and right
addHUDSimpleLine(nil, {0,0}, nil, VelocityVectorHUD.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{0.030,0},{0.055,0}})
addHUDSimpleLine(nil, {0,0}, nil, VelocityVectorHUD.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{-0.055,0},{-0.030,0}})
-- FPM stem (bottom)
addHUDSimpleLine(nil, {0,0}, nil, VelocityVectorHUD.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{0,-0.055},{0,-0.030}})

-- Approach reference line (visible when NOT in PAL mode)
addHUDSimpleLine(nil, {0, 0.045}, nil, VelocityVectorHUD.name, nil, nil,
    {"HUDBrightness","CURRENT_PHASE_PAL"},
    {{"opacity_using_parameter",0},{"parameter_in_range",1,-0.1,0.1}},
    0.002, {{-0.025,0},{0.025,0}})

-- AoA bracket (PAL approach mode – moves with AoA)
addHUDSimpleLine(nil, {0, 0.098}, nil, VelocityVectorHUD.name, nil, nil,
    {"HUDBrightness","CURRENT_PHASE_PAL","AoA"},
    {{"opacity_using_parameter",0},{"parameter_in_range",1,0.9,1.1},
     {"move_up_down_using_parameter",2,-0.0006115}},
    0.002, {{-0.025,0},{0.025,0}})

-- ── Out-of-frame FPM indicator (FPM below HUD lower edge) ───────────────────
local VelocityVectorLimited = addHUDSimple(nil, {0, -1.29}, nil, HUD_BASE.name, nil, nil,
    {"HUDBrightness","VV_LimitedLower","VELVEC_HUD_X"},
    {{"opacity_using_parameter",0},{"parameter_in_range",1,0.9,1.1},
     {"move_left_right_using_parameter",2,0.6465}})

addHUDSimpleLine(nil, {0,0}, nil, VelocityVectorLimited.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.003, {{-0.05,0},{0.05,0}})

local Alfa_readout = add_text_hud_param(0, 0, "AoA","HUDBrightness", "%0.0f", VelocityVectorLimited, HUD_strdefs_digit, "F-117_Font_green")
Alfa_readout.init_pos = {0, 0, 0.1}

addHUDSimpleLine(nil, {0, 0.06}, nil, VelocityVectorLimited.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{-0.012,0},{0.012,0}})

-- ── Aircraft boresight cross (normal flight / ground, not combat, not PAL) ──
local X_AxisSymbol = addHUDSimple(nil, {0,-0.022}, nil, HUD_BASE.name, nil, nil,
    {"HUDBrightness","CURRENT_PHASE_CO","VELVEC_HUD_Y","VELVEC_HUD_X","CURRENT_PHASE_PAL","VV_LimitedLower"},
    {{"opacity_using_parameter",0},{"parameter_in_range",1,-0.1,0.1},
     {"move_up_down_using_parameter",2,0.6465},{"move_left_right_using_parameter",3,0.6465},
     {"parameter_in_range",4,-0.1,0.1},{"parameter_in_range",5,-0.1,0.1}})

addHUDSimpleLine(nil, {0,0}, nil, X_AxisSymbol.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{-0.055,0},{0.055,0}})
addHUDSimpleLine(nil, {0,0}, nil, X_AxisSymbol.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{0,-0.035},{0,0.035}})

-- Rotation cue tick (rises with TO_SPEED, hidden above overspeed threshold)
addHUDSimpleLine(nil, {0,-0.044}, nil, X_AxisSymbol.name, nil, nil,
    {"HUDBrightness","TO_SPEED","TO_OVERSPEED"},
    {{"opacity_using_parameter",0},{"move_up_down_using_parameter",1,0.000075},
     {"parameter_in_range",2,-0.1,0.5}},
    0.002, {{-0.025,0},{0.025,0}})

-- ── Boresight cross – combat mode (CURRENT_PHASE_CO == 1) ───────────────────
local X_AxisSymbol_Combat = addHUDSimple(nil, {0,-0.022}, nil, HUD_BASE.name, nil, nil,
    {"HUDBrightness","CURRENT_PHASE_CO"},
    {{"opacity_using_parameter",0},{"parameter_in_range",1,0.9,1.1}})

addHUDSimpleLine(nil, {0,0}, nil, X_AxisSymbol_Combat.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{-0.055,0},{0.055,0}})
addHUDSimpleLine(nil, {0,0}, nil, X_AxisSymbol_Combat.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{0,-0.035},{0,0.035}})
addHUDSimpleLine(nil, {0, 0.025}, nil, X_AxisSymbol_Combat.name, nil, nil,
    {"HUDBrightness","CURRENT_PHASE_CO"},
    {{"opacity_using_parameter",0},{"parameter_in_range",1,0.9,1.1}},
    0.002, {{-0.020,0},{0.020,0}})

local PositivePitchLinesHUD                         = Hud_Pitch_Lines2(HUD_POSITIVE_PITCH, 0, 0, 9984, 9984, 6.9)
PositivePitchLinesHUD.name                                = create_guid_string()
PositivePitchLinesHUD.init_pos                        = {0, 7.7, 0}
PositivePitchLinesHUD.init_rot                        = {180, 0, 0}
PositivePitchLinesHUD.parent_element        = HUD_PITCH.name
PositivePitchLinesHUD.element_params         = {"HUDBrightness","HEADING_HUD",}
PositivePitchLinesHUD.controllers                 = {{"opacity_using_parameter" ,0},{"rotate_using_parameter" ,1, math.rad(360)/-360},}
AddHudElement(PositivePitchLinesHUD)

local NegativePitchLinesHUD                         = Hud_Pitch_Lines2(HUD_NEGATIVE_PITCH, 0, 0, 9984, 9984, 6.9)
NegativePitchLinesHUD.name                                = create_guid_string()
NegativePitchLinesHUD.init_pos                        = {0, -7.7, 0}
NegativePitchLinesHUD.parent_element        = HUD_PITCH.name
NegativePitchLinesHUD.element_params         = {"HUDBrightness","HEADING_HUD",}
NegativePitchLinesHUD.controllers                 = {{"opacity_using_parameter" ,0},{"rotate_using_parameter" ,1, math.rad(360)/360},}
AddHudElement(NegativePitchLinesHUD)




WVR_CircleLNGT                = create_HUD_tex(HUD_AimingCircle, 0, 0, 1024, 1024, 0.1)
WVR_CircleLNGT.name           = create_guid_string()
WVR_CircleLNGT.init_pos       = {0, 0, 0}
WVR_CircleLNGT.parent_element = HUD_BASE.name
WVR_CircleLNGT.element_params = {"HUDBrightness", "masterMode", "RED_HUD"}
WVR_CircleLNGT.controllers    = {{"opacity_using_parameter", 0}, {"parameter_compare_with_number", 1, 6}, {"parameter_compare_with_number", 2, 1}}
AddHudElement(WVR_CircleLNGT)

WVR_CircleVSBORE_AA                = create_HUD_tex(HUD_AimingCircleThin, 0, 0, 1024, 1024, 0.21)
WVR_CircleVSBORE_AA.name           = create_guid_string()
WVR_CircleVSBORE_AA.init_pos       = {0, 0, 0}
WVR_CircleVSBORE_AA.parent_element = HUD_BASE.name
WVR_CircleVSBORE_AA.element_params = {"HUDBrightness", "masterMode", "F117_TYPE", "RED_HUD"}
WVR_CircleVSBORE_AA.controllers    = {{"opacity_using_parameter", 0}, {"parameter_in_range", 1, 2, 6}, {"parameter_compare_with_number", 2, 1}, {"parameter_compare_with_number", 2, 1}}
AddHudElement(WVR_CircleVSBORE_AA)


local glideSlope          = Hud_Horizon_Line(HUD_HORIZON, 849, 1567, 2451, 1581, 1)
glideSlope.name           = create_guid_string()
glideSlope.init_pos       = {0, -.23967}
glideSlope.parent_element = HUD_PITCH.name
glideSlope.element_params = {"HUDBrightness", "landingMode", "VELVEC_HUD_X"}
glideSlope.controllers    = {{"opacity_using_parameter", 0}, {"parameter_compare_with_number", 1, 1}, {"move_left_right_using_parameter", 2, .6465}}
AddHudElement(glideSlope)

local TST_G                 = MakeMaterial(nil,{0,0,100,100})

local HeadingScaleMask                                         = CreateElement "ceMeshPoly"                -- change shape 
HeadingScaleMask.name                                         =  create_guid_string()
HeadingScaleMask.primitivetype                         = "triangles"
HeadingScaleMask.material                                = TST_G
HeadingScaleMask.parent_element                        = HUD_BASE.name
HeadingScaleMask.vertices                                    = { {-0.15, 0.15 }, { 0.15 , 0.15}, { 0.15 ,-0.15 }, {-0.15 ,-0.15 }, }
HeadingScaleMask.indices                                = {0, 1, 2, 0, 2, 3}
HeadingScaleMask.init_pos                                = {0, 0.35, 0}
HeadingScaleMask.h_clip_relation                   = h_clip_relations.INCREASE_IF_LEVEL 
HeadingScaleMask.level                                   = HUD_DEFAULT_LEVEL
HeadingScaleMask.element_params                        = {"masterMode"}
HeadingScaleMask.controllers                        = { {"parameter_in_range",0, -1,7}  }
HeadingScaleMask.isvisible                                = false
Add(HeadingScaleMask)


local HeadingScale                                                 = Hud_Heading_Scale(HUD_HeadingScale, 0, 0, 8400, 200, 2)
HeadingScale.name                                                = create_guid_string()
HeadingScale.init_pos                                        = {1.714, 0.27, 0}
HeadingScale.parent_element                                = HUD_BASE.name
HeadingScale.element_params                                = {"HUDBrightness","HEADING_HUD"}
HeadingScale.controllers                                = { {"opacity_using_parameter" ,0},{"move_left_right_using_parameter", 1, -0.0012575}  }
HeadingScale.h_clip_relation                           = h_clip_relations.DECREASE_IF_LEVEL 
HeadingScale.level                                           = HUD_DEFAULT_LEVEL + 1
AddHudElement2(HeadingScale)

addHUDSimple("Heading_Tape_POI", {-1.714, -.0325}, nil, HeadingScale, nil, nil, {"currentPhase", "nextWPHeadingClampedHUD"}, {{ctrl.inRange, 0, 6.9, 8.9}, {ctrl.moveX, 1, .0012575}})

for i = -1, 1 do
	local firstVert = {0, -.03}

	if i == 0 then
		firstVert = {0}
	end

	addHUDSimpleLine(nil, {i * .012}, nil, "Heading_Tape_POI", hcr.rw, nil, nil, nil, .002, {firstVert, {0, -.05}})
end


local HeadingScaleArrow                                        = Hud_Horizon_Line(HUD_HORIZON, 793, 987, 912, 1106, 0.5) 
HeadingScaleArrow.name                                        = create_guid_string()
HeadingScaleArrow.init_pos                                = {0, 0.20, 0}
HeadingScaleArrow.parent_element                = HUD_BASE.name                                                
HeadingScaleArrow.h_clip_relation           = h_clip_relations.DECREASE_IF_LEVEL 
HeadingScaleArrow.level                                   = HUD_DEFAULT_LEVEL + 1
HeadingScaleArrow.element_params                = {"HUDBrightness"}
HeadingScaleArrow.controllers                        = { {"opacity_using_parameter" ,0}  }        
AddHudElement2(HeadingScaleArrow)

--         headingMode:set(1)                        -- 1 = True, 2 = Magnetic 

local heading_mode_ind                                         = add_text_hud("T", 0.30, 0.30, HUD_BASE , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
heading_mode_ind.element_params                  = {"headingMode"}
heading_mode_ind.controllers                     = {{"parameter_in_range" ,0, 0.9, 1.1} }

local heading_mode_ind                                         = add_text_hud("M", -0.30, 0.30, HUD_BASE , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
heading_mode_ind.element_params                  = {"headingMode"}
heading_mode_ind.controllers                     = {{"parameter_in_range" ,0, 1.9, 2.1} }



local HorizonLineHeadingDots                        = add_text_hud("!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!,,,,!", 0, 0, HUD_PITCH , "F-117_Font_green", HUD_HorizonLineHeading, "CenterCenter")
--lol
HorizonLineHeadingDots.init_pos                        = {0.03025, 0.0110,0.1}
HorizonLineHeadingDots.element_params        = {"HEADING_HUD"}
HorizonLineHeadingDots.controllers                = { {"move_left_right_using_parameter",0, -0.0110555}  }

addHUDCircle(nil, {-.03025, -.011}, 0, HorizonLineHeadingDots.name, nil, nil, {"currentPhase", "nextWPHeadingHUD"}, {{ctrl.inRange, 0, 6.9, 8.9}, {ctrl.moveX, 1, .0110555}}, .011, .011 - .004, 360, 10)

local TerrainAltitudeBox                                = Hud_Horizon_Line(HUD_HORIZON, 1861, 969, 2296, 1116, 0.8) 
TerrainAltitudeBox.name                                        = create_guid_string()
TerrainAltitudeBox.init_pos                                = {0.68, -0.68, 0}
TerrainAltitudeBox.init_rot                                = {0, 0, 0}
TerrainAltitudeBox.parent_element                = HUD_BASE.name                
TerrainAltitudeBox.element_params                = {"HUDBrightness", "ALTITUDE_HUD"}
TerrainAltitudeBox.controllers                        = { {"opacity_using_parameter" ,0}, {"parameter_in_range" ,1, 1000,81000}  }                
AddHudElement(TerrainAltitudeBox)

local TerrainAltitude         = add_text_hud_param(0, 0.028, "TERRAIN_ALT","HUDBrightness", "%0.0f", TerrainAltitudeBox, HUD_strdefs_digit, "F-117_Font_green")


local AltimeterScaleMask           = CreateElement "ceMeshPoly"                               -- change shape
AltimeterScaleMask.name            = create_guid_string()
AltimeterScaleMask.primitivetype   = "triangles"
AltimeterScaleMask.material        = TST_G
AltimeterScaleMask.parent_element  = HUD_BASE.name
AltimeterScaleMask.vertices        = {{0.5, -0.02}, {0.8, -0.02},
	{0.8,  -0.48}, {0.5, -0.48}}
AltimeterScaleMask.indices         = {0, 1, 2, 0, 2, 3}
AltimeterScaleMask.init_pos        = {0, 0, 0}
AltimeterScaleMask.init_rot        = {0, 0, 0}
AltimeterScaleMask.h_clip_relation = h_clip_relations.INCREASE_IF_LEVEL
AltimeterScaleMask.level           = HUD_DEFAULT_LEVEL
AltimeterScaleMask.element_params  = {"altitudeDeclutt"}
AltimeterScaleMask.controllers     = {{"parameter_compare_with_number", 0, 0}}
AltimeterScaleMask.isvisible       = false
Add(AltimeterScaleMask)

local AltimeterScaleArrow                                = Hud_Horizon_Line(HUD_HORIZON, 793, 987, 912, 1106, 0.5) 
AltimeterScaleArrow.name                                = create_guid_string()
AltimeterScaleArrow.init_pos                        = {0.56, -0.282, 0}
AltimeterScaleArrow.init_rot                        = {-90, 0, 0}
AltimeterScaleArrow.parent_element                = HUD_BASE.name                                                
AltimeterScaleArrow.h_clip_relation          = h_clip_relations.DECREASE_IF_LEVEL 
AltimeterScaleArrow.level                                   = HUD_DEFAULT_LEVEL + 1
AltimeterScaleArrow.element_params                = {"HUDBrightness"}
AltimeterScaleArrow.controllers                        = { {"opacity_using_parameter" ,0}  }
AddHudElement2(AltimeterScaleArrow)

--ALTITUDE_MODE:set(1)                -- 1 = barometric, 2 = Radar 

local Altitude_mode_ind                                         = add_text_hud("77", 0.58, -0.50, HUD_BASE , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
Altitude_mode_ind.element_params                          = {"ALTITUDE_MODE","RadarAltAvail"}
Altitude_mode_ind.controllers                             = {{"parameter_in_range" ,0, 1.9, 2.1},{"parameter_in_range" ,1, 0.9, 1.1} }


local ALTIMETER_BASE                                 = CreateElement "ceSimple"
ALTIMETER_BASE.name                                  = create_guid_string()
ALTIMETER_BASE.init_pos                                = {0, 0.718}
ALTIMETER_BASE.parent_element                = HUD_BASE.name
ALTIMETER_BASE.element_params             = {"altTape"}             
ALTIMETER_BASE.controllers                = {{"move_up_down_using_parameter",0, -0.0001980675} }
AddHudElement(ALTIMETER_BASE)


local ThousandsOffsetX = 0.655        
local ThousandsOffsetY = -1

local HundredsOffsetX = 0.727
local HundredsOffsetY = -1.005
local AltLineOffset = 0.15
local AltTextOffset = 0.15

local counter = - 1
local hundreds = 0
local Thousands = 0

for i = 0,810 do
                local AltLine                                                 = Hud_Heading_Scale(HUD_HeadingScale, 193, 105, 207, 179, 2)
                AltLine.name                                                = create_guid_string()
                AltLine.init_pos                                        = {0.6, -1 + i * AltLineOffset, 0}
                AltLine.init_rot                                        = {90, 0, 0}
                AltLine.parent_element                                = ALTIMETER_BASE.name
                AltLine.element_params                                = {"HUDBrightness"}
                AltLine.controllers                                        = { {"opacity_using_parameter" ,0}  }
                AddHudElement3(AltLine)

                local AltLineShort                                                 = Hud_Heading_Scale(HUD_HeadingScale, 293, 141, 307, 179, 2)
                AltLineShort.name                                                = create_guid_string()
                AltLineShort.init_pos                                        = {0.591, -1.075 + i * AltLineOffset, 0}
                AltLineShort.init_rot                                        = {90, 0, 0}
                AltLineShort.parent_element                                = ALTIMETER_BASE.name
                AltLineShort.element_params                                = {"HUDBrightness"}
                AltLineShort.controllers                                = { {"opacity_using_parameter" ,0}  }
                AddHudElement3(AltLineShort)

                counter = counter + 1

                if counter == 10 then
                        counter = 0
                        Thousands = Thousands + 1
                end

                hundreds = counter

                if Thousands < 1 then

                        if hundreds == 0 then
                                local Ahundreds                = add_text_hud2(hundreds, HundredsOffsetX - 0.075, HundredsOffsetY+ i * AltTextOffset, ALTIMETER_BASE , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
                        else 
                                local Ahundreds                = add_text_hud2(hundreds .. "00", HundredsOffsetX - 0.05, HundredsOffsetY+ i * AltTextOffset, ALTIMETER_BASE , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
                        end

                elseif Thousands >= 1 and Thousands < 10 then

                        local AThousands                = add_text_hud2(Thousands, ThousandsOffsetX + 0.02, ThousandsOffsetY + i * AltTextOffset, ALTIMETER_BASE , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")

                        local Ahundreds                        = add_text_hud2(hundreds .. "00", HundredsOffsetX, HundredsOffsetY+ i * AltTextOffset, ALTIMETER_BASE , "F-117_Font_green", HUD_Heading_digit, "CenterCenter")

                else
                        local AThousands                = add_text_hud2(Thousands, ThousandsOffsetX , ThousandsOffsetY + i * AltTextOffset, ALTIMETER_BASE , "F-117_Font_green", HUD_strdefs_text, "CenterCenter")

                        local Ahundreds                        = add_text_hud2(hundreds .. "00", HundredsOffsetX, HundredsOffsetY+ i * AltTextOffset, ALTIMETER_BASE , "F-117_Font_green", HUD_Heading_digit, "CenterCenter")

                end

end

local RAltitudeInd          = add_text_hud("R", .6, -.6, AltimeterScaleMask, "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
RAltitudeInd.element_params = {"HUDBrightness", "altMode"}
RAltitudeInd.controllers    = {{"opacity_using_parameter", 0}, {"parameter_compare_with_number", 1, 2}}


-- Air to ground mode altimeter
local A2G_Altitude_BASE          = CreateElement "ceSimple"
A2G_Altitude_BASE.name           = create_guid_string()
A2G_Altitude_BASE.parent_element = HUD_BASE.name
A2G_Altitude_BASE.init_pos       = {0.65} -- {0, -1.345,0}
A2G_Altitude_BASE.element_params = {"altitudeDeclutt"}
A2G_Altitude_BASE.controllers    = {{"parameter_compare_with_number", 0, 1}}
AddHudElement(A2G_Altitude_BASE)

local A2G_Altitude          = add_text_hud("A", 0, -0.15, A2G_Altitude_BASE, "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
A2G_Altitude.element_params = {"HUDBrightness", "altMode"}
A2G_Altitude.controllers    = {{"opacity_using_parameter", 0}, {"parameter_compare_with_number", 1, 1}}

local A2G_Altitude_Readout          = add_text_hud_param(0, -0.21, "txtAlt", "HUDBrightness", "%0.0f", A2G_Altitude_BASE, HUD_strdefs_digit, "F-117_Font_green")
A2G_Altitude_Readout.element_params = {"HUDBrightness", "altMode", "txtAlt"}
A2G_Altitude_Readout.controllers    = {{"opacity_using_parameter", 0}, {"parameter_compare_with_number", 1, 1}, {"text_using_parameter", 2}}

local A2G_RAltitude          = add_text_hud("RA", 0, -0.15, A2G_Altitude_BASE, "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
A2G_RAltitude.element_params = {"HUDBrightness", "altMode"}
A2G_RAltitude.controllers    = {{"opacity_using_parameter", 0}, {"parameter_compare_with_number", 1, 2}}

local A2G_RAltitude_Readout          = add_text_hud_param(0, -0.21, "txtRalt", "HUDBrightness", "%0.0f", A2G_Altitude_BASE, HUD_strdefs_digit, "F-117_Font_green")
A2G_RAltitude_Readout.element_params = {"HUDBrightness", "altMode", "txtRalt"}
A2G_RAltitude_Readout.controllers    = {{"opacity_using_parameter", 0}, {"parameter_compare_with_number", 1, 2}, {"text_using_parameter", 2}}


-- Release cue / window marker for IRADS designation
local ReleaseCueBase = addHUDSimple(nil, {0, -0.36}, nil, HUD_BASE.name, nil, nil,
    {"HUDBrightness","F117_RELEASE_CUE_VALID"},
    {{"opacity_using_parameter",0},{"parameter_compare_with_number",1,1}})

addHUDSimpleLine(nil, {0,0}, nil, ReleaseCueBase.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{-0.18,0},{0.18,0}})

local ReleaseCueCursor = addHUDSimple(nil, {0,0}, nil, ReleaseCueBase.name, nil, nil,
    {"F117_RELEASE_CUE_ERROR"}, {{"move_left_right_using_parameter",0,0.0015}})
addHUDSimpleLine(nil, {0,0}, nil, ReleaseCueCursor.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{0,-0.035},{0,0.035}})

local ReleaseCueTTG = add_text_hud_param(0.23, 0.03, "F117_RELEASE_CUE_TTG", "HUDBrightness",
    "T%0.1f", ReleaseCueBase, HUD_strdefs_text, "F-117_Font_green")
ReleaseCueTTG.element_params = {"F117_RELEASE_CUE_TTG", "HUDBrightness"}
ReleaseCueTTG.controllers = {{"parameter_in_range",0,0,9999},{"text_using_parameter",0},{"opacity_using_parameter",1}}

local ReleaseCueReady = add_text_hud("REL", -0.23, 0.03, ReleaseCueBase, "F-117_Font_green", HUD_strdefs_text, "CenterCenter")
ReleaseCueReady.element_params = {"F117_RELEASE_CUE_IN_ZONE", "HUDBrightness"}
ReleaseCueReady.controllers = {{"parameter_compare_with_number",0,1},{"opacity_using_parameter",1}}
local SpeedScaleMask                                         = CreateElement "ceMeshPoly"                -- change shape 
SpeedScaleMask.name                                         =  create_guid_string()
SpeedScaleMask.primitivetype                         = "triangles"
SpeedScaleMask.material                                        = TST_G
SpeedScaleMask.parent_element                        = HUD_BASE.name
SpeedScaleMask.vertices                                            = { {-0.6, -0.02 }, { -0.639 , -0.02},
                                                                                                { -0.639 ,-0.48 }, {-0.6 ,-0.48 }, }
SpeedScaleMask.indices                                        = {0, 1, 2, 0, 2, 3}
SpeedScaleMask.init_pos                                        = {0, 0, 0}
SpeedScaleMask.init_rot                                        = {0, 0, 15}
SpeedScaleMask.h_clip_relation                   = h_clip_relations.INCREASE_IF_LEVEL 
SpeedScaleMask.level                                           = HUD_DEFAULT_LEVEL
--SpeedScaleMask.element_params                        = {"masterMode"}
--SpeedScaleMask.controllers                                = { {"parameter_in_range",0, -1,7}  }
SpeedScaleMask.isvisible                                = false
Add(SpeedScaleMask)


local SpeedScaleArrow                                = Hud_Horizon_Line(HUD_HORIZON, 793, 987, 912, 1106, 0.5) 
SpeedScaleArrow.name                                = create_guid_string()
SpeedScaleArrow.init_pos                        = {-0.68, -0.282, 0}
SpeedScaleArrow.init_rot                        = {-90, 0, 0}
SpeedScaleArrow.parent_element                = HUD_BASE.name                
SpeedScaleArrow.element_params                = {"HUDBrightness"}
SpeedScaleArrow.controllers                        = { {"opacity_using_parameter" ,0}  }                                                                        
AddHudElement(SpeedScaleArrow)

local SpeedScale                                = Hud_Horizon_Line(HUD_HORIZON, 3183, 1, 3221, 1251, 1.0) 
SpeedScale.name                                        = create_guid_string()
SpeedScale.init_pos                                = {-0.635, 0.131 ,0}
SpeedScale.init_rot                            = {0, 0, 15}
SpeedScale.parent_element                = HUD_BASE.name        
SpeedScale.h_clip_relation          = h_clip_relations.DECREASE_IF_LEVEL 
SpeedScale.level                                   = HUD_DEFAULT_LEVEL + 1                
SpeedScale.element_params             = {"HUDBrightness","CURR_IAS"}             
SpeedScale.controllers                = {{"opacity_using_parameter" ,0} ,{"move_up_down_using_parameter",1, -0.000078425} }                
AddHudElement2(SpeedScale)


local GroundCollisionWarning                                = create_HUD_GCW(HUD_GroundCollisionWarning, 184, 458, 2682, 1348, 0.333) 
GroundCollisionWarning.name                                        = create_guid_string()
GroundCollisionWarning.init_pos                                = {0, -0.3, 0}
GroundCollisionWarning.init_rot                                = {0, 0, 0}
GroundCollisionWarning.parent_element                = HUD_BASE.name                
GroundCollisionWarning.element_params                = {"HUDBrightness","PULLUPQUE", "ROLL_HUD", "VELVEC_HUD_Y","CURRENT_PHASE_STATIONARY","CURRENT_PHASE_PARKED","CURRENT_PHASE_TAXI",
                                                                                                "CURRENT_PHASE_TGR","CURRENT_PHASE_ROT","CURRENT_PHASE_TD","CURRENT_PHASE_LR","CURRENT_PHASE_PAL", "PULLMORE","VELVEC_HUD_X"}
GroundCollisionWarning.controllers                        = { {"opacity_using_parameter" ,0}, {"parameter_in_range",1, -10000,0},{"rotate_using_parameter" ,2, 1.00},
                                                                                                {"move_up_down_using_parameter",3, 0.322} ,{"parameter_compare_with_number",4, 0},{"parameter_compare_with_number",5, 0},
                                                                                                {"parameter_compare_with_number",6, 0},{"parameter_compare_with_number",7, 0},{"parameter_compare_with_number",8, 0},
                                                                                                {"parameter_compare_with_number",9, 0},{"parameter_compare_with_number",10, 0},{"parameter_compare_with_number",11, 0}, {"parameter_in_range",12, -0.99,0.5},{"move_left_right_using_parameter",13, 0.322} }                                                                        
AddHudElement(GroundCollisionWarning)

local GCW_Arrow_L                                        = create_HUD_GCW(HUD_GroundCollisionWarning, 23, 23, 508, 443, 0.333) 
GCW_Arrow_L.name                                        = create_guid_string()
GCW_Arrow_L.init_pos                                = {-0.2655, 0.09, 0}
GCW_Arrow_L.init_rot                                = {0, 0, 0}
GCW_Arrow_L.parent_element                        = GroundCollisionWarning.name        
GCW_Arrow_L.element_params                        = {"HUDBrightness","PULLUPQUE", "PULLMORE"}
GCW_Arrow_L.controllers                                = { {"opacity_using_parameter" ,0},{"move_up_down_using_parameter",1, -0.000006}, {"parameter_in_range",2, -0.99,0.5}  }                                                                        
AddHudElement(GCW_Arrow_L)

local GCW_Arrow_R                                        = create_HUD_GCW(HUD_GroundCollisionWarning, 23, 23, 508, 443, 0.333) 
GCW_Arrow_R.name                                        = create_guid_string()
GCW_Arrow_R.init_pos                                = {0.2655, 0.09, 0}
GCW_Arrow_R.init_rot                                = {0, 0, 0}
GCW_Arrow_R.parent_element                        = GroundCollisionWarning.name        
GCW_Arrow_R.element_params                        = {"HUDBrightness","PULLUPQUE", "PULLMORE"}
GCW_Arrow_R.controllers                                = { {"opacity_using_parameter" ,0},{"move_up_down_using_parameter",1, -0.000006}, {"parameter_in_range",2, -0.99,0.5}  }                                                                        
AddHudElement(GCW_Arrow_R)







-- HUD RWR
local RWRBase          = CreateElement "ceSimple"
RWRBase.name           = create_guid_string()
RWRBase.parent_element = HUD_BASE.name
RWRBase.init_pos       = {.7, -1.1}
RWRBase.element_params = {"currentPhase", "activeRWRThreats"}
RWRBase.controllers    = {{"parameter_in_range", 0, 5.9, 8.1}, {"parameter_in_range", 1, 0, 99}}
AddHudElement(RWRBase)

for i = 0, 90, 90 do
	local RWRCross          = CreateElement "ceSimpleLineObject"
	RWRCross.name           = create_guid_string()
	RWRCross.material       = MakeMaterial(nil, {0, 255, 0, 255})
	RWRCross.width          = .003
	RWRCross.init_rot       = {i}
	RWRCross.vertices       = {{-.6465 * math.rad(2.5 / 2) * 10}, {.6465 * math.rad(2.5 / 2) * 10}}
	RWRCross.parent_element = RWRBase.name
	RWRCross.element_params = {"HUDBrightness"}
	RWRCross.controllers    = {{"opacity_using_parameter", 0}}
	AddHudElement(RWRCross)
end

for i = 1, 20 do
	local index = ""
	if i < 10 then
		index = "_0" .. i .. "_"
	else
		index = "_" .. i .. "_"
	end

	local baseName = "RWR_Contact_" .. index
	local param = "RWR_CONTACT" .. index



	local rotBase          = CreateElement "ceSimple"
	rotBase.name           = baseName .. "Base"
	rotBase.parent_element = RWRBase.name
	rotBase.element_params = {param .. "heading", param .. "POWER", param .. "threat", "HUDBrightness"}
	rotBase.controllers    = {{"rotate_using_parameter", 0, -1}, {"parameter_in_range", 1, 0, 1.1}, {"parameter_compare_with_number", 2, 1}, {"opacity_using_parameter", 3}}
	AddHudElement(rotBase)


	local powerBase          = Copy(rotBase)
	powerBase.name           = baseName .. "Ground_Power_Base"
	powerBase.init_pos       = {0, .6465 * math.rad(2.5 / 2) * 10}
	powerBase.parent_element = rotBase.name
	powerBase.element_params = {param .. "range", "HUDBrightness"}
	powerBase.controllers    = {{"move_up_down_using_parameter", 0, 0.4}, {"opacity_using_parameter", 1}}
	AddHudElement(powerBase)

	for j = 0, 7 do
		local starLine          = CreateElement "ceSimpleLineObject"
		starLine.name           = create_guid_string()
		starLine.material       = MakeMaterial(nil, {0, 255, 0, 255})
		starLine.width          = .003
		starLine.vertices       = {{.6465 * math.rad(.1 / 2) * 10}, {.6465 * math.rad(.3 / 2) * 10}}
		starLine.init_rot       = {j * 45}
		starLine.parent_element = baseName .. "Ground_Power_Base"
		starLine.element_params = {param .. "heading", param .. "launchBlink", "HUDBrightness"}
		starLine.controllers    = {{"rotate_using_parameter", 0, 1}, {"parameter_compare_with_number", 1, 1}, {"opacity_using_parameter", 2}}
		AddHudElement(starLine)
	end


	local missileLine          = CreateElement "ceSimpleLineObject"
	missileLine.name           = create_guid_string()
	missileLine.material       = MakeMaterial(nil, {0, 255, 0, 255})
	missileLine.parent_element = baseName .. "Base"
	missileLine.width          = .003
	missileLine.vertices       = {{0, .6465 * math.rad(2.5 / 2) * 10}, {0, 0}}
	missileLine.element_params = {param .. "launch", "HUDBrightness"}
	missileLine.controllers    = {{"parameter_compare_with_number", 0, 1}, {"opacity_using_parameter", 1}}
	AddHudElement(missileLine)
end






-- Below are numbers indicating pitch angle

local PosPitch175_Base                                                 = CreateElement "ceSimple"
PosPitch175_Base.name                                                  = create_guid_string()
PosPitch175_Base.init_pos                                                = {0, 0}
PosPitch175_Base.init_rot                                                = {5, 0, 0}
PosPitch175_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch175_Base)


pitch1_175                                        = add_text_hud("+10", 0, 0, PosPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_175.init_pos                        = {0, 6.82, 0.10}
pitch1_175.init_rot                        = {180, 0, 0}

pitch2_175                                        = add_text_hud("+20", 0, 0, PosPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_175.init_pos                        = {0, 5.96, 0.10}
pitch2_175.init_rot                        = {180, 0, 0}

pitch3_175                                        = add_text_hud("+30", 0, 0, PosPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_175.init_pos                        = {0, 5.098, 0.10}
pitch3_175.init_rot                        = {180, 0, 0}

pitch4_175                                        = add_text_hud("+40", 0, 0, PosPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_175.init_pos                        = {0, 4.234, 0.10}
pitch4_175.init_rot                        = {180, 0, 0}

pitch5_175                                        = add_text_hud("+50", 0, 0, PosPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_175.init_pos                        = {0, 3.37, 0.10}
pitch5_175.init_rot                        = {180, 0, 0}

pitch6_175                                        = add_text_hud("+60", 0, 0, PosPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_175.init_pos                        = {0, 2.51, 0.10}
pitch6_175.init_rot                        = {180, 0, 0}



--
local PosPitch155_Base                                                 = CreateElement "ceSimple"
PosPitch155_Base.name                                                  = create_guid_string()
PosPitch155_Base.init_pos                                                = {0, 0}
PosPitch155_Base.init_rot                                                = {25, 0, 0}
PosPitch155_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch155_Base)


pitch1_155                                        = add_text_hud("+10", 0, 0, PosPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_155.init_pos                        = {0, 6.82, 0.10}
pitch1_155.init_rot                        = {180, 0, 0}

pitch2_155                                        = add_text_hud("+20", 0, 0, PosPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_155.init_pos                        = {0, 5.96, 0.10}
pitch2_155.init_rot                        = {180, 0, 0}

pitch3_155                                        = add_text_hud("+30", 0, 0, PosPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_155.init_pos                        = {0, 5.098, 0.10}
pitch3_155.init_rot                        = {180, 0, 0}

pitch4_155                                        = add_text_hud("+40", 0, 0, PosPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_155.init_pos                        = {0, 4.234, 0.10}
pitch4_155.init_rot                        = {180, 0, 0}

pitch5_155                                        = add_text_hud("+50", 0, 0, PosPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_155.init_pos                        = {0, 3.37, 0.10}
pitch5_155.init_rot                        = {180, 0, 0}

pitch6_155                                        = add_text_hud("+60", 0, 0, PosPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_155.init_pos                        = {0, 2.51, 0.10}
pitch6_155.init_rot                        = {180, 0, 0}

pitch7_155                                        = add_text_hud("+70", 0, 0, PosPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch7_155.init_pos                        = {0, 1.65, 0.10}
pitch7_155.init_rot                        = {180, 0, 0}

--

local PosPitch135_Base                                                 = CreateElement "ceSimple"
PosPitch135_Base.name                                                  = create_guid_string()
PosPitch135_Base.init_pos                                                = {0, 0}
PosPitch135_Base.init_rot                                                = {45, 0, 0}
PosPitch135_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch135_Base)


pitch1_135                                        = add_text_hud("+10", 0, 0, PosPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_135.init_pos                        = {0, 6.82, 0.10}
pitch1_135.init_rot                        = {180, 0, 0}

pitch2_135                                        = add_text_hud("+20", 0, 0, PosPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_135.init_pos                        = {0, 5.96, 0.10}
pitch2_135.init_rot                        = {180, 0, 0}

pitch3_135                                        = add_text_hud("+30", 0, 0, PosPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_135.init_pos                        = {0, 5.098, 0.10}
pitch3_135.init_rot                        = {180, 0, 0}

pitch4_135                                        = add_text_hud("+40", 0, 0, PosPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_135.init_pos                        = {0, 4.234, 0.10}
pitch4_135.init_rot                        = {180, 0, 0}

pitch5_135                                        = add_text_hud("+50", 0, 0, PosPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_135.init_pos                        = {0, 3.37, 0.10}
pitch5_135.init_rot                        = {180, 0, 0}

pitch6_135                                        = add_text_hud("+60", 0, 0, PosPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_135.init_pos                        = {0, 2.51, 0.10}
pitch6_135.init_rot                        = {180, 0, 0}



--

local PosPitch115_Base                                                 = CreateElement "ceSimple"
PosPitch115_Base.name                                                  = create_guid_string()
PosPitch115_Base.init_pos                                                = {0, 0}
PosPitch115_Base.init_rot                                                = {65, 0, 0}
PosPitch115_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch115_Base)


pitch1_115                                        = add_text_hud("+10", 0, 0, PosPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_115.init_pos                        = {0, 6.82, 0.10}
pitch1_115.init_rot                        = {180, 0, 0}

pitch2_115                                        = add_text_hud("+20", 0, 0, PosPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_115.init_pos                        = {0, 5.96, 0.10}
pitch2_115.init_rot                        = {180, 0, 0}

pitch3_115                                        = add_text_hud("+30", 0, 0, PosPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_115.init_pos                        = {0, 5.098, 0.10}
pitch3_115.init_rot                        = {180, 0, 0}

pitch4_115                                        = add_text_hud("+40", 0, 0, PosPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_115.init_pos                        = {0, 4.234, 0.10}
pitch4_115.init_rot                        = {180, 0, 0}

pitch5_115                                        = add_text_hud("+50", 0, 0, PosPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_115.init_pos                        = {0, 3.37, 0.10}
pitch5_115.init_rot                        = {180, 0, 0}

pitch6_115                                        = add_text_hud("+60", 0, 0, PosPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_115.init_pos                        = {0, 2.51, 0.10}
pitch6_115.init_rot                        = {180, 0, 0}




local PosPitch95_Base                                                 = CreateElement "ceSimple"
PosPitch95_Base.name                                                  = create_guid_string()
PosPitch95_Base.init_pos                                                = {0, 0}
PosPitch95_Base.init_rot                                                = {85, 0, 0}
PosPitch95_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch95_Base)


pitch1_95                                        = add_text_hud("+10", 0, 0, PosPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_95.init_pos                        = {0, 6.82, 0.10}
pitch1_95.init_rot                        = {180, 0, 0}

pitch2_95                                        = add_text_hud("+20", 0, 0, PosPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_95.init_pos                        = {0, 5.96, 0.10}
pitch2_95.init_rot                        = {180, 0, 0}

pitch3_95                                        = add_text_hud("+30", 0, 0, PosPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_95.init_pos                        = {0, 5.098, 0.10}
pitch3_95.init_rot                        = {180, 0, 0}

pitch4_95                                        = add_text_hud("+40", 0, 0, PosPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_95.init_pos                        = {0, 4.234, 0.10}
pitch4_95.init_rot                        = {180, 0, 0}

pitch5_95                                        = add_text_hud("+50", 0, 0, PosPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_95.init_pos                        = {0, 3.37, 0.10}
pitch5_95.init_rot                        = {180, 0, 0}

pitch6_95                                        = add_text_hud("+60", 0, 0, PosPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_95.init_pos                        = {0, 2.51, 0.10}
pitch6_95.init_rot                        = {180, 0, 0}

pitch7_95                                        = add_text_hud("+70", 0, 0, PosPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch7_95.init_pos                        = {0, 1.65, 0.10}
pitch7_95.init_rot                        = {180, 0, 0}

local PosPitch75_Base                                                 = CreateElement "ceSimple"
PosPitch75_Base.name                                                  = create_guid_string()
PosPitch75_Base.init_pos                                                = {0, 0}
PosPitch75_Base.init_rot                                                = {105, 0, 0}
PosPitch75_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch75_Base)


pitch1_75                                        = add_text_hud("+10", 0, 0, PosPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_75.init_pos                        = {0, 6.82, 0.10}
pitch1_75.init_rot                        = {180, 0, 0}

pitch2_75                                        = add_text_hud("+20", 0, 0, PosPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_75.init_pos                        = {0, 5.96, 0.10}
pitch2_75.init_rot                        = {180, 0, 0}

pitch3_75                                        = add_text_hud("+30", 0, 0, PosPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_75.init_pos                        = {0, 5.098, 0.10}
pitch3_75.init_rot                        = {180, 0, 0}

pitch4_75                                        = add_text_hud("+40", 0, 0, PosPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_75.init_pos                        = {0, 4.234, 0.10}
pitch4_75.init_rot                        = {180, 0, 0}

pitch5_75                                        = add_text_hud("+50", 0, 0, PosPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_75.init_pos                        = {0, 3.37, 0.10}
pitch5_75.init_rot                        = {180, 0, 0}

pitch6_75                                        = add_text_hud("+60", 0, 0, PosPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_75.init_pos                        = {0, 2.51, 0.10}
pitch6_75.init_rot                        = {180, 0, 0}



local PosPitch55_Base                                                 = CreateElement "ceSimple"
PosPitch55_Base.name                                                  = create_guid_string()
PosPitch55_Base.init_pos                                                = {0, 0}
PosPitch55_Base.init_rot                                                = {125, 0, 0}
PosPitch55_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch55_Base)


pitch1_55                                        = add_text_hud("+10", 0, 0, PosPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_55.init_pos                        = {0, 6.82, 0.10}
pitch1_55.init_rot                        = {180, 0, 0}

pitch2_55                                        = add_text_hud("+20", 0, 0, PosPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_55.init_pos                        = {0, 5.96, 0.10}
pitch2_55.init_rot                        = {180, 0, 0}

pitch3_55                                        = add_text_hud("+30", 0, 0, PosPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_55.init_pos                        = {0, 5.098, 0.10}
pitch3_55.init_rot                        = {180, 0, 0}

pitch4_55                                        = add_text_hud("+40", 0, 0, PosPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_55.init_pos                        = {0, 4.234, 0.10}
pitch4_55.init_rot                        = {180, 0, 0}

pitch5_55                                        = add_text_hud("+50", 0, 0, PosPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_55.init_pos                        = {0, 3.37, 0.10}
pitch5_55.init_rot                        = {180, 0, 0}

pitch6_55                                        = add_text_hud("+60", 0, 0, PosPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_55.init_pos                        = {0, 2.51, 0.10}
pitch6_55.init_rot                        = {180, 0, 0}



local PosPitch35_Base                                                 = CreateElement "ceSimple"
PosPitch35_Base.name                                                  = create_guid_string()
PosPitch35_Base.init_pos                                                = {0, 0}
PosPitch35_Base.init_rot                                                = {145, 0, 0}
PosPitch35_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch35_Base)


pitch1_35                                        = add_text_hud("+10", 0, 0, PosPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_35.init_pos                        = {0, 6.82, 0.10}
pitch1_35.init_rot                        = {180, 0, 0}

pitch2_35                                        = add_text_hud("+20", 0, 0, PosPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_35.init_pos                        = {0, 5.96, 0.10}
pitch2_35.init_rot                        = {180, 0, 0}

pitch3_35                                        = add_text_hud("+30", 0, 0, PosPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_35.init_pos                        = {0, 5.098, 0.10}
pitch3_35.init_rot                        = {180, 0, 0}

pitch4_35                                        = add_text_hud("+40", 0, 0, PosPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_35.init_pos                        = {0, 4.234, 0.10}
pitch4_35.init_rot                        = {180, 0, 0}

pitch5_35                                        = add_text_hud("+50", 0, 0, PosPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_35.init_pos                        = {0, 3.37, 0.10}
pitch5_35.init_rot                        = {180, 0, 0}

pitch6_35                                        = add_text_hud("+60", 0, 0, PosPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_35.init_pos                        = {0, 2.51, 0.10}
pitch6_35.init_rot                        = {180, 0, 0}

pitch7_35                                        = add_text_hud("+70", 0, 0, PosPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch7_35.init_pos                        = {0, 1.65, 0.10}
pitch7_35.init_rot                        = {180, 0, 0}

local PosPitch15_Base                                                 = CreateElement "ceSimple"
PosPitch15_Base.name                                                  = create_guid_string()
PosPitch15_Base.init_pos                                                = {0, 0}
PosPitch15_Base.init_rot                                                = {165, 0, 0}
PosPitch15_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch15_Base)


pitch1_15                                        = add_text_hud("+10", 0, 0, PosPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_15.init_pos                        = {0, 6.82, 0.10}
pitch1_15.init_rot                        = {180, 0, 0}

pitch2_15                                        = add_text_hud("+20", 0, 0, PosPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_15.init_pos                        = {0, 5.96, 0.10}
pitch2_15.init_rot                        = {180, 0, 0}

pitch3_15                                        = add_text_hud("+30", 0, 0, PosPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_15.init_pos                        = {0, 5.098, 0.10}
pitch3_15.init_rot                        = {180, 0, 0}

pitch4_15                                        = add_text_hud("+40", 0, 0, PosPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_15.init_pos                        = {0, 4.234, 0.10}
pitch4_15.init_rot                        = {180, 0, 0}

pitch5_15                                        = add_text_hud("+50", 0, 0, PosPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_15.init_pos                        = {0, 3.37, 0.10}
pitch5_15.init_rot                        = {180, 0, 0}

pitch6_15                                        = add_text_hud("+60", 0, 0, PosPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_15.init_pos                        = {0, 2.51, 0.10}
pitch6_15.init_rot                        = {180, 0, 0}



local PosPitch185_Base                                                 = CreateElement "ceSimple"
PosPitch185_Base.name                                                  = create_guid_string()
PosPitch185_Base.init_pos                                                = {0, 0}
PosPitch185_Base.init_rot                                                = {-15, 0, 0}
PosPitch185_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch185_Base)


pitch1_185                                        = add_text_hud("+10", 0, 0, PosPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_185.init_pos                        = {0, 6.82, 0.10}
pitch1_185.init_rot                        = {180, 0, 0}

pitch2_185                                        = add_text_hud("+20", 0, 0, PosPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_185.init_pos                        = {0, 5.96, 0.10}
pitch2_185.init_rot                        = {180, 0, 0}

pitch3_185                                        = add_text_hud("+30", 0, 0, PosPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_185.init_pos                        = {0, 5.098, 0.10}
pitch3_185.init_rot                        = {180, 0, 0}

pitch4_185                                        = add_text_hud("+40", 0, 0, PosPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_185.init_pos                        = {0, 4.234, 0.10}
pitch4_185.init_rot                        = {180, 0, 0}

pitch5_185                                        = add_text_hud("+50", 0, 0, PosPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_185.init_pos                        = {0, 3.37, 0.10}
pitch5_185.init_rot                        = {180, 0, 0}

pitch6_185                                        = add_text_hud("+60", 0, 0, PosPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_185.init_pos                        = {0, 2.51, 0.10}
pitch6_185.init_rot                        = {180, 0, 0}



local PosPitch205_Base                                                 = CreateElement "ceSimple"
PosPitch205_Base.name                                                  = create_guid_string()
PosPitch205_Base.init_pos                                                = {0, 0}
PosPitch205_Base.init_rot                                                = {-35, 0, 0}
PosPitch205_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch205_Base)


pitch1_205                                        = add_text_hud("+10", 0, 0, PosPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_205.init_pos                        = {0, 6.82, 0.10}
pitch1_205.init_rot                        = {180, 0, 0}

pitch2_205                                        = add_text_hud("+20", 0, 0, PosPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_205.init_pos                        = {0, 5.96, 0.10}
pitch2_205.init_rot                        = {180, 0, 0}

pitch3_205                                        = add_text_hud("+30", 0, 0, PosPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_205.init_pos                        = {0, 5.098, 0.10}
pitch3_205.init_rot                        = {180, 0, 0}

pitch4_205                                        = add_text_hud("+40", 0, 0, PosPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_205.init_pos                        = {0, 4.234, 0.10}
pitch4_205.init_rot                        = {180, 0, 0}

pitch5_205                                        = add_text_hud("+50", 0, 0, PosPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_205.init_pos                        = {0, 3.37, 0.10}
pitch5_205.init_rot                        = {180, 0, 0}

pitch6_205                                        = add_text_hud("+60", 0, 0, PosPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_205.init_pos                        = {0, 2.51, 0.10}
pitch6_205.init_rot                        = {180, 0, 0}

pitch7_205                                        = add_text_hud("+70", 0, 0, PosPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch7_205.init_pos                        = {0, 1.65, 0.10}
pitch7_205.init_rot                        = {180, 0, 0}

local PosPitch225_Base                                                 = CreateElement "ceSimple"
PosPitch225_Base.name                                                  = create_guid_string()
PosPitch225_Base.init_pos                                                = {0, 0}
PosPitch225_Base.init_rot                                                = {-55, 0, 0}
PosPitch225_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch225_Base)


pitch1_225                                        = add_text_hud("+10", 0, 0, PosPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_225.init_pos                        = {0, 6.82, 0.10}
pitch1_225.init_rot                        = {180, 0, 0}

pitch2_225                                        = add_text_hud("+20", 0, 0, PosPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_225.init_pos                        = {0, 5.96, 0.10}
pitch2_225.init_rot                        = {180, 0, 0}

pitch3_225                                        = add_text_hud("+30", 0, 0, PosPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_225.init_pos                        = {0, 5.098, 0.10}
pitch3_225.init_rot                        = {180, 0, 0}

pitch4_225                                        = add_text_hud("+40", 0, 0, PosPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_225.init_pos                        = {0, 4.234, 0.10}
pitch4_225.init_rot                        = {180, 0, 0}

pitch5_225                                        = add_text_hud("+50", 0, 0, PosPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_225.init_pos                        = {0, 3.37, 0.10}
pitch5_225.init_rot                        = {180, 0, 0}

pitch6_225                                        = add_text_hud("+60", 0, 0, PosPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_225.init_pos                        = {0, 2.51, 0.10}
pitch6_225.init_rot                        = {180, 0, 0}



local PosPitch245_Base                                                 = CreateElement "ceSimple"
PosPitch245_Base.name                                                  = create_guid_string()
PosPitch245_Base.init_pos                                                = {0, 0}
PosPitch245_Base.init_rot                                                = {-75, 0, 0}
PosPitch245_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch245_Base)


pitch1_245                                        = add_text_hud("+10", 0, 0, PosPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_245.init_pos                        = {0, 6.82, 0.10}
pitch1_245.init_rot                        = {180, 0, 0}

pitch2_245                                        = add_text_hud("+20", 0, 0, PosPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_245.init_pos                        = {0, 5.96, 0.10}
pitch2_245.init_rot                        = {180, 0, 0}

pitch3_245                                        = add_text_hud("+30", 0, 0, PosPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_245.init_pos                        = {0, 5.098, 0.10}
pitch3_245.init_rot                        = {180, 0, 0}

pitch4_245                                        = add_text_hud("+40", 0, 0, PosPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_245.init_pos                        = {0, 4.234, 0.10}
pitch4_245.init_rot                        = {180, 0, 0}

pitch5_245                                        = add_text_hud("+50", 0, 0, PosPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_245.init_pos                        = {0, 3.37, 0.10}
pitch5_245.init_rot                        = {180, 0, 0}

pitch6_245                                        = add_text_hud("+60", 0, 0, PosPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_245.init_pos                        = {0, 2.51, 0.10}
pitch6_245.init_rot                        = {180, 0, 0}



local PosPitch265_Base                                                 = CreateElement "ceSimple"
PosPitch265_Base.name                                                  = create_guid_string()
PosPitch265_Base.init_pos                                                = {0, 0}
PosPitch265_Base.init_rot                                                = {-95, 0, 0}
PosPitch265_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch265_Base)


pitch1_265                                        = add_text_hud("+10", 0, 0, PosPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_265.init_pos                        = {0, 6.82, 0.10}
pitch1_265.init_rot                        = {180, 0, 0}

pitch2_265                                        = add_text_hud("+20", 0, 0, PosPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_265.init_pos                        = {0, 5.96, 0.10}
pitch2_265.init_rot                        = {180, 0, 0}

pitch3_265                                        = add_text_hud("+30", 0, 0, PosPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_265.init_pos                        = {0, 5.098, 0.10}
pitch3_265.init_rot                        = {180, 0, 0}

pitch4_265                                        = add_text_hud("+40", 0, 0, PosPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_265.init_pos                        = {0, 4.234, 0.10}
pitch4_265.init_rot                        = {180, 0, 0}

pitch5_265                                        = add_text_hud("+50", 0, 0, PosPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_265.init_pos                        = {0, 3.37, 0.10}
pitch5_265.init_rot                        = {180, 0, 0}

pitch6_265                                        = add_text_hud("+60", 0, 0, PosPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_265.init_pos                        = {0, 2.51, 0.10}
pitch6_265.init_rot                        = {180, 0, 0}

pitch7_265                                        = add_text_hud("+70", 0, 0, PosPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch7_265.init_pos                        = {0, 1.65, 0.10}
pitch7_265.init_rot                        = {180, 0, 0}

local PosPitch285_Base                                                 = CreateElement "ceSimple"
PosPitch285_Base.name                                                  = create_guid_string()
PosPitch285_Base.init_pos                                                = {0, 0}
PosPitch285_Base.init_rot                                                = {-115, 0, 0}
PosPitch285_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch285_Base)


pitch1_285                                        = add_text_hud("+10", 0, 0, PosPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_285.init_pos                        = {0, 6.82, 0.10}
pitch1_285.init_rot                        = {180, 0, 0}

pitch2_285                                        = add_text_hud("+20", 0, 0, PosPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_285.init_pos                        = {0, 5.96, 0.10}
pitch2_285.init_rot                        = {180, 0, 0}

pitch3_285                                        = add_text_hud("+30", 0, 0, PosPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_285.init_pos                        = {0, 5.098, 0.10}
pitch3_285.init_rot                        = {180, 0, 0}

pitch4_285                                        = add_text_hud("+40", 0, 0, PosPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_285.init_pos                        = {0, 4.234, 0.10}
pitch4_285.init_rot                        = {180, 0, 0}

pitch5_285                                        = add_text_hud("+50", 0, 0, PosPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_285.init_pos                        = {0, 3.37, 0.10}
pitch5_285.init_rot                        = {180, 0, 0}

pitch6_285                                        = add_text_hud("+60", 0, 0, PosPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_285.init_pos                        = {0, 2.51, 0.10}
pitch6_285.init_rot                        = {180, 0, 0}



local PosPitch305_Base                                                 = CreateElement "ceSimple"
PosPitch305_Base.name                                                  = create_guid_string()
PosPitch305_Base.init_pos                                                = {0, 0}
PosPitch305_Base.init_rot                                                = {-135, 0, 0}
PosPitch305_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch305_Base)


pitch1_305                                        = add_text_hud("+10", 0, 0, PosPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_305.init_pos                        = {0, 6.82, 0.10}
pitch1_305.init_rot                        = {180, 0, 0}

pitch2_305                                        = add_text_hud("+20", 0, 0, PosPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_305.init_pos                        = {0, 5.96, 0.10}
pitch2_305.init_rot                        = {180, 0, 0}

pitch3_305                                        = add_text_hud("+30", 0, 0, PosPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_305.init_pos                        = {0, 5.098, 0.10}
pitch3_305.init_rot                        = {180, 0, 0}

pitch4_305                                        = add_text_hud("+40", 0, 0, PosPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_305.init_pos                        = {0, 4.234, 0.10}
pitch4_305.init_rot                        = {180, 0, 0}

pitch5_305                                        = add_text_hud("+50", 0, 0, PosPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_305.init_pos                        = {0, 3.37, 0.10}
pitch5_305.init_rot                        = {180, 0, 0}

pitch6_305                                        = add_text_hud("+60", 0, 0, PosPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_305.init_pos                        = {0, 2.51, 0.10}
pitch6_305.init_rot                        = {180, 0, 0}



local PosPitch325_Base                                                 = CreateElement "ceSimple"
PosPitch325_Base.name                                                  = create_guid_string()
PosPitch325_Base.init_pos                                                = {0, 0}
PosPitch325_Base.init_rot                                                = {-155, 0, 0}
PosPitch325_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch325_Base)


pitch1_325                                        = add_text_hud("+10", 0, 0, PosPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_325.init_pos                        = {0, 6.82, 0.10}
pitch1_325.init_rot                        = {180, 0, 0}

pitch2_325                                        = add_text_hud("+20", 0, 0, PosPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_325.init_pos                        = {0, 5.96, 0.10}
pitch2_325.init_rot                        = {180, 0, 0}

pitch3_325                                        = add_text_hud("+30", 0, 0, PosPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_325.init_pos                        = {0, 5.098, 0.10}
pitch3_325.init_rot                        = {180, 0, 0}

pitch4_325                                        = add_text_hud("+40", 0, 0, PosPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_325.init_pos                        = {0, 4.234, 0.10}
pitch4_325.init_rot                        = {180, 0, 0}

pitch5_325                                        = add_text_hud("+50", 0, 0, PosPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_325.init_pos                        = {0, 3.37, 0.10}
pitch5_325.init_rot                        = {180, 0, 0}

pitch6_325                                        = add_text_hud("+60", 0, 0, PosPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_325.init_pos                        = {0, 2.51, 0.10}
pitch6_325.init_rot                        = {180, 0, 0}

pitch7_325                                        = add_text_hud("+70", 0, 0, PosPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch7_325.init_pos                        = {0, 1.65, 0.10}
pitch7_325.init_rot                        = {180, 0, 0}

local PosPitch345_Base                                                 = CreateElement "ceSimple"
PosPitch345_Base.name                                                  = create_guid_string()
PosPitch345_Base.init_pos                                                = {0, 0}
PosPitch345_Base.init_rot                                                = {-175, 0, 0}
PosPitch345_Base.parent_element                                = PositivePitchLinesHUD.name
AddHudElement(PosPitch345_Base)


pitch1_345                                        = add_text_hud("+10", 0, 0, PosPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch1_345.init_pos                        = {0, 6.82, 0.10}
pitch1_345.init_rot                        = {180, 0, 0}

pitch2_345                                        = add_text_hud("+20", 0, 0, PosPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch2_345.init_pos                        = {0, 5.96, 0.10}
pitch2_345.init_rot                        = {180, 0, 0}

pitch3_345                                        = add_text_hud("+30", 0, 0, PosPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch3_345.init_pos                        = {0, 5.098, 0.10}
pitch3_345.init_rot                        = {180, 0, 0}

pitch4_345                                        = add_text_hud("+40", 0, 0, PosPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch4_345.init_pos                        = {0, 4.234, 0.10}
pitch4_345.init_rot                        = {180, 0, 0}

pitch5_345                                        = add_text_hud("+50", 0, 0, PosPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch5_345.init_pos                        = {0, 3.37, 0.10}
pitch5_345.init_rot                        = {180, 0, 0}

pitch6_345                                        = add_text_hud("+60", 0, 0, PosPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
pitch6_345.init_pos                        = {0, 2.51, 0.10}
pitch6_345.init_rot                        = {180, 0, 0}



-- Negative pitch values


local NegPitch175_Base                                                 = CreateElement "ceSimple"
NegPitch175_Base.name                                                  = create_guid_string()
NegPitch175_Base.init_pos                                                = {0, 0}
NegPitch175_Base.init_rot                                                = {-5, 0, 0}
NegPitch175_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch175_Base)


NegPitch1_175                                        = add_text_hud("-10", 0, 0, NegPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_175.init_pos                        = {0, 6.82, 0.10}
NegPitch1_175.init_rot                        = {0, 0, 0}

NegPitch2_175                                        = add_text_hud("-20", 0, 0, NegPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_175.init_pos                        = {0, 5.96, 0.10}
NegPitch2_175.init_rot                        = {0, 0, 0}

NegPitch3_175                                        = add_text_hud("-30", 0, 0, NegPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_175.init_pos                        = {0, 5.098, 0.10}
NegPitch3_175.init_rot                        = {0, 0, 0}

NegPitch4_175                                        = add_text_hud("-40", 0, 0, NegPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_175.init_pos                        = {0, 4.234, 0.10}
NegPitch4_175.init_rot                        = {0, 0, 0}

NegPitch5_175                                        = add_text_hud("-50", 0, 0, NegPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_175.init_pos                        = {0, 3.37, 0.10}
NegPitch5_175.init_rot                        = {0, 0, 0}

NegPitch6_175                                        = add_text_hud("-60", 0, 0, NegPitch175_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_175.init_pos                        = {0, 2.51, 0.10}
NegPitch6_175.init_rot                        = {0, 0, 0}



--
local NegPitch155_Base                                                 = CreateElement "ceSimple"
NegPitch155_Base.name                                                  = create_guid_string()
NegPitch155_Base.init_pos                                                = {0, 0}
NegPitch155_Base.init_rot                                                = {-25, 0, 0}
NegPitch155_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch155_Base)


NegPitch1_155                                        = add_text_hud("-10", 0, 0, NegPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_155.init_pos                        = {0, 6.82, 0.10}
NegPitch1_155.init_rot                        = {0, 0, 0}

NegPitch2_155                                        = add_text_hud("-20", 0, 0, NegPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_155.init_pos                        = {0, 5.96, 0.10}
NegPitch2_155.init_rot                        = {0, 0, 0}

NegPitch3_155                                        = add_text_hud("-30", 0, 0, NegPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_155.init_pos                        = {0, 5.098, 0.10}
NegPitch3_155.init_rot                        = {0, 0, 0}

NegPitch4_155                                        = add_text_hud("-40", 0, 0, NegPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_155.init_pos                        = {0, 4.234, 0.10}
NegPitch4_155.init_rot                        = {0, 0, 0}

NegPitch5_155                                        = add_text_hud("-50", 0, 0, NegPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_155.init_pos                        = {0, 3.37, 0.10}
NegPitch5_155.init_rot                        = {0, 0, 0}

NegPitch6_155                                        = add_text_hud("-60", 0, 0, NegPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_155.init_pos                        = {0, 2.51, 0.10}
NegPitch6_155.init_rot                        = {0, 0, 0}

Negpitch7_155                                        = add_text_hud("-70", 0, 0, NegPitch155_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
Negpitch7_155.init_pos                        = {0, 1.65, 0.10}
Negpitch7_155.init_rot                        = {0, 0, 0}

--

local NegPitch135_Base                                                 = CreateElement "ceSimple"
NegPitch135_Base.name                                                  = create_guid_string()
NegPitch135_Base.init_pos                                                = {0, 0}
NegPitch135_Base.init_rot                                                = {-45, 0, 0}
NegPitch135_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch135_Base)


NegPitch1_135                                        = add_text_hud("-10", 0, 0, NegPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_135.init_pos                        = {0, 6.82, 0.10}
NegPitch1_135.init_rot                        = {0, 0, 0}

NegPitch2_135                                        = add_text_hud("-20", 0, 0, NegPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_135.init_pos                        = {0, 5.96, 0.10}
NegPitch2_135.init_rot                        = {0, 0, 0}

NegPitch3_135                                        = add_text_hud("-30", 0, 0, NegPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_135.init_pos                        = {0, 5.098, 0.10}
NegPitch3_135.init_rot                        = {0, 0, 0}

NegPitch4_135                                        = add_text_hud("-40", 0, 0, NegPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_135.init_pos                        = {0, 4.234, 0.10}
NegPitch4_135.init_rot                        = {0, 0, 0}

NegPitch5_135                                        = add_text_hud("-50", 0, 0, NegPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_135.init_pos                        = {0, 3.37, 0.10}
NegPitch5_135.init_rot                        = {0, 0, 0}

NegPitch6_135                                        = add_text_hud("-60", 0, 0, NegPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_135.init_pos                        = {0, 2.51, 0.10}
NegPitch6_135.init_rot                        = {0, 0, 0}

NegPitch7_135                                        = add_text_hud("-70", 0, 0, NegPitch135_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch7_135.init_pos                        = {0, 1.65, 0.10}
NegPitch7_135.init_rot                        = {0, 0, 0}

--

local NegPitch115_Base                                                 = CreateElement "ceSimple"
NegPitch115_Base.name                                                  = create_guid_string()
NegPitch115_Base.init_pos                                                = {0, 0}
NegPitch115_Base.init_rot                                                = {-65, 0, 0}
NegPitch115_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch115_Base)


NegPitch1_115                                        = add_text_hud("-10", 0, 0, NegPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_115.init_pos                        = {0, 6.82, 0.10}
NegPitch1_115.init_rot                        = {0, 0, 0}

NegPitch2_115                                        = add_text_hud("-20", 0, 0, NegPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_115.init_pos                        = {0, 5.96, 0.10}
NegPitch2_115.init_rot                        = {0, 0, 0}

NegPitch3_115                                        = add_text_hud("-30", 0, 0, NegPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_115.init_pos                        = {0, 5.098, 0.10}
NegPitch3_115.init_rot                        = {0, 0, 0}

NegPitch4_115                                        = add_text_hud("-40", 0, 0, NegPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_115.init_pos                        = {0, 4.234, 0.10}
NegPitch4_115.init_rot                        = {0, 0, 0}

NegPitch5_115                                        = add_text_hud("-50", 0, 0, NegPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_115.init_pos                        = {0, 3.37, 0.10}
NegPitch5_115.init_rot                        = {0, 0, 0}

NegPitch6_115                                        = add_text_hud("-60", 0, 0, NegPitch115_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_115.init_pos                        = {0, 2.51, 0.10}
NegPitch6_115.init_rot                        = {0, 0, 0}



local NegPitch95_Base                                                 = CreateElement "ceSimple"
NegPitch95_Base.name                                                  = create_guid_string()
NegPitch95_Base.init_pos                                                = {0, 0}
NegPitch95_Base.init_rot                                                = {-85, 0, 0}
NegPitch95_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch95_Base)


NegPitch1_95                                        = add_text_hud("-10", 0, 0, NegPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_95.init_pos                        = {0, 6.82, 0.10}
NegPitch1_95.init_rot                        = {0, 0, 0}

NegPitch2_95                                        = add_text_hud("-20", 0, 0, NegPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_95.init_pos                        = {0, 5.96, 0.10}
NegPitch2_95.init_rot                        = {0, 0, 0}

NegPitch3_95                                        = add_text_hud("-30", 0, 0, NegPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_95.init_pos                        = {0, 5.098, 0.10}
NegPitch3_95.init_rot                        = {0, 0, 0}

NegPitch4_95                                        = add_text_hud("-40", 0, 0, NegPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_95.init_pos                        = {0, 4.234, 0.10}
NegPitch4_95.init_rot                        = {0, 0, 0}

NegPitch5_95                                        = add_text_hud("-50", 0, 0, NegPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_95.init_pos                        = {0, 3.37, 0.10}
NegPitch5_95.init_rot                        = {0, 0, 0}

NegPitch6_95                                        = add_text_hud("-60", 0, 0, NegPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_95.init_pos                        = {0, 2.51, 0.10}
NegPitch6_95.init_rot                        = {0, 0, 0}

Negpitch7_95                                        = add_text_hud("-70", 0, 0, NegPitch95_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
Negpitch7_95.init_pos                        = {0, 1.65, 0.10}
Negpitch7_95.init_rot                        = {0, 0, 0}

local NegPitch75_Base                                                 = CreateElement "ceSimple"
NegPitch75_Base.name                                                  = create_guid_string()
NegPitch75_Base.init_pos                                                = {0, 0}
NegPitch75_Base.init_rot                                                = {-105, 0, 0}
NegPitch75_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch75_Base)


NegPitch1_75                                        = add_text_hud("-10", 0, 0, NegPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_75.init_pos                        = {0, 6.82, 0.10}
NegPitch1_75.init_rot                        = {0, 0, 0}

NegPitch2_75                                        = add_text_hud("-20", 0, 0, NegPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_75.init_pos                        = {0, 5.96, 0.10}
NegPitch2_75.init_rot                        = {0, 0, 0}

NegPitch3_75                                        = add_text_hud("-30", 0, 0, NegPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_75.init_pos                        = {0, 5.098, 0.10}
NegPitch3_75.init_rot                        = {0, 0, 0}

NegPitch4_75                                        = add_text_hud("-40", 0, 0, NegPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_75.init_pos                        = {0, 4.234, 0.10}
NegPitch4_75.init_rot                        = {0, 0, 0}

NegPitch5_75                                        = add_text_hud("-50", 0, 0, NegPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_75.init_pos                        = {0, 3.37, 0.10}
NegPitch5_75.init_rot                        = {0, 0, 0}

NegPitch6_75                                        = add_text_hud("-60", 0, 0, NegPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_75.init_pos                        = {0, 2.51, 0.10}
NegPitch6_75.init_rot                        = {0, 0, 0}

NegPitch7_75                                        = add_text_hud("-70", 0, 0, NegPitch75_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch7_75.init_pos                        = {0, 1.65, 0.10}
NegPitch7_75.init_rot                        = {0, 0, 0}

local NegPitch55_Base                                                 = CreateElement "ceSimple"
NegPitch55_Base.name                                                  = create_guid_string()
NegPitch55_Base.init_pos                                                = {0, 0}
NegPitch55_Base.init_rot                                                = {-125, 0, 0}
NegPitch55_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch55_Base)


NegPitch1_55                                        = add_text_hud("-10", 0, 0, NegPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_55.init_pos                        = {0, 6.82, 0.10}
NegPitch1_55.init_rot                        = {0, 0, 0}

NegPitch2_55                                        = add_text_hud("-20", 0, 0, NegPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_55.init_pos                        = {0, 5.96, 0.10}
NegPitch2_55.init_rot                        = {0, 0, 0}

NegPitch3_55                                        = add_text_hud("-30", 0, 0, NegPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_55.init_pos                        = {0, 5.098, 0.10}
NegPitch3_55.init_rot                        = {0, 0, 0}

NegPitch4_55                                        = add_text_hud("-40", 0, 0, NegPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_55.init_pos                        = {0, 4.234, 0.10}
NegPitch4_55.init_rot                        = {0, 0, 0}

NegPitch5_55                                        = add_text_hud("-50", 0, 0, NegPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_55.init_pos                        = {0, 3.37, 0.10}
NegPitch5_55.init_rot                        = {0, 0, 0}

NegPitch6_55                                        = add_text_hud("-60", 0, 0, NegPitch55_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_55.init_pos                        = {0, 2.51, 0.10}
NegPitch6_55.init_rot                        = {0, 0, 0}



local NegPitch35_Base                                                 = CreateElement "ceSimple"
NegPitch35_Base.name                                                  = create_guid_string()
NegPitch35_Base.init_pos                                                = {0, 0}
NegPitch35_Base.init_rot                                                = {-145, 0, 0}
NegPitch35_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch35_Base)


NegPitch1_35                                        = add_text_hud("-10", 0, 0, NegPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_35.init_pos                        = {0, 6.82, 0.10}
NegPitch1_35.init_rot                        = {0, 0, 0}

NegPitch2_35                                        = add_text_hud("-20", 0, 0, NegPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_35.init_pos                        = {0, 5.96, 0.10}
NegPitch2_35.init_rot                        = {0, 0, 0}

NegPitch3_35                                        = add_text_hud("-30", 0, 0, NegPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_35.init_pos                        = {0, 5.098, 0.10}
NegPitch3_35.init_rot                        = {0, 0, 0}

NegPitch4_35                                        = add_text_hud("-40", 0, 0, NegPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_35.init_pos                        = {0, 4.234, 0.10}
NegPitch4_35.init_rot                        = {0, 0, 0}

NegPitch5_35                                        = add_text_hud("-50", 0, 0, NegPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_35.init_pos                        = {0, 3.37, 0.10}
NegPitch5_35.init_rot                        = {0, 0, 0}

NegPitch6_35                                        = add_text_hud("-60", 0, 0, NegPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_35.init_pos                        = {0, 2.51, 0.10}
NegPitch6_35.init_rot                        = {0, 0, 0}

NegPitch7_35                                        = add_text_hud("-70", 0, 0, NegPitch35_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch7_35.init_pos                        = {0, 1.65, 0.10}
NegPitch7_35.init_rot                        = {0, 0, 0}

local NegPitch15_Base                                                 = CreateElement "ceSimple"
NegPitch15_Base.name                                                  = create_guid_string()
NegPitch15_Base.init_pos                                                = {0, 0}
NegPitch15_Base.init_rot                                                = {-165, 0, 0}
NegPitch15_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch15_Base)


NegPitch1_15                                        = add_text_hud("-10", 0, 0, NegPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_15.init_pos                        = {0, 6.82, 0.10}
NegPitch1_15.init_rot                        = {0, 0, 0}

NegPitch2_15                                        = add_text_hud("-20", 0, 0, NegPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_15.init_pos                        = {0, 5.96, 0.10}
NegPitch2_15.init_rot                        = {0, 0, 0}

NegPitch3_15                                        = add_text_hud("-30", 0, 0, NegPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_15.init_pos                        = {0, 5.098, 0.10}
NegPitch3_15.init_rot                        = {0, 0, 0}

NegPitch4_15                                        = add_text_hud("-40", 0, 0, NegPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_15.init_pos                        = {0, 4.234, 0.10}
NegPitch4_15.init_rot                        = {0, 0, 0}

NegPitch5_15                                        = add_text_hud("-50", 0, 0, NegPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_15.init_pos                        = {0, 3.37, 0.10}
NegPitch5_15.init_rot                        = {0, 0, 0}

NegPitch6_15                                        = add_text_hud("-60", 0, 0, NegPitch15_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_15.init_pos                        = {0, 2.51, 0.10}
NegPitch6_15.init_rot                        = {0, 0, 0}



local NegPitch185_Base                                                 = CreateElement "ceSimple"
NegPitch185_Base.name                                                  = create_guid_string()
NegPitch185_Base.init_pos                                                = {0, 0}
NegPitch185_Base.init_rot                                                = {15, 0, 0}
NegPitch185_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch185_Base)


NegPitch1_185                                        = add_text_hud("-10", 0, 0, NegPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_185.init_pos                        = {0, 6.82, 0.10}
NegPitch1_185.init_rot                        = {0, 0, 0}

NegPitch2_185                                        = add_text_hud("-20", 0, 0, NegPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_185.init_pos                        = {0, 5.96, 0.10}
NegPitch2_185.init_rot                        = {0, 0, 0}

NegPitch3_185                                        = add_text_hud("-30", 0, 0, NegPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_185.init_pos                        = {0, 5.098, 0.10}
NegPitch3_185.init_rot                        = {0, 0, 0}

NegPitch4_185                                        = add_text_hud("-40", 0, 0, NegPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_185.init_pos                        = {0, 4.234, 0.10}
NegPitch4_185.init_rot                        = {0, 0, 0}

NegPitch5_185                                        = add_text_hud("-50", 0, 0, NegPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_185.init_pos                        = {0, 3.37, 0.10}
NegPitch5_185.init_rot                        = {0, 0, 0}

NegPitch6_185                                        = add_text_hud("-60", 0, 0, NegPitch185_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_185.init_pos                        = {0, 2.51, 0.10}
NegPitch6_185.init_rot                        = {0, 0, 0}



local NegPitch205_Base                                                 = CreateElement "ceSimple"
NegPitch205_Base.name                                                  = create_guid_string()
NegPitch205_Base.init_pos                                                = {0, 0}
NegPitch205_Base.init_rot                                                = {35, 0, 0}
NegPitch205_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch205_Base)


NegPitch1_205                                        = add_text_hud("-10", 0, 0, NegPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_205.init_pos                        = {0, 6.82, 0.10}
NegPitch1_205.init_rot                        = {0, 0, 0}

NegPitch2_205                                        = add_text_hud("-20", 0, 0, NegPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_205.init_pos                        = {0, 5.96, 0.10}
NegPitch2_205.init_rot                        = {0, 0, 0}

NegPitch3_205                                        = add_text_hud("-30", 0, 0, NegPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_205.init_pos                        = {0, 5.098, 0.10}
NegPitch3_205.init_rot                        = {0, 0, 0}

NegPitch4_205                                        = add_text_hud("-40", 0, 0, NegPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_205.init_pos                        = {0, 4.234, 0.10}
NegPitch4_205.init_rot                        = {0, 0, 0}

NegPitch5_205                                        = add_text_hud("-50", 0, 0, NegPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_205.init_pos                        = {0, 3.37, 0.10}
NegPitch5_205.init_rot                        = {0, 0, 0}

NegPitch6_205                                        = add_text_hud("-60", 0, 0, NegPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_205.init_pos                        = {0, 2.51, 0.10}
NegPitch6_205.init_rot                        = {0, 0, 0}

Negpitch7_205                                        = add_text_hud("-70", 0, 0, NegPitch205_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
Negpitch7_205.init_pos                        = {0, 1.65, 0.10}
Negpitch7_205.init_rot                        = {0, 0, 0}

local NegPitch225_Base                                                 = CreateElement "ceSimple"
NegPitch225_Base.name                                                  = create_guid_string()
NegPitch225_Base.init_pos                                                = {0, 0}
NegPitch225_Base.init_rot                                                = {55, 0, 0}
NegPitch225_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch225_Base)


NegPitch1_225                                        = add_text_hud("-10", 0, 0, NegPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_225.init_pos                        = {0, 6.82, 0.10}
NegPitch1_225.init_rot                        = {0, 0, 0}

NegPitch2_225                                        = add_text_hud("-20", 0, 0, NegPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_225.init_pos                        = {0, 5.96, 0.10}
NegPitch2_225.init_rot                        = {0, 0, 0}

NegPitch3_225                                        = add_text_hud("-30", 0, 0, NegPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_225.init_pos                        = {0, 5.098, 0.10}
NegPitch3_225.init_rot                        = {0, 0, 0}

NegPitch4_225                                        = add_text_hud("-40", 0, 0, NegPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_225.init_pos                        = {0, 4.234, 0.10}
NegPitch4_225.init_rot                        = {0, 0, 0}

NegPitch5_225                                        = add_text_hud("-50", 0, 0, NegPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_225.init_pos                        = {0, 3.37, 0.10}
NegPitch5_225.init_rot                        = {0, 0, 0}

NegPitch6_225                                        = add_text_hud("-60", 0, 0, NegPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_225.init_pos                        = {0, 2.51, 0.10}
NegPitch6_225.init_rot                        = {0, 0, 0}

NegPitch7_225                                        = add_text_hud("-70", 0, 0, NegPitch225_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch7_225.init_pos                        = {0, 1.65, 0.10}
NegPitch7_225.init_rot                        = {0, 0, 0}

local NegPitch245_Base                                                 = CreateElement "ceSimple"
NegPitch245_Base.name                                                  = create_guid_string()
NegPitch245_Base.init_pos                                                = {0, 0}
NegPitch245_Base.init_rot                                                = {75, 0, 0}
NegPitch245_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch245_Base)


NegPitch1_245                                        = add_text_hud("-10", 0, 0, NegPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_245.init_pos                        = {0, 6.82, 0.10}
NegPitch1_245.init_rot                        = {0, 0, 0}

NegPitch2_245                                        = add_text_hud("-20", 0, 0, NegPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_245.init_pos                        = {0, 5.96, 0.10}
NegPitch2_245.init_rot                        = {0, 0, 0}

NegPitch3_245                                        = add_text_hud("-30", 0, 0, NegPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_245.init_pos                        = {0, 5.098, 0.10}
NegPitch3_245.init_rot                        = {0, 0, 0}

NegPitch4_245                                        = add_text_hud("-40", 0, 0, NegPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_245.init_pos                        = {0, 4.234, 0.10}
NegPitch4_245.init_rot                        = {0, 0, 0}

NegPitch5_245                                        = add_text_hud("-50", 0, 0, NegPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_245.init_pos                        = {0, 3.37, 0.10}
NegPitch5_245.init_rot                        = {0, 0, 0}

NegPitch6_245                                        = add_text_hud("-60", 0, 0, NegPitch245_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_245.init_pos                        = {0, 2.51, 0.10}
NegPitch6_245.init_rot                        = {0, 0, 0}



local NegPitch265_Base                                                 = CreateElement "ceSimple"
NegPitch265_Base.name                                                  = create_guid_string()
NegPitch265_Base.init_pos                                                = {0, 0}
NegPitch265_Base.init_rot                                                = {95, 0, 0}
NegPitch265_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch265_Base)


NegPitch1_265                                        = add_text_hud("-10", 0, 0, NegPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_265.init_pos                        = {0, 6.82, 0.10}
NegPitch1_265.init_rot                        = {0, 0, 0}

NegPitch2_265                                        = add_text_hud("-20", 0, 0, NegPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_265.init_pos                        = {0, 5.96, 0.10}
NegPitch2_265.init_rot                        = {0, 0, 0}

NegPitch3_265                                        = add_text_hud("-30", 0, 0, NegPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_265.init_pos                        = {0, 5.098, 0.10}
NegPitch3_265.init_rot                        = {0, 0, 0}

NegPitch4_265                                        = add_text_hud("-40", 0, 0, NegPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_265.init_pos                        = {0, 4.234, 0.10}
NegPitch4_265.init_rot                        = {0, 0, 0}

NegPitch5_265                                        = add_text_hud("-50", 0, 0, NegPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_265.init_pos                        = {0, 3.37, 0.10}
NegPitch5_265.init_rot                        = {0, 0, 0}

NegPitch6_265                                        = add_text_hud("-60", 0, 0, NegPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_265.init_pos                        = {0, 2.51, 0.10}
NegPitch6_265.init_rot                        = {0, 0, 0}

Negpitch7_265                                        = add_text_hud("-70", 0, 0, NegPitch265_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
Negpitch7_265.init_pos                        = {0, 1.65, 0.10}
Negpitch7_265.init_rot                        = {0, 0, 0}

local NegPitch285_Base                                                 = CreateElement "ceSimple"
NegPitch285_Base.name                                                  = create_guid_string()
NegPitch285_Base.init_pos                                                = {0, 0}
NegPitch285_Base.init_rot                                                = {115, 0, 0}
NegPitch285_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch285_Base)


NegPitch1_285                                        = add_text_hud("-10", 0, 0, NegPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_285.init_pos                        = {0, 6.82, 0.10}
NegPitch1_285.init_rot                        = {0, 0, 0}

NegPitch2_285                                        = add_text_hud("-20", 0, 0, NegPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_285.init_pos                        = {0, 5.96, 0.10}
NegPitch2_285.init_rot                        = {0, 0, 0}

NegPitch3_285                                        = add_text_hud("-30", 0, 0, NegPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_285.init_pos                        = {0, 5.098, 0.10}
NegPitch3_285.init_rot                        = {0, 0, 0}

NegPitch4_285                                        = add_text_hud("-40", 0, 0, NegPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_285.init_pos                        = {0, 4.234, 0.10}
NegPitch4_285.init_rot                        = {0, 0, 0}

NegPitch5_285                                        = add_text_hud("-50", 0, 0, NegPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_285.init_pos                        = {0, 3.37, 0.10}
NegPitch5_285.init_rot                        = {0, 0, 0}

NegPitch6_285                                        = add_text_hud("-60", 0, 0, NegPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_285.init_pos                        = {0, 2.51, 0.10}
NegPitch6_285.init_rot                        = {0, 0, 0}

NegPitch7_285                                        = add_text_hud("-70", 0, 0, NegPitch285_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch7_285.init_pos                        = {0, 1.65, 0.10}
NegPitch7_285.init_rot                        = {0, 0, 0}

local NegPitch305_Base                                                 = CreateElement "ceSimple"
NegPitch305_Base.name                                                  = create_guid_string()
NegPitch305_Base.init_pos                                                = {0, 0}
NegPitch305_Base.init_rot                                                = {135, 0, 0}
NegPitch305_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch305_Base)


NegPitch1_305                                        = add_text_hud("-10", 0, 0, NegPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_305.init_pos                        = {0, 6.82, 0.10}
NegPitch1_305.init_rot                        = {0, 0, 0}

NegPitch2_305                                        = add_text_hud("-20", 0, 0, NegPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_305.init_pos                        = {0, 5.96, 0.10}
NegPitch2_305.init_rot                        = {0, 0, 0}

NegPitch3_305                                        = add_text_hud("-30", 0, 0, NegPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_305.init_pos                        = {0, 5.098, 0.10}
NegPitch3_305.init_rot                        = {0, 0, 0}

NegPitch4_305                                        = add_text_hud("-40", 0, 0, NegPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_305.init_pos                        = {0, 4.234, 0.10}
NegPitch4_305.init_rot                        = {0, 0, 0}

NegPitch5_305                                        = add_text_hud("-50", 0, 0, NegPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_305.init_pos                        = {0, 3.37, 0.10}
NegPitch5_305.init_rot                        = {0, 0, 0}

NegPitch6_305                                        = add_text_hud("-60", 0, 0, NegPitch305_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_305.init_pos                        = {0, 2.51, 0.10}
NegPitch6_305.init_rot                        = {0, 0, 0}



local NegPitch325_Base                                                 = CreateElement "ceSimple"
NegPitch325_Base.name                                                  = create_guid_string()
NegPitch325_Base.init_pos                                                = {0, 0}
NegPitch325_Base.init_rot                                                = {155, 0, 0}
NegPitch325_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch325_Base)


NegPitch1_325                                        = add_text_hud("-10", 0, 0, NegPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_325.init_pos                        = {0, 6.82, 0.10}
NegPitch1_325.init_rot                        = {0, 0, 0}

NegPitch2_325                                        = add_text_hud("-20", 0, 0, NegPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_325.init_pos                        = {0, 5.96, 0.10}
NegPitch2_325.init_rot                        = {0, 0, 0}

NegPitch3_325                                        = add_text_hud("-30", 0, 0, NegPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_325.init_pos                        = {0, 5.098, 0.10}
NegPitch3_325.init_rot                        = {0, 0, 0}

NegPitch4_325                                        = add_text_hud("-40", 0, 0, NegPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_325.init_pos                        = {0, 4.234, 0.10}
NegPitch4_325.init_rot                        = {0, 0, 0}

NegPitch5_325                                        = add_text_hud("-50", 0, 0, NegPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_325.init_pos                        = {0, 3.37, 0.10}
NegPitch5_325.init_rot                        = {0, 0, 0}

NegPitch6_325                                        = add_text_hud("-60", 0, 0, NegPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_325.init_pos                        = {0, 2.51, 0.10}
NegPitch6_325.init_rot                        = {0, 0, 0}

Negpitch7_325                                        = add_text_hud("-70", 0, 0, NegPitch325_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
Negpitch7_325.init_pos                        = {0, 1.65, 0.10}
Negpitch7_325.init_rot                        = {0, 0, 0}

local NegPitch345_Base                                                 = CreateElement "ceSimple"
NegPitch345_Base.name                                                  = create_guid_string()
NegPitch345_Base.init_pos                                                = {0, 0}
NegPitch345_Base.init_rot                                                = {175, 0, 0}
NegPitch345_Base.parent_element                                = NegativePitchLinesHUD.name
AddHudElement(NegPitch345_Base)


NegPitch1_345                                        = add_text_hud("-10", 0, 0, NegPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch1_345.init_pos                        = {0, 6.82, 0.10}
NegPitch1_345.init_rot                        = {0, 0, 0}

NegPitch2_345                                        = add_text_hud("-20", 0, 0, NegPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch2_345.init_pos                        = {0, 5.96, 0.10}
NegPitch2_345.init_rot                        = {0, 0, 0}

NegPitch3_345                                        = add_text_hud("-30", 0, 0, NegPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch3_345.init_pos                        = {0, 5.098, 0.10}
NegPitch3_345.init_rot                        = {0, 0, 0}

NegPitch4_345                                        = add_text_hud("-40", 0, 0, NegPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch4_345.init_pos                        = {0, 4.234, 0.10}
NegPitch4_345.init_rot                        = {0, 0, 0}

NegPitch5_345                                        = add_text_hud("-50", 0, 0, NegPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch5_345.init_pos                        = {0, 3.37, 0.10}
NegPitch5_345.init_rot                        = {0, 0, 0}

NegPitch6_345                                        = add_text_hud("-60", 0, 0, NegPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch6_345.init_pos                        = {0, 2.51, 0.10}
NegPitch6_345.init_rot                        = {0, 0, 0}

NegPitch7_345                                        = add_text_hud("-70", 0, 0, NegPitch345_Base , "F-117_Font_green", HUD_pitch_digit, "CenterCenter")
NegPitch7_345.init_pos                        = {0, 1.65, 0.10}
NegPitch7_345.init_rot                        = {0, 0, 0}

-- ════════════════════════════════════════════════════════════════════════════
-- BANK ANGLE SCALE
-- Arc of tick marks at top of HUD; pointer triangle rotates with roll.
-- Arc centre: {0, 0.0} in HUD_BASE space; radius 0.55.
-- ════════════════════════════════════════════════════════════════════════════
local BANK_R   = 0.55
local BANK_CX  = 0.00
local BANK_CY  = 0.00
local BANK_DG  = math.pi / 180

-- Fixed tick marks: major (longer) at 0, ±10, ±20, ±30; minor at ±5, ±15, ±25
local bankTicks = {
    {  0, 0.040}, {  5, 0.020}, { -5, 0.020},
    { 10, 0.030}, {-10, 0.030}, { 15, 0.020}, {-15, 0.020},
    { 20, 0.030}, {-20, 0.030}, { 25, 0.020}, {-25, 0.020},
    { 30, 0.030}, {-30, 0.030},
}
for _, t in ipairs(bankTicks) do
    local theta = t[1] * BANK_DG
    local len   = t[2]
    local xo = BANK_CX + BANK_R * math.sin(theta)
    local yo = BANK_CY + BANK_R * math.cos(theta)
    local xi = BANK_CX + (BANK_R - len) * math.sin(theta)
    local yi = BANK_CY + (BANK_R - len) * math.cos(theta)
    addHUDSimpleLine(nil, {0,0}, nil, HUD_BASE.name, nil, nil,
        {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.002, {{xo,yo},{xi,yi}})
end

-- Bank pointer: small downward-pointing triangle on the arc, rotates with roll
local BankPointerPivot = addHUDSimple(nil, {BANK_CX, BANK_CY}, nil, HUD_BASE.name, nil, nil,
    {"ROLL_HUD"}, {{"rotate_using_parameter", 0, 1.00}})

addHUDMeshPoly(nil, {0, 0}, nil, BankPointerPivot.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}},
    {{-0.012, BANK_R},{0.012, BANK_R},{0, BANK_R - 0.025}},
    {0,1,2})

-- ════════════════════════════════════════════════════════════════════════════
-- VERTICAL VELOCITY INDICATOR (VVI)
-- Right side of HUD. Scale: +1000 fpm (top) to -2000 fpm (bottom).
-- Pointer driven by VVI_SCALE; digital readout from VVI_HUD.
-- ════════════════════════════════════════════════════════════════════════════
local VVI_X      = 0.88
local VVI_ZERO_Y = 0.05
local VVI_SF     = 0.0001   -- HUD units per fpm

-- Vertical reference line
addHUDSimpleLine(nil, {0,0}, nil, HUD_BASE.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.001,
    {{VVI_X, VVI_ZERO_Y + 1000 * VVI_SF}, {VVI_X, VVI_ZERO_Y - 2000 * VVI_SF}})

-- Tick marks at key fpm values (inward from scale line)
local vviTicks = {
    { 1000, 0.020}, {  500, 0.012},
    {    0, 0.015},
    { -500, 0.012}, {-1000, 0.020}, {-1500, 0.012}, {-2000, 0.020},
}
for _, t in ipairs(vviTicks) do
    local fpm = t[1]
    local len = t[2]
    local ty  = VVI_ZERO_Y + fpm * VVI_SF
    addHUDSimpleLine(nil, {0,0}, nil, HUD_BASE.name, nil, nil,
        {"HUDBrightness"}, {{"opacity_using_parameter",0}},
        0.002, {{VVI_X, ty},{VVI_X + len, ty}})
end

-- Moving pointer (short horizontal arrow pointing left, tracks VVI_SCALE)
local VVI_Pointer_Base = addHUDSimple(nil, {VVI_X, VVI_ZERO_Y}, nil, HUD_BASE.name, nil, nil,
    {"VVI_SCALE"}, {{"move_up_down_using_parameter", 0, VVI_SF}})

addHUDSimpleLine(nil, {0,0}, nil, VVI_Pointer_Base.name, nil, nil,
    {"HUDBrightness"}, {{"opacity_using_parameter",0}}, 0.003, {{-0.05, 0},{0, 0}})

-- Digital VVI readout (fpm, rounded to nearest 10)
add_text_hud_param(VVI_X + 0.07, VVI_ZERO_Y - 0.22, "VVI_HUD", "HUDBrightness",
    "%0.0f", HUD_BASE, HUD_strdefs_digit, "F-117_Font_green")
