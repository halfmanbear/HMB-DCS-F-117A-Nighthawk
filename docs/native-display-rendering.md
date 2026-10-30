# Native display rendering investigation

Read-only examination on 2026-10-29 of the user's live IDA GUI databases for F16C.dll and CockpitBase.dll, and the supplied installed F-16 cockpit Scripts/IndicationResources directories. No binary or IDA database changes. Raw selected results are retained in `native-display-evidence.json`.

## Identity and coverage

- F16C.dll SHA-256: e5e706fc18f3c279b4a14d681bc3a0021d944462cd9123e553688e4c09d5aec1.
- CockpitBase.dll SHA-256: fb0a09be70627c7790dea1527cedfee43082bb8b112484d5c85be1d99d33de95.
- Both database hashes match Get-FileHash on the installed binaries.
- F16C's database exposes only 53 recognized functions and has UPX-named sections. Imports and packaged Lua are useful evidence, but the internal F-16 LCD implementation was not recovered. No unpacking attempted.
- Static analysis does not show the actual render pass chosen in the user's running mission.

## Findings

| Question | Observation and source | Meaning |
|---|---|---|
| Does missing NOTYPE explain the difference? | CockpitBase `ccIndicator::initialize`, 0x180373720: failure to read indicator_type explicitly sets the type byte to zero. Installed devices_defs.lua defines COMMON=0. | No. Our nil NOTYPE already fell back to COMMON. Using COMMON explicitly is cleanup, not an established rendering fix. |
| Does the F-16 draw everything through its EFM? | F16C imports ccIndicator draw/update/purpose functions, ccIndicatorBake init/addSource/posteffect functions and ceStringPoly formatting from CockpitBase. Its device_init.lua also registers F16-specific cockpit classes. | The DLL has cockpit/avionics code as well as EFM code. The actual drawing uses shared cockpit infrastructure with Lua layouts/resources. An EFM layout port is not needed to obtain sharper output. |
| What distinguishes the fonts? | Installed F-16 Scripts/fonts.lua defines class ceSLineFont with symb_storage stroke_font/MFD_stroke_font, default dimensions and thickness/fuzziness. Corresponding SVG files are present in IndicationResources/Displays. | F-16 HUD/MFD core text is stroke-based, rather than the UI bitmap font originally used in this mod. Increasing bitmap raster dimensions alone does not reproduce stroke rendering. |
| What distinguishes the lines? | Scripts/symbology_defs.lua addStrokeLine builds ceSMultiLine elements with thickness/fuzziness; HUD_init.lua and MFD_left_init.lua enable shaderLineParamsUpdatable, default thickness 0.8 and fuzziness 0.5. Specular-pass use is false for HUD and true for MFD. | Our ceMeshPoly line widths are geometry widths; they do not automatically gain these stroke shader controls. Adding shaderLine settings alone cannot convert them into stroke primitives. |
| Does F-16 use an MFD texture stage? | config.lua USE_LCD_MFD=true. MFD_left_init.lua selects render_purpose.BAKE. device_init.lua registers F16::ccMFD_LCD_F16 holders. LCD/page.lua displays MFD_LCD_F16_LEFT/RIGHT materials on a quad. | Yes, its LCD path is not identical to our directly drawn side indicators. The native baking class is separate from the EFM entry points. |
| Where are render targets registered? | CockpitBase ccIndicator::set_render_materials, 0x180376980, reads render_target and used_render_mask, creates an MFD material and calls assign_as_render_target_source. | A Lua page can configure shared target infrastructure, but assigning an arbitrary target ID alone does not reproduce F-16's LCD baking/compositing path. |
| Is 1024 a universal HUD/MFD coordinate system? | ccLuaLoader::bind_options, 0x1803d6b80, exports render_target_resolution from globalOptions. Text size, target assignment and display geometry are configured separately. | No. Target pixel dimensions, font glyph raster dimensions, physical/angular layout units and final output resolution are separate. This investigation does not establish the current target size of either aircraft. |
| What posteffects route exists? | ccIndicator::get_render_purpose, 0x1803721a0, returns 8/9 when byte_18054B308 is set. Callback 0x18040b830 brackets cockpit drawing with this byte. devices_defs.lua calls 8/9 GENERAL_AFTER_POSTEFFECTS/HUD_ONLY_VIEW_AFTER_POSTEFFECTS. | A distinct after-posteffects pass exists. This does not prove that DLSS routes through this pass or that adding it to every indicator is correct. |
| Does the autoexec switch need copying into page Lua? | Config/autoexec.cfg already contains HUD_MFD_after_DLSS=true and DLSS_Preset='K'. Bounded string searches in these two loaded databases found no DLSS setting name. | No evidence supports a per-page copy of this engine option. Backend handling and actual runtime eligibility remain unresolved; the renderer module was outside these two targets. |

