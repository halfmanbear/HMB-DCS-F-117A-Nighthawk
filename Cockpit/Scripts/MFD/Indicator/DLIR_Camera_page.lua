dofile(LockOn_Options.common_script_path.."elements_defs.lua")

-- Scale coordinate space to match the camera FOV so geometry fills the indicator.
SetScale(FOV)

-- Full-screen quad that samples the COMMON indicator's camera render target.
-- Material name is "render_target_1" because set_render_materials() creates it via
-- sprintf("render_target_%d", render_target + 1) with render_target=0 → "render_target_1".
picture                 = CreateElement "ceTexPoly"
picture.name            = "dlir_picture"
picture.vertices        = {{-1,  1},
                            { 1,  1},
                            { 1, -1},
                            {-1, -1}}
picture.indices         = {0, 1, 2,  0, 2, 3}
picture.tex_coords      = {{0, 0},
                            {1, 0},
                            {1, 1},
                            {0, 1}}
picture.material        = "render_target_1"
picture.use_mipfilter   = false
picture.element_params = {"F117_IRADS_POWER","mainpower"}
picture.controllers = {{"parameter_in_range", 0, 0.9, 1.1},{"parameter_in_range",1,.9,1.1}}
if F117_COMPOSITE_PAGE then
    picture.element_params[3]="F117_LCD_READY"
    picture.controllers[3]={"parameter_in_range",2,.9,1.1}
end
Add(picture)
