-- Named textures are produced by F117Displays.dll/ccIndicatorBake.
-- Camera target 0 remains reserved for the EFM/IRADS camera bridge.
return {
    enabled=true,
    -- resolution=nil uses DCS's exposed option, falling back to 1024 pixels.
    left={texture="F117_LCD_LEFT",half_width=.0521,half_height=.0498},
    right={texture="F117_LCD_RIGHT",half_width=.0528,half_height=.0498},
    centre={texture="F117_LCD_CENTRE",half_width=.0881,half_height=.0748},
}
