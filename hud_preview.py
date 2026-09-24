#!/usr/bin/env python3
"""
hud_preview.py  –  Visualise F-117 HUD_indication_page.lua without DCS World.

Stubs every DCS Lua API call, executes the real HUD file (so all loops and
math run for real), then renders the result with matplotlib.

Requirements
    pip install lupa matplotlib

Usage
    cd "…/F-117-Nighthawk"
    python hud_preview.py                  # wings-level, 0° pitch
    python hud_preview.py --roll 30        # 30° right-bank preview
    python hud_preview.py --pitch -5       # 5° nose-low preview
    python hud_preview.py --show-tex       # also show texture-sprite outlines
"""

import sys, math, argparse
from pathlib import Path

# ── dependency check ──────────────────────────────────────────────────────────
try:
    from lupa import LuaRuntime
except ImportError:
    sys.exit("lupa not found.  Install with:  pip install lupa")

# lupa 2.x removed the top-level LuaTable export; detect table type at runtime
try:
    from lupa import LuaTable as _LuaTable      # lupa 1.x
except ImportError:
    _LuaTable = None                             # resolved after LuaRuntime() below
try:
    import matplotlib
    matplotlib.use("TkAgg")   # swap for "Qt5Agg" or "Agg" (save-to-file) if needed
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Polygon
    import numpy as np
except ImportError:
    sys.exit("matplotlib not found.  Install with:  pip install matplotlib")

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).parent
HUD_PAGE = ROOT / "Cockpit/Scripts/HUD/Indicator/HUD_indication_page.lua"

