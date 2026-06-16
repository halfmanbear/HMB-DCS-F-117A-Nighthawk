-- F-117A IRADS (Infra-Red Acquisition and Designation System)
-- Sensor database registration using the declare_sensor() API.
-- declare_sensor() is the correct global (same as used in CoreMods/aircraft/AircraftWeaponPack/targeting_pods.lua).
-- type = OPTIC_SENSOR_IR; magnifications stepped by iCommandTVSensorZoomIn/Out (103/104).

declare_sensor({
    category       = SENSOR_OPTICAL,
    Name           = "IRADS",
    type           = OPTIC_SENSOR_IR,
    scan_volume    = {
        azimuth   = {-60.0, 60.0},
        elevation = {-140.0, 30.0},
    },
    view_volume_max = {
        azimuth_sector   = 50,
        elevation_sector = 50,
    },
    magnifications = {1.4, 10, 80},
    resolution     = 0.07,
    laserRanger    = true,
})
