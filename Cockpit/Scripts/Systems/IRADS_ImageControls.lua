-- Presentation-only image adjustment. Manual settings survive sensor/page changes.
local commands=irads_image_commands
local brightness=get_param_handle("F117_IRADS_BRIGHTNESS")
local contrast=get_param_handle("F117_IRADS_CONTRAST")
local native_active=get_param_handle("F117_NATIVE_BRIGHTNESS_ACTIVE")
local draw_brightness=get_param_handle("F117_IRADS_DRAW_BRIGHTNESS")
local video_draw=get_param_handle("F117_IRADS_VIDEO_DRAW_BRIGHTNESS")
local centre=get_param_handle("CDBrightness")
local dim=get_param_handle("F117_IRADS_DIM_OPACITY")
local band=get_param_handle("F117_IRADS_CONTRAST_BAND")
-- L reports control travel, not the nonlinear internal video multiplier.
-- This is a DCS presentation mapping, not a calibrated thermal level model.
local level=get_param_handle("F117_IRADS_LEVEL")
local gain=get_param_handle("F117_IRADS_GAIN")
-- Forty equal control steps: fine low-light adjustment, wider daytime coverage.
local LOW,HIGH,STEP=.025,.80,.025
local b,c=.80,.80
local function clamp(value,low,high) return math.max(low,math.min(high,value)) end
local function finite(v) return type(v)=="number" and v==v and math.abs(v)<math.huge end
-- Installed only while the screenshot harness owns a DCS session.
if LockOn_Options and LockOn_Options.script_path then
    local ok,enabled=pcall(dofile,LockOn_Options.script_path.."Systems/IRADS_LevelCalibration.local.lua")
    if ok and enabled==true then LOW,HIGH=0,1 end
end
local function brightness_for_level(u) return LOW+(HIGH-LOW)*u*u end
local function level_for_brightness(v) return math.sqrt(clamp((v-LOW)/(HIGH-LOW),0,1)) end
local function daylight_fraction(seconds)
    local hour=(finite(seconds) and seconds or 43200)%86400/3600
    -- Local mission clock, with two-hour dawn/dusk ramps; not a solar model.
    local daylight=clamp((hour-6)/2,0,1)*clamp((19-hour)/2,0,1)
    return daylight
end
local function default_brightness(seconds)
    return .065+(.80-.065)*daylight_fraction(seconds)
end
local function default_contrast(seconds)
    return .96-(.96-.80)*daylight_fraction(seconds)
end
local function default_side_brightness(seconds)
    return .12+(1-.12)*daylight_fraction(seconds)
end
-- DEP gain under the HUD brightness control; full HUD by day still dims it a little.
local function default_dep_brightness(seconds)
    return .30+(.85-.30)*daylight_fraction(seconds)
end
local function publish()
    brightness:set(b);contrast:set(c)
    local native=native_active:get()==1
    draw_brightness:set(native and 1 or (1-clamp(centre:get(),0,1))*math.min(1,b*3))
    video_draw:set(1)
    dim:set(1-b);band:set(math.floor((c-.35)*100+.5))
    level:set(level_for_brightness(b));gain:set((c-.35)/.65)
end
local function initialize()
    local seconds=get_absolute_model_time()
    b=default_brightness(seconds);c=default_contrast(seconds)
    publish()
end
-- Stock I-251 commands act like the mod's own buttons.
local STOCK={[native_commands.I251_BRIGHTNESS_UP]=commands.BRIGHTNESS_UP,
             [native_commands.I251_BRIGHTNESS_DOWN]=commands.BRIGHTNESS_DOWN,
             [native_commands.I251_CONTRAST_UP]=commands.CONTRAST_UP,
             [native_commands.I251_CONTRAST_DOWN]=commands.CONTRAST_DOWN}
local function set_command(command,value)
    command=STOCK[command] or command
    if command==commands.BRIGHTNESS_AXIS or command==commands.CONTRAST_AXIS then
        if finite(value) then
            local unit=(clamp(value,-1,1)+1)/2
            if command==commands.BRIGHTNESS_AXIS then b=brightness_for_level(unit) else c=.35+.65*unit end
        end
    elseif command==commands.BRIGHTNESS_UP then b=brightness_for_level(clamp(level_for_brightness(b)+STEP,0,1))
    elseif command==commands.BRIGHTNESS_DOWN then b=brightness_for_level(clamp(level_for_brightness(b)-STEP,0,1))
    elseif command==commands.CONTRAST_UP then c=clamp(c+.05,.35,1)
    elseif command==commands.CONTRAST_DOWN then c=clamp(c-.05,.35,1)
    else return false end
    publish()
    return true
end
return {initialize=initialize,set_command=set_command,default_brightness=default_brightness,
        default_contrast=default_contrast,default_side_brightness=default_side_brightness,
        default_dep_brightness=default_dep_brightness}
