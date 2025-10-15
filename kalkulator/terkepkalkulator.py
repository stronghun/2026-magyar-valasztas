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