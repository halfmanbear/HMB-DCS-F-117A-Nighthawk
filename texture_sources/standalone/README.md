# Independent texture sources

Work started 2026-11-05 for STANDALONE_PLAN.md section 3.4, textures only.

Browse [CATALOGUE.md](CATALOGUE.md) for direct links to every primary source,
review proof and layered master. Packaging regenerates this inventory and checks
that its linked source/export files exist.

## Status

The consolidated source-preparation pass is finished. The library contains
383 primary sources (including separated seat components), 22 reviewed proof
sheets and 18 layered XCF masters, plus 24 separate instrument-component SVGs.
See [UV_HANDOFF.md](UV_HANDOFF.md) for coverage by surface, known gaps and the
replacement UV/material input contract. This is a source handoff, not completion
of the aircraft texture remake. [MATERIAL_REVIEW.md](MATERIAL_REVIEW.md) records
read-only material diagnostics; none of the generated studies is qualified as
seamless or as measured albedo.

The existing Blender masters are documented as retaining the original UV layouts.
New aircraft and cockpit atlases therefore need the replacement UVs before they
can be painted and installed in accordance with section 3.4. Models, runtime
textures and liveries have not been changed by this source preparation.

## Material studies

The future-UV source set now includes eight independent PNG material studies:

| File under `materials/` | Intended painting use |
| --- | --- |
| `graphite-coating-albedo.png` | Exterior dark coating |
| `cockpit-charcoal-paint-albedo.png` | Instrument panels, consoles, painted structure |
| `bay-offwhite-paint-albedo.png` | Bay interiors, inner doors, painted gear parts |
| `rubber-black-albedo.png` | Tyres, seals and flexible boots; add tread separately |
| `olive-flight-fabric-albedo.png` | Pilot clothing and applicable seat fabric |
| `black-seat-fabric-albedo.png` | Seat upholstery |
| `satin-alloy-albedo.png` | Generic exposed alloy fittings and housings |
| `dark-oxidised-alloy-albedo.png` | Generic engine interior and hot metal detail |

All were generated without input images using built-in imagegen. Full prompts
for the seven added studies are in `generation-manifest.json`; the first prompt
is recorded below. These are separate colour inputs for painting, not a
one-to-one replacement for the old texture files. Do not paste the old artwork
over them or transfer the old atlas layout.

Colour, material assignments and grain scale are editorial starting points to
check against permitted references. The fabric studies contain visible weave
shading and need an albedo review. No physical weave size is established.
Requested output size was 2048 square; actual saved sizes and hashes are recorded
in `validation.json`. Generation requests do not guarantee output dimensions.
All eight saved PNGs are 1254 x 1254 RGB. Keep these originals as source studies;
the final UV atlases must be authored at the chosen runtime resolution before
BC7/BC5 export and mip generation. Enlarging these studies does not add detail.

For future integration, load colour PNGs as sRGB, decide physical tiling scale
on the replacement geometry, and check repeated edges in a tiled preview. Paint
unique details onto the new UVs. Keep normal and RoughMet inputs separate and
linear. Do not derive normal or height maps from these generated colour images:
their shading is not measured surface relief. Author structural detail from
geometry or explicit masks, then validate the DCS shader response.

Glass transmission, display emission, measured inlet grille geometry, turbine
blade structure, pilot features and calibrated instrument markings still need
separate sources or shader setup. The vector library below supplies a subset of
cockpit labels and generic grille masks, with the limits described there.

`materials/graphite-coating-albedo.png` is a new generic dark coating study,
generated with the built-in imagegen tool without any input image. It does not
sample, trace or reprocess the existing aircraft artwork. Colour and grain are
editorial choices, not measured properties of an F-117 coating.

Prompt: "Use case: photorealistic-natural. Asset type: original game material
source, square 2048 by 2048 albedo texture for a dark graphite aircraft coating.
Generate a completely new full-frame flat texture with no input artwork. Uniform
near-black neutral charcoal coating with extremely restrained fine matte stipple
and faint low-contrast application mottling. Orthographic surface only, evenly
exposed diffuse albedo with no directional lighting, no highlights, no shadows,
no ambient occlusion, no perspective. No panels, seams, rivets, screws, scratches,
lettering, markings, logos, objects, border, or watermark. Texture fills every
pixel. Opposite edges should join seamlessly. This is a generic editorial
material study, not a claim about measured F-117 coating."

