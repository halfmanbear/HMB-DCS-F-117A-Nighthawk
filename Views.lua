-- Cockpit, chase and arcade cameras, and the cockpit snap views.
-- Model axes, metres: x forward, y up, z right.

ViewSettings = {
    Cockpit = {
        [1] = { -- player seat
            CockpitLocalPoint = {5.32, 1.21, -0.004}, -- head position in the exterior model
            EyePoint = {0, 0, 0},
            CameraViewAngleLimits = {20, 105}, -- field of view, degrees
            CameraAngleRestriction = {false, 90, 0.4},
            CameraAngleLimits = {200, -110, 110}, -- yaw range, then pitch down and up
            limits_6DOF = {
                x = {-0.05, 0.45},
                y = {-0.2, 0.2},
                z = {-0.22, 0.22},
                roll = 90,
            },
            ShoulderSize = 0.2,
            Allow360rotation = false,
            NightVisionGoggles = {enable = true},
        },
    },
    Chase  = {LocalPoint = {1.3, 3.604, 0}, AnglesDefault = {180, -8}},
    Arcade = {LocalPoint = {-13.79, 6.204, 0}, AnglesDefault = {0, -8}},
}

-- One snap view: field of view, then yaw and pitch in degrees,
-- then an optional head offset forward and up in metres.
local function snap(fov, yaw, pitch, forward, up)
    return {
        viewAngle = fov,
        hAngle = yaw,
        vAngle = pitch,
        x_trans = forward or 0,
        y_trans = up or 0,
        z_trans = 0,
        rollAngle = 0,
    }
end

local WIDE = 87.468338

SnapViews = {
    [1] = { -- player seat, views 1 to 13 in order
        snap(71.824692, 0, -32.458889),
        snap(33.361835, 41.045925, -40.805656),
        snap(30.427544, 0, -41.808968),
        snap(34.392349, -32.597401, -35.293747),
        snap(WIDE, 129.012665, 14.547977),
        snap(43.977936, 0, -4.951577),
        snap(WIDE, -129.012665, 14.491872),
        snap(WIDE, 82.862923, -9.5),
        snap(WIDE, 0, 38.979362),
        snap(WIDE, -82.461266, -12.843998),
        snap(68.786629, 15.618313, 7.522498),
        snap(69.165199, -15.683434, 8.54915),
        snap(WIDE, 0, -9.5, 0.113927, -0.02), -- 13: default view
    },
}