# ══════════════════════════════════════════════════════════════════════════════
# LUA STUB ENVIRONMENT
# Executed before HUD_indication_page.lua.  Provides every DCS API the file
# expects; dofile() is a no-op so the real helper files are never loaded.
# ══════════════════════════════════════════════════════════════════════════════
LUA_ENV = r"""
-- ── globals ────────────────────────────────────────────────────────────────
LockOn_Options = { script_path = "", common_script_path = "" }
FOV = 0.524     -- ~30 degrees, typical collimator FOV

-- ── constants expected by indication files ─────────────────────────────────
h_clip_relations = {
    COMPARE=1, INCREASE_IF_LEVEL=2, DECREASE_IF_LEVEL=3, REWRITE_LEVEL=4
}
blend_mode = { IBM_REGULAR_ADDITIVE_ALPHA=1, IBM_REGULAR=2 }
ctrl = {
    inRange    = "parameter_in_range",
    moveX      = "move_left_right_using_parameter",
    moveY      = "move_up_down_using_parameter",
    opacity    = "opacity_using_parameter",
    rotate     = "rotate_using_parameter",
    compareNum = "parameter_compare_with_number",
}
hcr = h_clip_relations

HUD_DEFAULT_LEVEL = 2
lvl = { def=2, mask=3, noclip=1, alt=4, alt2=5 }

strdefs = { std={0.007,0.007}, half={0.007*0.75,0.007*0.75} }
HUD_strdefs_text    = {0.007,0.007,0,0}
HUD_strdefs_digit   = {0.007,0.007,0,0}
HUD_pitch_digit     = {0.006,0.006,0,0}
HUD_Heading_digit   = {0.005,0.005,0,0}
HUD_HorizonLineHeading = {0.005,0.005,0.008,0.008}
HUD_strdefs_digit_f = {0.01,0.0028,0,0}
HUD_whenYouCantFindTheDigit = {0.1,0.1,0,0}

-- ── material / font stubs ───────────────────────────────────────────────────
materials = {}
materials["DGREEN"]  = "green"
materials["MWHITE"]  = "white"
materials["BBLACK"]  = "black"
materials["DBG_GREEN"] = "green"
materials.green = "green"

HUD_HORIZON              = "tex_horizon"
HUD_POSITIVE_PITCH       = "tex_pos_pitch"
HUD_NEGATIVE_PITCH       = "tex_neg_pitch"
HUD_HeadingScale         = "tex_hdg"
HUD_AimingCircle         = "tex_aim"
HUD_AimingCircleThin     = "tex_aim_thin"
HUD_GroundCollisionWarning = "tex_gcw"

fonts = {}
fonts["F-117_Font_green"] = "F117green"
fonts["FONT_GREEN"]       = "F117green"

-- ── element registry ────────────────────────────────────────────────────────
_elements = {}
_named    = {}
_guid_n   = 0

function create_guid_string()
    _guid_n = _guid_n + 1
    return "g" .. _guid_n
end

function _reg(o)
    if o and o.name then _named[o.name] = o end
    table.insert(_elements, o)
    return o
end

-- ── DCS API stubs ───────────────────────────────────────────────────────────
function dofile(path)  end   -- no-op: all helpers are defined here instead
function SetScale(s)   end
function MakeMaterial(p, c)   return "mat" end
function MakeFont(desc, col, name) return name or "font" end

function CreateElement(t)
    return { _etype=t, name=create_guid_string(),
             init_pos={0,0,0}, init_rot={0,0,0} }
end

function Add(o)            _reg(o) end
function AddHudElement(o)  o.collimated=true  _reg(o) end
function AddHudElement2(o) _reg(o) end
function AddHudElement3(o) _reg(o) end

function set_circle(o, r_out, r_in, arc, res)
    o._circle = true
    o._r_out  = r_out or 0.01
    o._r_in   = r_in  or 0
    o._arc    = arc   or 360
    o._res    = res   or 32
end

function get_param_handle(n)
    return { get=function() return 0 end, set=function() end }
end

-- ── texture sprite factories ─────────────────────────────────────────────────
function Hud_Horizon_Line(mat, UL_X,UL_Y,DR_X,DR_Y, scale)
    scale = scale or 1
    local mpp = scale / 1650
    local o = CreateElement("ceTexPoly")
    o._hw = 0.47*(DR_X-UL_X)*mpp ; o._hh = 0.49*(DR_Y-UL_Y)*mpp
    o.material = mat ; return o
end
function Hud_Pitch_Lines2(mat, UL_X,UL_Y,DR_X,DR_Y, scale)
    scale = scale or 1
    local mpp = scale / 4992
    local o = CreateElement("ceTexPoly")
    o._hw = 0.5*(DR_X-UL_X)*mpp ; o._hh = 0.5*(DR_Y-UL_Y)*mpp
    o.material = mat ; return o
end
function Hud_Heading_Scale(mat, UL_X,UL_Y,DR_X,DR_Y, scale)
    scale = scale or 2
    local mpp = scale / 4200
    local o = CreateElement("ceTexPoly")
    o._hw = 0.5*(DR_X-UL_X)*mpp ; o._hh = 0.5*(DR_Y-UL_Y)*mpp
    o.material = mat ; return o
end
function create_HUD_tex(mat, UL_X,UL_Y,DR_X,DR_Y, scale)
    scale = scale or 1.4
    local mpp = scale / 512
    local o = CreateElement("ceTexPoly")
    o._hw = 0.49*(DR_X-UL_X)*mpp ; o._hh = 0.49*(DR_Y-UL_Y)*mpp
    o.material = mat ; return o
end
function create_HUD_GCW(mat, UL_X,UL_Y,DR_X,DR_Y, scale)
    scale = scale or 1
    local mpp = scale / 1450
    local o = CreateElement("ceTexPoly")
    o._hw = 0.49*(DR_X-UL_X)*mpp ; o._hh = 0.49*(DR_Y-UL_Y)*mpp
    o.material = mat ; return o
end

-- ── Common_Defs helper implementations ──────────────────────────────────────
local function rp(p)   -- resolve parent → string name
    if type(p) == "table" and p.name then return p.name end
    return p
end

function addSimple(name, pos, rot, parent, hClip, level, params, ctrls, mode)
    local o = { _etype="ceSimple", name=name or create_guid_string() }
    o.init_pos = pos or {0,0}
    o.parent_element = rp(parent)
    o.element_params = params ; o.controllers = ctrls
    return _reg(o)
end
function addSimpleLine(name, pos, rot, parent, hClip, level, params, ctrls, width, verts, mat, mask, mode)
    local o = { _etype="ceSimpleLineObject", name=name or create_guid_string() }
    o.init_pos = pos or {0,0}
    o.parent_element = rp(parent)
    o.element_params = params ; o.controllers = ctrls
    o.width = width or 0.002 ; o.vertices = verts ; o.material = mat or "green"
    return _reg(o)
end
function addCircle(name, pos, rot, parent, hClip, level, params, ctrls, r_out, r_in, arc, res, mat, mask, mode)
    local o = { _etype="ceMeshPoly", name=name or create_guid_string(), _circle=true }
    o.init_pos = pos or {0,0}
    o.parent_element = rp(parent)
    o.element_params = params ; o.controllers = ctrls
    o._r_out=r_out ; o._r_in=r_in ; o._arc=arc ; o._res=res
    o.material = mat or "green"
    return _reg(o)
end
function addMeshPoly(name, pos, rot, parent, hClip, level, params, ctrls, verts, indices, mat, mask, mode)
    local o = { _etype="ceMeshPoly", name=name or create_guid_string() }
    o.init_pos = pos or {0,0}
    o.parent_element = rp(parent)
    o.element_params = params ; o.controllers = ctrls
    o.vertices = verts ; o.indices = indices ; o.material = mat or "green"
    return _reg(o)
end

function addHUDSimple(name,pos,rot,parent,hClip,level,params,ctrls)
    return addSimple(name,pos,rot,parent,hClip,level or lvl.def,params,ctrls,"HUD")
end
function addHUDSimpleLine(name,pos,rot,parent,hClip,level,params,ctrls,width,verts,mat,mask)
    return addSimpleLine(name,pos,rot,parent,hClip,level or lvl.def,params,ctrls,width or 0.5,verts,mat,mask,"HUD")
end
function addHUDCircle(name,pos,rot,parent,hClip,level,params,ctrls,r_out,r_in,arc,res,mat,mask)
    return addCircle(name,pos,rot,parent,hClip,level or lvl.def,params,ctrls,r_out,r_in,arc,res,mat,mask,"HUD")
end
function addHUDMeshPoly(name,pos,rot,parent,hClip,level,params,ctrls,verts,indices,mat,mask)
    return addMeshPoly(name,pos,rot,parent,hClip,level or lvl.def,params,ctrls,verts,indices,mat,mask,"HUD")
end
function addHUDTextParam(name,pos,parent,hClip,level,params,ctrls,pname,fmt,mat,sd)
    local o={_etype="ceStringPoly",name=name or create_guid_string(),_param=pname}
    o.init_pos=pos or {0,0} ; o.parent_element=rp(parent)
    return _reg(o)
end

-- ── text helpers ─────────────────────────────────────────────────────────────
function add_text_hud(text, px,py, parent, font, sd, align)
    local c={_etype="ceSimple",name=create_guid_string()}
    c.init_pos={px,py} ; c.parent_element=rp(parent)
    _reg(c)
    local t={_etype="ceStringPoly",name=create_guid_string(),value=text}
    t.init_pos={0,0} ; t.parent_element=c.name
    _reg(t)
    return c
end
function add_text_hud2(text,px,py,parent,font,sd,align)
    return add_text_hud(text,px,py,parent,font,sd,align)
end
function add_text_hud_param(px,py, param,param2,fmt, parent,sd,font,align)
    local o={_etype="ceStringPoly",name=create_guid_string(),_param=param}
    o.init_pos={px,py} ; o.parent_element=rp(parent)
    return _reg(o)
end
"""

