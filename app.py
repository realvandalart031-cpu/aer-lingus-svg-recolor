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

# Init palette in session state
if "palette" not in st.session_state:
    st.session_state.palette = dict(DEFAULT_PALETTE)

# Header
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("## ☘️")
with col_title:
    st.markdown("## Aer Lingus SVG Recolor Tool")
    st.caption("Automatically converts SVGs to the official brand colour palette")

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
