"""Generate the mod's own cockpit switch click and its sound definition."""
import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RATE = 44100
WAVE_PATH = ROOT / "Sounds/Effects/Aircrafts/F-117/Cockpit/Click.wav"
SDEF_PATH = ROOT / "Sounds/sdef/Aircrafts/F-117/Cockpit/Click.sdef"


def samples():
    """A short decaying metallic tick with a broadband contact transient."""
    noise = random.Random(117)
    for n in range(int(RATE * 0.045)):
        t = n / RATE
        tone = (0.55 * math.sin(2 * math.pi * 2400 * t)
                + 0.30 * math.sin(2 * math.pi * 5100 * t)) * math.exp(-t / 0.006)
        transient = (noise.random() * 2 - 1) * math.exp(-t / 0.0015)
        yield max(-1.0, min(1.0, 0.6 * (tone + transient)))


def main():
    WAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SDEF_PATH.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(WAVE_PATH), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(b"".join(struct.pack("<h", int(s * 32767)) for s in samples()))
    SDEF_PATH.write_text('wave = "Effects/Aircrafts/F-117/Cockpit/Click"\n'
                         "inner_radius = 10\nouter_radius = 100\n", newline="\n")


if __name__ == "__main__":
    main()