Visually reviewed for absence of markings and atlas artwork. Seamlessness,
physical scale and colour still require material review. This PNG is a source
study, not a finished atlas, verified seamless tile or runtime DDS replacement.

## Vector decal sources

Added 82 transparent painting sources, each supplied as an editable SVG under
`vectors/` and a matching PNG under `vector_png/`:

- 63 legends: sensor-display controls, fuel quantity/selector wording,
  autopilot/autothrottle engage/channel wording, environmental controls,
  emergency power, electrical controls, lighting, armament, oxygen and seat
  safety wording.
- Ten separate numerals, 0 through 9.
- Seven simple marking shapes: two tick lengths, triangle, witness line, arrow,
  chevron and knob index.
- Two repeating grille masks with new, arbitrary 16-unit spacing.

`lettering-proof.png` and `lettering-proof-2.png` through `lettering-proof-4.png`
show the set on a dark background for review, with editable SVG equivalents in
`vectors/`. These proof sheets are not UV atlases. Source decal canvases
are transparent and padded; text uses editable Arial with a sans-serif fallback.
SVG `currentColor` sets ink colour, defaulting to `#deded5`. Change colour before
rasterising when different ink or a pure white mask is needed. The grille masks
are generic design inputs; their pitch is not an aircraft measurement.

Wording comes from short functional labels in the local manual OCR, with page
markers and line locators in `vector-manifest.json`. No old texture, mesh,
instrument registration or UV coordinates were read by the generator. The
existing `tools/textures/legacy/build_cockpit_stencil_sources.py` is not used because it traces
the current atlas coordinates. This new set uses independent proof spacing.
The original 63 legend wordings have now been reviewed against rendered manual
figures and their descriptions; `cockpit-wording-review.json` records the ten
groups, pages, evidence limits and reference PDF hashes. The font, hyphenation,
line breaks, physical sizes and locations are not claims of exact reproduction.
Description-based spelling or punctuation is identified where the figure differs.
DUCT OVHT remains a shared word fragment to combine with L/R. Seat safety wording
is established by prose; its checker artwork and installed typography remain open.

This review corrected the charger legend from CHR FAIL to CHGR FAIL, confirmed
by Figure 1-21 (PDF page 47) and the page 44 description. Its SVG, PNG and proof
were regenerated and validated. The source filename remains `label-charger-fail`.
No calibrated dial scale, movable needle or digital reading is baked in.

All 86 SVGs (82 sources and four proofs) passed XML parsing and GIMP rasterisation.
The PNG set passed decoding, dimensions, source/export hash and coverage checks.
All 82 source PNGs have nonempty alpha and transparent pixels; every label and
numeral has clear canvas padding. All four proof sheets were visually reviewed.
Reports are `vector-export-validation.json` and `vector-pixel-validation.json`.

To rebuild SVGs, run `python texture_sources/standalone/build_vector_sources.py`.
Then execute `export_vectors_gimp.py` in GIMP 3's Python console and call
`export_all()`. Its `ROOT` points to this checkout; update that path if relocated.
Run `python texture_sources/standalone/inspect_vector_exports.py` to verify the
PNG set (Pillow required). The exporter leaves other open GIMP images alone.

## Exterior safety marking sources

Nine additional transparent sources are in `exterior_vectors/` (editable SVG)
and `exterior_png/` (PNG): four rescue arrows (left/right, colour/grey), two
ejection-seat triangles, two fire-pierce markers and one generic NO STEP legend.
Review them in `exterior-markings-proof.png`.

Symbol identity and short wording were checked visually against USAF TO
00-105E-9, revision 11, 1 February 2006, printed page F-117A.3 (PDF page 35),
using a local copy of the document (AF1 R11 Segment 12 PDF).
The manual and rendered reference pages remain untracked under `docs/reference/`.
The local PDF hash, page locators and limits are in
`exterior-markings-manifest.json`. No manual artwork pixels, old texture pixels
or traced vertices are embedded in these newly drawn sources.

