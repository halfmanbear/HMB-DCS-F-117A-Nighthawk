"""Build a faint HUD glass tint, independent of the canopy (Pillow required)."""
from pathlib import Path
import io
import struct

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Liveries/Cockpit_F-117/Default/F-117_glass_clear.dds'
TARGET = SOURCE.with_name('F-117_hud_glass_clear.dds')


def build():
    source = Image.open(SOURCE).convert('RGBA')
    # Keep the source's subtle surface variation, with neutral RGB and one
    # seventh of its opacity. Both combiner panes can overlap in the pilot view.
    grey = source.convert('L').point(lambda value: 210 + round(value * 25 / 255))
    alpha = source.getchannel('A').point(lambda value: round(value / 7))
    image = Image.merge('RGBA', (grey, grey, grey, alpha))
    levels = []
    while True:
        buffer = io.BytesIO()
        image.save(buffer, format='DDS')
        levels.append(buffer.getvalue())
        if image.size == (1, 1):
            break
        image = image.resize(tuple(max(1, n // 2) for n in image.size), Image.Resampling.BOX)
    header = bytearray(levels[0][:128])
    struct.pack_into('<I', header, 8, struct.unpack_from('<I', header, 8)[0] | 0x20000)
    struct.pack_into('<I', header, 28, len(levels))
    struct.pack_into('<I', header, 108, 0x401008)  # texture, complex, mipmap
    TARGET.write_bytes(header + b''.join(level[128:] for level in levels))
    saved = Image.open(TARGET)
    assert saved.size == source.size
    assert saved.getchannel('A').getextrema() == (13, 13)
    assert saved.getchannel('R').tobytes() == saved.getchannel('G').tobytes() == saved.getchannel('B').tobytes()
    print(f'{TARGET}: {saved.size}, {len(levels)} mip levels, alpha 13/255')


if __name__ == '__main__':
    build()
