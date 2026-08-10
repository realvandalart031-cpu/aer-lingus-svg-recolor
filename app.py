import streamlit as st
import xml.etree.ElementTree as ET
import re
import math
import io

# ─── Default Palette ──────────────────────────────────────────────────────────

DEFAULT_PALETTE = {
    "Aer Lingus Teal":   "#006272",
    "Deep Teal":         "#083D4B",
    "Shamrock Green":    "#84BD00",
    "Black":             "#050606",
    "Pure White":        "#FFFFFF",
    "Cloud Grey":        "#E8E8E8",
    "Bear — Body":       "#DDA152",
    "Bear — Muzzle":     "#FAE8C8",
    "Bear — Ears/Feet":  "#BE813A",
    "Bear — Nose":       "#67401C",
    "Bear — Buttons":    "#94A8AD",
}

LOGO_B64 = "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c3ZnIGlkPSJMYXllcl8xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0NDAuMyA4Mi41Ij48ZGVmcz48c3R5bGU+LmNscy0xe2ZpbGw6I2ZmZjt9LmNscy0ye2ZpbGw6Izg0YmQwMDt9LmNscy0ze2ZpbGw6IzQ4YTIzZjt9PC9zdHlsZT48L2RlZnM+PHBhdGggY2xhc3M9ImNscy0xIiBkPSJtMjcuNjgsMTYuODNoLTcuNjNMMCw2My43N2g3Ljg5bDUuMTEtMTEuOTNoMjEuNzRsNS4xMSwxMS45M2g3Ljg5TDI3LjY4LDE2LjgzWm0tMTIuMDMsMjguNTRsOC4xNy0xOS4xNyw4LjE3LDE5LjE3SDE1LjY1WiIvPjxwYXRoIGNsYXNzPSJjbHMtMSIgZD0ibTEwNi44MywyNi44NGMtNC44NCwwLTguODkuOTQtMTEuNjEsMi44Ny00LjA0LDIuODYtNS42NCw3LjItNS42NCwxMi44djIxLjI3aDcuMzR2LTIxLjYyYzAtMi42NS41MS00LjU0LDEuNDUtNS44OSwxLjY5LTIuNDQsNC43Ny0zLjA5LDguNjktMy4wOCwxLjgzLDAsMy45Mi4yMyw1Ljk3LjYybDEuNDctNi4xOGMtMi4yNy0uNDYtNC44NS0uNzctNy42Ny0uNzdaIi8+PHBhdGggY2xhc3M9ImNscy0xIiBkPSJtODMuMiw0Mi4wNmMtLjg3LTkuOTgtNi44Mi0xNS4yMy0xNy4zNi0xNS4yMy0xMS40MywwLTE3LjQ4LDYuMTgtMTcuNDgsMTcuODZ2MS44NWMwLDExLjY5LDYuNjgsMTcuODYsMTkuMzEsMTcuODYsNS4xNCwwLDEwLjAzLS43NiwxNC4xOC0yLjE5bC0xLjU0LTYuMTctLjMzLjEzYy0yLjQuOTEtNi44OSwxLjg5LTEyLjMxLDEuODlzLTExLjU3LTEuNjctMTEuNzItOS41M2gyNy4zNnYtMy44NGMwLS45MS0uMDQtMS43OS0uMTEtMi42M1ptLTE3LjM2LTguODljNC4zOCwwLDkuNTcsMS41Nyw5Ljk1LDguODloLTE5LjgyYy4zLTUuODIsMy43LTguODksOS44Ny04Ljg5WiIvPjxwYXRoIGNsYXNzPSJjbHMtMSIgZD0ibTI0OC44MSw1Ny40N2M1Ljc5LTIuOTIsNy44OC04Ljg3LDcuODktMTMuNjIsMC01LjMyLTEuNjMtOS41Mi00Ljc1LTEyLjU5LS4yNy0uMjctLjU2LS41Mi0uODYtLjc3bDQuOTgtOC4zMmgtNy4zOGwtMy4xOCw1LjMxYy0yLjQyLS44MS00Ljk5LTEuMTktNy4zMS0xLjE5LTQuNjQsMC05LjI3LDEuNjYtMTIuNjksNC41NC0yLjcxLDIuMjktNS45NSw2LjQxLTUuOTUsMTMuMDEsMCwxMS40Niw4LjYyLDE0LjI3LDE2Ljk2LDE2Ljk4bDQuNjQsMS40NmM0Ljk1LDEuNDgsNy45NCwyLjM3LDcuOTQsNi4yNiwwLDEuNzgtLjYzLDMuMjgtMS44OCw0LjQ3LTEuOTQsMS44NC01LjMyLDIuODItOS4wNCwyLjYyLTMuMjctLjE3LTEwLjIxLS44NS0xMS4wNi03Ljk4aC03LjE0YzAsOS4xLDguMTIsMTQuODMsMTguMiwxNC44Myw2LjQ3LDAsMTEuMjctMS44NCwxNC40Ny00LjkzLDIuNTItMi40NCwzLjg1LTUuNTgsMy44NS05LjA4LDAtNS4wMS0yLjcyLTguODktNy42OC0xMS4wMVptLTEuMTYtNi42NWMtMS4yMSwyLjAyLTMuMzUsNC4wMy02LjAzLDQuNjIsMCwwLTUuMDMtMS40Mi04LjMyLTIuNTYtNC40Mi0xLjUzLTYuNDgtNC40LTYuNDgtOS4wMywwLTcuMzUsNS45LTEwLjY5LDExLjM3LTEwLjY5czExLjMsMy40MSwxMS4zLDEwLjY3YzAsMi45NC0uNzIsNS4xMy0xLjg0LDYuOTlaIi8+PHBvbHlnb24gY2xhc3M9ImNscy0xIiBwb2ludHM9IjE2NC44IDYzLjc3IDE3Mi4xNCA2My43NyAxNzIuMTQgNTcuMzQgMTcyLjE0IDI3LjQ4IDE2NC44IDI3LjQ4IDE2NC44IDYzLjc3Ii8+PHBhdGggY2xhc3M9ImNscy0xIiBkPSJtMTY0LjM2LDE4LjQxYzAtMi4zLDEuNTEtMy45NCw0LjE0LTMuOTRzNC4wOCwxLjY0LDQuMDgsMy45NGMwLDIuNDMtMS41MSw0LjA4LTQuMDgsNC4wOHMtNC4xNC0xLjY0LTQuMTQtNC4wOFoiLz48cG9seWdvbiBjbGFzcz0iY2xzLTEiIHBvaW50cz0iMTM2LjMyIDE2LjgzIDEyOC41OCAxNi44MyAxMjguNTggNjMuNzcgMTYwLjM0IDYzLjc3IDE2MC4zNCA1Ny4yOSAxMzYuMzIgNTcuMjkgMTM2LjMyIDE2LjgzIi8+PHBhdGggY2xhc3M9ImNscy0xIiBkPSJtMzA4LjQzLDI4LjFjLTMuOTEsMS43NC02LjA3LDQuOS02LjI0LDguNTEtLjM5LDguNTEsNi4xLDEwLjUsMTQuODIsMTEuNzEsNi45NS45NywxMC45MSwyLDEwLjc1LDUuNDgtLjA1LDEuMDYtLjkzLDIuMzgtMi4yMSwzLjAyLTQuNjcsMi4zMy0xNi41MiwxLjA5LTIyLjExLTIuMzVsLTEuNTMsNi4xOWMzLjM3LDIuMTcsOC40MSwzLjQ1LDEzLjIxLDMuNjcsNS4yMS4yNSwxMC40Ni0uMTEsMTQuMjUtMS45NCwzLjctMS43OSw1LjYyLTUuMDgsNS43OS04LjYuMzgtOC4zMy03LjQtMTAuMTUtMTQuNjgtMTEuNDItOC4yOS0xLjQ0LTExLjI5LTIuMjgtMTEuMDctNS44Ni4xLTEuNywxLjY1LTIuNzYsMi45LTMuMTUsNC41LTEuMzksMTQuMDEtLjQ4LDE5LjU2LDIuNThsMS40Ny02LjI1Yy03LjI5LTMuNjItMTguMjYtNC41NC0yNC45MS0xLjU5WiIvPjxwYXRoIGNsYXNzPSJjbHMtMSIgZD0ibTE5Ni41NiwyNi44NGMtOC4wNiwwLTEzLjQ4LDEuMTctMTUuOTksMS44NmwtLjI5LjA4djM0Ljk5aDcuNDJ2LTI5LjgzYzIuNTMtLjU5LDQuNS0uNzcsOC40Ni0uNzcsNi4wOCwwLDEwLjEzLDEuNTMsMTAuMTMsOC45N3YyMS42Mmg3LjM0di0yMS4yN2MwLTEwLjM5LTUuNzUtMTUuNjYtMTcuMDgtMTUuNjZaIi8+PHBhdGggY2xhc3M9ImNscy0xIiBkPSJtMjg3Ljk4LDU3LjM3Yy0yLjM5LjUyLTQuNTguNy04LjQ2LjctNi4yNiwwLTEwLjEzLTEuNDktMTAuMTMtOC45di0yMS43aC03LjM0djIxLjM0YzAsMTAuMzUsNS43NSwxNS41OSwxNy4wOCwxNS41OSw3LjU4LDAsMTIuMzMtLjk0LDE1Ljk4LTEuODZsLjMtLjA4VjI3LjQ4aC03LjQydjI5Ljg5WiIvPjxwYXRoIGNsYXNzPSJjbHMtMiIgZD0ibTQzOS44Myw0My4zNmMtMS42LDUuMTEtNi44OCw5LjkxLTEzLjIyLDEwLjg4LDEuMDEsMS41NywxLjUsMy41NCwxLjI1LDUuNzMtLjY4LDUuOTMtNi4zNiwxMC42OS0xMi40MiwxMC43My00LjExLjAzLTkuNjctMS43NS0xMy42MS03LjkzLTMuNTEtNS41MS00LjAzLTE0LjI1LTMuNzYtMTYuOTEtNC4zLDQuNC02Ljk3LDguNjUtOC4yMywxMS42Mi0yLjg2LDYuNy0zLjk1LDE0Ljg1LTMuODksMTguNjYsMCwwLS41MS40OS0xLjAyLjU5LTEuNTktLjI4LTIuOTYtLjg3LTQtMS43OC0xLjI2LTEuMTEtMS41My0yLjE4LTEuNTMtMi4xOCwxLjg5LTkuNDgsNC45MS0xNS40MSw5LjQyLTIyLjE3LDYuMDgtOS4xMSwxNS40NS0xNC43NiwyNi41NS0xOC4xNSw4LjAzLTIuNDUsMTYuMzctMi45OCwyMi4xMSwxLjg3LDMuMDksMi42LDMuMjcsNi4yNywyLjM3LDkuMDRabS00Ny4yOS01LjA0Yy0xLjkxLDMuMTctNy4wOCw4LjI3LTExLjIsMTAuOTEtOC41Niw1LjQ4LTE0LjcyLDUuODQtMTcuODEsMy44OC0uMzYtLjIzLS42OC0uNDgtLjk1LS43Ny0yLjQxLTIuNTEtMi03LjAxLjgtMTAuNjgsMS4zOC0xLjgyLDMuMTMtMy4wOCw0Ljg3LTMuNjYtMS4zMy0uNjMtMi4yNC0xLjk0LTIuNDMtMy43OC0uMzctMy42OCwyLjQtOC41MSw2LjIyLTEwLjQ1LDMuMzctMS43MiwxMC42LTMuNDIsMTUuOTIsNC41MywyLjA3LDMuMDksMy45NSw3LjQ5LDQuNTgsMTAuMDNoMFptMzUuMTUtMzMuMzVjLS40Ni00LjU3LTUuMzUtNi4yNi0xMC43NC0zLjk1LTIuNTYsMS4xLTQuOCwyLjkyLTYuMzksNSwuMjYtMi4wOC0uMzMtMy45MS0xLjg0LTUuMDEtMi45Ny0yLjE1LTguMzItLjU1LTEyLDMuNDQtMS4yOCwxLjM5LTUuNDYsNi40NS01LjY4LDEzLjg0LS4xMSwzLjU3LDEuNDksMTEuNTIsNi43MywxN2gwYzEzLjk1LTUuMjcsMjEuNDUtMTMuMzMsMjQuMjktMTYuNjUsMy4zLTMuODUsNC43MS03LjI2LDUuMjgtOS43NC40Ni0xLjk4LjM5LTMuMzguMzQtMy45M1oiLz48cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Im00MzkuODMsNDMuMzZjLjIyLS42Ny4zNy0xLjM5LjQ0LTIuMTQtLjQ1LDIuOTYtMi40Miw2LjUzLTUuNTksOC41LTIuODEsMS43NC02LjA1LDIuOS05LjcxLDIuNTguNTguNTcsMS4wNywxLjAyLDEuNjQsMS45NGgwczAsMCwwLDBjNi4zNS0uOTYsMTEuNjItNS43NywxMy4yMi0xMC44OFoiLz48cGF0aCBjbGFzcz0iY2xzLTMiIGQ9Im00MjIuMDgsMTguNjVjMy4zLTMuODUsNC43MS03LjI2LDUuMjgtOS43NC4wMy0uMTMuMDYtLjI2LjA5LS4zOS0uNjksMi43Ny02LjUyLDkuOTItMTQuNjIsMTYuMDMtOC4zOSw2LjMzLTEzLjIsOS41LTE1LjAzLDEwLjc1LDEzLjk0LTUuMjcsMjEuNDQtMTMuMzIsMjQuMjgtMTYuNjRaIi8+PHBhdGggY2xhc3M9ImNscy0zIiBkPSJtMzgxLjM0LDQ5LjI0YzQuMTItMi42NCw5LjI5LTcuNzQsMTEuMi0xMC45MWgwYy0zLjY5LDMuNDgtOS4wOSw4LjY5LTE4LjM5LDEyLjc5LTQuNjEsMS45Ni05LjExLDIuNzEtMTAuNjIsMi4wMSwzLjA4LDEuOTUsOS4yNCwxLjU5LDE3LjgxLTMuODhaIi8+PHBhdGggY2xhc3M9ImNscy0zIiBkPSJtMzk4Ljg2LDQwLjMxYy05Ljk4LDcuMTctMTMuMzgsMjAuMDMtMTMuOTQsMzYuNDNoMGMuNS0uMTEsMS4wMi0uNTksMS4wMi0uNTktLjA2LTMuODEsMS4wMy0xMS45NiwzLjg5LTE4LjY2LDEuMjctMi45NywzLjk0LTcuMjIsOC4yMy0xMS42Mi4zMi0yLjkyLjY0LTQuNjQuODgtNS42MS0uMDIuMDItLjA1LjAzLS4wNy4wNVoiLz48L3N2Zz4="

