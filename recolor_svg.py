#!/usr/bin/env python3
"""
SVG Recolor Tool — Aer Lingus Brand Palette
Handles SVGs exported from Adobe Illustrator with CSS class-based fills.
- Parses <style> block and remaps all fill colors to nearest brand color
- Merges classes that end up with the same color (reducing path complexity)
- Removes micro paths below area threshold
"""

import xml.etree.ElementTree as ET
import re
import math
import sys
import os

# ─── Paleta Aer Lingus + Ursinho ─────────────────────────────────────────────

BRAND_PALETTE = {
    # Brand core
    "aer-lingus-teal":  "#006272",
    "deep-teal":        "#083D4B",
    "shamrock-green":   "#84BD00",
    "black":            "#050606",
    "pure-white":       "#FFFFFF",
    "cloud-grey":       "#E8E8E8",  # nuvens e sombras neutras claras
    # Bear character colors
    "bear-body":        "#DDA152",
    "bear-muzzle":      "#FAE8C8",  # bege claro cremoso do focinho
    "bear-ears-feet":   "#BE813A",
    "bear-nose":        "#67401C",
    "bear-buttons":     "#94A8AD",
}

MIN_AREA = 5.0  # área mínima de path para manter

OUTPUT_DIR = "/Users/arthurpescuma/Servidor/Aer Lingus/Vetores Recoloridos"

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

def nearest_brand_color(hex_color):
    try:
        rgb = hex_to_rgb(hex_color)
        lab = rgb_to_lab(rgb)
    except Exception:
        return None, None

    r, g, b = rgb

    # Override: verdes (G dominante, não é turquesa/teal onde B também é alto)
    if g > r + 10 and g > b + 10 and g > 80 and b < 120:
        return BRAND_PALETTE["shamrock-green"], "shamrock-green"

    # Override azuis:
    # - muito claros (todos canais > 175, tipo nuvem branca) → cloud-grey via Delta E
    # - médios/teais com B dominante sobre R → teal (inclui teais claros da etiqueta)
    is_very_light = r > 175 and g > 175 and b > 175
    if not is_very_light and b > r + 30 and b > 100:
        return BRAND_PALETTE["aer-lingus-teal"], "aer-lingus-teal"

    # Override: charcoals escuros e neutros → black, não deep-teal
    # Exclui azuis escuros (navy) que devem ir para deep-teal
    if max(r, g, b) < 75 and (max(r, g, b) - min(r, g, b)) < 25 and not (b > r + 8 or b > g + 8):
        return BRAND_PALETTE["black"], "black"

    best = min(PALETTE_LAB, key=lambda n: delta_e(lab, PALETTE_LAB[n]))

    # Dark blues going to black → redirect to deep-teal
    if best == "black" and b > r + 15 and b >= g - 5:
        best = "deep-teal"

    # Bear-muzzle só deve capturar beges quentes (R >> B, tom alaranjado)
    if best == "bear-muzzle":
        if (r - b) < 35:
            best = "cloud-grey"

    # Bear-nose só deve ser o nariz de verdade (muito escuro, L* baixo)
    # Sombras médias do corpo (marrom médio) → bear-ears-feet
    if best == "bear-nose":
        l_star = lab[0]
        if l_star > 34:
            best = "bear-ears-feet"

    return BRAND_PALETTE[best], best

# ─── SVG style block parser ───────────────────────────────────────────────────

def parse_style_block(style_text):
    """Returns dict: class_name → {prop: value}"""
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
    """Rebuild CSS text from class dict."""
    lines = []
    for name, props in classes.items():
        body = "; ".join(f"{k}: {v}" for k, v in props.items())
        lines.append(f"      .{name} {{\n        {body}\n      }}")
    return "\n\n".join(lines)

# ─── Path area ────────────────────────────────────────────────────────────────

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

# ─── Main ─────────────────────────────────────────────────────────────────────

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

