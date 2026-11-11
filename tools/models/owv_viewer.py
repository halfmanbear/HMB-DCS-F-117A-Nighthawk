"""Interactive viewer for the overwing vapour effect.

Loads Effects/f-117-nighthawk_overwingVapor.lua and the .owv it names, then
lets you change the preset values with sliders, drag the OpacityOverPower
curve, and see the result as plan and side views of the spawn points plus
graphs. "Save Lua" writes the values back into the Lua file, keeping its
comments.

    python tools/models/owv_viewer.py [effect.lua] [--owv file.owv]
        [--power 0.12] [--snapshot out.png]

Needs Python with tkinter, numpy and matplotlib.

What the preview does and does not know:
* Slice choice follows the .owv layout: the first slice whose threshold is at
  or above the vapour power is drawn, and its opacity is scaled by
  count / last count.
* Particle size is ParticleSize * (1 + age * ScaleOverAgeFactor), from the
  comment in the Lua file. Ages are random.
* Per-particle opacity is OpacityMax * curve(power) * slice factor * point
  weight. The point weight factor and the aft drift of VaporLengthMax are
  assumptions for a rough look, not confirmed behaviour.
* AoA to vapour power uses the rough values noted in the Lua comment
  (about 0.05 below 7 deg, 0.12 at 12 deg). Edit AOA_POWER to change it.
"""

from __future__ import annotations

import argparse
import re
import struct
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
import numpy as np
from matplotlib.collections import EllipseCollection
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

MOD = Path(__file__).resolve().parents[2]
DEFAULT_LUA = MOD / "Effects" / "f-117-nighthawk_overwingVapor.lua"

AOA_POWER = [(0.0, 0.05), (7.0, 0.05), (12.0, 0.12)]
AOA_MAX = 12.0

INT_KEYS = {"ParticlesCount"}

# key, min, max, step
SCALARS = [
    ("ParticlesCount", 10, 1000, 10),
    ("ParticleSize", 0.2, 10.0, 0.05),
    ("ScaleOverAgeFactor", 0.0, 5.0, 0.05),
    ("VaporLengthMax", 0.0, 10.0, 0.05),
    ("AlbedoSRGB", 0.0, 1.0, 0.01),
    ("OpacityMax", 0.0, 1.0, 0.01),
]

BG = "#14181d"
FG = "#d8dde3"
GRID = "#2b323a"
ACCENT = "#4ea8de"
WARM = "#f2a65a"


# ---------------------------------------------------------------- .owv

_PREFIX = struct.Struct("<4s9fII")
_ENTRY = struct.Struct("<If")
_POINT = struct.Struct("<7f")


class Owv:
    """Points (n x 7: x y z nx ny nz weight) and the slice counts."""

    def __init__(self, path: Path):
        data = path.read_bytes()
        magic, *floats, _tables, length = _PREFIX.unpack_from(data, 0)
        if magic != b"owv\x00":
            raise ValueError("not an .owv file")
        base = _PREFIX.size
        self.counts = [
            _ENTRY.unpack_from(data, base + i * _ENTRY.size)[0] for i in range(length)
        ]
        start = base + length * _ENTRY.size
        self.points = np.frombuffer(data, dtype="<f4", offset=start).reshape(-1, 7)
        if sum(self.counts) != len(self.points):
            raise ValueError("slice counts do not add up to the point count")
        self.edges = np.concatenate([[0], np.cumsum(self.counts)])

    def thresholds(self):
        n = len(self.counts)
        first = 0.5 / n
        return [first + i * (1.0 - first) / (n - 1) for i in range(n)]

    def slice_index(self, power: float) -> int:
        for i, t in enumerate(self.thresholds()):
            if power <= t:
                return i
        return len(self.counts) - 1

    def slice_points(self, index: int):
        return self.points[self.edges[index] : self.edges[index + 1]]


# ---------------------------------------------------------------- Lua

_NUM = r"-?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?"
_CURVE_BLOCK = re.compile(r"(OpacityOverPower\s*=\s*\{)(.*?)(\n[ \t]*\})", re.S)
_PAIR = re.compile(r"\{\s*(" + _NUM + r")\s*,\s*(" + _NUM + r")\s*\}")


def fmt(value: float) -> str:
    text = f"{value:.4f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