MIN_AREA = 5.0
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

# ─── Color math ───────────────────────────────────────────────────────────────

def hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_lab(rgb):
    r, g, b = [x / 255.0 for x in rgb]
    def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = lin(r), lin(g), lin(b)
    x = (r * 0.4124564 + g * 0.3575761 + b * 0.1804375) / 0.95047
    y = (r * 0.2126729 + g * 0.7151522 + b * 0.0721750)
    z = (r * 0.0193339 + g * 0.1191920 + b * 0.9503041) / 1.08883
    def f(t): return t ** (1/3) if t > 0.008856 else 7.787 * t + 16/116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)

def delta_e(lab1, lab2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))

def build_palette_lab(palette):
    lab = {}
    for name, hex_val in palette.items():
        try:
            lab[name] = rgb_to_lab(hex_to_rgb(hex_val))
        except Exception:
            pass
    return lab

def nearest_brand_color(hex_color, palette, palette_lab):
    try:
        rgb = hex_to_rgb(hex_color)
        lab = rgb_to_lab(rgb)
    except Exception:
        return None, None

    r, g, b = rgb

    # Green override: G dominant and not teal/cyan
    if g > r + 10 and g > b + 10 and g > 80 and b < 120:
        for name, val in palette.items():
            if "green" in name.lower() or "shamrock" in name.lower():
                return val, name
        # fallback: pick greenest palette color
        green_name = min(palette_lab, key=lambda n: delta_e(lab, palette_lab[n]))
        return palette[green_name], green_name

    # Blue override: medium saturated blues → teal
    is_very_light = r > 150 and g > 150 and b > 150
    if not is_very_light and b > r + 30 and b > 100:
        for name, val in palette.items():
            if "teal" in name.lower() and "deep" not in name.lower():
                return val, name

    best = min(palette_lab, key=lambda n: delta_e(lab, palette_lab[n]))

    # Muzzle check: only warm beige (R >> B) qualifies
    if "muzzle" in best.lower() and (r - b) < 35:
        grey_candidates = [n for n in palette_lab if "grey" in n.lower() or "gray" in n.lower() or "white" in n.lower()]
        if grey_candidates:
            best = min(grey_candidates, key=lambda n: delta_e(lab, palette_lab[n]))

    return palette[best], best

