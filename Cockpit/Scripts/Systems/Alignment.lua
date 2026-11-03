-- Attitude/heading alignment and air-data settling after bus power-up.
-- Gyros erect and the INS heading aligns as a damped seek with slight overshoot:
-- err = E0 * exp(-t/tau) * cos(2*pi*t/period). Errors are exactly 0 after 5 tau.
-- The air data blend winds altitude and vertical speed up from zero.
local M={}
local RAD=math.pi/180
M.AXES={
    pitch={min=3*RAD, max=6*RAD,  tau=6, period=10},
    roll ={min=6*RAD, max=12*RAD, tau=6, period=10},
    hdg  ={min=20*RAD,max=60*RAD, tau=10,period=20},
}
M.ADC_TAU=1.2
M.SETTLED=5 -- time constants

-- random(lo,hi) returns a magnitude; sign(axis) returns -1 or 1. Both injectable.
function M.new(random,sign)
    random=random or function(lo,hi) return lo+(hi-lo)*math.random() end
    sign=sign or function() return math.random()<.5 and -1 or 1 end
    local s={initial={pitch=0,roll=0,hdg=0}}
    function s.seed()
        for axis,a in pairs(M.AXES) do s.initial[axis]=sign(axis)*random(a.min,a.max) end
    end
    local function error(axis,t)
        local a=M.AXES[axis]
        if t>=M.SETTLED*a.tau then return 0 end
        return s.initial[axis]*math.exp(-t/a.tau)*math.cos(2*math.pi*t/a.period)
    end
    -- t: seconds since bus power, or nil when aligned (hot/air start).
    function s.evaluate(t)
        if not t then return {pitch=0,roll=0,hdg=0,adc=1} end
        local adc=t>=M.SETTLED*M.ADC_TAU and 1 or 1-math.exp(-t/M.ADC_TAU)
        return {pitch=error("pitch",t),roll=error("roll",t),hdg=error("hdg",t),adc=adc}
    end
    return s
end
return M
