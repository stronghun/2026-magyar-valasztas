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
def jelmagyarazat(soup, kulonbseg_minmax, shade_threshold):
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