# ─── SVG processing ───────────────────────────────────────────────────────────

def parse_style_block(style_text):
    classes = {}
    for m in re.finditer(r'\.([\w-]+)\s*\{([^}]*)\}', style_text):
        name = m.group(1)
        props = {}
        for part in m.group(2).split(";"):
            part = part.strip()
            if ":" in part:
                k, _, v = part.partition(":")
                props[k.strip()] = v.strip()
        classes[name] = props
    return classes

def build_style_block(classes):
    lines = []
    for name, props in classes.items():
        body = "; ".join(f"{k}: {v}" for k, v in props.items())
        lines.append(f"      .{name} {{\n        {body}\n      }}")
    return "\n\n".join(lines)

def estimate_bbox_area(d_attr):
    if not d_attr:
        return float("inf")
    nums = re.findall(r"[-+]?\d*\.?\d+", d_attr)
    if len(nums) < 4:
        return 0
    fs = [float(n) for n in nums]
    xs, ys = fs[0::2], fs[1::2]
    if not xs or not ys:
        return 0
    return (max(xs) - min(xs)) * (max(ys) - min(ys))

def process_svg_bytes(svg_bytes, min_area, palette, palette_lab):
    tree = ET.parse(io.BytesIO(svg_bytes))
    root = tree.getroot()

    style_elem = root.find(f".//{{{SVG_NS}}}style")
    color_map = {}
    merged_count = 0

    if style_elem is not None:
        classes = parse_style_block(style_elem.text or "")

        for cls_name, props in classes.items():
            fill = props.get("fill")
            if not fill or fill.lower() in ("none", "transparent") or not fill.startswith("#"):
                continue
            if fill not in color_map:
                brand_hex, brand_name = nearest_brand_color(fill, palette, palette_lab)
                color_map[fill] = (brand_hex, brand_name)
            props["fill"] = color_map[fill][0]

        hex_to_canonical = {}
        class_alias = {}
        for cls_name, props in classes.items():
            fill = props.get("fill")
            if not fill:
                continue
            if fill not in hex_to_canonical:
                hex_to_canonical[fill] = cls_name
            else:
                class_alias[cls_name] = hex_to_canonical[fill]

        for dup_cls in class_alias:
            if dup_cls in classes:
                del classes[dup_cls]
                merged_count += 1

        style_elem.text = "\n" + build_style_block(classes) + "\n    "

        for elem in root.iter():
            cls_attr = elem.get("class", "")
            if not cls_attr:
                continue
            cls_list = cls_attr.split()
            new_cls = [class_alias.get(c, c) for c in cls_list]
            seen = set()
            deduped = [c for c in new_cls if not (c in seen or seen.add(c))]
            elem.set("class", " ".join(deduped))

    shape_tags = {f"{{{SVG_NS}}}{t}" for t in ("path", "rect", "circle", "ellipse", "polygon")}
    removed = 0
    def remove_small(parent):
        nonlocal removed
        for child in [c for c in list(parent) if c.tag in shape_tags and estimate_bbox_area(c.get("d", "")) < min_area]:
            parent.remove(child)
            removed += 1
        for child in parent:
            remove_small(child)

    remove_small(root)

    out = io.StringIO()
    tree.write(out, xml_declaration=True, encoding="unicode")
    return out.getvalue(), color_map, merged_count, removed

