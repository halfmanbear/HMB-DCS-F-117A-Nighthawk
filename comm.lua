HumanRadio = {
    frequency    = 251.000,     -- MHz was 127.5
    editable     = true,
    maxFrequency = 399.975,     -- UHF upper : was 156.000
    minFrequency = 30.000,      -- include VHF/FM band so Easy Comms / FM tankers/JTAC can work : was 100.000
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
