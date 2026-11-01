-- Minimal cockpit livery to satisfy DCS and map mirrors
livery = {
    {"Glass", DIFFUSE , "F-117_glass_clear", false};
    {"Material.001", DIFFUSE , "F-117_glass_clear", false};
    -- Warm instrument illumination: #E0C5C3 (replaces the white gauge material).
    -- EDM material labels verified against Cockpit_F-117.blend; keep emissive strength.
    {"Material.002", DIFFUSE, "F117_gauge_backlight_warm", false};
    {"Material.003", DIFFUSE, "F117_gauge_backlight_warm", false};
    {"Material.004", DIFFUSE, "F117_gauge_backlight_warm", false};
    {"Material.005", DIFFUSE, "F117_gauge_backlight_warm", false};
    {"Material.006", DIFFUSE, "F117_gauge_backlight_warm", false};
    {"Material.007", DIFFUSE, "F117_gauge_backlight_warm", false};
    {"Material.008", DIFFUSE, "F117_gauge_backlight_warm", false};
    {"mirrors", 0};
}
name = "Default"