class Preset:
    def __init__(self, path: Path):
        self.path = path
        self.load()

    def load(self):
        self.text = self.path.read_text(encoding="utf-8")
        self.values = {}
        for key, *_ in SCALARS:
            m = re.search(r"^[ \t]*" + key + r"\s*=\s*(" + _NUM + r")", self.text, re.M)
            if m:
                self.values[key] = float(m.group(1))
        m = re.search(r'SpawnLocationsFile\s*=\s*"([^"]+)"', self.text)
        self.owv_name = m.group(1) if m else None
        block = _CURVE_BLOCK.search(self.text)
        self.curve = (
            [[float(a), float(b)] for a, b in _PAIR.findall(block.group(2))]
            if block
            else [[0.0, 0.0], [1.0, 1.0]]
        )

    def save(self, values: dict, curve: list):
        text = self.text
        for key, value in values.items():
            if abs(value - self.values.get(key, float("nan"))) < 1e-9:
                continue  # unchanged: keep the file's own formatting
            shown = str(int(round(value))) if key in INT_KEYS else fmt(value)
            text, n = re.subn(
                r"(^[ \t]*" + key + r"\s*=\s*)" + _NUM,
                lambda m: m.group(1) + shown,
                text,
                count=1,
                flags=re.M,
            )
            if not n:
                raise ValueError(f"{key} not found in {self.path.name}")
        block = _CURVE_BLOCK.search(text)
        if not block:
            raise ValueError("OpacityOverPower block not found")
        if curve != self.curve:
            first = re.search(r"\n([ \t]*)\{", block.group(2))
            indent = first.group(1) if first else "    "
            body = "".join(f"\n{indent}{{{fmt(x)}, {fmt(y)}}}," for x, y in curve)
            text = text[: block.start(2)] + body + text[block.end(2) :]
        self.path.write_text(text, encoding="utf-8", newline="")
        self.text = text
        self.values.update(values)
        self.curve = [list(p) for p in curve]


def interp_curve(curve, power):
    xs = [p[0] for p in curve]
    ys = [p[1] for p in curve]
    return float(np.interp(power, xs, ys))


def aoa_to_power(aoa):
    return float(np.interp(aoa, [a for a, _ in AOA_POWER], [p for _, p in AOA_POWER]))


# ---------------------------------------------------------------- app


