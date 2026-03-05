FM = {
    center_of_mass = {0.0, 0.1, 0.0}, --{0.35, -0.10, 0.0} --(+forward/-back,+up/-down,+right/-left)
    moment_of_inertia = {3.0e5, 6.8e5, 9.0e5, 0.0},
    disable_built_in_oxygen_system = true,
    new_FCS = true,
    suspension = {
        {
            mass = 120,
            pos = {5.0765, -2.150, 0}, --(+forward/-back,+up/-down,+right/-left)
            damage_element = 83,
            self_attitude = true,
            wheel_axle_offset = 0.07,
            yaw_limit = 0.262, --0.785
            moment_limit = 750.0,
            damper_coeff = 120.0,
            amortizer_min_length = 0.00,
            amortizer_max_length = 0.53,
            amortizer_basic_length = 0.53,
            amortizer_reduce_length = 0.40,
            --amortizer_static_force = 4.0e4,           -- ~40,000 N
            --amortizer_spring_force_factor = 5.0e5,    -- ~500,000 N/m
            amortizer_spring_force_factor = 1.20e6,
            amortizer_spring_force_factor_rate = 2.0,
            amortizer_static_force = 0.30e6,
            amortizer_direct_damper_force_factor = 4.0e4,
            amortizer_back_damper_force_factor = 2.0e4,
            allowable_hard_contact_length = 0.020,
            anti_skid_installed = false,
            wheel_damage_speed = 130,
            wheel_radius = 0.2794, -- 22inch = 0.5588m diameter = 0.2794m radius
            wheel_static_friction_factor = 0.55,
            wheel_side_friction_factor = 0.68,
            wheel_roll_friction_factor = 0.04,
            wheel_glide_friction_factor = 0.5,
            wheel_damage_force_factor = 450.0,
            wheel_moment_of_inertia = 1.00,
            arg_post = 0,
            arg_amortizer = 1,
            arg_wheel_rotation = 101,
            arg_wheel_yaw = 2,
            collision_shell_name = "WHEEL_F"
        },
        {
            mass = 220,
            pos = {-0.292856, -2.055, -2.095716}, -- {-0.292856, -2.055, -2.095716} --(+forward/-back,+up/-down,+right/-left)
            damage_element = 84,
            wheel_axle_offset = 0.38,
            self_attitude = false,
            yaw_limit = 0,
            moment_limit = 750.0,
            damper_coeff = 40.0,
            amortizer_max_length = 0.4,
            amortizer_basic_length = 0.4,
            amortizer_reduce_length = 0.35,
            amortizer_spring_force_factor = 2.00e6, -- ~2,000,000 N/m
            --amortizer_spring_force_factor = 1.20e6,
            amortizer_spring_force_factor_rate = 2.5,
            amortizer_static_force = 0.185e6,
            amortizer_direct_damper_force_factor = 8.0e4,
            amortizer_back_damper_force_factor = 4.0e4,
            allowable_hard_contact_length = 0.025,
            anti_skid_improved = true,
            anti_skid_installed = true,
            wheel_damage_speed = 130,
            wheel_moment_of_inertia = 1.0,
            wheel_radius = 0.4064, -- 32inch = 0.8128m diameter = 0.4064m radius
            wheel_static_friction_factor = 0.75,
            wheel_side_friction_factor = 0.70,
            wheel_roll_friction_factor = 0.035,
            wheel_glide_friction_factor = 0.5,
            wheel_damage_force_factor = 650.0,
            wheel_brake_moment_max = 20000.0,
            arg_post = 5,
            arg_amortizer = 6,
            arg_wheel_rotation = 102,
            collision_shell_name = "WHEEL_L"
        },
        {
            mass = 220,
            pos = {-0.292856, -2.055, 2.095716}, --{-0.292856, -2.055, 2.095716}, --(+forward/-back,+up/-down,+right/-left)
            damage_element = 85,
            wheel_axle_offset = 0.38,
            self_attitude = false,
            yaw_limit = 0,
            moment_limit = 750.0,
            damper_coeff = 40.0,
            amortizer_max_length = 0.4,
            amortizer_basic_length = 0.4,
            amortizer_reduce_length = 0.35,
            amortizer_spring_force_factor = 2.00e6, -- ~2,000,000 N/m
            --amortizer_spring_force_factor = 1.20e6,
            amortizer_spring_force_factor_rate = 2.5,
            amortizer_static_force = 0.185e6,
            amortizer_direct_damper_force_factor = 8.0e4,
            amortizer_back_damper_force_factor = 4.0e4,
            allowable_hard_contact_length = 0.025,
            anti_skid_improved = true,
            anti_skid_installed = true,
            wheel_damage_speed = 103,
            wheel_moment_of_inertia = 1.0,
            wheel_radius = 0.4064, -- 32inch = 0.8128m diameter = 0.4064m radius
            wheel_static_friction_factor = 0.75,
            wheel_side_friction_factor = 0.70,
            wheel_roll_friction_factor = 0.035,
            wheel_glide_friction_factor = 0.5,
            wheel_damage_force_factor = 650.0,
            wheel_brake_moment_max = 20000.0,
            arg_post = 3,
            arg_amortizer = 4,
            arg_wheel_rotation = 130,
            collision_shell_name = "WHEEL_R"
        },
    },
    -- Shake Amp
    minor_shake_ampl = 0.10,
    major_shake_ampl = 0.25,
    -- DEBUG
    debugLine = "{M}:%1.3f {IAS}:%4.1f {AoA}:%2.1f {ny}:%2.1f {nx}:%1.2f {AoS}:%2.1f {mass}:%2.1f {Fy}:%2.1f {Fx}:%2.1f {wx}:%.1f {wy}:%.1f {wz}:%.1f {Vy}:%2.1f {dPsi}:%2.1f",
    record_enabled = false
}