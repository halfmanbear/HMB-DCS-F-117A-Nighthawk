  dofile(LockOn_Options.script_path .. "devices.lua")

  local dev = GetSelf()
  local weapons = nil
  local DT = 0.02
  local gate = get_param_handle("F117_WEAPON_RELEASE_GATE")
  local trig_on = false
  local direct_launch_available = false

  local FIRE_ON  = 350  -- iCommandPlanePickleOn  → avSimpleWeaponSystem::start_unloading_with_first_shot_delay
  local FIRE_OFF = 351  -- iCommandPlanePickleOff → avSimpleWeaponSystem::stop_unloading

  make_default_activity(DT)

  function post_initialize()
      weapons = GetDevice(devices.WEAPONS)
      direct_launch_available = weapons ~= nil and type(weapons.launch_station) == "function"
  end

  function update()
      local want_trigger = gate:get() > 0.5
      if want_trigger and not trig_on then
          if direct_launch_available then
              -- IDA: avSimpleWeaponSystem exposes launch_station(station), with no
              -- argument using the native selected/default station path.
              local ok, err = pcall(function() weapons:launch_station() end)
              if not ok then
                  log.write("F117_WEAPONS", log.ERROR, "launch_station() failed, falling back to pickle command: " .. tostring(err))
                  direct_launch_available = false
                  dispatch_action(nil, FIRE_ON)
              end
          else
              dispatch_action(nil, FIRE_ON)
          end
          trig_on = true
      elseif trig_on == true and not want_trigger then
          if not direct_launch_available then
              dispatch_action(nil, FIRE_OFF)
          end
          trig_on = false
      end
  end

  need_to_be_closed = false