class App:
    def __init__(self, root, preset: Preset, owv_path: Path | None, power=None):
        self.root = root
        self.preset = preset
        self.owv_path = owv_path
        self.owv = Owv(owv_path) if owv_path else None
        self.defaults = dict(preset.values)
        self.default_curve = [list(p) for p in preset.curve]
        self.curve = [list(p) for p in preset.curve]
        self.vars = {}
        self.drag = None
        self.seed = 1
        self.pending = None

        root.title("Overwing vapour viewer - " + preset.path.name)
        root.configure(bg=BG)
        self._build_panel()
        self._build_figure()
        start = power if power is not None else aoa_to_power(10.0)
        self.power_var.set(start)
        self.redraw()

    # ---- UI
    def _build_panel(self):
        panel = tk.Frame(self.root, bg=BG, padx=8, pady=8)
        panel.pack(side="left", fill="y")
        style = ttk.Style()
        style.theme_use("clam")

        def slider(label, var, lo, hi, step, command=None):
            row = tk.Frame(panel, bg=BG)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, bg=BG, fg=FG, width=20, anchor="w").pack(side="left")
            s = tk.Scale(
                row, variable=var, from_=lo, to=hi, resolution=step,
                orient="horizontal", length=210, bg=BG, fg=FG,
                troughcolor=GRID, highlightthickness=0,
                command=lambda _v: (command or self.schedule)(),
            )
            s.pack(side="left")
            return s

        tk.Label(panel, text="Preset values", bg=BG, fg=ACCENT, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x")
        for key, lo, hi, step in SCALARS:
            v = tk.DoubleVar(value=self.preset.values.get(key, lo))
            self.vars[key] = v
            slider(key, v, lo, hi, step)

        tk.Label(panel, text="Flight condition", bg=BG, fg=ACCENT, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(10, 0))
        self.aoa_var = tk.DoubleVar(value=10.0)
        self.power_var = tk.DoubleVar(value=0.1)
        slider("AoA (deg, approx)", self.aoa_var, 0, AOA_MAX, 0.1, self.on_aoa)
        slider("Vapour power", self.power_var, 0, 1, 0.005, self.on_power)

        tk.Label(panel, text="Display", bg=BG, fg=ACCENT, anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", pady=(10, 0))
        self.preview_scale = tk.DoubleVar(value=0.4)
        slider("Preview size x (not saved)", self.preview_scale, 0.05, 1.5, 0.05)
        self.show_all = tk.BooleanVar(value=True)
        self.show_drift = tk.BooleanVar(value=False)
        for text, var in (("Show all spawn points (faint)", self.show_all),
                          ("Show aft drift (assumed)", self.show_drift)):
            tk.Checkbutton(panel, text=text, variable=var, command=self.schedule,
                           bg=BG, fg=FG, selectcolor=GRID, activebackground=BG,
                           activeforeground=FG).pack(anchor="w")

        self.status = tk.Label(panel, text="", bg=BG, fg=FG, justify="left",
                               anchor="w", font=("Consolas", 9))
        self.status.pack(fill="x", pady=(10, 4))

        for text, cmd in (("Resample particles", self.resample),
                          ("Save Lua", self.save),
                          ("Reload from disk", self.reload),
                          ("Reset to loaded values", self.reset),
                          ("Open .owv...", self.open_owv)):
            ttk.Button(panel, text=text, command=cmd).pack(fill="x", pady=1)

        tk.Label(panel, text="Curve: drag points, double-click to add,\nright-click to delete.",
                 bg=BG, fg="#8a939c", justify="left", anchor="w").pack(fill="x", pady=(8, 0))

    def _build_figure(self):
        self.fig = Figure(figsize=(11, 8), facecolor=BG)
        gs = self.fig.add_gridspec(2, 4, height_ratios=[1.5, 1], hspace=0.38, wspace=0.42,
                                   left=0.05, right=0.985, top=0.95, bottom=0.08)
        self.ax_plan = self.fig.add_subplot(gs[0, 0:2])
        self.ax_side = self.fig.add_subplot(gs[0, 2:4])
        self.ax_curve = self.fig.add_subplot(gs[1, 0])
        self.ax_age = self.fig.add_subplot(gs[1, 1])
        self.ax_slice = self.fig.add_subplot(gs[1, 2])
        self.ax_aoa = self.fig.add_subplot(gs[1, 3])
        for ax in self.fig.axes:
            ax.set_facecolor(BG)
            ax.tick_params(colors=FG, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(GRID)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side="right", fill="both", expand=True)
        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.canvas.mpl_connect("button_release_event", self.on_release)

    # ---- events
    def on_aoa(self):
        self.power_var.set(round(aoa_to_power(self.aoa_var.get()), 4))
        self.schedule()

    def on_power(self):
        self.schedule()

    def schedule(self):
        if self.pending is None:
            self.pending = self.root.after(30, self.redraw)

    def resample(self):
        self.seed += 1
        self.schedule()

    def values(self):
        return {k: self.vars[k].get() for k, *_ in SCALARS}

    def save(self):
        try:
            vals = self.values()
            vals["ParticlesCount"] = int(vals["ParticlesCount"])
            self.preset.save(vals, sorted(self.curve))
        except Exception as exc:  # shown to the user
            messagebox.showerror("Save failed", str(exc))
            return
        self.defaults = dict(self.values())
        self.default_curve = [list(p) for p in self.curve]
        self.status_extra = f"Saved {self.preset.path.name}"
        self.redraw()

    def reload(self):
        self.preset.load()
        self.reset(from_preset=True)

    def reset(self, from_preset=False):
        if from_preset:
            self.defaults = dict(self.preset.values)
            self.default_curve = [list(p) for p in self.preset.curve]
        for key, v in self.defaults.items():
            self.vars[key].set(v)
        self.curve = [list(p) for p in self.default_curve]
        if self.owv_path and self.owv_path.exists():
            self.owv = Owv(self.owv_path)
        self.redraw()

    def open_owv(self):
        name = filedialog.askopenfilename(filetypes=[("Overwing vapour", "*.owv")],
                                          initialdir=str(MOD / "Shapes"))
        if name:
            self.owv_path = Path(name)
            self.owv = Owv(self.owv_path)
            self.redraw()

    # curve dragging
    def _nearest(self, event):
        best, bi = 0.04, None
        for i, (x, y) in enumerate(self.curve):
            d = np.hypot(x - event.xdata, (y - event.ydata) * 0.6)
            if d < best:
                best, bi = d, i
        return bi

    def on_press(self, event):
        if event.inaxes is not self.ax_curve or event.xdata is None:
            return
        i = self._nearest(event)
        if event.button == 3:
            if i is not None and 0 < i < len(self.curve) - 1:
                del self.curve[i]
                self.redraw()
        elif event.button == 1:
            if event.dblclick and i is None:
                self.curve.append([float(np.clip(event.xdata, 0, 1)),
                                   float(np.clip(event.ydata, 0, 1))])
                self.curve.sort()
                self.redraw()
            elif i is not None:
                self.drag = i

    def on_motion(self, event):
        if self.drag is None or event.inaxes is not self.ax_curve or event.xdata is None:
            return
        i = self.drag
        last = len(self.curve) - 1
        if 0 < i < last:
            lo, hi = self.curve[i - 1][0] + 0.001, self.curve[i + 1][0] - 0.001
            self.curve[i][0] = float(np.clip(event.xdata, lo, hi))
        self.curve[i][1] = float(np.clip(event.ydata, 0, 1))
        self.schedule()

    def on_release(self, _event):
        self.drag = None

    # ---- drawing
    def sample(self, pts, count):
        rng = np.random.default_rng(self.seed)
        n = len(pts)
        if n == 0:
            return pts[:0], np.zeros(0)
        w = np.clip(pts[:, 6], 0.02, None)
        idx = rng.choice(n, size=min(count, n), replace=False, p=w / w.sum())
        return pts[idx], rng.random(len(idx))

    def redraw(self):
        self.pending = None
        vals = self.values()
        power = self.power_var.get()
        curve = sorted(self.curve)
        curve_op = interp_curve(curve, power)
        size, grow = vals["ParticleSize"], vals["ScaleOverAgeFactor"]
        drift_len = vals["VaporLengthMax"]
        base = vals["OpacityMax"] * curve_op
        grey = vals["AlbedoSRGB"]

        info = ["No .owv loaded"]
        for ax in (self.ax_plan, self.ax_side):
            ax.clear()
        if self.owv is not None:
            si = self.owv.slice_index(power)
            pts = self.owv.slice_points(si)
            last = max(self.owv.counts[-1], 1)
            factor = self.owv.counts[si] / last
            chosen, age = self.sample(pts, int(vals["ParticlesCount"]))
            diam = size * (1 + age * grow) * self.preview_scale.get()
            x = chosen[:, 0] - (drift_len * age if self.show_drift.get() else 0)
            y, z = chosen[:, 1], chosen[:, 2]
            alpha = np.clip(base * factor * chosen[:, 6], 0, 1) if len(chosen) else age
            colors = np.zeros((len(chosen), 4))
            colors[:, :3] = grey
            colors[:, 3] = alpha
            allp = self.owv.points
            for ax, h, v, hl, vl in (
                (self.ax_plan, z, x, "z (right)", "x (forward)"),
                (self.ax_side, x, y, "x (forward)", "y (up)"),
            ):
                if self.show_all.get():
                    ah = allp[:, 2] if ax is self.ax_plan else allp[:, 0]
                    av = allp[:, 0] if ax is self.ax_plan else allp[:, 1]
                    ax.plot(ah, av, ",", color="#3a434d", alpha=0.6)
                if len(chosen):
                    ax.add_collection(EllipseCollection(
                        diam, diam, 0, units="xy", offsets=np.column_stack([h, v]),
                        offset_transform=ax.transData, facecolors=colors, edgecolors="none"))
                ax.set_aspect("equal", adjustable="box")
                ax.set_xlabel(hl, color=FG, fontsize=8)
                ax.set_ylabel(vl, color=FG, fontsize=8)
                ax.grid(color=GRID, lw=0.5)
            self.ax_plan.set_title("Plan view (meters)", color=FG, fontsize=9)
            self.ax_side.set_title("Side view (meters)", color=FG, fontsize=9)
            if len(allp):
                self.ax_plan.set_xlim(allp[:, 2].min() - 3, allp[:, 2].max() + 3)
                self.ax_plan.set_ylim(allp[:, 0].min() - 3, allp[:, 0].max() + 3)
                self.ax_side.set_xlim(allp[:, 0].min() - 3, allp[:, 0].max() + 3)
                self.ax_side.set_ylim(allp[:, 1].min() - 2, allp[:, 1].max() + 2)
            mean_a = float(alpha.mean()) if len(chosen) else 0.0
            info = [
                f"slice {si} of {len(self.owv.counts)}  (<= {self.owv.thresholds()[si]:.3f})",
                f"points in slice  {self.owv.counts[si]}",
                f"slice factor     {factor:.2f}",
                f"drawn particles  {len(chosen)}",
                f"mean opacity     {mean_a:.3f}",
            ]
        else:
            for ax in (self.ax_plan, self.ax_side):
                ax.set_title("No .owv loaded", color=FG, fontsize=9)
        info.insert(0, f"power {power:.3f}  curve {curve_op:.3f}  x OpacityMax {base:.3f}")
        extra = getattr(self, "status_extra", "")
        if extra:
            info.append(extra)
            self.status_extra = ""
        self.status.config(text="\n".join(info))
        self.draw_graphs(vals, curve, power, curve_op)
        self.canvas.draw_idle()

    def draw_graphs(self, vals, curve, power, curve_op):
        # opacity over power
        ax = self.ax_curve
        ax.clear()
        cx, cy = zip(*curve)
        grid = np.linspace(0, 1, 200)
        ax.plot(grid, np.interp(grid, cx, cy), color=ACCENT, lw=1.6)
        ax.plot(cx, cy, "o", color=ACCENT, ms=7)
        ax.axvline(power, color=WARM, lw=1)
        ax.plot([power], [curve_op], "o", color=WARM)
        if self.owv is not None:
            for t in self.owv.thresholds():
                ax.axvline(t, color=GRID, lw=0.5, zorder=0)
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.03, 1.05)
        ax.set_title("OpacityOverPower (drag points)", color=FG, fontsize=9)
        ax.set_xlabel("vapour power (lines: slice thresholds)", color=FG, fontsize=8)
        ax.set_ylabel("curve value", color=FG, fontsize=8)
        ax.grid(color=GRID, lw=0.5)

        # size and drift over age
        ax = self.ax_age
        ax.clear()
        age = np.linspace(0, 1, 50)
        ax.plot(age, vals["ParticleSize"] * (1 + age * vals["ScaleOverAgeFactor"]),
                color=ACCENT, label="diameter")
        ax.plot(age, vals["VaporLengthMax"] * age, color=WARM, ls="--",
                label="aft drift (assumed)")
        ax.set_title("Size over age", color=FG, fontsize=9)
        ax.set_xlabel("normalized age", color=FG, fontsize=8)
        ax.set_ylabel("meters", color=FG, fontsize=8)
        ax.grid(color=GRID, lw=0.5)
        ax.set_ylim(bottom=0)
        ax.legend(fontsize=7, facecolor=BG, labelcolor=FG, edgecolor=GRID)

        # slices
        ax = self.ax_slice
        ax.clear()
        if self.owv is not None:
            n = len(self.owv.counts)
            si = self.owv.slice_index(power)
            colors = [WARM if i == si else ACCENT for i in range(n)]
            ax.bar(range(n), self.owv.counts, color=colors)
            ax.set_xticks(range(n))
            ax.set_xticklabels([f"{t:.2f}" for t in self.owv.thresholds()],
                               rotation=60, fontsize=7)
            ax.set_ylabel("points", color=FG, fontsize=8)
            ax.set_xlabel("slice threshold (power)", color=FG, fontsize=8)
        ax.set_title("Points per slice", color=FG, fontsize=9)
        ax.grid(color=GRID, lw=0.5, axis="y")

        # opacity against AoA
        self._aoa_graph(vals, curve)

    def _aoa_graph(self, vals, curve):
        ax = self.ax_aoa
        ax.clear()
        aoa = np.linspace(0, AOA_MAX, 100)
        op = [vals["OpacityMax"] * interp_curve(curve, aoa_to_power(a)) for a in aoa]
        ax.plot(aoa, op, color=ACCENT)
        ax.axvline(self.aoa_var.get(), color=WARM, lw=1)
        ax.set_ylim(-0.02, 1.0)
        ax.set_title("Opacity vs AoA (approx)", color=FG, fontsize=9)
        ax.set_xlabel("AoA (deg)", color=FG, fontsize=8)
        ax.set_ylabel("OpacityMax x curve", color=FG, fontsize=8)
        ax.grid(color=GRID, lw=0.5)


def resolve_owv(preset: Preset, override):
    if override:
        return Path(override)
    if preset.owv_name:
        for folder in (preset.path.parents[1] / "Shapes", preset.path.parent):
            candidate = folder / preset.owv_name
            if candidate.exists():
                return candidate
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("lua", nargs="?", default=str(DEFAULT_LUA))
    parser.add_argument("--owv")
    parser.add_argument("--power", type=float)
    parser.add_argument("--snapshot", help="save a PNG of the window and exit")
    args = parser.parse_args()

    preset = Preset(Path(args.lua))
    root = tk.Tk()
    root.geometry("1500x860")
    app = App(root, preset, resolve_owv(preset, args.owv), args.power)
    if args.snapshot:
        root.update()
        app.redraw()
        app.fig.savefig(args.snapshot, dpi=110, facecolor=BG)
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
