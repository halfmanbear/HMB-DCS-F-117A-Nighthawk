-- F-117A mass and landing gear data, loaded by entry.lua as the FM table for make_flyable.
--
-- Who reads this file:
--   DCS reads the table when it builds the player aircraft.
--   The EFM reads none of it: DCS offers the path through ed_fm_configure, and that hook is empty.
--   Values reach the EFM only through DCS, such as ed_fm_set_current_mass_state.
--
-- Positions are {+forward/-back, +up/-down, +right/-left} in metres from the model origin.
-- Most suspension notes follow CoreMods/aircraft/C130J/Entry/suspension_30.lua.
--
-- Strut force, per those notes:
--   spring_force = amortizer_static_force + amortizer_spring_force_factor * strut_length ^ amortizer_spring_force_factor_rate
--   if strut_length < amortizer_reduce_length then spring_force = spring_force * strut_length / amortizer_reduce_length
--   damper = amortizer_direct_damper_force_factor while compressing, amortizer_back_damper_force_factor while extending
FM = {
    ---------------------------------------------------------------------------
    -- Mass properties
    ---------------------------------------------------------------------------
    center_of_mass = {0.0, 0.1, 0.0}, -- Centre of mass for empty weight (earlier value {0.35, -0.10, 0.0})
    -- kg m2: roll, yaw, pitch, Ixy. DCS has Y up and Z right, so Iy is yaw and Iz is pitch.
    -- An estimate, about +/-30%: the manuals give no inertia, so these follow the F-15C, which has almost the same mass and size.
    moment_of_inertia = {40000, 260000, 225000, 0.0},

    ---------------------------------------------------------------------------
    -- Systems
    ---------------------------------------------------------------------------
    disable_built_in_oxygen_system = true, -- Turns off the DCS oxygen system; the EFM reports ED_FM_OXYGEN_SUPPLY

    ---------------------------------------------------------------------------
    -- Landing gear: 1 nose, 2 left main, 3 right main
    -- The EFM also reports brake, steering, antiskid and gear state each frame through ed_fm_get_param.
    ---------------------------------------------------------------------------
    suspension = {
        { -- Nose gear
            -- Identity and position
            damage_element = 83, -- Damage cell for this wheel; matches WHEEL_F in the aircraft Damage table
            collision_shell_name = "WHEEL_F", -- Model collision shell for this wheel
            mass = 120, -- kg by its name: gear mass. Stock files don't document it
            pos = {5.076543, -2.022782, 0.00}, -- Wheel position (earlier test value {5.0765, -2.150, 0})
            -- EDM tyre contact point: -2.089264 strut extended, -1.925919 strut compressed, delta 0.163345 m.
            -- EDM wheel position when aligned with the user/bounding box: -2.022782.

            -- Steering
            self_attitude = false, -- Not self-orienting: the EFM steers this wheel and also reports 0 for self-attitude
            wheel_axle_offset = 0.00, -- m: horizontal offset of the wheel centre from the strut axis
            yaw_limit = math.rad(45), -- Maximum steering range (TO 1F-117A-1 page 1-29). The EFM commands 10 deg, or 45 deg while the authority button is held. Keep in step with kNoseWheelYawHigh_RAD in the EFM and tand_gear_max in F-117-NightHawk.lua
            moment_limit = 750.0, -- Steering moment limit. Undocumented; stock F-16C uses the same value
            damper_coeff = 300.0, -- Yaw axis rotation damping

            -- Strut
            amortizer_min_length = 0.00, -- m: minimum strut length
            amortizer_max_length = 0.12, -- m: maximum (unloaded) strut length
            amortizer_basic_length = 0.12, -- m: normally the same as the maximum length
            amortizer_reduce_length = 0.06, -- m: length below which the gear reaction force starts to reduce
            amortizer_static_force = 7.0e4, -- N: strut preload, 70 kN (earlier value 5815)
            amortizer_spring_force_factor = 1.00e6, -- Spring factor (earlier values 4050770 and 6200000)
            amortizer_spring_force_factor_rate = 4, -- Spring exponent
            amortizer_direct_damper_force_factor = 60000, -- Damping while the strut compresses
            amortizer_back_damper_force_factor = 60000, -- Damping while the strut extends; usually below the direct factor
            allowable_hard_contact_length = 0.01, -- m: excess strut travel allowed under heavy loads; tunes strut damage strength

            -- Wheel
            wheel_radius = 0.2794, -- m: 22 in diameter
            wheel_moment_of_inertia = 1.00, -- kg m2: about the wheel's rotation axis
            wheel_static_friction_factor = 0.75, -- Friction at rest along the aircraft's length, as a multiple of ground reaction force
            wheel_side_friction_factor = 0.5, -- As static friction, across the aircraft
            wheel_roll_friction_factor = 0.04, -- As static friction, for the rolling wheel
            wheel_glide_friction_factor = 0.3, -- As static friction, when gliding (wet runway, locked brakes)
            anti_skid_installed = false, -- No antiskid on this wheel
            wheel_damage_speedX = 130, -- m/s: speed from which overspeed can damage the wheel

            -- Model draw arguments
            arg_post = 0, -- Gear post extension
            arg_amortizer = 1, -- Strut compression
            arg_wheel_rotation = 101, -- Wheel rotation
            arg_wheel_yaw = 2, -- Wheel yaw
        },
        { -- Left main gear
            -- Identity and position
            damage_element = 84, -- Damage cell for this wheel; matches WHEEL_L in the aircraft Damage table
            collision_shell_name = "WHEEL_L", -- Model collision shell for this wheel
            mass = 220, -- kg by its name: gear mass. Stock files don't document it
            pos = {-0.287757, -2.0250, -2.100359}, -- Wheel position (earlier test value {-0.292856, -2.055, -2.095716})
            -- EDM tyre contact point: -2.089264 strut extended, -2.016436 strut compressed, delta 0.072828 m.
            -- EDM wheel position when aligned with the user/bounding box: -2.029545.

            -- Steering: fixed wheel
            self_attitude = false, -- Not self-orienting
            wheel_axle_offset = 0.0, -- m: horizontal offset of the wheel centre from the strut axis
            --yaw_limit = 0,
            --moment_limit = 750.0,
            --damper_coeff = 40.0,

            -- Strut
            amortizer_max_length = 0.229362, -- m: maximum (unloaded) strut length
            amortizer_basic_length = 0.229362, -- m: normally the same as the maximum length
            amortizer_reduce_length = 0.08, -- m: length below which the gear reaction force starts to reduce
            amortizer_static_force = 653.35, -- N: strut preload (earlier value 0.185e6)
            amortizer_spring_force_factor = 4.900125e7, -- Spring factor (earlier value 2.00e6)
            amortizer_spring_force_factor_rate = 2.5, -- Spring exponent
            amortizer_direct_damper_force_factor = 60000, -- Damping while the strut compresses
            amortizer_back_damper_force_factor = 40000, -- Damping while the strut extends; usually below the direct factor
            allowable_hard_contact_length = 0.02, -- m: excess strut travel allowed under heavy loads; tunes strut damage strength

            -- Wheel
            wheel_radius = 0.4064, -- m: 32 in diameter
            wheel_moment_of_inertia = 1.0, -- kg m2: about the wheel's rotation axis
            wheel_static_friction_factor = 0.80, -- Friction at rest along the aircraft's length, as a multiple of ground reaction force
            wheel_side_friction_factor = 0.45, -- As static friction, across the aircraft
            wheel_roll_friction_factor = 0.04, -- As static friction, for the rolling wheel. Same as the stock F-15E and F-16C main wheels
            wheel_glide_friction_factor = 0.5, -- As static friction, when gliding (wet runway, locked brakes)
            wheel_brake_moment_max = 20000.0, -- Maximum wheel braking moment
            anti_skid_installed = true, -- Enables integrated wheel antiskid physics
            anti_skid_improved = true, -- Undocumented; stock F-16C and FA-18C set it with antiskid
            anti_skid_gain = 400, -- Undocumented antiskid gain; stock uses 200 to 1000
            wheel_damage_speedX = 130, -- m/s: speed from which overspeed can damage the wheel

            -- Model draw arguments
            arg_post = 5, -- Gear post extension
            arg_amortizer = 6, -- Strut compression
            arg_wheel_rotation = 102, -- Wheel rotation
        },
        { -- Right main gear
            -- Identity and position
            damage_element = 85, -- Damage cell for this wheel; matches WHEEL_R in the aircraft Damage table
            collision_shell_name = "WHEEL_R", -- Model collision shell for this wheel
            mass = 220, -- kg by its name: gear mass. Stock files don't document it
            pos = {-0.287757, -2.0250, 2.100359}, -- Wheel position (earlier test value {-0.292856, -2.055, 2.095716})
            -- EDM tyre contact point: -2.089264 strut extended, -2.025144 strut compressed, delta 0.06412 m.
            -- EDM wheel position when aligned with the user/bounding box: -2.035596.

            -- Steering: fixed wheel
            self_attitude = false, -- Not self-orienting
            wheel_axle_offset = 0.0, -- m: horizontal offset of the wheel centre from the strut axis
            --yaw_limit = 0,
            --moment_limit = 750.0,
            --damper_coeff = 40.0,

            -- Strut
            amortizer_max_length = 0.229362, -- m: maximum (unloaded) strut length
            amortizer_basic_length = 0.229362, -- m: normally the same as the maximum length
            amortizer_reduce_length = 0.08, -- m: length below which the gear reaction force starts to reduce
            amortizer_static_force = 653.35, -- N: strut preload (earlier value 0.185e6)
            amortizer_spring_force_factor = 4.900125e7, -- Spring factor (earlier value 2.00e6)
            amortizer_spring_force_factor_rate = 2.5, -- Spring exponent
            amortizer_direct_damper_force_factor = 60000, -- Damping while the strut compresses
            amortizer_back_damper_force_factor = 40000, -- Damping while the strut extends; usually below the direct factor
            allowable_hard_contact_length = 0.02, -- m: excess strut travel allowed under heavy loads; tunes strut damage strength

            -- Wheel
            wheel_radius = 0.4064, -- m: 32 in diameter
            wheel_moment_of_inertia = 1.0, -- kg m2: about the wheel's rotation axis
            wheel_static_friction_factor = 0.80, -- Friction at rest along the aircraft's length, as a multiple of ground reaction force
            wheel_side_friction_factor = 0.45, -- As static friction, across the aircraft
            wheel_roll_friction_factor = 0.04, -- As static friction, for the rolling wheel. Same as the stock F-15E and F-16C main wheels
            wheel_glide_friction_factor = 0.5, -- As static friction, when gliding (wet runway, locked brakes)
            wheel_brake_moment_max = 20000.0, -- Maximum wheel braking moment
            anti_skid_installed = true, -- Enables integrated wheel antiskid physics
            anti_skid_improved = true, -- Undocumented; stock F-16C and FA-18C set it with antiskid
            anti_skid_gain = 400, -- Undocumented antiskid gain; stock uses 200 to 1000
            wheel_damage_speedX = 130, -- m/s: speed from which overspeed can damage the wheel

            -- Model draw arguments
            arg_post = 3, -- Gear post extension
            arg_amortizer = 4, -- Strut compression
            arg_wheel_rotation = 103, -- Wheel rotation
        },
    },
}