## Current mod corrections and next comparison

The broken ceUITTF experiment has been replaced with an explicit ceTexPolyFont-compatible DDS atlas, using the existing cockpit texture/size/resolution/default/chars contract. MFD registrations now explicitly use COMMON, and the checker no longer invents NOTYPE. Font alpha/cell boundaries, Lua checks and 17 tests pass, but DCS validation is still pending.

The next architectural improvement suggested by the F-16 comparison is to implement the mod's own stroke glyphs and line primitives through the shared cockpit renderer, retaining Lua page positions/controllers and the calibrated masks. A dedicated MFD target/holder stage can then be evaluated separately. Do not relocate layouts into the EFM or force all pages into an after-posteffects pass as a substitute for this work.

F-16 source paths inspected: E:/Eagle Dynamics/DCS World/Mods/aircraft/F-16C/Cockpit/Scripts/{fonts.lua,materials.lua,symbology_defs.lua,config.lua,device_init.lua,Displays/HUD/indicator/HUD_init.lua,Displays/MFD/indicator/MFD_left_init.lua,Displays/MFD/indicator/LCD/MFD_LCD.lua,Displays/MFD/indicator/LCD/page.lua}. Resources inspected by inventory/format: IndicationResources/Displays/{stroke_font.svg,MFD_stroke_font.svg,stroke_symbols_HUD.svg,stroke_symbols_MFD.svg}. No F-16 artwork copied into this mod.

## Implementation update (2026-10-30)

The subsequent port replaces operational bitmap fonts with mod-owned ceSLineFont SVG glyphs and procedural ribbon quads with ceSMultiLine primitives. VSD/HSD/IRADS composition now render to unique native targets and use separate depth-tested holders. HUD optics remain unchanged. See display-readability.md for current configuration, routing and validation limits; the earlier bitmap experiment described above is retired.


## Runtime correction (2026-10-30)

The generic render_target + BAKE-only source/holder attempt produced black MFDs in the user's runtime screenshot. Native ccIndicatorBake::init (0x180379750) initializes a separate offscreen channel and requires preconfigured sources; this was missing from the Lua-only port. The experimental holders are now unregistered, source targets 1–3 removed, and GENERAL/HUD_ONLY_VIEW drawing restored for all MFDs. The IRADS camera retains its original target 0 and separate direct overlay. Stroke resources and HUD optics are unchanged. The earlier implementation update describes the failed experiment, not the current operational route. Actual F-16-style LCD baking remains unimplemented.


## Native adapter implementation (2026-10-30)

A separate F117Displays.dll Lua extension now constructs and owns three actual ccIndicatorBake objects, calls addSource and init, and only then switches source draw purposes/enables holders. This supersedes the direct-only correction above. It uses the shared native baking machinery with original mod artwork and no F16C dependency. Native addSource's second and third integers are pixel width/height: the source-record construction writes x/y separately and init computes extents from x+width/y+height. Some old IDA database analyst comments label these arguments offsets; that label is inconsistent with the actual code. Source indices are zero-based (0x18037A170 indexes context+0xB0 directly). The deleting destructor at 0x180378F70 uses an object stride of 0x1D0. No binary or IDA database was modified.

The DLL is pinned to the analyzed CockpitBase SHA-256, resolves exported methods by name, and uses Lua userdata for cleanup. Host tests pass with DCS Lua 5.1 and instrumented native API calls, including actual DLL loading. This does not establish DCS render output, MT teardown safety or DLSS routing; a mission test remains required. See native/displays/README.md.
