"""Preview the current F-117 HUD using the maintained Layout Studio renderer.

python tools/cockpit/hud_preview.py --roll 30 --pitch -5
python tools/cockpit/hud_preview.py --output tmp/hud-preview.png
Requires lupa and Pillow, as listed in tools/cockpit/layout_editor_requirements.txt.
"""
from pathlib import Path
import argparse
import math
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout_editor import DEFAULTS, Model, PAGES, Renderer, default_view, hud_working_area


def render_preview(roll=0.0, pitch=0.0, size=850):
    params = dict(DEFAULTS, ROLL_HUD=math.radians(roll), PITCH_HUD=math.radians(pitch))
    model = Model('HUD', PAGES['HUD'].read_text(encoding='utf-8-sig'))
    area = hud_working_area()
    extent, center = default_view('HUD')
    if area['boundary'] is None:
        # The maintained model uses one source unit per mrad without a captured
        # DCS scale. Show an angular layout, without claiming glass projection.
        extent = math.radians(max(area['half_width_deg'], area['half_height_deg'])) * 1000 * 1.2
        center = tuple(area['origin_mrad'])
    image, hits, missing = Renderer().render(model, params, size=size,
        extent=extent, center=center, boundary=area['boundary'])
    if missing:
        raise RuntimeError('Missing HUD textures: ' + ', '.join(sorted(missing)))
    if not hits:
        raise RuntimeError('The current HUD produced no visible preview elements.')
    return image, model, hits


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roll', type=float, default=0.0, help='Bank angle in degrees')
    parser.add_argument('--pitch', type=float, default=0.0, help='Pitch angle in degrees')
    parser.add_argument('--show-tex', action='store_true',
        help='Accepted for compatibility; the current HUD uses vector strokes')
    parser.add_argument('--output', type=Path, help='Save a PNG instead of opening the preview')
    args = parser.parse_args(argv)
    image, model, hits = render_preview(args.roll, args.pitch)
    print(f'HUD: {len(model.elements)} elements; {len(hits)} visible')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output)
        print(args.output)
    else:
        image.show(title=f'F-117 HUD | roll {args.roll:+g} | pitch {args.pitch:+g}')


if __name__ == '__main__':
    main()
