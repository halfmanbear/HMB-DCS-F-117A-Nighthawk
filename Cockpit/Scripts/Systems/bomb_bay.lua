  local dev = GetSelf()
  local DT = 0.02
  local gate = get_param_handle("F117_WEAPON_RELEASE_GATE")
  local trig_on = false

  local FIRE_ON = 84
  local FIRE_OFF = 85

  make_default_activity(DT)

  function update()
      local want_trigger = gate:get() > 0.5
      if want_trigger and not trig_on then
          dispatch_action(nil, FIRE_ON)
          trig_on = true
      elseif trig_on == true and not want_trigger then
          dispatch_action(nil, FIRE_OFF)
          trig_on = false
      end
  end

  need_to_be_closed = false