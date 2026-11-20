"""Build separate warm emission DDS maps, retaining alpha and full mip chains."""
import io
import json
from pathlib import Path
import struct
import sys
from PIL import Image

source, output = map(Path, sys.argv[1:])
report = json.loads((output / 'emission-bindings.json').read_text())
for old, new in report['warm_textures'].items():
    image = (Image.new('RGBA', (4, 4), 'white') if old == 'white'
             else Image.open(source / (old + '.dds')).convert('RGBA'))
    channels = list(image.split())
    for i, scale in enumerate(report['warm_rgb_multiplier']):
        channels[i] = channels[i].point([round(n * scale) for n in range(256)])
    warm = Image.merge('RGBA', channels)
    assert warm.getchannel('A').tobytes() == image.getchannel('A').tobytes()
    stream = io.BytesIO()
    warm.save(stream, format='DDS')
    header = bytearray(stream.getvalue()[:128])
    levels, level = [], warm
    while True:
        levels.append(level.tobytes('raw', 'BGRA'))
        if level.size == (1, 1): break
        level = level.resize((max(1, level.width // 2), max(1, level.height // 2)), Image.Resampling.LANCZOS)
    flags = struct.unpack_from('<I', header, 8)[0] | 0x20000
    struct.pack_into('<I', header, 8, flags)
    struct.pack_into('<I', header, 28, len(levels))
    struct.pack_into('<I', header, 108, 0x401008)
    path = output / (new + '.dds')
    path.write_bytes(header + b''.join(levels))
    with Image.open(path) as check:
        assert check.size == warm.size
        assert check.convert('RGBA').tobytes() == warm.tobytes()
    print('TEXTURE_PASS', new, warm.size, len(levels), 'mips')
