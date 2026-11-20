-- Native communicator for the custom cockpit. HumanRadio supplies ME defaults;
-- this device and the linked intercom provide the in-flight communication path.
dofile(LockOn_Options.common_script_path .. "Radio.lua")
device_timer_dt = 0.2
innerNoise = getInnerNoise(2.5E-6, 6.0)
frequency_accuracy = 500.0
band_width = 22E3
power = 10.0
RxfreqResponseQuality = 10
TxSpectrumPowerFactor = 8
TxBandwidth = 7E3
agr = {
    input_signal_deviation = rangeUtoDb(2.5E-6, 0.5),
    output_signal_deviation = 4,
    input_signal_linear_zone = 15,
    regulation_time = 0.15,
}
GUI = {
    range = {min = 30.0E6, max = 399.975E6, step = 25.0E3},
    displayName = "Radio",
    AM = true,
    FM = true,
}
guard_receiver = {default_frequency = 243.0E6, modulation = 0}
local initialized = false
function update()
    if initialized then return end
    local radio = GetSelf()
    radio:push_frequency_range(30.0E6, 399.975E6, 25.0E3)
    local frequency, modulation = 251.0E6, 0
    if get_aircraft_mission_data then
        local mission_frequency = tonumber(get_aircraft_mission_data("frequency"))
        local mission_modulation = tonumber(get_aircraft_mission_data("modulation"))
        if mission_frequency and mission_frequency >= 30 and mission_frequency <= 399.975 then
            frequency = mission_frequency * 1.0E6
        end
        if mission_modulation == 0 or mission_modulation == 1 then
            modulation = mission_modulation
        end
    end
    radio:set_frequency(frequency)
    radio:set_modulation(modulation)
    radio:set_on_off(true)
    initialized = true
    if log then log.write("F117_COMMS", log.INFO, "Native radio initialized") end
end
function SetCommand(command, value) end
function LoadSettings(path) return 0 end
function SaveSettings(path) end
need_to_be_closed = false
