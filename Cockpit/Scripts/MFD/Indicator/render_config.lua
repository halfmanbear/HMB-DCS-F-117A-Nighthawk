-- Named textures are produced by F117Displays.dll/ccIndicatorBake.
-- Camera target 0 remains reserved for the EFM/IRADS camera bridge.
return {
    enabled=false,
    -- Opt-in centre holder test: static colour/UV card, no native baking.
    -- Keep enabled=false; see docs/compositor-diagnostics.md.
    holder_test=false,
    -- Centre-only native bake; ignores holder_test when active.
    bake_test=true,
    -- "pattern", "map", or "text" (fixed font text versus line glyphs).
    bake_test_source="map",
    -- Show the selected diagnostic source directly, with the holder hidden.
    bake_test_direct=false,
    -- Controlled map-bake experiment: route strokes outside the specular pass.
    bake_test_specular=false,
    -- resolution=nil uses DCS's exposed option, falling back to 1024 pixels.
    resolution=1024,
    left={texture="F117_LCD_LEFT",half_width=.0521,half_height=.0498},
    right={texture="F117_LCD_RIGHT",half_width=.0528,half_height=.0498},
    centre={texture="F117_LCD_CENTRE",half_width=.0881,half_height=.0748},
}
