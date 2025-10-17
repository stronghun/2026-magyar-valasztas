import pandas as pd
from bs4 import BeautifulSoup
import unidecode
import numpy as np
from datetime import date
import os

PART_COLORS = {
    "Fidesz": ((255, 206, 173), (142, 59, 0)),
    "Tisza": ((168, 184, 224), (15, 34, 87)),
    "DK-MSZP-Párbeszéd": ((245, 163, 183), (92, 10, 30)),
    "Momentum": ((211, 165, 225), (58, 12, 72)),
    "MKKP": ((177, 225, 183), (24, 72, 30)),
    "Mi Hazánk": ((255, 243, 163), (102, 90, 10)),
    "Független": ((0xF5, 0xF5, 0xF5), (0x33, 0x33, 0x33))
}

DISPLAY_NAMES = {
    "Fidesz": "Fidesz",
    "Tisza": "Tisza",
    "DK-MSZP-Párbeszéd": "Dobrev Klára Pártja",
    "Momentum": "Momentum",
    "MKKP": "MKKP",
    "Mi Hazánk": "Mi Hazánk",
    "Független": "Független"
}

GREY = "#F5F5F5"

def korzet_to_svg_id(korzetnev):
    s = unidecode.unidecode(korzetnev.lower()).replace("–", "-").replace(" ", "-")
    helyettesites = {
        "borsod-abauj-zemplen": "borsod", "szabolcs-szatmar-bereg": "szabolcs",
        "jasz-nagykun-szolnok": "jasz", "gyor-moson-sopron": "gyor",
        "komarom-esztergom": "komarom", "bacs-kiskun": "bacs",
        "csongrad-csanad": "csongrad", "hajdu-bihar": "hajdu"
    }
    for regi, uj in helyettesites.items():
        s = s.replace(regi, uj)
    return s

def safe_max(series):
    val = series.max()
    return val if not np.isnan(val) else 0.0

def safe_min(series):
    val = series.min()
    return val if not np.isnan(val) else 0.0

# Két színintervallum közötti rgb értékek számolása
def interpolate_color(c1, c2, t):
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

# Árnyalat kiválasztása a szín alapján
def szin_kulonbseg_alapjan(row, shade_threshold):
    gyoztes = row["Győztes"]
    kulonbseg = abs(row["Különbség"])
    if gyoztes in PART_COLORS:
        light, dark = PART_COLORS[gyoztes]
        t = min(kulonbseg / shade_threshold, 1.0) if shade_threshold > 0 else 0.0
        return interpolate_color(light, dark, t)
    return GREY

# Szöveg kiírása
def jelmagyarazat(soup, kulonbseg_minmax, shade_threshold, korzet_df):
    defs = soup.new_tag("defs")

    def create_gradient(id_, c_light, c_dark, min_val, max_val):
        grad = soup.new_tag("linearGradient", id=id_, x1="0%", y1="0%", x2="100%", y2="0%")
        t_min = min_val / shade_threshold if shade_threshold > 0 else 0.0
        t_max = min(max_val / shade_threshold, 1.0)
        grad.append(soup.new_tag("stop", offset="0%", **{"stop-color": interpolate_color(c_light, c_dark, t_min)}))
        grad.append(soup.new_tag("stop", offset="100%", **{"stop-color": interpolate_color(c_light, c_dark, t_max)}))
        return grad

    # Csak azokat a pártokat nézzük, akik nyertek is
    active_parties = [(party, PART_COLORS[party], kulonbseg_minmax[party]) for party in PART_COLORS if kulonbseg_minmax[party][1] > 0]

    for party, (c_light, c_dark), (min_val, max_val) in active_parties:
        grad_id = f"grad_{unidecode.unidecode(party).replace(' ', '-')}"
        defs.append(create_gradient(grad_id, c_light, c_dark, min_val, max_val))

    soup.svg.insert(0, defs)
    group = soup.new_tag("g", id="legend", transform="translate(50, 30)")

    n = len(active_parties)
    scale_factor = 1.0
    layout = []

    if n == 1:
        layout = [(0, 0)]
    elif n == 2:
        layout = [(0, 0), (0, 1)]
    elif n == 3:
        scale_factor = 0.8
        layout = [(0, i) for i in range(3)]
    elif n == 4:
        scale_factor = 0.7
        layout = [(0, i) for i in range(2)] + [(1, i) for i in range(2)]
    elif n == 5:
        scale_factor = 0.7
        layout = [(0, i) for i in range(3)] + [(1, i) for i in range(2)]
    elif n == 6:
        scale_factor = 0.6
        layout = [(0, i) for i in range(3)] + [(1, i) for i in range(3)]
    elif n >= 7:
        scale_factor = 0.6
        layout = [(0, i) for i in range(3)] + [(1, i) for i in range(3)] + [(2, i) for i in range(n - 6)]

    box_width = 260 * scale_factor
    box_height = 30 * scale_factor
    font_size = int(18 * scale_factor)
    label_size = int(16 * scale_factor)
    spacing_x = 400 * scale_factor
    spacing_y = 80 * scale_factor

    # Minden párthoz külön box és szöveg
    for (col, row_index), (party, (c_light, c_dark), (min_val, max_val)) in zip(layout, active_parties):
        x = col * spacing_x
        y = row_index * spacing_y
        grad_id = f"grad_{unidecode.unidecode(party).replace(' ', '-')}"
        rect = soup.new_tag("rect", x=str(x), y=str(y), width=str(box_width), height=str(box_height), fill=f"url(#{grad_id})")
        group.append(rect)

        for pos, val in zip([0, box_width / 2, box_width], [min_val, (min_val + max_val)/2, max_val]):
            label = soup.new_tag("text", x=str(x + pos), y=str(y + box_height + 18), fill=interpolate_color(c_light, c_dark, 0.8),
                                 **{"font-size": str(label_size), "text-anchor": "middle", "font-weight": "bold"})
            label.string = f"{val:.2f}%"
            group.append(label)

        # Pártneveket jobboldalra írjuk + egyéni OEVK győzelmek hozzáfűzése
        egyeni_db = korzet_df["Győztes"].value_counts().to_dict().get(party, 0)
        text = soup.new_tag("text", x=str(x + box_width + 12), y=str(y + box_height - 3),
                            fill=interpolate_color(c_light, c_dark, 0.8),
                            **{"font-size": str(font_size), "font-weight": "bold"})
        text.string = f"{DISPLAY_NAMES.get(party, party)} ({egyeni_db})"
        group.append(text)


    soup.svg.append(group)