Arrow proportions, triangle vertices, text spacing, typeface and colour values
are new editorial choices. Grey variants are studies, not verified markings for
a particular aircraft/date. The diagram identifies NO STEP zones; it does not
prove that the generic NO STEP lettering source was painted on those surfaces.
Exact rescue instructions, serial numbers, crew names, squadron insignia and
livery layouts are not supplied. Rescue arrows must point to the actual access
panel when placed on the replacement model. The diagram's annotations are not
being treated as installed placards or operational rescue instructions.

All ten SVGs (nine sources and proof) passed XML parsing and GIMP rendering.
The ten PNGs passed decoding, dimension, alpha, manifest coverage and hash
checks. The proof was inspected; triangle side lettering was moved inside its
border and the final triangle was inspected again. The existing 86 cockpit
source/proof PNGs also passed validation after the shared exporter was updated.
Reports: `exterior-export-validation.json` and `exterior-pixel-validation.json`.

Rebuild with `python texture_sources/standalone/build_exterior_markings.py`.
In GIMP, execute `export_vectors_gimp.py`, then call
`export_all('exterior-markings-manifest.json', 'exterior_png', 'exterior-export-validation.json')`.
Verify with `python texture_sources/standalone/inspect_vector_exports.py --exterior`.

## Instrument-face design sources

Six 1024-square face designs are in `instrument_vectors/` and `instrument_png/`:
standby altimeter, standby airspeed, angle of attack, beta, vertical velocity and
clock. `instrument-faces-proof.png` shows all six. Each is a separately editable
SVG with a transparent exterior and an opaque dark dial plate. These plates are
painting sources, not installed instruments or final atlas regions.

The local base flight manual was visually inspected at PDF pages 71-74,
Figures 1-32 through 1-37. Its descriptions on pages 70-71 establish AOA
(-10 to 20 degrees in 2-degree increments), beta (16 degrees either side in
2-degree increments), airspeed (60-800 knots), altimeter (one revolution per
1000 feet with 20-foot increments), VVI (+/-6000 feet/minute), and the clock's
12-hour/seconds scales. These facts define ranges and units. Font, tick lengths,
label positions and angular spacing are new design proposals, not traced scale
geometry or measured calibration of an original instrument.

`instrument-faces-manifest.json` records value-to-angle anchors and figure/page
locators. Angles run clockwise from twelve o'clock and can be unwrapped beyond
360 degrees. Future model and gauge work must agree with these contracts:

- The current IAS argument 1006 binding stops at 600 knots. The proposed
  nonlinear 60-800 knot face requires remapping and sufficient pointer travel.
- Altimeter argument 1005 requires a full clockwise revolution per 0..1 cycle;
  counter and barometric windows/cutouts still need the replacement geometry.
- AOA argument 1007 has a piecewise mapping. The manifest records the new
  pointer angles required at argument values -1, 0.5 and 1.
- Beta, VVI and clock do not have bindings declared in the current
  `mainpanel_init.lua`; their pointers and bindings remain future model work.

No needles, live readings, counters, flags or physical bezels are baked into the
faces. Lua, EFM and model files were not changed. Do not install these against
the current gauge geometry and assume they read correctly.

All seven SVGs rendered through GIMP. PNG decoding, dimensions, transparency,
coverage and hashes passed. `instrument-contract-validation.json` also checks
the declared manual ranges, reference locators, monotonic finite angle anchors
and applicable minor intervals; it does not validate DCS runtime calibration.
The proof was reviewed, clock seconds labels were separated from long ticks,
and the corrected clock was visually checked. Export/pixel reports are
`instrument-export-validation.json` and `instrument-pixel-validation.json`.

Rebuild: `python texture_sources/standalone/build_instrument_faces.py`, then
`python texture_sources/standalone/check_instrument_contracts.py`. In GIMP,
execute `export_vectors_gimp.py` and call
`export_all('instrument-faces-manifest.json', 'instrument_png', 'instrument-export-validation.json')`.
Verify: `python texture_sources/standalone/inspect_vector_exports.py --instruments`.

