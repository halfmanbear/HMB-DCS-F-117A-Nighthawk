# Exterior texture restoration

The first restoration pass covers all 27 DDS files in
`Textures/F-117-NightHawk-TEXTURES`. Validated candidates are installed under
their existing runtime filenames. The original EDM and the source
`blender_files/f-117-nighthawk-exterior.blend` are unchanged.

## Review

Open `dist/exterior-texture-remake/review-sheet-1.jpg` for the airframe comparison.
Sheets 2 through 7 cover the remaining textures. Every row places the decoded
original on the left and the lossless restored source on the right.

The working Blender project is
`dist/exterior-texture-remake/F117_Exterior_Texture_Remake.blend`.
All 27 target image datablocks now load lossless PNG sources instead of the
1-pixel placeholders found in the exterior source. Their original image names
are retained so EDM material texture identifiers continue to match the installed
DDS files. The original model has 594 objects and 73 objects in its Collision
collection; the object hierarchy, mesh counts, UV layer sizes and actions were
checked before and after binding.

`exterior-before.png` and `exterior-after.png` use the same temporary studio
scene. They show the source model's current animation pose and exporter shader
defaults. They are texture inspection aids, not a DCS runtime validation.

## Work performed

| Group | Treatment |
|---|---|
| Aircraft 01 / 02 | Selectively restore neutral dark coating toward the same graphite treatment used in the cockpit pass. Retain existing UVs, markings, wear, shading and coloured details. |
| Bays, doors, left/right gear, launcher, missile | Selectively clean neutral midtones. Preserve coloured equipment, dark rubber, labels and existing surface artwork. |
| Eleven shared textures | Reuse the completed cockpit restoration, including finished lettering, only after verifying the source DDS SHA-256 matches the exterior original. |
| Front grille, turbine, grey and texture tiles | Preserve the decoded source pixels; update the delivery format/mips. |

The shared group comprises Aircraft 03, Cockpit 01-04, glass, nose gear, display
green, pilot colour/normal and seat. Each texture has an editable XCF and a
lossless PNG in `dist/exterior-texture-remake/sources/`. Newly restored XCFs
retain the original layer beneath the selective finish layer; reused XCFs
retain the layers from the cockpit project.

This pass restores existing artwork. It does not redraw every marking, add
surface geometry, or claim recovered detail from the original BC1 compression.

## Delivery and validation

- Colour maps use BC7 with full mip chains, at their existing 8K/4K/smaller
  resolutions. BC7 uses twice BC1's block storage at the same dimensions.
- The tiny front grille uses lossless RGBA8: a BC7 trial produced up to 12 alpha
  levels of error, so it was replaced. Its final base RGB and alpha are exact.
- The pilot normal reuses the normalized linear BC5 cockpit result. The Blender
  PNG is set to Non-Color. No new normal or RoughMet maps were invented.
- The verified constant green texture reuses the lossless 4x4 RGBA8 tile.
- All 27 exports passed dimension, mip-count, DDS byte-size, colour/alpha and
  applicable preserved-pixel checks. Installed hashes match validated exports.
- All seven atlas comparison sheets were visually inspected. Blender before and
  after renders were produced.
- No EDM export, Model Viewer round-trip or DCS runtime test was performed.

Existing liveries with their own local texture overrides continue to use those
overrides. This pass changes the shared base texture folder only. Helmet and
navigation-light image identifiers outside the requested folder retain their
existing dependencies/placeholders.

Reports, source hashes, restoration actions and installation checks are in
`dist/exterior-texture-remake/texture-manifest.json`, `validation.json`,
`blender-validation.json` and `installation-validation.json`.

## Rollback

Exact original files are in `dist/exterior-texture-remake/originals/`.
From the repository root run:

```powershell
python tools/install_exterior_texture_remake.py restore
```

The restore command verifies the backup hashes and refuses to overwrite texture
files that have changed since this installation.

## Reproduction

1. In GIMP MCP's Python console, execute
   `tools/remake_exterior_textures_gimp.py`, then call `run_batch()`.
   It uses the saved originals when present and otherwise the shared texture
   folder. The prior cockpit sources are required for the shared work.
   `PYTHON` identifies the local Python with NumPy/Pillow for the mask helper.
2. Run `python tools/exterior_texture_pixels.py validate` to check the staged
   exports and generate comparison sheets.
3. In Blender, open the exterior source and execute
   `tools/remake_exterior_blend.py`. It saves only the separate review blend.
4. Run `python tools/install_exterior_texture_remake.py install` after restoring
   originals if already installed. Installation checks candidate and original
   hashes, backs up all files before replacement, and verifies installed hashes.

The `dist/` directory is ignored by Git. The installed DDS changes and workflow
scripts are available as unstaged changes. The pre-existing Git index was not
modified.
