"""Interactive viewer for the platypus exhaust nozzles and glow lights.

Reads the values behind platypus_nozzles() and platypus_glow_lights() in
F-117-NightHawk.lua, lets you change every one with a slider, and draws plan,
side and rear views of the slots, nozzles, exhaust direction and glow lights.
"Save Lua" writes the values back into the Lua file in place, keeping its
comments.

    python tools/models/platypus_viewer.py [F-117-NightHawk.lua]
        [--glow 1.0] [--snapshot out.png]

Needs Python with tkinter and matplotlib.

What the preview does and does not know:
* Positions use the Lua convention {+forward/-back, +up/-down, +right/-left}.
  Plan view is x (forward) against z (right); side view is x against y; the
  rear view is z against y looking forward.
* Nozzle flame length is exhaust_length_ab, drawn along the orientation. DCS
  only draws it with afterburner, which this aircraft does not have.
* Glow circles are the light range. Their strength is colour alpha times the
  "Glow draw argument" slider, which stands in for arguments 1002 / 1003.
* The slot height is only used to suggest a nozzle diameter. It is not saved.
* Haze has two types, switched in the panel. Both use stock DCS config files that
  a mod cannot change, so they have no sliders and Save Lua ignores them. The
  values are read from the DCS install, or the stock numbers are used.
  - Visible shimmer (hotAir.lua and hotAir.fx): one circle per particle age along
    each nozzle's flow line. Distance along the flow and billboard size follow the
    stock vertex shader at low altitude, so the clouds grow from ScaleBase to many
    metres and merge. The status line says where the left and right clouds meet.
    Lifetime comes from the LifeTime table at the "Aircraft speed" slider. Start
    speed (nozzle speed plus aircraft speed) and the random term are assumed.
    Seen in game: stationary, the clouds do follow the nozzle splay (80 degrees
    sent them out along the wing trailing edges). Moving, they trail straight back
    along the flight path and are much wider, so this preview only matches the game
    at ground idle. It does not model the flight-path effect.
    Tested in game: with graphics heat blur off all exhaust effects vanish, so the
    shimmer is the only visible exhaust and shimmer mode is the one to trust.
    Not tested: whether diameter or exhaust_length_ab change the shimmer (a
    two-engine test is in the Lua), splay at ground idle below 80 degrees, and
    the exact size and length of the haze against the model. The aircraft outline
    in the plan view is a rough planform for scale, not taken from the model.
  - Infrared (exhaustTrailFlir.lua): a tube trailLength long, trailRadius either
    side of the flow line. That the radius is a half-width is assumed.
* DCS has no bar light, only omnilight (all directions) and spotlight (cone). A
  thin bar is built from a row of small-range omnilights: raise "Lights per slot",
  set first/last t near 0 and 1, and lower range until the circles just overlap.
  The status panel says GAPS when the spacing is more than twice the range.
"""

from __future__ import annotations

import argparse
import math
import re
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle, PathPatch
from matplotlib.path import Path as MplPath

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LUA = ROOT / "F-117-NightHawk.lua"

# Stock DCS exhaust haze settings. A mod cannot change them. They are read from the
# install when the files can be found (and lupa is installed for hotAir.lua),
# otherwise these stock values are used.
DCS_ROOTS = [Path(r"E:\Eagle Dynamics\DCS World"), Path(r"C:\Program Files\Eagle Dynamics\DCS World")]
KMH = 1.0 / 3.6
IR_DEFAULT = {"trailLength": 4.0, "trailRadius": 1.3}  # exhaustTrailFlir.lua
SHIMMER_DEFAULT = {  # hotAir.lua; speeds in m/s
    "scale": 1.3,
    "nozzle_speed": 200 * KMH,
    "dist": [(200 * KMH, 8.0), (700 * KMH, 3.0)],
    "trail": [(0.0, 30.0), (100 * KMH, 55.0), (500 * KMH, 90.0), (1000 * KMH, 40.0)],
    "life": [(200 * KMH, 2.2), (500 * KMH, 1.2), (700 * KMH, 0.5), (900 * KMH, 0.06)],
}
SHIMMER_FILE = "hotAir.lua"
IR_FILE = "exhaustTrailFlir.lua"