The library now comprises eight material PNGs, 82 cockpit/generic decals, nine
exterior decals and six instrument-face proposals, plus six review PNGs. Atlas
painting, runtime calibration and remaining bespoke sources are still open.

## Detail coverage masks

Twelve new 512-square masks are supplied as editable SVGs in `detail_vectors/`
and transparent PNGs in `detail_png/`. Review `detail-masks-proof.png`:

- Six separate fastener components: head disc, washer ring, straight slot,
  cross recess, hex socket and external hex head.
- Straight seam, rounded seam corner and rounded panel outline.
- Single and double stitch rows, and box-and-cross webbing stitching.

These are new analytic primitives with generic editorial proportions. No old
textures, models, UVs or reference artwork were read. Fastener components share
a 512-square centre so head and recess can be layered independently. White RGB
with antialiased alpha represents coverage only. Assign colours and materials
after placement; choose any relief from the intended geometry, not from these
white pixels. These are not normal, height, AO or RoughMet maps.

Physical sizes, drive standards, thread pitch, panel shapes and aircraft
locations are not established. Seams and stitching have padded endpoints and
are not seamless tiles. Match them to permitted references on the replacement
UVs before painting. The proof was visually reviewed; all 13 PNGs passed the
shared source/export hash, decoding, dimensions, coverage and alpha checks.

Rebuild with `python texture_sources/standalone/build_detail_masks.py`. In GIMP,
execute `export_vectors_gimp.py`, then call
`export_all('detail-masks-manifest.json', 'detail_png', 'detail-export-validation.json')`.
Verify with `python texture_sources/standalone/inspect_vector_exports.py --details`.
Provenance and limitations are in `detail-masks-manifest.json`; validation is in
`detail-export-validation.json` and `detail-pixel-validation.json`.

## Annunciator lettering

`annunciator_vectors/` and `annunciator_png/` add 29 legends and a separate
resettable-light asterisk. These are white lettering coverage sources on alpha,
not illuminated lamp textures. `annunciator-lettering-proof.png` shows the set.
Wording was visually checked against local TO 1F-117A-1, Figure 1-23, PDF page 51
(printed 1-40), rather than trusting the figure's inaccurate OCR. The manifest
records the reference PDF hash and scope. Reference images remain untracked.

The single-line typography, spacing and proof order are new editorial choices.
This is a subset, not a complete annunciator-panel reconstruction. Existing
generator/converter lettering can be reused from the earlier source library;
unclear legends are omitted. No scanned pixels or panel-grid coordinates are
used. Place and size each source on the new UVs, confirm reset-symbol assignment,
and assign lamp colour and emission separately. No lamp brightness, runtime
state, shader behaviour or systems logic is supplied by these masks.

All 31 SVGs were XML-checked and rendered through GIMP. The proof was visually
reviewed; all PNGs passed decoding, size, alpha, hash and coverage checks,
including clear padding around every legend.

Rebuild: `python texture_sources/standalone/build_annunciator_sources.py`.
In GIMP, execute `export_vectors_gimp.py`, then call
`export_all('annunciator-manifest.json', 'annunciator_png', 'annunciator-export-validation.json')`.
Verify: `python texture_sources/standalone/inspect_vector_exports.py --annunciators`.

## Master-test and lighting lettering

`control_vectors/` and `control_png/` contain 23 additional editable legends,
reviewed in `control-legends-proof.png`. They cover master-test selector wording,
its push-to-test and ADC-pass legends, ground-control door and starter legends,
exterior lighting, sub-instrument lighting and APEX LIGHT.

TO 1F-117A-1 Figures 1-22 and 1-24 were visually checked at PDF pages 49 and 54
(printed 1-38 and 1-43). APEX LIGHT comes from the description on PDF page 52
(printed 1-41). `control-legends-manifest.json` records these locators and the
local reference PDF hash. The figure spellings FUS LTS and ANTICOLL are retained;
ADC-NIAC is a single-line adaptation of the figure's split legend. Existing
OFF, ON, BRT, DIM, TEST and MACH WARN sources remain available in earlier sets.

