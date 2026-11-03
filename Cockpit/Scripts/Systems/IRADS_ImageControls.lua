-- Presentation-only image adjustment. Manual settings survive sensor/page changes.
local commands=irads_image_commands
local brightness=get_param_handle("F117_IRADS_BRIGHTNESS")
local contrast=get_param_handle("F117_IRADS_CONTRAST")
local native_active=get_param_handle("F117_NATIVE_BRIGHTNESS_ACTIVE")
local draw_brightness=get_param_handle("F117_IRADS_DRAW_BRIGHTNESS")
local dim=get_param_handle("F117_IRADS_DIM_OPACITY")
local band=get_param_handle("F117_IRADS_CONTRAST_BAND")
local b,c=.45,.80
local function clamp(value,low,high) return math.max(low,math.min(high,value)) end
local function finite(v) return type(v)=="number" and v==v and math.abs(v)<math.huge end
local function daylight_fraction(seconds)
    local hour=(finite(seconds) and seconds or 43200)%86400/3600
    -- Local mission clock, with two-hour dawn/dusk ramps; not a solar model.
    local daylight=clamp((hour-6)/2,0,1)*clamp((19-hour)/2,0,1)
    return daylight
end
local function default_brightness(seconds)
    return .11+(.45-.11)*daylight_fraction(seconds)
end
local function default_contrast(seconds)
    return .96-(.96-.80)*daylight_fraction(seconds)
end
local function default_side_brightness(seconds)
    return .12+(1-.12)*daylight_fraction(seconds)
end
local function publish()
    brightness:set(b);contrast:set(c)
    local native=native_active:get()==1
    draw_brightness:set(native and 1 or b)
    dim:set(native and 0 or 1-b);band:set(math.floor((c-.35)*100+.5))
end
local function initialize()
    local seconds=get_absolute_model_time()
    b=default_brightness(seconds);c=default_contrast(seconds)
    publish()
end
local function set_command(command,value)
    if command==commands.BRIGHTNESS_AXIS or command==commands.CONTRAST_AXIS then
        if finite(value) then
            local unit=(clamp(value,-1,1)+1)/2
            if command==commands.BRIGHTNESS_AXIS then b=.08+.92*unit else c=.35+.65*unit end
        end
    elseif command==commands.BRIGHTNESS_UP then b=clamp(b+.05,.08,1)
    elseif command==commands.BRIGHTNESS_DOWN then b=clamp(b-.05,.08,1)
    elseif command==commands.CONTRAST_UP then c=clamp(c+.05,.35,1)
    elseif command==commands.CONTRAST_DOWN then c=clamp(c-.05,.35,1)
    elseif command==commands.RESET then initialize();return true
    else return false end
    publish()
    return true
end
return {initialize=initialize,set_command=set_command,default_brightness=default_brightness,
        default_contrast=default_contrast,default_side_brightness=default_side_brightness}
