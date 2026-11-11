dofile(LockOn_Options.common_script_path.."devices_defs.lua")
dofile(LockOn_Options.common_script_path.."elements_defs.lua")

local readability = dofile(LockOn_Options.script_path.."display_readability.lua")

-- Green centre sensor display; the left CMDI repeater is grayscale.
local sensor_colour=F117_IRADS_OVERLAY_OPTIONS and {230,230,230,255} or {0,255,0,255}
MFD_COLOUR = sensor_colour
MFD_WHITE = MakeMaterial(nil, sensor_colour)

-- Font for symbology text
MFD_FONT  = MakeFont(
    readability.font,
    sensor_colour
)

MFD_READABILITY = readability
MFD_LEVEL  = 0   -- 0 = default stencil; COMPARE at level 0 renders everywhere in the indicator viewport
MFD_SD     = {0.010, 0.010, 0, 0}
MFD_SD_SM  = {0.006, 0.006, 0, 0}
MFD_SD_XS  = {0.004, 0.004, 0, 0}

-- The overlay is a separate physical indicator. Do not inherit the sensor's
-- FOV scale or resample its render target into this page.
SetScale(METERS)
local finish
if not F117_IRADS_OVERLAY_OPTIONS then
    finish=dofile(LockOn_Options.script_path.."Indicator/native_brightness_page.lua")("F117_IRADS_SOURCE")
    F117_IRADS_REGISTERED=true
    for band=0,65 do
        local video=CreateElement "ceTexPoly"
        video.name="F117_CENTRE_BAKED_VIDEO_"..band
        video.vertices={{-.0881,.0748},{.0881,.0748},{.0881,-.0748},{-.0881,-.0748}}
        video.indices={0,1,2,0,2,3};video.tex_coords={{0,0},{1,0},{1,1},{0,1}}
        video.material=MakeMaterial("mfd0",readability.irads_video_colour)
        video.input_space_SRGB=true;video.additive_alpha=true
        video.element_params={"F117_ON_SD","F117_IRADS_POWER","F117_LCD_READY","F117_IRADS_DRAW_BRIGHTNESS","F117_IRADS_CONTRAST_BAND"}
        video.controllers={{"parameter_in_range",0,.9,1.1},{"parameter_in_range",1,.9,1.1},
            {"parameter_in_range",2,.9,1.1},{"opacity_using_parameter",3},
            {"parameter_in_range",4,band-.1,band+.1},{"set_contrast_raw",(.35+band*.01)/.80}}
        Add(video)
    end
end
dofile(LockOn_Options.script_path.."MFD/Indicator/MFD_indication_page.lua")
if not F117_IRADS_OVERLAY_OPTIONS then
    dofile(LockOn_Options.script_path.."Indicator/boot_page.lua"){
        display="SD",title="SD",name="F117_SD_BOOT",font=MFD_FONT,line_material=MFD_WHITE,
        half_w=.0881,half_h=.0748,sd={.0011,.0011,0,0},text_scale=readability.mfd_text_scale}
end
if finish then F117_IRADS_REGISTERED=nil;finish() end