The sources use new font sizing, spacing and proof placement, with white text
on transparent canvases. No figure pixels, panel grid, UVs, selector angles or
illumination are copied or supplied. Confirm physical placement and any final
line breaks when painting the replacement UVs. All 24 SVG/PNG outputs passed
XML, decoding, dimensions, hash, coverage and alpha checks. Every legend has
clear padding; the proof was visually reviewed.

Rebuild: `python texture_sources/standalone/build_control_legends.py`.
In GIMP, execute `export_vectors_gimp.py`, then call
`export_all('control-legends-manifest.json', 'control_png', 'control-export-validation.json')`.
Verify: `python texture_sources/standalone/inspect_vector_exports.py --controls`.

A subsequent review of clearer Figure 1-45 (PDF page 87) corrected HRS MON to
RCS MON. The source is now `control-rcs-mon`; the superseded HRS files were
removed from the source library and archive. CLOSE remains a Figure 1-24 wording
variant; Figure 1-45 abbreviates it as CLS. Final configuration selection is open.

## Landing-gear and anti-ice lettering

`gear_ice_vectors/` and `gear_ice_png/` provide 22 new lettering sources,
shown in `gear-ice-lettering-proof.png`. Nine cover engine anti-ice lamps and
switch wording, deice fluid, inlet wiper positions, windshield heat and pitot
heat. Thirteen cover landing gear, the nose-position letter, horn silence,
brakes, emergency gear, tail hook and drag chute.

Wording was checked visually against TO 1F-117A-1 Figures 1-16 and 1-29,
PDF pages 39 and 63 (printed 1-28 and 1-52), with adjacent descriptions used
to confirm abbreviations. `gear-ice-manifest.json` records locators and the
reference PDF hash. The source text is newly typeset as single lines; split
figure legends such as EMER BRAKE PUSH and WIPER & FL require final line-break
decisions on the replacement UVs. Shared switch-position and landing-light
legends remain available in the earlier libraries.

These white-on-alpha sources supply coverage only. They establish no physical
size, panel layout, selector angles, lamp colour, runtime state or functional
instructions. Tail-hook lettering does not implement the separate tail-hook
model/EFM task. No scanned pixels, old artwork or UV coordinates were used.
All 23 SVG/PNG outputs passed XML, decoding, dimensions, source/export hashes,
coverage and alpha checks, with padding around every legend. The proof was
visually reviewed.

Rebuild: `python texture_sources/standalone/build_gear_ice_sources.py`.
In GIMP, execute `export_vectors_gimp.py`, then call
`export_all('gear-ice-manifest.json', 'gear_ice_png', 'gear-ice-export-validation.json')`.
Verify: `python texture_sources/standalone/inspect_vector_exports.py --gear-ice`.

## Flight-control lettering

`flight_control_vectors/` and `flight_control_png/` provide 16 new legends for
trim, built-in test and surface centering, plus DUAL FCS. The proof is
`flight-control-lettering-proof.png`. TO 1F-117A-1 Figure 1-27 was visually
reviewed at PDF page 58 (printed 1-47), with descriptions on PDF pages 59-60.
DUAL FCS is supported by its page 59 description and belongs to a separate
warning light, not the FCSP. The manifest records scope and the reference hash.

IN/OUT are separate words to combine with existing L/R sources. NORMAL follows
the selector description and is separate from the earlier NORM abbreviation.
Existing TEST/OFF and UP/DN sources can be reused. The typeface, spacing and
proof order are editorial; no panel geometry or scanned pixels were traced.
BIT display/sequence windows have no baked readings. Physical placement, lamp
colour, runtime behaviour and control calibration remain integration work.

All 17 SVG/PNG outputs passed XML, decoding, dimensions, source/export hash,
coverage and alpha checks. Every legend has transparent padding; the proof was
visually reviewed.

Rebuild: `python texture_sources/standalone/build_flight_control_sources.py`.
In GIMP, execute `export_vectors_gimp.py`, then call
`export_all('flight-control-manifest.json', 'flight_control_png', 'flight-control-export-validation.json')`.
Verify: `python texture_sources/standalone/inspect_vector_exports.py --flight-controls`.

## Fuel, refueling and cutoff lettering

