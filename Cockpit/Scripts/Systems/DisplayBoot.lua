-- Staggered display power-up after the bus comes on.
-- state: 0 off, 1 warm-up/backlight, 2 BIT screen, 3 operational.
-- stage (state 2): 1 POWER ON, 2 SELF TEST, 3 AUTO CAL, 4 PASS.
-- The sequence is illustrative; real F-117 boot screens are not documented.
local M={}
M.OFF,M.WARMUP,M.BIT,M.OPERATIONAL=0,1,2,3
M.PASS_TIME=.6
-- Seconds after bus power. bit=nil skips the BIT screen (the HUD only fades in).
-- fade_from: "on" ramps with the backlight, "ready" ramps after operational.
M.TIMELINE={
    DEP   ={on=.3, bit=.8, ready=3.0, fade=.8, fade_from="on"},
    HUD   ={on=1.5,bit=nil,ready=3.5, fade=2.5,fade_from="ready"},
    CMDI_L={on=1.0,bit=1.8,ready=7.0, fade=1.0,fade_from="on"},
    SD    ={on=2.2,bit=3.0,ready=8.5, fade=1.0,fade_from="on"},
    CMDI_R={on=3.4,bit=4.2,ready=10.0,fade=1.0,fade_from="on"},
}
M.DISPLAYS={"DEP","HUD","CMDI_L","SD","CMDI_R"}

local function clamp01(x) return x<0 and 0 or x>1 and 1 or x end

-- t: seconds since bus power, or nil when unpowered.
function M.evaluate(name,t)
    local d=M.TIMELINE[name]
    if not t or t<d.on then return {state=M.OFF,stage=0,progress=0,fade=0} end
    local start=d.fade_from=="ready" and d.ready or d.on
    local fade=clamp01((t-start)/d.fade)
    if t>=d.ready then return {state=M.OPERATIONAL,stage=0,progress=100,fade=fade} end
    if not d.bit or t<d.bit then return {state=M.WARMUP,stage=0,progress=0,fade=fade} end
    local span=d.ready-d.bit
    local p=clamp01((t-d.bit)/span)
    local stage
    if t>=d.ready-M.PASS_TIME then stage=4
    elseif p<.2 then stage=1
    elseif p<.65 then stage=2
    else stage=3 end
    local test=clamp01((t-d.bit)/math.max(span-M.PASS_TIME,.01))
    return {state=M.BIT,stage=stage,progress=math.floor(test*100),fade=fade}
end

-- Fully operational, for hot and air starts.
function M.operational() return {state=M.OPERATIONAL,stage=0,progress=100,fade=1} end
return M
