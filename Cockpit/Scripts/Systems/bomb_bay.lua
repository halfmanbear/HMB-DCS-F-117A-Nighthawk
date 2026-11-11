-- Release consent, bay actuation and targeted store launch are owned by the EFM.
-- Never fall back to avSimpleWeaponSystem's default forward aim point.
--
-- This device only reports the two weapon bays, as the amber door and green trapeze lights
-- of the armament control panel do (TO 1F-117A-1, Weapons Bay Door Open and Trapeze Down
-- Lights). The EFM publishes each bay as one 0-1 position, the same value as its draw
-- argument (26 left, 27 right): the door opens over the first 0.7 and the trapeze
-- lowers from 0.6 to 1. Each light is 0 off, 1 in transit (flashing) or 2 steady.
make_default_activity(0.1)

local DOOR_OPEN = 0.7    -- door fully open (the EDM keys)
local TRAPEZE_UP = 0.6   -- the trapeze starts to lower here
local EDGE = 0.005

local bays = {
    { position = get_param_handle("F117_BAY_L"), door = get_param_handle("F117_BAY_L_DOOR"), trapeze = get_param_handle("F117_BAY_L_TRAP") },
    { position = get_param_handle("F117_BAY_R"), door = get_param_handle("F117_BAY_R_DOOR"), trapeze = get_param_handle("F117_BAY_R_TRAP") },
}

local function light(value, off, on)
    if value <= off + EDGE then return 0 end
    if value >= on - EDGE then return 2 end
    return 1
end

function update()
    for _, bay in ipairs(bays) do
        local position = bay.position:get()
        bay.door:set(light(position, 0, DOOR_OPEN))
        bay.trapeze:set(light(position, TRAPEZE_UP, 1))
    end
end
need_to_be_closed = false
