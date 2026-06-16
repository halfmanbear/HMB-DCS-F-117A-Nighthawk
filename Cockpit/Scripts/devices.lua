local count = 0
local function counter()
	count = count + 1
	return count
end
-------DEVICE ID----------
devices = {}
devices["NVG"]			            = counter()
devices["LIGHTS"]					= counter()
devices["MISCFUNC"]					= counter()
devices["BOMB_BAY"]					= counter()
devices["TAILHOOK"]					= counter()
devices["HUD"]					    = counter()
devices["DISPLAYS"]					= counter()
devices["FC3"]					    = counter()
devices["IRADS"]				    = counter()
devices["GAUGES"]				    = counter()
devices["WEAPONS"]				    = counter()
