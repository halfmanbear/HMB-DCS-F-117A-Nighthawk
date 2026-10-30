-- Native stroke presentation. Values are shader controls, not quad widths.
return {
    font=dofile(LockOn_Options.script_path.."display_font.lua"),
    hud_text_scale=2.2, -- 3.2 mrad readout becomes 7.04 mrad, like native HUD sizes.
    mfd_text_scale=4.0, -- physical glyph sizes: small 2.8 mm, values 4.6 mm.
    thickness=0.8,
    fuzziness=0.5,
}