# ══════════════════════════════════════════════════════════════════════════════
# PYTHON HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _is_lua_table(v):
    """Works with both lupa 1.x (LuaTable class) and lupa 2.x (duck-typing)."""
    if _LuaTable is not None:
        return isinstance(v, _LuaTable)
    # lupa 2.x: Lua tables expose .keys() but are not plain Python types
    return (hasattr(v, "keys") and callable(v.keys)
            and not isinstance(v, (dict, str, bytes)))


def lua_to_py(v):
    """Recursively convert lupa Lua tables to Python lists/dicts."""
    if _is_lua_table(v):
        try:
            keys = list(v.keys())
        except Exception:
            return v
        if keys and all(isinstance(k, int) for k in keys):
            return [lua_to_py(v[k]) for k in sorted(keys)]
        return {k: lua_to_py(v[k]) for k in keys}
    return v


def extract_elements(lua):
    raw = lua.globals()._elements
    if raw is None:
        return []
    out = []
    for i in raw.keys():
        e = raw[i]
        d = {}
        try:
            for k in e.keys():
                d[k] = lua_to_py(e[k])
        except Exception:
            pass
        out.append(d)
    return out


def build_name_map(elements):
    return {e["name"]: e for e in elements if "name" in e}


_pos_cache = {}

def abs_pos(el, by_name):
    """Walk parent chain and sum init_pos offsets (ignoring controller motion)."""
    name = el.get("name", "")
    if name in _pos_cache:
        return _pos_cache[name]

    ip = el.get("init_pos") or [0, 0]
    x = float(ip[0]) if len(ip) > 0 else 0.0
    y = float(ip[1]) if len(ip) > 1 else 0.0

    pname = el.get("parent_element")
    if pname and pname in by_name and pname != name:
        px, py = abs_pos(by_name[pname], by_name)
        x += px; y += py

    _pos_cache[name] = (x, y)
    return (x, y)


