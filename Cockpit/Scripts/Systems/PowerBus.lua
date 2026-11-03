-- Display power bus. The battery gates everything; with it on, the APU, an
-- engine-driven generator or external ground power brings the bus up. Display
-- power only: no FCS BIT, APU caution lights or EPU are modelled.
local M={}
M.APU_SPOOL=8        -- seconds from APU start to rated output (approximation)
M.GEN_ONLINE_N2=56   -- percent core rpm, TO 1F-117A-1 page 2-7; ground idle is 60 %
M.APU_OFF,M.APU_STARTING,M.APU_RUNNING=0,1,2

function M.new()
    local s={battery=false,apu=M.APU_OFF,apu_time=0,gen_online=false,ground_power=false}
    function s.set_battery(on)
        s.battery=on and true or false
        if not s.battery then s.apu=M.APU_OFF;s.apu_time=0 end
    end
    function s.toggle_battery() s.set_battery(not s.battery) end
    function s.toggle_apu()
        if s.apu~=M.APU_OFF then s.apu=M.APU_OFF;s.apu_time=0
        elseif s.battery then s.apu=M.APU_STARTING;s.apu_time=0 end
    end
    -- rpm_left/right in percent N2.
    function s.update(dt,rpm_left,rpm_right)
        if s.apu==M.APU_STARTING then
            s.apu_time=s.apu_time+dt
            if s.apu_time>=M.APU_SPOOL then s.apu=M.APU_RUNNING end
        end
        local l,r=tonumber(rpm_left) or 0,tonumber(rpm_right) or 0
        s.gen_online=math.max(l,r)>=M.GEN_ONLINE_N2
        return s.powered()
    end
    function s.powered()
        return s.battery and (s.apu==M.APU_RUNNING or s.gen_online or s.ground_power)
    end
    return s
end
return M
