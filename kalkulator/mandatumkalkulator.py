import pandas as pd

def normalize_party_name(name: str) -> str:
    """
    Normalizálja a pártneveket: eltávolítja a ' (%)' végződést, és egységesíti az elnevezéseket.
    """
    name = name.strip()
    if name.endswith(" (%)"):
        name = name[:-4]
    return name

def mandatumkalkulacio(
    csv_path,
    orszagos_eredmenyek: dict,
    reszvetel_szazalek: float = 70.0,
    kulhoni_szavazatok: dict = None,
    fix_mandatumok: dict = None,
    taktikai_atszavazas: dict = None,
    taktikai_atszavazas_korzet: dict = None,
    output_path: str = "mandatum_kalkulacio_eredmeny.csv"
):
    # Normalizáljuk az országos eredmények kulcsait
    orszagos_eredmenyek = {normalize_party_name(k): v for k, v in orszagos_eredmenyek.items()}
    kulhoni_szavazatok = {normalize_party_name(k): v for k, v in (kulhoni_szavazatok or {}).items()}
    fix_mandatumok = {normalize_party_name(k): v for k, v in (fix_mandatumok or {}).items()}
    taktikai_atszavazas = {
        normalize_party_name(k): (v[0], normalize_party_name(v[1]))
        for k, v in (taktikai_atszavazas or {}).items()
    }
    taktikai_atszavazas_korzet = {
        korzet: {
            normalize_party_name(k): (v[0], normalize_party_name(v[1]))
            for k, v in szabalyok.items()
        }
        for korzet, szabalyok in (taktikai_atszavazas_korzet or {}).items()
    }

    return None