`fuel_vectors/` and `fuel_png/` add 24 independent legends, reviewed in
`fuel-lettering-proof.png`. Fourteen cover the fuel panel, five cover refueling
indicators and the emergency air-refuel handle, and five are separate engine/APU
cutoff and fire-warning words. TO 1F-117A-1 Figure 1-8 was visually checked at
PDF page 24 (printed 1-14); the refuel and cutoff wording comes from descriptions
on PDF pages 25-26 (printed 1-15 and 1-16). `fuel-manifest.json` distinguishes
these evidence scopes and records the reference PDF hash.

APEX LIGHTS follows the figure; the earlier APEX LIGHT source follows prose and
remains available. ON/OFF/AUTO/NORM, BRT, L/R and X FEED OPEN can be reused from
earlier sources. New words use editable system-font text with original spacing
and single-line canvases. Refuel/cutoff installed typography, final line breaks
and switchlight segmentation remain unverified. No lamp state, colour,
brightness, operating procedure, physical size or panel layout is supplied.
No scanned pixels, old texture pixels or UV coordinates were used.

All 25 SVG/PNG outputs passed XML, decoding, dimensions, source/export hash,
coverage and alpha checks. All legends have transparent canvas padding; the
proof was visually reviewed and the source catalogue/bundle refreshed.

Rebuild: `python texture_sources/standalone/build_fuel_sources.py`.
In GIMP, execute `export_vectors_gimp.py`, then call
`export_all('fuel-manifest.json', 'fuel_png', 'fuel-export-validation.json')`.
Verify: `python texture_sources/standalone/inspect_vector_exports.py --fuel`.

## Seat-safety placard proposals

`seat_vectors/` and `seat_png/` contain four complete placard proposals and eight
separate backdrop/lettering components. `seat-placards-proof.png` shows the
LOCKED and ARMED pair; `seat-kit-beacon-proof.png` shows the kit/beacon pair.
TO 1F-117A-1 PDF page 89 (printed 1-78), Ejection Controls Safety Lever, describes
a yellow/black checkerboard EJECTION CONTROLS LOCKED placard and a black/white
EJECTION CONTROLS ARMED placard. The prose does not establish a checkerboard for
ARMED, so that proposal uses a plain black/white design.

Checker pitch, panel proportions, border, font, spacing and exact colour values
are new editorial choices, not measured reproduction. Both proposals have
transparent canvas padding. Assign physical size, seat-lever sides and UV
placement on the replacement geometry. No scanned pixels, old artwork or UVs
were used; these do not change seat controls or runtime bindings.

KIT DEPLOYMENT (FWD — AUTOMATIC / AFT — MANUAL) and RADIO BEACON (MAN / AUTO)
wording was checked against Figure 1-48 sheet 1, views D/E, PDF page 91
(printed 1-80), with the page 90 descriptions. Their black/white presentation,
typeface, proportions, spacing and beacon arrow geometry are editorial choices.
The kit directional arrow is omitted until its orientation can be established
on the replacement seat; the FWD/AFT wording is retained. Confirm all physical
orientation and placard fit on that geometry before installation.

All fourteen SVG/PNG files passed XML, decoding, dimensions, hash, coverage and
alpha checks. Both proofs were visually reviewed. Four three-layer XCFs separate
Backdrop, Lettering and an empty Paint details layer; original SVGs retain
editable text. Saved/reopened composites passed the shared master pixel check.
Reference provenance and limits are in `seat-placards-manifest.json`.

Rebuild: `python texture_sources/standalone/build_seat_placards.py`. In GIMP,
execute `export_vectors_gimp.py` and call
`export_all('seat-placards-manifest.json', 'seat_png', 'seat-export-validation.json')`.
Then rebuild paint masters as below. Verify the PNGs with
`python texture_sources/standalone/inspect_vector_exports.py --seat`.

## Oxygen regulator lettering

`oxygen_vectors/` and `oxygen_png/` contain eight new editable SVG and transparent
PNG legends: OXYGEN REGULATOR, PRESSURE DEMAND, FLOW, EMERGENCY, TEST MASK,
100% OXYGEN, NORMAL OXYGEN and SUPPLY. Wording was visually checked against
TO 1F-117A-1 Figure 1-46, Detail A, PDF page 87 (printed 1-76).
`oxygen-regulator-proof.png` was visually reviewed; all nine exports passed
hash, decoding, dimension, coverage and alpha checks.

