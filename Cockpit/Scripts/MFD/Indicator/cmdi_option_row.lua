-- Bottom option row shared by the CMDI VSD, HSD and MAP formats, so its legends
-- and selection box have one size and stroke weight on every page.
-- Sizes are metres on the CMDI glass. `scale` is the factor CMDI_formats.lua
-- draws the page at (the MAP page is drawn at about .58); dividing by it keeps
-- the final size the same on every page.
local M={
    height=.0028,            -- glyph height: the VSD small text size
    weight=1.8,              -- text and box stroke weight; the MAP needs it to read over the chart
    box_w=.0080,box_h=.0036, -- selection box around a three-letter legend
}
function M.stringdefs(scale)
    local h=M.height/(scale or 1)
    return {h,h*.55,h*.10,0}
end
-- Closed selection box outline centred on x,y.
function M.outline(x,y,scale)
    local w,h=M.box_w/2/(scale or 1),M.box_h/2/(scale or 1)
    return {{x-w,y-h},{x+w,y-h},{x+w,y+h},{x-w,y+h},{x-w,y-h}}
end
return M