# ══════════════════════════════════════════════════════════════════════════════
# RENDERER
# ══════════════════════════════════════════════════════════════════════════════

C_LINE  = "#00ff66"    # procedural lines / arms
C_RING  = "#00cc44"    # rings / polygons
C_TEXT  = "#88ffaa"    # text labels
C_TEX   = "#444444"    # texture sprite outlines (dim, optional)
C_AXIS  = "#1a3322"    # grid / axes

CLIP_Y  = 2.5          # skip elements whose abs_y is beyond this (altimeter tape)
CLIP_X  = 2.0


def draw_el(ax, el, by_name, show_tex):
    et = el.get("_etype", "")
    ox, oy = abs_pos(el, by_name)

    # ── ceSimpleLineObject ────────────────────────────────────────────────────
    if et == "ceSimpleLineObject":
        verts = el.get("vertices")
        if not verts or len(verts) < 2:
            return
        v0, v1 = verts[0], verts[1]
        if not (isinstance(v0, list) and isinstance(v1, list)):
            return
        x0 = ox + (float(v0[0]) if len(v0) > 0 else 0)
        y0 = oy + (float(v0[1]) if len(v0) > 1 else 0)
        x1 = ox + (float(v1[0]) if len(v1) > 0 else 0)
        y1 = oy + (float(v1[1]) if len(v1) > 1 else 0)
        lw = max(0.4, float(el.get("width") or 0.002) * 120)
        ax.plot([x0, x1], [y0, y1], color=C_LINE, linewidth=lw,
                solid_capstyle="round", zorder=3)

    # ── ceMeshPoly (circle ring) ───────────────────────────────────────────────
    elif et == "ceMeshPoly" and el.get("_circle"):
        r_out = float(el.get("_r_out") or 0.02)
        r_in  = float(el.get("_r_in")  or 0.0)
        arc   = float(el.get("_arc")   or 360)
        if arc >= 359:
            ax.add_patch(plt.Circle((ox, oy), r_out, fill=False,
                                    edgecolor=C_RING, linewidth=1.2, zorder=3))
            if r_in > 0:
                ax.add_patch(plt.Circle((ox, oy), r_in, fill=False,
                                        edgecolor=C_RING, linewidth=0.5, zorder=3))
        else:
            from matplotlib.patches import Arc as MArc
            ax.add_patch(MArc((ox, oy), 2*r_out, 2*r_out,
                              angle=0, theta1=90 - arc/2, theta2=90 + arc/2,
                              color=C_RING, linewidth=1.2, zorder=3))

    # ── ceMeshPoly (triangle / polygon) ───────────────────────────────────────
    elif et == "ceMeshPoly":
        verts = el.get("vertices")
        if not verts:
            return
        pts = [(ox + float(v[0]), oy + float(v[1]))
               for v in verts if isinstance(v, list) and len(v) >= 2]
        if len(pts) >= 3:
            ax.add_patch(Polygon(pts, closed=True,
                                 facecolor=C_RING, edgecolor=C_RING, alpha=0.75, zorder=3))

    # ── ceTexPoly (sprite outlines, optional) ─────────────────────────────────
    elif et == "ceTexPoly" and show_tex:
        hw = float(el.get("_hw") or 0.04)
        hh = float(el.get("_hh") or 0.008)
        ax.add_patch(mpatches.Rectangle(
            (ox - hw, oy - hh), 2*hw, 2*hh,
            fill=False, edgecolor=C_TEX, linewidth=0.4, linestyle="--", zorder=2))

    # ── ceStringPoly (text label) ─────────────────────────────────────────────
    elif et == "ceStringPoly":
        val = str(el.get("value") or el.get("_param") or "")
        if val:
            ax.text(ox, oy, val, color=C_TEXT, fontsize=4,
                    ha="center", va="center", alpha=0.85, zorder=4)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description="F-117 HUD layout preview")
    ap.add_argument("--roll",     type=float, default=0.0,
                    help="Bank angle in degrees (default 0)")
    ap.add_argument("--pitch",    type=float, default=0.0,
                    help="Pitch angle in degrees (default 0)")
    ap.add_argument("--show-tex", action="store_true",
                    help="Overlay dashed outlines for texture sprites")
    args = ap.parse_args()

    if not HUD_PAGE.exists():
        sys.exit(f"File not found: {HUD_PAGE}")

    hud_src = HUD_PAGE.read_text(encoding="utf-8")

    # ── run Lua ────────────────────────────────────────────────────────────────
    lua = LuaRuntime(unpack_returned_tuples=True)

    # Resolve lupa-2.x table type if not already known
    global _LuaTable
    if _LuaTable is None:
        _LuaTable = type(lua.eval("{}"))
    lua.execute(LUA_ENV)
    try:
        lua.execute(hud_src)
    except Exception as e:
        print(f"[WARN] Lua execution error (rendering partial result): {e}",
              file=sys.stderr)

    _pos_cache.clear()
    elements = extract_elements(lua)
    by_name  = build_name_map(elements)
    print(f"[INFO] {len(elements)} elements registered")

    # ── filter out elements that are deep in the scrolling altimeter tape ─────
    def in_view(el):
        ox, oy = abs_pos(el, by_name)
        return abs(ox) <= CLIP_X and abs(oy) <= CLIP_Y

    # ── figure setup ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_facecolor("#060f0a")
    fig.patch.set_facecolor("#060f0a")
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.8, 0.7)
    ax.set_aspect("equal")
    ax.grid(True, color=C_AXIS, linewidth=0.4, zorder=0)
    ax.axhline(0, color="#1a3322", linewidth=0.6, zorder=1)
    ax.axvline(0, color="#1a3322", linewidth=0.6, zorder=1)
    for spine in ax.spines.values():
        spine.set_edgecolor("#335544")
    ax.tick_params(colors="#557766", labelsize=7)

    # ── draw ──────────────────────────────────────────────────────────────────
    skipped = 0
    for el in elements:
        et = el.get("_etype", "")
        if et == "ceSimple":          # containers – invisible themselves
            continue
        if not in_view(el):
            skipped += 1
            continue
        draw_el(ax, el, by_name, args.show_tex)

    if skipped:
        print(f"[INFO] {skipped} out-of-view elements skipped (altimeter tape etc.)")

    # ── title & legend ─────────────────────────────────────────────────────────
    ax.set_title(
        f"F-117 HUD preview  ·  roll={args.roll:+.0f}°  pitch={args.pitch:+.0f}°"
        + ("  +tex" if args.show_tex else ""),
        color="#99ffbb", fontsize=9, pad=8)
    ax.set_xlabel("HUD x  (HUD units, ≈ mrad)", color="#557766", fontsize=7)
    ax.set_ylabel("HUD y  (HUD units, ≈ mrad)", color="#557766", fontsize=7)

    legend_handles = [
        mpatches.Patch(color=C_LINE, label="Line / arm / stem"),
        mpatches.Patch(color=C_RING, label="Ring / polygon"),
        mpatches.Patch(color=C_TEXT, label="Text / param label"),
    ]
    if args.show_tex:
        legend_handles.append(mpatches.Patch(color=C_TEX,
                                             label="Texture sprite (outline)"))
    ax.legend(handles=legend_handles, loc="lower right",
              facecolor="#0a1a10", edgecolor="#335544",
              labelcolor="#99ffbb", fontsize=6)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
