"""Draw new UV-independent exterior safety marking sources from references.

No model, photograph pixels or existing texture is loaded. The rescue-manual
figures establish symbol identity and wording, not these newly chosen vertices.
"""
from pathlib import Path
import hashlib
import html
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'exterior_vectors'
REFERENCE = 'USAF TO 00-105E-9 rev 11 (AF1 R11 Segment 12 PDF), local copy under docs/reference/'


def text(label, x, y, size, fill='#141414', transform=''):
    return (f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" '
            f'font-size="{size}" fill="{fill}" text-anchor="middle" '
            f'transform="{transform}">{html.escape(label)}</text>')


def rescue(left=False, grey=False):
    # Reflect only arrow geometry; the lettering remains normally readable.
    points = '40,70 780,70 780,30 984,128 780,226 780,186 40,186'
    transform = 'translate(1024 0) scale(-1 1)' if left else ''
    paint = '#b0b3b5' if grey else '#ead62d'
    return (f'<g transform="{transform}"><polygon points="{points}" fill="{paint}" '
            'stroke="#deded5" stroke-width="22" stroke-linejoin="miter"/>'
            f'<polygon points="{points}" fill="{paint}" '
            'stroke="#141414" stroke-width="7" stroke-linejoin="miter"/></g>'
            + text('RESCUE', 620 if left else 404, 155, 86))


def ejection(grey=False):
    inner = '#292c30' if grey else '#c92936'
    ink = '#c3c5c6' if grey else '#141414'
    return ('<path d="M512 32L32 864H992Z" fill="#b0b3b5" '
            'stroke="#141414" stroke-width="6"/>'
            f'<path d="M512 135L125 806H899Z" fill="{inner}" '
            'stroke="#141414" stroke-width="5"/>'
            + text('DANGER', 302, 475, 35, transform='rotate(-60 302 475)')
            + text('DANGER', 722, 475, 35, transform='rotate(60 722 475)')
            + text('DANGER', 512, 850, 35)
            + text('UPWARD', 512, 524, 61, ink)
            + text('EJECTION', 512, 602, 61, ink)
            + text('SEAT', 512, 680, 61, ink))


def fire_pierce(grey=False):
    paint = '#c3c5c6' if grey else '#c92936'
    return (f'<path d="M48 166V48H166 M346 48H464V166 '
            f'M464 346V464H346 M166 464H48V346" fill="none" '
            f'stroke="{paint}" stroke-width="23"/>'
            f'<circle cx="256" cy="256" r="27" fill="{paint}"/>'
            + text('FIRE', 256, 174, 65, '#deded5')
            + text('PIERCE', 256, 392, 65, '#deded5'))


def build():
    OUT.mkdir(exist_ok=True)
    rows = []
    artworks = []

    def write(name, width, height, body, title, kind, **metadata):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
               f'height="{height}" viewBox="0 0 {width} {height}">'
               f'<title>{html.escape(title)}</title>{body}</svg>\n')
        ET.fromstring(svg)
        path = OUT / (name + '.svg')
        path.write_text(svg, encoding='utf-8')
        rows.append(dict(file=path.relative_to(ROOT).as_posix(), width=width,
                         height=height, kind=kind,
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest(), **metadata))
        if kind != 'review only':
            artworks.append((name, width, height, body))

    for grey in (False, True):
        variant = 'grey-study' if grey else 'colour-reference'
        for left in (False, True):
            direction = 'left' if left else 'right'
            write(f'rescue-arrow-{direction}-{variant}', 1024, 256,
                  rescue(left, grey), 'Rescue arrow ' + direction, 'exterior symbol',
                  evidence='rescue-symbol', variant=variant,
                  placement='Choose direction to point at the actual new rescue access panel')
        write('ejection-triangle-' + variant, 1024, 896, ejection(grey),
              'Upward ejection seat warning', 'exterior symbol',
              evidence='ejection-symbol', variant=variant)
        write('fire-pierce-' + variant, 512, 512, fire_pierce(grey),
              'Fire pierce point marker', 'exterior symbol',
              evidence='fire-pierce-symbol', variant=variant)
    write('no-step-wording-study', 1024, 160, text('NO STEP', 512, 112, 100, '#c3c5c6'),
          'No step generic wording study', 'legend', evidence='no-step-zone',
          status='Generic wording only; the figure identifies no-step zones, not this painted stencil')

    body = ['<rect width="2048" height="2048" fill="#292c30"/>',
            text('Independent exterior marking sources', 1024, 70, 38, '#deded5')]
    # Nine isolated review cells, independent of any aircraft UV coordinates.
    for index, (name, width, height, artwork) in enumerate(artworks):
        column, row = index % 3, index // 3
        scale = min(560 / width, 400 / height)
        x = 64 + column * 674 + (560 - width * scale) / 2
        y = 160 + row * 600 + (400 - height * scale) / 2
        body.append(f'<g transform="translate({x} {y}) scale({scale})">{artwork}</g>')
        body.append(text(name, 344 + column * 674, 620 + row * 600, 20, '#aeb4ba'))
    body.append(text('Grey variants are artwork studies. No physical size or UV placement assigned.',
                     1024, 1990, 25, '#deded5'))
    write('exterior-markings-proof', 2048, 2048, ''.join(body),
          'Exterior marking proof sheet', 'review only')
    evidence = {
        'rescue-symbol': dict(source=REFERENCE, pdf_page=35, printed_page='F-117A.3',
                              scope='Diagram shows RESCUE in a right-pointing arrow'),
        'ejection-symbol': dict(source=REFERENCE, pdf_page=35, printed_page='F-117A.3',
                                scope='Diagram shows triangle with DANGER and UPWARD EJECTION SEAT'),
        'fire-pierce-symbol': dict(source=REFERENCE, pdf_page=35, printed_page='F-117A.3',
                                   scope='Diagram shows broken-corner frame, centre dot, FIRE / PIERCE'),
        'no-step-zone': dict(source=REFERENCE, pdf_page=35, printed_page='F-117A.3',
                             scope='Diagram identifies blow-in doors as NO STEP; does not verify a painted legend'),
    }
    manifest = dict(schema_version=1, date='2026-11-05',
                    method='New SVG geometry and editable system-font text; no traced vertices or copied pixels',
                    input_textures=[], input_meshes=[], uv_coordinates_used=False,
                    reference_document='USAF TO 00-105E-9, revision 11, 1 February 2006; mirrored primary document',
                    local_reference='docs/reference/TO00-105E-9-R11-Segment12.pdf (untracked)',
                    reference_sha256=hashlib.sha256((ROOT.parents[1] / 'docs/reference/TO00-105E-9-R11-Segment12.pdf').read_bytes()).hexdigest(),
                    evidence=evidence,
                    limitations=['Symbol identity/wording from the manual; dimensions, font and spacing are editorial',
                                 'Colours are visual approximations, not sampled aircraft paint standards',
                                 'Grey variants are editorial and not verified for a particular aircraft or date',
                                 'Left-pointing rescue variant is an adaptation; do not mirror the text',
                                 'Not a complete exterior stencil inventory; no unit insignia, serials or livery sets',
                                 'Exact rescue instructions and small unreadable legends are deliberately omitted'],
                    sources=rows)
    (ROOT / 'exterior-markings-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Wrote and XML-checked {len(rows)} exterior SVGs')


if __name__ == '__main__':
    build()
