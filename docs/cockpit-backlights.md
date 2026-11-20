# Cockpit backlight power and colour

Normal panel/instrument backlights start dark for a cold spawn, with the lighting
switch selected on so they illuminate automatically when power becomes available.
The existing Cockpit Illumination binding toggles that selection. Battery alone leaves
the normal AC lighting off; the electrical system supplies it after the first
engine generator comes online at 56% core RPM, or with connected ground power.
The APU supplies start air and does not bring the main electrical bus online.
Hot/air starts retain the selected-on panel lights. Losing power extinguishes the
backlights without changing the selected switch position.

Instrument emission is 65% of its previous brightness. Separate emission-only DDS
maps use RGB multipliers (1.00, 0.94, 0.84) for a slight warm-white tint. Albedo,
display colour, and flood-light controls retain their original values. The two
emissive screen materials follow the existing mainpower bus independently of the
panel switch. Indicator boot sequences remain controlled by Electrical.lua.

Cockpit draw argument 196 reads PANEL_LGT; 197 reads mainpower. The material patch
script in Cockpit/ModelSupport operates on the installed EDM, using iEDM_10's parser
to locate material byte spans. Only the emission properties, emission texture
references, string table and type inventory change. Meshes, transforms, connectors,
lights, bounding boxes, and existing gauge animations retain their original bytes.
This avoids unrelated changes introduced by importing/re-exporting the whole model.

Build with Blender/iEDM_10:

    blender -b --python Cockpit/ModelSupport/patch_powered_emission.py -- input.edm output_directory
    python Cockpit/ModelSupport/build_warm_backlights.py texture_directory output_directory

Install the generated EDM into the companion mod's Cockpit/Shape, the generated DDS
files into its mounted cockpit texture folder, and both Lua files into Cockpit/Scripts.
Keep backups of the installed EDM and Lua files. Run the patch against the original
unpatched model; it rejects existing animated emission rather than overwriting it.
The generated model belongs to the companion mod, not the EFM DLL build.

Validation: lighting-device regression checks cold/hot/air spawns, power loss,
restoration and switch operation; model structural/pose comparison passes with
zero movement at ten sampled frames. DDS dimensions, full mip chains, alpha, and
saved pixel values are checked. Final perceived brightness/tint needs an in-DCS
night/dusk check, including battery-only, APU spool-up and hot start.

HUD, DEP and CMDI startup follows the first online main generator (or external
power), with the existing staggered boot and alignment. The centre IRADS BIT page
has its own clock: on a cold start it remains absent until command 87, the existing
IRADS Power toggle, selects IRADS on and both engines have completed starting.
An early power selection waits for that condition. Switching off resets its BIT.
The BIT timing remains an illustrative 8.5 seconds, not a documented sensor cooling
time. Hot/air starts begin operational. Once both engines have completed startup,
one remaining generator can sustain IRADS; a further engine start inhibits the
sensor and restarts its BIT afterward. Loss of main power resets qualification.
Native camera updates, designation, slew and laser eligibility are also gated by
F117_ON_IRADS, so hiding the video is not the only effect of delayed startup.
