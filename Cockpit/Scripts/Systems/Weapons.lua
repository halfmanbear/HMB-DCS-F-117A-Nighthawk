dofile(LockOn_Options.script_path .. "devices.lua")

local update_time_step = 0.25
make_default_activity(update_time_step)

local dev = GetSelf()
local F117_CCRP_PROFILE = get_param_handle("F117_CCRP_PROFILE")
local LOG_TAG = "F117_WEAPONS"

local detected_profile = nil
local detected_station = nil
local signature_logged = false
local profile_logged = false
local empty_station_logged = false

local function collect_tokens(value, tokens, seen)
	if value == nil then
		return
	end

	local value_type = type(value)
	if value_type == "string" or value_type == "number" then
		tokens[#tokens + 1] = tostring(value)
		return
	end

	if value_type ~= "table" then
		return
	end

	if seen[value] then
		return
	end

	seen[value] = true
	for key, nested in pairs(value) do
		collect_tokens(key, tokens, seen)
		collect_tokens(nested, tokens, seen)
	end
end

local function classify_station_signature(signature)
	local s = string.lower(signature)

	if s:find("gbu_31_v_3b", 1, true) or s:find("gbu-31v3b", 1, true) or s:find("gbu31v3b", 1, true) then
		return 1
	end

	if s:find("gbu_32_v_2b", 1, true) or s:find("gbu-32", 1, true) or s:find("gbu32_jdam", 1, true) or s:find("gbu_32", 1, true) then
		return 2
	end

	if s:find("gbu_27", 1, true) or s:find("gbu-27", 1, true) or s:find("ef0a9419", 1, true) then
		return 4
	end

	if s:find("gbu_12", 1, true) or s:find("gbu-12", 1, true) or s:find("db769d48", 1, true) then
		return 3
	end

	if s:find("gbu_31_v_1b", 1, true) or s:find("gbu31_jdam", 1, true) or s:find("gbu-31", 1, true) or s:find("gbu_31", 1, true) then
		return 0
	end

	return nil
end

local function try_detect_profile_from_station(station_index)
	local count_ok, count = pcall(function()
		return dev:get_weapon_count(station_index)
	end)

	if count_ok and type(count) == "number" and count <= 0 then
		if not empty_station_logged then
			log.write(LOG_TAG, log.INFO, string.format("station %d empty according to get_weapon_count()", station_index))
			empty_station_logged = true
		end
		return nil
	end

	local ok, station_info = pcall(function()
		return dev:get_station_info(station_index)
	end)

	if not ok or station_info == nil then
		return nil
	end

	local tokens = {}
	collect_tokens(station_info, tokens, {})
	local signature = table.concat(tokens, " | ")
	if not signature_logged and #signature > 0 then
		log.write(LOG_TAG, log.INFO, string.format("station %d signature: %s", station_index, signature))
		signature_logged = true
	end
	local profile = classify_station_signature(signature)
	if profile ~= nil then
		return profile, station_index
	end

	return nil
end

local function sync_ccrp_profile()
	if detected_profile ~= nil then
		return true
	end

	local stations_to_probe = {-1, 0, 1, 2, 3, 4, 5, 6, 7, 8}
	for _, station in ipairs(stations_to_probe) do
		local profile, station_index = try_detect_profile_from_station(station)
		if profile ~= nil then
			detected_profile = profile
			detected_station = station_index
			F117_CCRP_PROFILE:set(profile)
			if not profile_logged then
				log.write(LOG_TAG, log.INFO, string.format("CCRP profile detected: %d station: %d", profile, detected_station))
				profile_logged = true
			end
			return true
		end
	end

	return false
end

function post_initialize()
	sync_ccrp_profile()
end

function update()
	if detected_profile == nil then
		sync_ccrp_profile()
	end
end
