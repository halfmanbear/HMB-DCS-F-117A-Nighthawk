dofile(LockOn_Options.script_path .. "devices.lua")
dofile(LockOn_Options.script_path .. "command_defs.lua")
local dev = GetSelf()
make_default_activity(0.1)
local profile_param = get_param_handle("F117_CCRP_PROFILE")
local valid_param = get_param_handle("F117_STORE_VALID")
local station_param = get_param_handle("F117_RELEASE_STATION")
local selected_param = get_param_handle("PLAYER_SELECTED_STATION")
local release_sequence_param = get_param_handle("F117_RELEASE_SEQUENCE")
local cue_valid_param = get_param_handle("F117_RELEASE_CUE_VALID")
-- VSD store legend: the fired store stays listed, crossed out, until the pilot
-- steps station or a new release cue starts (fresh designation).
local vsd_store_param = get_param_handle("F117_VSD_STORE")
local vsd_fired_param = get_param_handle("F117_VSD_STORE_FIRED")
local fired_profile = nil
local last_cue_valid = 0
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

-- Store profiles. The index is F117_CCRP_PROFILE and must match the order of
-- kCcrpStoreModels in the EFM. Profiles 0-4 never move.
--  0 GBU-31(V)1/B  1 GBU-31(V)3/B  2 GBU-32(V)2/B  3 GBU-12  4 GBU-27
--  5 GBU-10  6 Mk-82  7 Mk-84  8 CBU-105  9 AGM-154A  10 AGM-154B  11 AGM-154C
--  12 AGM-65D  13 AGM-65E (laser)
local function any(s,...)
    for _,needle in ipairs({...}) do if s:find(needle,1,true) then return true end end
    return false
end

local function classify(info)
    local t={}; tokens(info,t,{})
    local s=string.lower(table.concat(t," | "))
    -- Most specific first: the GBU-31 and GBU-10 are built on the Mk-84 body.
    if any(s,"gbu31_v3b","gbu_31_v_3b","gbu-31-v3b","gbu-31v3") then return 1 end
    if any(s,"gbu32","gbu_32","gbu-32") then return 2 end
    if any(s,"gbu_27","gbu-27","ef0a9419") then return 4 end
    if any(s,"gbu_12","gbu-12","db769d48") then return 3 end
    if any(s,"gbu31","gbu_31","gbu-31") then return 0 end
    if any(s,"gbu_10","gbu-10","51f9aae5") then return 5 end
    if any(s,"agm_154c","agm-154c","9bcc2a2b") then return 11 end
    if any(s,"agm_154b","agm-154b") then return 10 end
    if any(s,"agm_154a","agm-154a","agm_154","agm-154") then return 9 end
    if any(s,"agm_65e","agm-65e","agm_65l","agm-65l","f16a4de0") then return 13 end
    if any(s,"agm_65d","agm-65d","444ba8ae") then return 12 end
    if any(s,"cbu_105","cbu-105") then return 8 end
    if any(s,"mk_84","mk-84","ab8b8299") then return 7 end
    if any(s,"mk_82","mk-82","bce4e030") then return 6 end
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
    vsd_store_param:set(fired_profile or (valid and profile or -1))
    vsd_fired_param:set(fired_profile and 1 or 0)
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
    if command==f117_commands.WEAPON_STATION_NEXT then fired_profile=nil; next_station(1)
    elseif command==f117_commands.WEAPON_STATION_PREV then fired_profile=nil; next_station(-1) end
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
    local cue_valid=cue_valid_param:get()
    if cue_valid>.5 and last_cue_valid<=.5 then fired_profile=nil end
    last_cue_valid=cue_valid
    if sequence>last_release_sequence then
        local fired=profile_param:get()
        if fired>=0 then fired_profile=fired end
        next_station(1)
    else sync() end
    last_release_sequence=sequence
end
need_to_be_closed = false