# ─── UI ───────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Aer Lingus — SVG Recolor",
    page_icon="☘️",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stBottom"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
.viewerBadge_container__1QSob { display: none !important; }
.styles_viewerBadge__1yB5_ { display: none !important; }
</style>
""", unsafe_allow_html=True)

# Init palette in session state
if "palette" not in st.session_state:
    st.session_state.palette = dict(DEFAULT_PALETTE)

# Header
st.markdown(f"""
<div style="background:#006272;padding:20px 28px;border-radius:8px;margin-bottom:20px">
  <img src="data:image/svg+xml;base64,{LOGO_B64}" style="height:44px;display:block">
  <p style="color:rgba(255,255,255,0.8);margin:8px 0 0 0;font-size:13px">
    Automatically converts SVGs to the official brand colour palette
  </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ─── Sidebar — palette editor ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎨 Active Palette")
    st.caption("Colours applied to the SVG")

    palette = st.session_state.palette
    to_delete = None

    for name in list(palette.keys()):
        hex_val = palette[name]
        col_swatch, col_name, col_hex, col_del = st.columns([1, 3, 3, 1])
        with col_swatch:
            st.markdown(
                f'<div style="width:24px;height:24px;border-radius:4px;'
                f'background:{hex_val};border:1px solid #555;margin-top:8px"></div>',
                unsafe_allow_html=True,
            )
        with col_name:
            new_name = st.text_input("Name", value=name, key=f"name_{name}", label_visibility="collapsed")
        with col_hex:
            new_hex = st.text_input("Hex", value=hex_val, key=f"hex_{name}", label_visibility="collapsed")
            if not new_hex.startswith("#"):
                new_hex = "#" + new_hex
        with col_del:
            if st.button("✕", key=f"del_{name}", help="Remove colour"):
                to_delete = name

        # Apply rename/recolor
        if new_name != name or new_hex != hex_val:
            palette[new_name] = new_hex
            if new_name != name:
                del palette[name]

    if to_delete and to_delete in palette:
        del palette[to_delete]
        st.rerun()

    st.divider()

    # Add new colour
    st.markdown("**Add colour**")
    col_new_name, col_new_hex = st.columns([3, 3])
    with col_new_name:
        new_color_name = st.text_input("Name", placeholder="e.g. Sky Blue", key="new_name", label_visibility="collapsed")
    with col_new_hex:
        new_color_hex = st.text_input("Hex", placeholder="#4A90D9", key="new_hex", label_visibility="collapsed")
    if st.button("+ Add", use_container_width=True):
        if new_color_name and new_color_hex:
            if not new_color_hex.startswith("#"):
                new_color_hex = "#" + new_color_hex
            palette[new_color_name] = new_color_hex
            st.rerun()

    if st.button("↺ Reset to defaults", use_container_width=True):
        st.session_state.palette = dict(DEFAULT_PALETTE)
        st.rerun()

    st.divider()
    min_area = st.slider("Remove paths smaller than (area)", 0, 100, 5,
                         help="Paths below this bounding-box area are deleted")

