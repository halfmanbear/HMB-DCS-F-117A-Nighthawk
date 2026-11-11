"""Generate the deterministic, opaque TGA used by the LCD holder diagnostic."""
from pathlib import Path
import struct


def generate():
    size = 256
    # Top-left red, top-right green, bottom-left blue, bottom-right yellow.
    colours = ((220, 35, 35), (35, 220, 35), (35, 70, 230), (230, 210, 35))
    pixels = bytearray()
    for y in range(size):
        for x in range(size):
            colour = colours[(y >= size // 2) * 2 + (x >= size // 2)]
            if min(x, y, size - 1 - x, size - 1 - y) < 6:
                colour = (255, 255, 255)
            elif abs(x - size // 2) < 3 or abs(y - size // 2) < 3:
                colour = (0, 0, 0)
            # An asymmetric white square identifies the top-left corner.
            elif 18 <= x < 42 and 18 <= y < 42:
                colour = (255, 255, 255)
            pixels.extend(reversed(colour))
    header = struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, size, size, 24, 0x20)
    destination = Path(__file__).resolve().parents[2] / 'Cockpit/Scripts/Resources/LCD/holder_test.tga'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(header + pixels)
    print(destination)


if __name__ == '__main__':
    generate()
