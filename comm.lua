HumanRadio = {
    frequency    = 251.000,     -- MHz
    editable     = true,
    maxFrequency = 399.975,     -- UHF upper
    minFrequency = 30.000,      -- include VHF/FM band so Easy Comms / FM tankers/JTAC can work
    modulation   = MODULATION_AM -- use the constant; 0 works but this is clearer
}
local parameters = {
    fighter = true,
    radar = false,
    ECM = false,
    refueling = true
}
return utils.verifyChunk(utils.loadfileIn("Scripts/UI/RadioCommandDialogPanel/Config/LockOnAirplane.lua", getfenv()))(
    parameters
)
