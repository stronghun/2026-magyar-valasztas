import pandas as pd
from mandatumkalkulator import mandatumkalkulacio
from terkepkalkulator import terkep_svg

mandatumkalkulacio(
    csv_path="2024_ep_input_korzetek_bovitett.csv",
    orszagos_eredmenyek={
        "Fidesz": 50.0,
        "Tisza": 42.0,
        "DK-MSZP-Párbeszéd": 2.0,
        "Momentum": 0,
        "MKKP": 3.0,
        "Mi Hazánk": 4.0,
        "Független": 1.0
    },
    reszvetel_szazalek=70.0,
    kulhoni_szavazatok={
        "Fidesz": 300000,
        "Tisza": 0,
        "DK-MSZP-Párbeszéd": 0,
        "Momentum": 0,
        "MKKP": 0,
        "Mi Hazánk": 0,
        "Független": 0
    },
    fix_mandatumok={
        "Fidesz": 2,
        "Tisza": 0,
        "DK-MSZP-Párbeszéd": 0,
        "Momentum": 0,
        "MKKP": 0,
        "Mi Hazánk": 0,
        "Független": 0
    },
    taktikai_atszavazas={
        #"DK-MSZP-Párbeszéd" : (0.5, "Tisza")
    },
    taktikai_atszavazas_korzet={
        #"Budapest 05": {
        #    "Tisza": (0.5, "Független"),  # „%” jel nélkül is működik most már
        #}
    },
    output_path="mandatum_kalkulacio_eredmeny.csv"
)

korzet_df = pd.read_csv("mandatum_kalkulacio_eredmeny.csv", sep=";", encoding="utf-8-sig")
terkep_svg("2026_korzetek_alap.svg", korzet_df, shade_threshold=30, bp_zoom_enabled=True)