DEEPCOPY = """function deepcopy(o)
  if type(o) ~= 'table' then return o end
  local c = {}
  for k, v in pairs(o) do c[k] = deepcopy(v) end
  return c
end"""


def stock_file(name: str):
    for root in DCS_ROOTS:
        path = root / "Config" / "Effects" / "ParticleSystem2" / name
        if path.exists():
            return path
    return None


def load_ir() -> dict:
    values = dict(IR_DEFAULT)
    path = stock_file(IR_FILE)
    if path:
        text = path.read_text(encoding="utf-8", errors="replace")
        for key in values:
            m = re.search(key + r"\s*=\s*(-?\d+(?:\.\d+)?)", text)
            if m:
                values[key] = float(m.group(1))
    return values


def load_shimmer() -> dict:
    values = {k: (list(v) if isinstance(v, list) else v) for k, v in SHIMMER_DEFAULT.items()}
    path = stock_file(SHIMMER_FILE)
    if not path:
        return values
    try:
        from lupa import LuaRuntime
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(DEEPCOPY)
        lua.execute(path.read_text(encoding="utf-8", errors="replace"))
        eff = lua.eval("Effect")[1]

        def pairs(tbl):
            return [(float(tbl[i][1]), float(tbl[i][2])) for i in range(1, len(tbl) + 1)]

        # The file reassigns nozzleSpdMin for the KO_50 preset after Effect is built, so
        # the first value (200 km/h) is the one used by Effect.
        values.update(scale=float(eff.ScaleBase), dist=pairs(eff.DistMax), trail=pairs(eff.TrailLength),
                      life=pairs(eff.LifeTime))
    except Exception:  # lupa missing or an unexpected file: keep the stock values
        pass
    return values


def shimmer_particle(shim: dict, speed: float, age: float):
    """Distance along the flow (m) and billboard size (m) of a hotAir particle of a
    given age (s), following the stock hotAir.fx vertex shader at low altitude.
    Start speed is nozzle speed plus aircraft speed (assumed), random term fixed at 0.5."""
    scale, start = shim["scale"], shim["nozzle_speed"] + speed
    n_speed = start / 277.75
    n_conv = 1 - min(1.0, max(0.0, speed * 3.6 / 100))
    offset = -2 * (1 + (start - 55.556) / 100)
    along = ((math.log(math.exp(offset) + age * 2) - offset) * scale * (1 + n_conv)
             + n_conv * age * (4 + 0.5) + scale + age)
    life = interp(shim["life"], start)
    fade = min(1.0, age / life * 30 * (1 + n_speed * 4)) ** 0.3
    size = scale * (1 + 7 * abs(age * 3) ** 0.8 * n_speed + fade)
    return along, size