# Ha akarsz, bp-i körzeteket nagyobbra rakjuk
def nagyits_budapestet(soup):
    budapest_ids = [f"budapest-{i:02}" for i in range(1, 17)]
    scale = 5.5
    translate_x = 1000
    translate_y = 750
    rotate_deg = 7
    pivot_x = 244.1
    pivot_y = 172.8
    stroke_width = 0.05

    for korzet_id in budapest_ids:
        path = soup.find("path", {"id": korzet_id})
        if path:
            new_path = soup.new_tag("path", d=path["d"])
            new_path["id"] = korzet_id + "-zoom"
            szin = path.get("style", "").split(";")[0]
            new_path["style"] = f"{szin}; stroke: #000; stroke-width: {stroke_width};"
            new_path["transform"] = (
                f"translate({translate_x},{translate_y}) scale({scale}) rotate({rotate_deg}) translate({-pivot_x},{-pivot_y})"
            )
            soup.svg.append(new_path)

def terkep_svg(svg_path, korzet_df, shade_threshold=30, bp_zoom_enabled=True):
    today = date.today().isoformat()
    os.makedirs("terkep", exist_ok=True)
    suffix = "_teljes_bp" if bp_zoom_enabled else "_teljes"
    output_path = f"terkep/{today}{suffix}.svg"

    if "Különbség" not in korzet_df.columns:
        korzet_df["Különbség"] = 0.0
    else:
        korzet_df["Különbség"] = korzet_df["Különbség"].astype(float)
    required_columns = ["Körzet", "Győztes"] + list(PART_COLORS.keys())
    if not all(col in korzet_df.columns for col in required_columns):
        raise ValueError(f"A korzet_df-nek tartalmaznia kell a következő oszlopokat: {required_columns}")
    
    for i, row in korzet_df.iterrows():
        gy = row["Győztes"]
        if gy in PART_COLORS:
            max_ellenfel = max([row[p] for p in PART_COLORS if p != gy])
            korzet_df.at[i, "Különbség"] = row[gy] - max_ellenfel

    with open(svg_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")

    svg_tag = soup.find("svg")
    viewbox = svg_tag.get("viewBox")
    if viewbox:
        x, y, w, h = map(float, viewbox.split())
        padding = 20  # px-ben, a térkép alja felé
        svg_tag["viewBox"] = f"{x} {y} {w * 2} {h * 2 + padding}"  # növeljük a magasságot
        svg_tag["width"] = str(w * 2)
        svg_tag["height"] = str(h * 2 + padding)


    # Duplázzuk a nagyságot
    for path in soup.find_all("path"):
        path["transform"] = f"scale(2) {path.get('transform', '')}".strip()

    # A szöveget is
    for text in soup.find_all("text"):
        text["font-size"] = str(float(text.get("font-size", 10)) * 2)
        if "x" in text.attrs:
            text["x"] = str(float(text["x"]) * 2)
        if "y" in text.attrs:
            text["y"] = str(float(text["y"]) * 2)
    kulonbseg_minmax = {}
    for party in PART_COLORS:
        part_vals = korzet_df[korzet_df["Győztes"] == party]["Különbség"].abs()
        kulonbseg_minmax[party] = (safe_min(part_vals), safe_max(part_vals))

    for _, row in korzet_df.iterrows():
        korzet_id = korzet_to_svg_id(row["Körzet"])
        path = soup.find("path", {"id": korzet_id})
        if path:
            szin = szin_kulonbseg_alapjan(row, shade_threshold)
            path["style"] = f"fill: {szin}; stroke: #000; stroke-width: 0.1;"

    if bp_zoom_enabled:
        print(">> Budapest nagyítása bekapcsolva.")
        nagyits_budapestet(soup)
    else:
        print(">> Budapest nagyítása kikapcsolva.")

    jelmagyarazat(soup, kulonbseg_minmax, shade_threshold, korzet_df)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f">> SVG fájl elmentve: {output_path}")