Font, spacing and single-line arrangements are new editorial choices. TEST MASK,
100% OXYGEN and NORMAL OXYGEN are split across lines in the figure. Choose final
line breaks, dimensions and placement on replacement cockpit UVs. Existing
NORMAL, ON/OFF and oxygen-gauge lettering sources are reused separately. No
gauge calibration, needle, flow state or illumination is supplied by this set.
Reference hash and limits are recorded in `oxygen-manifest.json`.

Rebuild: `python texture_sources/standalone/build_oxygen_sources.py`. In GIMP,
execute `export_vectors_gimp.py`, then call
`export_all('oxygen-manifest.json', 'oxygen_png', 'oxygen-export-validation.json')`.
Verify: `python texture_sources/standalone/inspect_vector_exports.py --oxygen`.

## Auxiliary-navigation and AHRS lettering

`navigation_vectors/` and `navigation_png/` contain sixteen independent SVG and
transparent-PNG legends for auxiliary navigation and AHRS controls. Wording was
visually checked against TO 1F-117A-1 Figures 1-40 and 1-42, PDF pages 78/80
(printed 1-67/1-69), with descriptions on pages 77-79. The figure's short TCN
engraving is retained; prose calls the system TACAN. AUX NAV combines separated
words, SYN IND combines words either side of the meter, and PUSH TO SYNC follows
figure spacing. Existing N and PUSH sources remain available separately.

`navigation-lettering-proof.png` is a reviewed arrangement for checking the
sources, not an aircraft panel layout. All seventeen exports passed hashes,
decoding, dimensions, manifest coverage and transparent-padding checks. Font,
spacing, line breaks, physical size and UV placement require fitting on the
replacement geometry. No latitude scale, magnetic-variation values, selector
angles, meter indication or illumination has been assigned.
Reference provenance and limits are in `navigation-manifest.json`.

Rebuild: `python texture_sources/standalone/build_navigation_sources.py`. In
GIMP, execute `export_vectors_gimp.py` and call
`export_all('navigation-manifest.json', 'navigation_png', 'navigation-export-validation.json')`.
Verify: `python texture_sources/standalone/inspect_vector_exports.py --navigation`.

## Engine-panel lettering

`engine_vectors/` and `engine_png/` contain eighteen independent editable SVG and
transparent-PNG legends: nine for the throttle/start panel, five for the engine
performance display and four for AMAD/start warnings. Wording was visually
checked against TO 1F-117A-1 Figures 1-3 and 1-5, PDF pages 16/18 (printed
1-6/1-8), with descriptions on pages 15/17. FF retains the short figure legend.
Stacked ENGINE START, AMAD RUN and L/R AMAD UNCOUPLE wording is flattened for
these individual painting inputs. Exact line breaks and spacing await fitting.

`engine-lettering-proof.png` was visually reviewed. All nineteen SVG/PNG exports
passed XML, hashes, decoding, dimensions, manifest coverage and padding checks.
Font and spacing are editorial choices; the proof is not a panel layout. White
warning lettering carries no lamp colour, state or resettable asterisk. Friction
arrows, display readings, oil-pressure scales, calibration, physical dimensions
and UV placement remain open. Reuse earlier L/R, NORM and starter-engaged
sources separately. Reference hash and limitations are in `engine-manifest.json`.

Rebuild: `python texture_sources/standalone/build_engine_sources.py`. In GIMP,
execute `export_vectors_gimp.py`, then call
`export_all('engine-manifest.json', 'engine_png', 'engine-export-validation.json')`.
Verify: `python texture_sources/standalone/inspect_vector_exports.py --engine`.

## Consolidated cockpit-system lettering

`completion_vectors/` and `completion_png/` add 97 independently drawn lettering
sources for recorder, antenna, UHF, intercom, selected KY-58, IFF, TACAN, selected
INS, hydraulic, canopy and ECS words. Nine shared-word uses link existing
sources instead of duplicating artwork. Five `systems-lettering-proof-*.png`
sheets were visually reviewed. All 102 exports passed hashes, decoding,
dimensions, coverage and padding checks.

