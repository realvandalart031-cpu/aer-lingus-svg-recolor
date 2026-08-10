import streamlit as st
import xml.etree.ElementTree as ET
import re
import math
import os
import io

# ─── Paleta Aer Lingus + Ursinho ─────────────────────────────────────────────

BRAND_PALETTE = {
    "aer-lingus-teal":  "#006272",
    "deep-teal":        "#083D4B",
    "shamrock-green":   "#84BD00",
    "black":            "#050606",
    "pure-white":       "#FFFFFF",
    "cloud-grey":       "#E8E8E8",
    "bear-body":        "#DDA152",
    "bear-muzzle":      "#FAE8C8",
    "bear-ears-feet":   "#BE813A",
    "bear-nose":        "#67401C",
    "bear-buttons":     "#94A8AD",
}

PALETTE_LABELS = {
    "aer-lingus-teal":  "Aer Lingus Teal",
    "deep-teal":        "Deep Teal",
    "shamrock-green":   "Shamrock Green",
    "black":            "Black",
    "pure-white":       "Pure White",
    "cloud-grey":       "Cloud Grey",
    "bear-body":        "Bear — Corpo",
    "bear-muzzle":      "Bear — Focinho",
    "bear-ears-feet":   "Bear — Orelhas/Pés",
    "bear-nose":        "Bear — Nariz",
    "bear-buttons":     "Bear — Botões",
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

PALETTE_LAB = {name: rgb_to_lab(hex_to_rgb(h)) for name, h in BRAND_PALETTE.items()}

def nearest_brand_color(hex_color, palette_lab, palette):
    try:
        rgb = hex_to_rgb(hex_color)
        lab = rgb_to_lab(rgb)
    except Exception:
        return None, None

    r, g, b = rgb

    # Override: verdes (G dominante, não é turquesa)
    if g > r + 10 and g > b + 10 and g > 80 and b < 120:
        return palette["shamrock-green"], "shamrock-green"

    # Override: azuis médios saturados → teal
    is_very_light = r > 150 and g > 150 and b > 150
    if not is_very_light and b > r + 30 and b > 100:
        return palette["aer-lingus-teal"], "aer-lingus-teal"

    best = min(palette_lab, key=lambda n: delta_e(lab, palette_lab[n]))

    # Bear-muzzle só para beges quentes (R >> B)
    if best == "bear-muzzle" and (r - b) < 35:
        best = "cloud-grey"

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

def process_svg_bytes(svg_bytes, min_area, active_palette, active_palette_lab):
    tree = ET.parse(io.BytesIO(svg_bytes))
    root = tree.getroot()

    style_elem = root.find(f".//{{{SVG_NS}}}style")
    color_map = {}
    merged_count = 0

    if style_elem is not None:
        original_style = style_elem.text or ""
        classes = parse_style_block(original_style)

        for cls_name, props in classes.items():
            fill = props.get("fill")
            if not fill or fill.lower() in ("none", "transparent") or not fill.startswith("#"):
                continue
            if fill not in color_map:
                brand_hex, brand_name = nearest_brand_color(fill, active_palette_lab, active_palette)
                color_map[fill] = (brand_hex, brand_name)
            brand_hex, _ = color_map[fill]
            props["fill"] = brand_hex

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
        to_remove = []
        for child in list(parent):
            if child.tag in shape_tags:
                if estimate_bbox_area(child.get("d", "")) < min_area:
                    to_remove.append(child)
            else:
                remove_small(child)
        for el in to_remove:
            parent.remove(el)
            removed += 1

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

# Header
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("## ☘️")
with col_title:
    st.markdown("## Aer Lingus SVG Recolor Tool")
    st.caption("Converte automaticamente SVGs para a paleta oficial da marca")

st.divider()

# Sidebar — paleta
with st.sidebar:
    st.markdown("### 🎨 Paleta ativa")
    st.caption("Cores que serão aplicadas ao SVG")

    active_palette = {}
    active_palette_lab = {}

    for key, hex_val in BRAND_PALETTE.items():
        label = PALETTE_LABELS[key]
        col_swatch, col_info = st.columns([1, 4])
        with col_swatch:
            st.markdown(
                f'<div style="width:28px;height:28px;border-radius:4px;'
                f'background:{hex_val};border:1px solid #ccc;margin-top:6px"></div>',
                unsafe_allow_html=True,
            )
        with col_info:
            new_hex = st.text_input(label, value=hex_val, key=f"color_{key}", label_visibility="visible")
            new_hex = new_hex.strip()
            if not new_hex.startswith("#"):
                new_hex = "#" + new_hex

        active_palette[key] = new_hex
        try:
            active_palette_lab[key] = rgb_to_lab(hex_to_rgb(new_hex))
        except Exception:
            active_palette_lab[key] = PALETTE_LAB[key]

    st.divider()
    min_area = st.slider("Remover paths menores que (área)", 0, 100, 5, help="Micro-paths abaixo desse valor são deletados")

# Main
uploaded = st.file_uploader("Arraste o SVG aqui ou clique para selecionar", type=["svg"], accept_multiple_files=True)

if uploaded:
    for file in uploaded:
        st.markdown(f"#### `{file.name}`")
        col_btn, col_dl = st.columns([2, 3])

        svg_bytes = file.read()

        with st.spinner("Processando..."):
            result_svg, color_map, merged, removed = process_svg_bytes(
                svg_bytes, min_area, active_palette, active_palette_lab
            )

        # Stats
        c1, c2, c3 = st.columns(3)
        c1.metric("Cores remapeadas", len(color_map))
        c2.metric("Classes mescladas", merged)
        c3.metric("Paths removidos", removed)

        # Download
        out_name = file.name.replace(".svg", "_recolored.svg")
        st.download_button(
            label=f"⬇️ Baixar {out_name}",
            data=result_svg.encode("utf-8"),
            file_name=out_name,
            mime="image/svg+xml",
            type="primary",
        )

        # Color map table
        with st.expander("Ver mapeamento de cores"):
            rows = []
            for orig, (brand_hex, brand_name) in color_map.items():
                label = PALETTE_LABELS.get(brand_name, brand_name)
                rows.append({
                    "Original": orig,
                    "→ Marca": brand_hex,
                    "Nome": label,
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

        st.divider()

else:
    st.info("Faça upload de um ou mais arquivos SVG para começar.")
    st.markdown("""
    **Como funciona:**
    1. Faça upload do SVG (exportado do Illustrator via Image Trace)
    2. Cada cor é mapeada para a cor mais próxima da paleta Aer Lingus
    3. Baixe o SVG já recolorido e com paths desnecessários removidos

    **Dica:** Você pode editar as cores da paleta na barra lateral antes de processar.
    """)
