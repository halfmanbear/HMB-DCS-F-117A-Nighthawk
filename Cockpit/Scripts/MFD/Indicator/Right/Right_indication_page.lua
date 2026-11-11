-- RIGHT DISPLAY LAYOUT STARTER: editable in Layout Studio.
-- Not connected to an in-game indicator yet. Coordinates use the same
-- approximate +/-0.08 design area as the centre MFD overlay.
-- Replace these alignment marks with the desired systems/mission layout.
-- Existing device parameters include RD_EMGY_MODE, RD_TEMP_TOGGLE,
-- RD_ENG_TOGGLE and RD_VSI_TOGGLE; no page content is assumed here.
local LW = 0.0004

local ROOT = CreateElement "ceSimple"
ROOT.name = create_guid_string()
ROOT.init_pos = {0, 0}
ROOT.element_params = {"mainpower"}
ROOT.controllers = {{"parameter_in_range", 0, 0.9, 1.1}}
Add(ROOT)

local function props(obj, params, ctrls)
    obj.name = obj.name or create_guid_string()
    obj.parent_element = ROOT.name
    obj.h_clip_relation = h_clip_relations.COMPARE
    obj.level = SIDE_LEVEL
    obj.collimated = false
    obj.additive_alpha = true
    obj.blend_mode = blend_mode.IBM_REGULAR_ADDITIVE_ALPHA
    obj.element_params = params
    obj.controllers = ctrls
    Add(obj)
    return obj
end

local function line(x1, y1, x2, y2)
    local obj = CreateElement "ceSimpleLineObject"
    obj.vertices = {{x1, y1}, {x2, y2}}
    obj.width = LW
    obj.material = SIDE_GREEN
    return props(obj)
end

local function text(value, x, y, sd, align, params, ctrls)
    local obj = CreateElement "ceStringPoly"
    obj.init_pos = {x, y}
    obj.value = value
    obj.material = SIDE_FONT
    obj.stringdefs = sd or SIDE_SD
    obj.alignment = align or "CenterCenter"
    return props(obj, params, ctrls)
end

-- Alignment guides only, not simulated avionics data.
text("RIGHT DISPLAY", 0, 0.065)
line(-0.075, 0.075, -0.060, 0.075)
line(-0.075, 0.075, -0.075, 0.060)
line( 0.075, 0.075,  0.060, 0.075)
line( 0.075, 0.075,  0.075, 0.060)
line(-0.075,-0.075, -0.060,-0.075)
line(-0.075,-0.075, -0.075,-0.060)
line( 0.075,-0.075,  0.060,-0.075)
line( 0.075,-0.075,  0.075,-0.060)
line(-0.004, 0, 0.004, 0)
line(0, -0.004, 0, 0.004)
