dofile(LockOn_Options.script_path .. "devices.lua")
dofile(LockOn_Options.script_path .. "command_defs.lua")
local dev = GetSelf()
make_default_activity(0.1)
local profile_param = get_param_handle("F117_CCRP_PROFILE")
local valid_param = get_param_handle("F117_STORE_VALID")
local station_param = get_param_handle("F117_RELEASE_STATION")
local selected_param = get_param_handle("PLAYER_SELECTED_STATION")
local release_sequence_param = get_param_handle("F117_RELEASE_SEQUENCE")
local last_release_sequence = 0
local station = 0
local last_signature = nil
dev:listen_command(f117_commands.WEAPON_STATION_NEXT)
dev:listen_command(f117_commands.WEAPON_STATION_PREV)

local function tokens(value, result, seen)
    if type(value)=="string" or type(value)=="number" then result[#result+1]=tostring(value)
    elseif type(value)=="table" and not seen[value] then
        seen[value]=true
        for k,v in pairs(value) do tokens(k,result,seen); tokens(v,result,seen) end
    end
end

local function classify(info)
    local t={}; tokens(info,t,{})
    local s=string.lower(table.concat(t," | "))
    if s:find("gbu31_v3b",1,true) or s:find("gbu_31_v_3b",1,true) or s:find("gbu-31-v3b",1,true) or s:find("gbu-31v3",1,true) then return 1 end
    if s:find("gbu32",1,true) or s:find("gbu_32",1,true) or s:find("gbu-32",1,true) then return 2 end
    if s:find("gbu_27",1,true) or s:find("gbu-27",1,true) or s:find("ef0a9419",1,true) then return 4 end
    if s:find("gbu_12",1,true) or s:find("gbu-12",1,true) or s:find("db769d48",1,true) then return 3 end
    if s:find("gbu31",1,true) or s:find("gbu_31",1,true) or s:find("gbu-31",1,true) then return 0 end
    local weapon=info.weapon
    if type(weapon)=="table" then
        local stock = {[38]=3,[43]=4,[85]=0,[92]=1}
        return stock[weapon.level4]
    end
end

local function read_station(index)
    local ok,info=pcall(function() return dev:get_station_info(index) end)
    if not ok or type(info)~="table" then return nil end
    local count=info.count
    if type(count)~="number" then
        local good,n=pcall(function() return dev:get_weapon_count(index) end)
        if good then count=n end
    end
    if type(count)~="number" or count<=0 then return nil end
    return info,classify(info)
end

local function sync()
    local info,profile=read_station(station)
    local valid=info~=nil and profile~=nil
    profile_param:set(valid and profile or -1)
    valid_param:set(valid and 1 or 0)
    station_param:set(valid and station or -1)
    selected_param:set(station)
    get_param_handle("F117_WEAPON_STATION"):set(station+1)
    local signature=tostring(station)..":"..tostring(profile)..":"..tostring(info and info.count)
    if signature~=last_signature then
        last_signature=signature
        log.write("F117_WEAPONS",log.INFO,"selected station/profile/count "..signature)
    end
end

local function next_station(direction)
    for step=1,9 do
        local candidate=(station+direction*step)%9
        local info,profile=read_station(candidate)
        if info and profile~=nil then station=candidate; break end
    end
    sync()
end

function SetCommand(command,value)
    if command==f117_commands.WEAPON_STATION_NEXT then next_station(1)
    elseif command==f117_commands.WEAPON_STATION_PREV then next_station(-1) end
end
function post_initialize()
    last_release_sequence=release_sequence_param:get()
    local info,profile=read_station(station)
    if not info or profile==nil then next_station(1) else sync() end
end
function update()
    -- Step once per accepted native launch, never from a failed attempt or rearm.
    -- Gate-firing remains latched until pickle is released, so selecting the next
    -- store cannot release it on the same held press.
    local sequence=release_sequence_param:get()
    if sequence>last_release_sequence then next_station(1) else sync() end
    last_release_sequence=sequence
end
need_to_be_closed = false
