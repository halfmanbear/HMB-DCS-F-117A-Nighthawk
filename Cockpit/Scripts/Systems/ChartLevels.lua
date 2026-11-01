-- Select common DCS chart levels by theatre, matching common kneeboard defaults.
local M={}
function M.level(theatre,range)
    if range<20 then return 2 end
    if theatre=="Caucasus" then return range<=40 and 3 or 6 end
    if range<=40 then return 4 end
    return range<=80 and 5 or 6
end
return M