# ─── Main ─────────────────────────────────────────────────────────────────────

active_palette = st.session_state.palette
active_palette_lab = build_palette_lab(active_palette)

uploaded = st.file_uploader(
    "Drag and drop your SVG here, or click to browse",
    type=["svg"],
    accept_multiple_files=True,
)

if uploaded:
    for file in uploaded:
        st.markdown(f"#### `{file.name}`")
        svg_bytes = file.read()

        with st.spinner("Processing…"):
            result_svg, color_map, merged, removed = process_svg_bytes(
                svg_bytes, min_area, active_palette, active_palette_lab
            )

        c1, c2, c3 = st.columns(3)
        c1.metric("Colours remapped", len(color_map))
        c2.metric("Classes merged", merged)
        c3.metric("Paths removed", removed)

        out_name = file.name.replace(".svg", "_recolored.svg")
        st.download_button(
            label=f"⬇️ Download {out_name}",
            data=result_svg.encode("utf-8"),
            file_name=out_name,
            mime="image/svg+xml",
            type="primary",
        )

        with st.expander("View colour mapping"):
            rows = [
                {"Original": orig, "→ Brand": brand_hex, "Colour name": brand_name}
                for orig, (brand_hex, brand_name) in color_map.items()
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

        st.divider()

else:
    st.info("Upload one or more SVG files to get started.")
    st.markdown("""
**How it works:**
1. Upload an SVG exported from Illustrator via Image Trace
2. Every colour is mapped to the closest colour in the Aer Lingus palette using perceptual Delta E matching
3. Download the recoloured SVG with noise paths removed

**Tip:** Edit, add, or remove colours in the sidebar before processing.
    """)
