-- Cockpit device IDs. Each is written out: input bindings, saved user bindings
-- and missions refer to a device by its number, so an ID must never move.
-- Give a new device the next free number.
devices = {
    NVG           = 1,
    LIGHTS        = 2,
    CONTROL_STICK = 3,
    BOMB_BAY      = 4,
    TAILHOOK      = 5, -- reserved; the EFM runs the hook
    HUD           = 6,
    DISPLAYS      = 7,
    FC3           = 8,
    IRADS         = 9,
    GAUGES        = 10,
    WEAPONS       = 11,
    MAP_CHARTS    = 12,
    ELECTRICAL    = 13,
}
