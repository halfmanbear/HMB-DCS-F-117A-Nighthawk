-- Presentation-only IRADS readouts; never changes camera, designation or delivery.
-- Formats follow the sensor display (TO 1F-117A-1 Figure 4-17 and the recorded
-- frames in docs/reference/CockpitImages/IRADS). Text parameters always carry
-- letters: DCS stores a numeric-looking string as a number, which a %s format
-- cannot print. Mach and airspeed are published as numbers instead.
local function handle(name) return get_param_handle(name) end
local function finite(v) return type(v)=="number" and v==v and math.abs(v)<math.huge end
local FT=3.2808399
local KT=1.94384449
local altitude=handle("F117_IRADS_ALT_TEXT")
local range=handle("F117_IRADS_RANGE_TEXT")
local time=handle("F117_IRADS_TIME_TEXT")
local coords=handle("F117_IRADS_COORD_TEXT")
local laser_text=handle("F117_IRADS_LASER_TEXT")
local mach=handle("F117_IRADS_MACH")
local cas=handle("F117_IRADS_CAS")
local clock=handle("F117_IRADS_CLOCK_TEXT")
local valid=handle("F117_IRADS_LOCK_VALID")
local distance=handle("F117_IRADS_LOCK_RANGE")
local flight=handle("F117_STORE_FLIGHT_TIME")
local sequence=handle("F117_RELEASE_SEQUENCE")
local cue_valid=handle("F117_RELEASE_CUE_VALID")
local cue_ttg=handle("F117_RELEASE_CUE_TTG")
local laser_armed=handle("F117_LASER_ARMED")
local laser_firing=handle("F117_LASER_FIRING")
local nav_valid=handle("F117_NAV_VALID")
local nav_range=handle("F117_NAV_RANGE_NM")
local nav_ttg=handle("F117_NAV_TTG_TEXT")
local air_valid=handle("F117_AIR_DATA_VALID")
local efm_cas=handle("F117_CAS_MPS")
local x,z=handle("F117_IRADS_LOCK_X"),handle("F117_IRADS_LOCK_Z")
local sensor=get_base_data()
local terrain,attempted=nil,false
local lastX,lastZ,lastCoords=nil,nil,nil
local lastSequence,released=nil,false
local function ddm(v,positive,negative,width)
    local total=math.floor(math.abs(v)*6000+.5)
    local degrees=math.floor(total/6000)
    local minutes=(total-degrees*6000)/100
    return string.format("%s %0"..width.."d'%05.2f",v<0 and negative or positive,degrees,minutes)
end
local function mmss(prefix,t)
    local seconds=math.min(5999,math.floor(t+.5))
    return string.format("%s %02d:%02d",prefix,math.floor(seconds/60),seconds%60)
end
local function update_range(locked)
    -- Feet while designated (LR with the laser on, ER from geometry without it);
    -- otherwise whole nautical miles to the INS destination.
    local r=distance:get()
    if locked and finite(r) and r>0 and r*FT<99999.5 then
        range:set(string.format("%s %05.0f",laser_firing:get()>.5 and "LR" or "ER",r*FT))
        return
    end
    local nm=nav_range:get()
    if nav_valid:get()>.5 and finite(nm) and nm>=0 then
        range:set(string.format(" R %03.0fNM",math.min(999,nm)))
    else range:set(" R -----") end
end
local function update_time(locked)
    -- TTI from release until the designation is dropped (holding at 00:00 after
    -- impact), then TTG to the release point or to the INS destination.
    local s=sequence:get()
    if finite(s) and lastSequence and s>lastSequence then released=true end
    lastSequence=finite(s) and s or lastSequence
    if not locked then released=false end
    local t=flight:get()
    if released then time:set(mmss("TTI",finite(t) and t>0 and t or 0));return end
    local ttg=cue_ttg:get()
    if locked and cue_valid:get()>.5 and finite(ttg) and ttg>=0 then time:set(mmss("TTG",ttg));return end
    local text=nav_ttg:get()
    time:set(type(text)=="string" and text:find("^TTG") and text or "TTG --:--")
end
local function update_air_data()
    local m=sensor.getMachNumber and sensor.getMachNumber()
    mach:set(finite(m) and math.max(0,math.min(99,m*100)) or 0)
    local v=air_valid:get()>.5 and efm_cas:get() or sensor.getIndicatedAirSpeed and sensor.getIndicatedAirSpeed()
    cas:set(finite(v) and math.max(0,math.min(999,v*KT)) or 0)
    local seconds=get_absolute_model_time and get_absolute_model_time()
    if finite(seconds) then
        seconds=math.floor(seconds)%86400
        clock:set(string.format("GPS %02d%02d:%02d",math.floor(seconds/3600),math.floor(seconds/60)%60,seconds%60))
    else clock:set("GPS --:--") end
end
local function update()
    local alt=sensor.getBarometricAltitude()
    altitude:set(finite(alt) and string.format("ALT %05.0f",alt*FT) or "ALT -----")
    local locked=valid:get()>.5
    update_range(locked)
    update_time(locked)
    update_air_data()
    if laser_armed:get()>.5 then
        laser_text:set(laser_firing:get()>.5 and "AF" or locked and "AX" or "A")
    else laser_text:set("") end
    if not locked then
        coords:set("");lastX,lastZ,lastCoords=nil,nil,nil
        return
    end
    if not attempted then
        attempted=true
        local ok,result=pcall(require,"terrain")
        if ok and type(result)=="table" and type(result.convertMetersToLatLon)=="function" then terrain=result end
    end
    local px,pz=x:get(),z:get()
    if not finite(px) or not finite(pz) then coords:set("");return end
    if px==lastX and pz==lastZ and lastCoords then coords:set(lastCoords);return end
    local label="GPS COORD UNAVAILABLE"
    if terrain then
        local ok,lat,lon=pcall(terrain.convertMetersToLatLon,px,pz)
        if ok and finite(lat) and finite(lon) and math.abs(lat)<=90 and math.abs(lon)<=180 then
            label=ddm(lat,"N LAT","S LAT",2).." "..ddm(lon,"E LNG","W LNG",3)
        end
    end
    lastX,lastZ,lastCoords=px,pz,label
    coords:set(label)
end
return {update=update}