def process_svg(input_path, output_path=None, min_area=MIN_AREA):
    # Parse preserving namespaces
    tree = ET.parse(input_path)
    root = tree.getroot()

    # 1. Find and parse <style> block
    style_elem = root.find(f".//{{{SVG_NS}}}style")
    if style_elem is None:
        print("Nenhum bloco <style> encontrado. Tentando fills inline...")
        style_elem = None

    color_map = {}       # original hex → (brand hex, brand name)
    class_color = {}     # class name → original hex
    class_remap = {}     # old class name → new brand hex

    if style_elem is not None:
        original_style = style_elem.text or ""
        classes = parse_style_block(original_style)

        # 2. Remap fills and strokes in each class
        for cls_name, props in classes.items():
            for prop_name in ("fill", "stroke"):
                val = props.get(prop_name)
                if not val or val.lower() in ("none", "transparent"):
                    continue
                if not val.startswith("#"):
                    continue
                if val not in color_map:
                    brand_hex, brand_name = nearest_brand_color(val)
                    color_map[val] = (brand_hex, brand_name)
                brand_hex, _ = color_map[val]
                if prop_name == "fill":
                    class_color[cls_name] = val
                    class_remap[cls_name] = brand_hex
                props[prop_name] = brand_hex

        # 3. Merge classes that now share the same fill
        hex_to_canonical = {}  # brand hex → first class that uses it
        class_alias = {}       # class → canonical class (for renaming in elements)

        for cls_name, props in classes.items():
            fill = props.get("fill")
            if not fill:
                continue
            if fill not in hex_to_canonical:
                hex_to_canonical[fill] = cls_name
            else:
                class_alias[cls_name] = hex_to_canonical[fill]

        # Remove merged duplicate classes
        merged_count = 0
        for dup_cls in class_alias:
            if dup_cls in classes:
                del classes[dup_cls]
                merged_count += 1

        # Rebuild style block
        style_elem.text = "\n" + build_style_block(classes) + "\n    "

        # 4. Update class references in all elements
        for elem in root.iter():
            cls_attr = elem.get("class", "")
            if not cls_attr:
                continue
            cls_list = cls_attr.split()
            new_cls = [class_alias.get(c, c) for c in cls_list]
            # Remove duplicates while preserving order
            seen = set()
            deduped = [c for c in new_cls if not (c in seen or seen.add(c))]
            elem.set("class", " ".join(deduped))

    # 4b. Recolor gradient <stop> elements (not covered by CSS classes)
    stops_recolored = 0
    for stop in root.iter(f"{{{SVG_NS}}}stop"):
        stop_color = stop.get("stop-color")
        if stop_color and stop_color.startswith("#"):
            if stop_color not in color_map:
                brand_hex, brand_name = nearest_brand_color(stop_color)
                color_map[stop_color] = (brand_hex, brand_name)
            brand_hex, _ = color_map[stop_color]
            stop.set("stop-color", brand_hex)
            stops_recolored += 1
        style_attr = stop.get("style", "")
        if "stop-color" in style_attr:
            m = re.search(r"stop-color:\s*(#[0-9a-fA-F]{3,6})", style_attr)
            if m:
                orig = m.group(1)
                if orig not in color_map:
                    brand_hex, brand_name = nearest_brand_color(orig)
                    color_map[orig] = (brand_hex, brand_name)
                brand_hex, _ = color_map[orig]
                stop.set("style", re.sub(r"stop-color:\s*#[0-9a-fA-F]{3,6}", f"stop-color:{brand_hex}", style_attr))
                stops_recolored += 1

    # 5. Remove micro paths
    shape_tags = {f"{{{SVG_NS}}}{t}" for t in ("path", "rect", "circle", "ellipse", "polygon")}
    removed = 0
    def remove_small(parent):
        nonlocal removed
        to_remove = []
        for child in list(parent):
            if child.tag in shape_tags:
                area = estimate_bbox_area(child.get("d", ""))
                if area < min_area:
                    to_remove.append(child)
            else:
                remove_small(child)
        for el in to_remove:
            parent.remove(el)
            removed += 1

    remove_small(root)

    # 6. Write output
    if output_path is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filename = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{filename}_recolored.svg")

    tree.write(output_path, xml_declaration=True, encoding="unicode")

    # Report
    print(f"\n✓ Concluído!")
    print(f"  Classes recoloridas  : {len(class_remap)}")
    print(f"  Classes mescladas    : {merged_count if style_elem else 0}")
    print(f"  Paths removidos      : {removed}")
    print(f"  Output               : {output_path}")
    print(f"\n  Mapeamento de cores:")
    seen_orig = set()
    for orig, (brand_hex, brand_name) in color_map.items():
        if orig not in seen_orig:
            print(f"    {orig}  →  {brand_hex}  ({brand_name})")
            seen_orig.add(orig)

    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 recolor_svg.py <input.svg> [output.svg] [min_area]")
        sys.exit(1)

    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    area = float(sys.argv[3]) if len(sys.argv) > 3 else MIN_AREA
    process_svg(inp, out, min_area=area)
