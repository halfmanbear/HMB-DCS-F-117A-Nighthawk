local count = 0
local function counter()
	count = count + 1
	return count
end
-------DEVICE ID----------
devices = {}
devices["HELMET_DEVICE"]			= counter()
devices["LIGHTS"]					= counter()
devices["MISCFUNC"]					= counter()
devices["BOMB_BAY"]					= counter()
devices["TAILHOOK"]					= counter()