`completion-manifest.json` records the manual figures, PDF pages, reference hash,
shared-source links and limits. Small unreadable engravings and configuration
details remain unresolved. Word fragments and multi-line figure labels are
flattened into separate painting inputs; exact font, line breaks and physical
fit remain open. No entered codes, numerical display readings, lamp states,
selector calibration or UV layout is supplied.

Rebuild: `python texture_sources/standalone/build_completion_sources.py`. In
GIMP, execute `export_vectors_gimp.py` and call
`export_all('completion-manifest.json', 'completion_png', 'completion-export-validation.json')`.
Verify: `python texture_sources/standalone/inspect_vector_exports.py --completion`.

## Layered paint masters and source bundle

`paint_masters/` contains 18 GIMP XCF masters, with matching flattened previews
in `paint_masters/previews/`:

- Eight material masters: unchanged generated colour source plus empty
  `Unique markings` and `Paint details` layers. These empty layers are working
  space, not completed aircraft-specific detail.
- Six instrument masters: separate `Plate`, `Ticks`, `Numerals`, `Legends` and
  empty `Paint details` layers. The clock has an empty legends layer because
  its two rings contain numerals only.
- Four seat placards: separate `Backdrop`, `Lettering` and empty `Paint details`
  layers, as described above.

The instrument components also exist as 24 separate SVGs in
`instrument_components/`; this retains editable vector text and geometry.
Their XCF counterparts are raster layers. The component builder separates the
new source elements by role without changing their coordinates or styles.
Original full-face SVGs remain the scale/layout authority.

GIMP layer blend/composite colour spaces are set to non-linear RGB to match the
approved SVG rasterisation. Each XCF is saved and reopened, with its canvas and
layer count checked. The reopened master supplies the preview used for pixel
comparison against the approved material or full-face PNG. Reports are
`paint-master-validation.json` and `paint-master-pixel-validation.json`.
All 18 masters passed save/reopen, canvas and layer-count checks. Material
composites match their approved source pixels exactly; the six instrument
composites differ by at most 1/255 per RGBA channel after separation and
rasterisation. No artwork was repainted during the assembly.

To rebuild, run `python texture_sources/standalone/build_paint_components.py`.
Execute `build_paint_masters_gimp.py` in GIMP 3 and call `build_all()`. This GIMP
script's `ROOT` must point to the source folder if the library is relocated.
Wait for the build to finish before running
`python texture_sources/standalone/inspect_paint_masters.py`.
`paint-master-build-state.json` must say `complete`; the validator rejects a
running or failed build so partially written previews cannot pass review.

Run `python texture_sources/standalone/package_sources.py` to produce
`dist/standalone-texture-sources.zip` and its validation report. The archive
contains only this source folder, with a per-file `PACKAGE_INDEX.json`. It
excludes Python caches, reference manuals, runtime DDS files and models.
Packaging refreshes source checks, verifies ZIP CRCs and verifies every member's
SHA-256 after reading it back. The ZIP is a source handoff, not an installable mod.

Packaging also runs `inspect_material_sources.py` and `audit_source_handoff.py`.
These check approved material integrity, record edge/interior pixel diagnostics,
validate cross-library shared-source links, SVG coverage and local documentation
links, and compare recorded reference hashes with local PDFs when available.
References remain outside the source bundle. The audit verifies provenance
records and declared inputs; it is not independent certification of authorship.

## Remaining texture work

- Obtain the new exterior and cockpit UV templates and material assignments.
- Paint aircraft panels, bays, doors, gear, launcher, missile, cockpit structure,
  instrument and console surfaces from permitted references on those templates.
- Create new pilot, seat, glass, grille, turbine and other shared maps as needed
  by the replacement materials. Independently author normal maps where required.
- Validate cockpit labels against the manuals and new instrument placement.
- Export final colour maps as BC7 and normal maps as BC5 with full mip chains.
- Check DDS headers, mip counts, colour space, alpha and decoded results; inspect
  all atlases on the replacement models and in DCS before installing.

Section 3.4 remains incomplete. New material names and EDM texture bindings are
part of model integration; livery repainting remains a separate plan item.