def interp(table, x: float) -> float:
    """Piecewise linear lookup, clamped at both ends."""
    if x <= table[0][0]:
        return table[0][1]
    for (x0, y0), (x1, y1) in zip(table, table[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return table[-1][1]


BG = "#14181c"
FG = "#d8dee4"
GRID = "#2c343c"
ACCENT = "#e8a24a"
LEFT_COL = "#5fb0ff"
RIGHT_COL = "#7be08a"

# key, label, low, high, step, group
SCALARS = [
    ("in_x", "Slot inboard x", -8.0, -2.0, 0.01, "Slot"),
    ("in_y", "Slot inboard y", -0.6, 0.3, 0.005, "Slot"),
    ("in_z", "Slot inboard z", 0.0, 2.0, 0.01, "Slot"),
    ("out_x", "Slot outboard x", -8.0, -2.0, 0.01, "Slot"),
    ("out_y", "Slot outboard y", -0.6, 0.3, 0.005, "Slot"),
    ("out_z", "Slot outboard z", 0.5, 4.0, 0.01, "Slot"),
    ("slot_h", "Slot height (ref only)", 0.02, 0.3, 0.005, "Slot"),
    ("segments", "Nozzles per slot", 1, 12, 1, "Nozzles"),
    ("splay", "Splay outboard (deg)", -5, 90, 0.5, "Nozzles"),
    ("nz_aft", "Nozzle aft offset", -0.2, 0.6, 0.005, "Nozzles"),
    ("diameter", "diameter", 0.005, 0.6, 0.005, "Nozzles"),
    ("len_ab", "exhaust_length_ab", 0, 12, 0.1, "Nozzles"),
    ("len_ab_k", "exhaust_length_ab_K", 0, 12, 0.1, "Nozzles"),
    ("smoke", "smokiness_level", 0, 0.1, 0.001, "Nozzles"),
    ("glow_n", "Lights per slot", 1, 24, 1, "Glow lights"),
    ("glow_t0", "First light t (0 in, 1 out)", 0, 1, 0.01, "Glow lights"),
    ("glow_t1", "Last light t", 0, 1, 0.01, "Glow lights"),
    ("glow_aft", "Light aft offset", -0.2, 1.0, 0.01, "Glow lights"),
    ("glow_r", "Colour R", 0, 1, 0.01, "Glow lights"),
    ("glow_g", "Colour G", 0, 1, 0.01, "Glow lights"),
    ("glow_b", "Colour B", 0, 1, 0.01, "Glow lights"),
    ("glow_a", "Brightness (4th value)", 0, 1, 0.01, "Glow lights"),
    ("glow_range", "range", 0.05, 6.0, 0.01, "Glow lights"),
    ("haze_alpha", "Haze strength (display)", 0.0, 1.0, 0.01, "Haze (fixed by DCS)"),
]
DEFAULTS = {k: lo for k, _l, lo, _h, _s, _g in SCALARS}
INT_KEYS = {"segments", "glow_n"}

NUM = r"(-?\d+(?:\.\d+)?)"
OVERRIDE = r"(?:engine == \d and -?\d+(?:\.\d+)? or )?"  # optional per-engine test value


def keep(m, value: float) -> str:
    """Group 1 + number, leaving the original text when the value is unchanged."""
    old = m.group(2)
    return m.group(1) + (old if abs(float(old) - value) < 1e-9 else fmt(value))


def fmt(value: float) -> str:
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


class Source:
    """Reads and rewrites the platypus block of the aircraft Lua."""

    def __init__(self, path: Path):
        self.path = path
        with path.open(encoding="utf-8", newline="") as handle:  # keep CRLF as is
            self.text = handle.read()
        self.values = self.parse()

    def _find(self, pattern: str, count: int):
        m = re.search(pattern, self.text)
        if not m:
            raise SystemExit(f"{self.path.name}: could not find pattern {pattern}")
        return [float(g) for g in m.groups()[:count]]

    def parse(self) -> dict:
        v = dict(DEFAULTS)
        inb = self._find(r"inboard = \{" + NUM + r", " + NUM + r", " + NUM + r"\}", 3)
        out = self._find(r"outboard = \{" + NUM + r", " + NUM + r", " + NUM + r"\}", 3)
        v.update(in_x=inb[0], in_y=inb[1], in_z=inb[2], out_x=out[0], out_y=out[1], out_z=out[2])
        v["segments"] = self._find(r"PLATYPUS_SEGMENTS = " + NUM, 1)[0]
        v["splay"] = self._find(r"PLATYPUS_SPLAY = math\.rad\(" + NUM + r"\)", 1)[0]
        v["nz_aft"] = self._find(r"/ PLATYPUS_SEGMENTS, side, " + NUM + r"\)", 1)[0]
        v["diameter"] = self._find(r"diameter = " + OVERRIDE + NUM, 1)[0]
        v["len_ab"] = self._find(r"exhaust_length_ab = " + OVERRIDE + NUM, 1)[0]
        v["len_ab_k"] = self._find(r"exhaust_length_ab_K = " + NUM, 1)[0]
        v["smoke"] = self._find(r"smokiness_level = " + NUM, 1)[0]
        ts = [float(x) for x in re.findall(NUM, re.search(r"ipairs\(\{([^}]*)\}\) do\s*\n\s*lights", self.text).group(1))]
        v["glow_n"], v["glow_t0"], v["glow_t1"] = len(ts), ts[0], ts[-1]
        v["glow_aft"] = self._find(r"platypus_point\(t, side, " + NUM + r"\)", 1)[0]
        c = self._find(r"color = \{" + NUM + r", " + NUM + r", " + NUM + r", " + NUM + r"\}", 4)
        v.update(glow_r=c[0], glow_g=c[1], glow_b=c[2], glow_a=c[3])
        v["glow_range"] = self._find(r"range = " + NUM, 1)[0]
        v.update(slot_h=0.10, haze_alpha=0.25)
        return v

    def lua_ts(self, v: dict) -> list:
        n = int(v["glow_n"])
        if n == 1:
            return [v["glow_t0"]]
        return [v["glow_t0"] + (v["glow_t1"] - v["glow_t0"]) * i / (n - 1) for i in range(n)]

    def save(self, v: dict):
        def sub(pattern, repl):
            new, n = re.subn(pattern, repl, self.text, count=1)
            if n != 1:
                raise ValueError(f"pattern not found: {pattern}")
            self.text = new

        f = fmt
        old = self.parse()

        def same(*keys):
            return all(abs(old[k] - v[k]) < 1e-9 for k in keys)

        if not same("in_x", "in_y", "in_z"):
            sub(r"inboard = \{[^}]*\}",
                f"inboard = {{{f(v['in_x'])}, {f(v['in_y'])}, {f(v['in_z'])}}}")
        if not same("out_x", "out_y", "out_z"):
            sub(r"outboard = \{[^}]*\}",
                f"outboard = {{{f(v['out_x'])}, {f(v['out_y'])}, {f(v['out_z'])}}}")
        sub(r"(PLATYPUS_SEGMENTS = )" + NUM, lambda m: keep(m, v["segments"]))
        sub(r"(PLATYPUS_SPLAY = math\.rad\()" + NUM, lambda m: keep(m, v["splay"]))
        sub(r"(/ PLATYPUS_SEGMENTS, side, )" + NUM, lambda m: keep(m, v["nz_aft"]))
        sub(r"(\bdiameter = " + OVERRIDE + r")" + NUM, lambda m: keep(m, v["diameter"]))
        sub(r"(exhaust_length_ab = " + OVERRIDE + r")" + NUM, lambda m: keep(m, v["len_ab"]))
        sub(r"(exhaust_length_ab_K = )" + NUM, lambda m: keep(m, v["len_ab_k"]))
        sub(r"(smokiness_level = )" + NUM, lambda m: keep(m, v["smoke"]))
        if not same("glow_n", "glow_t0", "glow_t1"):
            ts = ", ".join(f(t) for t in self.lua_ts(v))
            sub(r"(for _, t in ipairs\(\{)[^}]*(\}\))", lambda m: m.group(1) + ts + m.group(2))
        sub(r"(platypus_point\(t, side, )" + NUM, lambda m: keep(m, v["glow_aft"]))
        if not same("glow_r", "glow_g", "glow_b", "glow_a"):
            sub(r"color = \{[^}]*\}",
                f"color = {{{f(v['glow_r'])}, {f(v['glow_g'])}, {f(v['glow_b'])}, {f(v['glow_a'])}}}")
        sub(r"(\brange = )" + NUM, lambda m: keep(m, v["glow_range"]))
        with self.path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(self.text)


# ---- geometry, mirroring the Lua helpers
def point(v, t, side, aft):
    x = v["in_x"] + (v["out_x"] - v["in_x"]) * t - aft
    y = v["in_y"] + (v["out_y"] - v["in_y"]) * t
    z = side * (v["in_z"] + (v["out_z"] - v["in_z"]) * t)
    return x, y, z


def nozzles(v):
    n, out, splay = int(v["segments"]), [], math.radians(v["splay"])
    for engine, side in ((1, -1), (2, 1)):
        for i in range(1, n + 1):
            pos = point(v, (i - 0.5) / n, side, v["nz_aft"])
            ori = (math.cos(splay), 0.0, -side * math.sin(splay))
            out.append((engine, pos, ori))
    return out


def haze_polygon(v, p, o, vertical):
    """Tube from a nozzle: trailLength long and trailRadius either side of the flow
    line (sideways in plan, vertical in side and rear views). Both come from the
    stock DCS heat-trail config; that the radius is a half-width is assumed."""
    d = (-o[0], -o[1], -o[2])  # aft along the flow (o points up the exhaust)
    lat = (0.0, 1.0, 0.0) if vertical else (-d[2], 0.0, d[0])
    r = v["haze_radius"]
    end = [p[i] + d[i] * v["haze_throw"] for i in range(3)]
    return [tuple(p[i] + lat[i] * r for i in range(3)),
            tuple(end[i] + lat[i] * r for i in range(3)),
            tuple(end[i] - lat[i] * r for i in range(3)),
            tuple(p[i] - lat[i] * r for i in range(3))]


def glow(v, src):
    return [(engine, point(v, t, side, v["glow_aft"]))
            for engine, side in ((1, -1), (2, 1)) for t in src.lua_ts(v)]


class App:
    def __init__(self, root, src: Source, glow_level: float):
        self.root, self.src = root, src
        self.defaults = dict(src.values)
        self.vars, self.pending = {}, None
        self.ir, self.shimmer = load_ir(), load_shimmer()
        root.title("Platypus nozzle and glow viewer - " + src.path.name)
        root.configure(bg=BG)
        self._build_panel(glow_level)
        self._build_figure()
        self.redraw()

    def _build_panel(self, glow_level):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(side="left", fill="y")
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0, width=340)
        bar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        panel = tk.Frame(canvas, bg=BG, padx=8, pady=8)
        panel.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=panel, anchor="nw")
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side="left", fill="y")
        bar.pack(side="left", fill="y")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        ttk.Style().theme_use("clam")

        def heading(text):
            tk.Label(panel, text=text, bg=BG, fg=ACCENT, anchor="w",
                     font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(8, 0))

        def slider(label, var, lo, hi, step):
            row = tk.Frame(panel, bg=BG)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, bg=BG, fg=FG, width=20, anchor="w").pack(side="left")
            tk.Scale(row, variable=var, from_=lo, to=hi, resolution=step, orient="horizontal",
                     length=170, bg=BG, fg=FG, troughcolor=GRID, highlightthickness=0,
                     command=lambda _v: self.schedule()).pack(side="left")

        group = None
        for key, label, lo, hi, step, grp in SCALARS:
            if grp != group:
                heading(grp)
                group = grp
            if not lo <= self.src.values[key] <= hi:  # the slider would silently clamp it
                print(f"warning: {key} = {self.src.values[key]} is outside the slider range {lo} to {hi}")
            var = tk.DoubleVar(value=self.src.values[key])
            self.vars[key] = var
            slider(label, var, lo, hi, step)

        heading("Haze type")
        self.haze_mode = tk.StringVar(value="shimmer")
        for text, mode in (("Visible shimmer (hotAir)", "shimmer"),
                           ("Infrared, FLIR only (exhaustTrailFlir)", "ir")):
            tk.Radiobutton(panel, text=text, variable=self.haze_mode, value=mode,
                           command=self.schedule, bg=BG, fg=FG, selectcolor=GRID,
                           activebackground=BG, activeforeground=FG).pack(anchor="w")
        self.speed = tk.DoubleVar(value=0.0)
        slider("Aircraft speed (m/s)", self.speed, 0, 300, 1)

        heading("Display")
        self.glow_level = tk.DoubleVar(value=glow_level)
        slider("Glow draw argument", self.glow_level, 0, 1, 0.01)
        self.show_flame = tk.BooleanVar(value=True)
        tk.Checkbutton(panel, text="Show flame length", variable=self.show_flame,
                       command=self.schedule, bg=BG, fg=FG, selectcolor=GRID,
                       activebackground=BG, activeforeground=FG).pack(anchor="w")

        self.status = tk.Label(panel, text="", bg=BG, fg=FG, justify="left", anchor="w",
                               font=("Consolas", 9))
        self.status.pack(fill="x", pady=(10, 4))
        for text, cmd in (("Save Lua", self.save), ("Reload from disk", self.reload),
                          ("Reset to loaded values", self.reset)):
            ttk.Button(panel, text=text, command=cmd).pack(fill="x", pady=1)

    def _build_figure(self):
        self.fig = Figure(figsize=(11, 8), facecolor=BG)
        gs = self.fig.add_gridspec(2, 2, height_ratios=[1.3, 1], hspace=0.28, wspace=0.18,
                                   left=0.06, right=0.985, top=0.95, bottom=0.07)
        self.ax_plan = self.fig.add_subplot(gs[0, :])
        self.ax_side = self.fig.add_subplot(gs[1, 0])
        self.ax_rear = self.fig.add_subplot(gs[1, 1])
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

    # ---- state
    def values(self):
        v = {k: var.get() for k, var in self.vars.items()}
        for k in INT_KEYS:
            v[k] = int(round(v[k]))
        if self.haze_mode.get() == "ir":
            v.update(haze_mode="ir", haze_throw=self.ir["trailLength"],
                     haze_radius=self.ir["trailRadius"])
        else:
            s, speed = self.shimmer, self.speed.get()
            life = interp(s["life"], s["nozzle_speed"] + speed)
            along, size = shimmer_particle(s, speed, life)
            v.update(haze_mode="shimmer", haze_throw=along, haze_radius=size / 2,
                     haze_life=life, haze_speed=speed)
        return v

    def schedule(self):
        if self.pending is None:
            self.pending = self.root.after(30, self.redraw)

    def set_values(self, values):
        for k, var in self.vars.items():
            var.set(values[k])
        self.schedule()

    def reset(self):
        self.set_values(self.defaults)

    def reload(self):
        self.src = Source(self.src.path)
        self.defaults = dict(self.src.values)
        self.reset()

    def save(self):
        try:
            self.src.save(self.values())
        except (OSError, ValueError) as err:
            messagebox.showerror("Save Lua", str(err))
            return
        self.defaults = self.values()
        messagebox.showinfo("Save Lua", f"Wrote {self.src.path.name}")

    @staticmethod
    def validity(v) -> str:
        """Say whether the current settings are something the game has been compared to."""
        if v["haze_mode"] == "ir":
            return "NOT SEEN in normal view: infrared (FLIR) only"
        if v["haze_speed"] > 0:
            return "NOT VALID moving: game sends haze straight back"
        return "valid: ground idle (splay and nozzle count tested)"

    def gap_text(self, v, nz) -> str:
        """Where the left and right shimmer clouds first touch (shimmer mode)."""
        if v["haze_mode"] != "shimmer":
            return "shimmer gap  (shimmer mode only)"
        left = [n for n in nz if n[0] == 1]
        right = [n for n in nz if n[0] == 2]
        for step in range(1, 61):
            age = v["haze_life"] * step / 60
            along, size = shimmer_particle(self.shimmer, v["haze_speed"], age)

            def at(n):
                return (n[1][0] - n[2][0] * along, n[1][2] - n[2][2] * along)

            if min(math.dist(at(a), at(b)) for a in left for b in right) <= size:
                x = min(at(a)[0] for a in left)
                return f"shimmer gap  closes at age {age:.2f} s, about {abs(x):.0f} m aft of origin"
        return "shimmer gap  stays open for the whole life"

    # ---- drawing
    def _style(self, ax, title, xlabel, ylabel):
        ax.clear()
        ax.set_facecolor(BG)
        ax.set_title(title, color=FG, fontsize=10)
        ax.set_xlabel(xlabel, color=FG, fontsize=8)
        ax.set_ylabel(ylabel, color=FG, fontsize=8)
        ax.tick_params(colors=FG, labelsize=8)
        ax.grid(True, color=GRID, linewidth=0.5)
        ax.set_aspect("equal", adjustable="datalim")
        for s in ax.spines.values():
            s.set_color(GRID)

    def redraw(self):
        self.pending = None
        v = self.values()
        nz, gl = nozzles(v), glow(v, self.src)
        level = self.glow_level.get()
        colour = (v["glow_r"], v["glow_g"], v["glow_b"])
        alpha = max(0.0, min(1.0, v["glow_a"] * level * 3.0))  # x3: alpha 0.12 would be invisible
        edge = {1: LEFT_COL, 2: RIGHT_COL}

        # axes: (horizontal index, vertical index, flip)
        views = (
            (self.ax_plan, "Plan (nose up)", "z right (m)", "x forward (m)", 2, 0),
            (self.ax_side, "Side (nose left)", "x forward (m)", "y up (m)", 0, 1),
            (self.ax_rear, "Rear (looking forward)", "z right (m)", "y up (m)", 2, 1),
        )
        for ax, title, xl, yl, hi, vi in views:
            self._style(ax, title, xl, yl)
            if ax is self.ax_plan:
                # rough planform for scale: nose, wingtips (span 13.2 m), trailing edge
                # through the slot ends, tail. Not from the model, only for comparing sizes.
                half = [(13.4, 0.0), (-6.63, 6.6), (-3.19, 2.48), (-5.29, 0.66), (-5.9, 0.0)]
                zs = [-p[1] for p in reversed(half[1:])] + [p[1] for p in half]
                xs = [p[0] for p in reversed(half[1:])] + [p[0] for p in half]
                ax.plot(zs, xs, color="#56626e", linewidth=1.2, zorder=0.5)
            # slot centreline
            for side in (-1, 1):
                a, b = point(v, 0, side, 0), point(v, 1, side, 0)
                ax.plot([a[hi], b[hi]], [a[vi], b[vi]], color=GRID, linewidth=5,
                        solid_capstyle="round", zorder=1)
            # heat haze wedge per nozzle (assumed shape, see module docstring)
            if v["haze_mode"] == "ir":
                # One compound path with every tube wound the same way, so overlaps
                # fill evenly instead of stacking brighter.
                verts, codes = [], []
                for engine, p, o in nz:
                    pts = [(c[hi], c[vi]) for c in haze_polygon(v, p, o, vertical=(ax is not self.ax_plan))]
                    area = sum(pts[i][0] * pts[(i + 1) % 4][1] - pts[(i + 1) % 4][0] * pts[i][1]
                               for i in range(4))
                    if area < 0:
                        pts.reverse()
                    verts += pts + [pts[0]]
                    codes += [MplPath.MOVETO] + [MplPath.LINETO] * 3 + [MplPath.CLOSEPOLY]
                if verts:
                    ax.add_patch(PathPatch(MplPath(verts, codes), facecolor="#cfd8e0",
                                           edgecolor="#cfd8e0", linewidth=0.5,
                                           alpha=v["haze_alpha"] * 0.5, zorder=1.5))
            else:
                # shimmer particles at evenly spaced ages: centre moves along the flow,
                # circle is the billboard size, which grows quickly with age
                for engine, p, o in nz:
                    for k in range(7):
                        along, size = shimmer_particle(self.shimmer, v["haze_speed"],
                                                       v["haze_life"] * k / 6 + 1e-3)
                        ax.add_patch(Circle((p[hi] - o[hi] * along, p[vi] - o[vi] * along),
                                            size / 2, facecolor="#cfd8e0", edgecolor="#cfd8e0",
                                            linewidth=0.4,
                                            # the shader fades particles out over their life
                                            alpha=v["haze_alpha"] * 0.16 * (1 - k / 7),
                                            zorder=1.5))
            # glow
            for engine, p in gl:
                ax.add_patch(Circle((p[hi], p[vi]), v["glow_range"], facecolor=colour,
                                    alpha=alpha * 0.5, edgecolor="none", zorder=2))
                ax.plot(p[hi], p[vi], marker="*", color=colour, markersize=9,
                        markeredgecolor=FG, markeredgewidth=0.4, zorder=5)
            # nozzles
            for engine, p, o in nz:
                if self.show_flame.get():
                    ax.plot([p[hi], p[hi] - o[hi] * v["len_ab"]],
                            [p[vi], p[vi] - o[vi] * v["len_ab"]],
                            color=edge[engine], alpha=0.25, linewidth=1, zorder=3)
                ax.plot([p[hi], p[hi] - o[hi] * 0.6], [p[vi], p[vi] - o[vi] * 0.6],
                        color=edge[engine], linewidth=1.6, zorder=4)
                ax.add_patch(Circle((p[hi], p[vi]), v["diameter"] / 2, facecolor=edge[engine],
                                    edgecolor=FG, linewidth=0.4, zorder=6))
            ax.autoscale_view()
        # DCS x is forward, so aft is negative: plan plots x up, side plots nose to the left
        self.ax_side.invert_xaxis()

        slot_len = math.dist(point(v, 0, 1, 0), point(v, 1, 1, 0))
        n = v["segments"]
        ts = self.src.lua_ts(v)
        gap = slot_len * abs(ts[-1] - ts[0]) / (len(ts) - 1) if len(ts) > 1 else 0.0
        d_area = math.sqrt(4 * slot_len * v["slot_h"] / n / math.pi)
        self.status.config(text=(
            f"slot length  {slot_len:.2f} m\n"
            f"nozzles      {2 * n} ({n} per slot)\n"
            f"smoke total  {v['smoke'] * n:.3f} per engine\n"
            f"area-match d {d_area:.3f} m (slot h {v['slot_h']:.3f})\n"
            f"glow lights  {len(gl)}, strength {alpha:.2f}\n"
            f"haze {v['haze_mode']}: {v['haze_throw']:.1f} m long, "
            f"{'life %.1f s, ' % v['haze_life'] if v['haze_mode'] == 'shimmer' else ''}"
            f"end width {2 * v['haze_radius']:.1f} m\n"
            f"{self.gap_text(v, nz)}\n"
            f"{self.validity(v)}\n"
            f"light gap    {gap:.2f} m vs range {v['glow_range']:.2f} m "
            f"({'overlap' if gap <= 2 * v['glow_range'] else 'GAPS'})\n"
            f"glow t       {', '.join(fmt(t) for t in self.src.lua_ts(v))}"))
        self.canvas.draw_idle()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("lua", nargs="?", default=str(DEFAULT_LUA))
    parser.add_argument("--glow", type=float, default=1.0, help="initial glow draw argument 0-1")
    parser.add_argument("--haze", choices=("shimmer", "ir"), default="shimmer",
                        help="initial haze type")
    parser.add_argument("--speed", type=float, default=0.0, help="initial aircraft speed, m/s")
    parser.add_argument("--snapshot", help="save a PNG of the window and exit")
    args = parser.parse_args()

    src = Source(Path(args.lua))
    root = tk.Tk()
    root.geometry("1600x880")
    app = App(root, src, args.glow)
    app.haze_mode.set(args.haze)
    app.speed.set(args.speed)
    if args.snapshot:
        root.update()
        app.redraw()
        app.fig.savefig(args.snapshot, dpi=110, facecolor=BG)
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
