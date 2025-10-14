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

    df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')
    df.drop(columns=['Index'], inplace=True, errors='ignore')

    df.columns = [normalize_party_name(col) if col not in ['Körzet', 'Népesség'] else col for col in df.columns]

    parties = [col for col in df.columns if col not in ['Körzet', 'Népesség']]

    total_population = df['Népesség'].sum()

    # EP országos eredmények számítása a fájlból
    ep_eredmenyek = {
        party: (df['Népesség'] * df[party] / 100).sum() / total_population * 100
        for party in parties
    }

    # Arányszám számítása: körzeti % / országos %
    aranyok = {
        party: df[party] / ep_eredmenyek[party]
        for party in parties
    }

    # Előrejelzett körzeti %-ok
    pred_szazalek_df = pd.DataFrame({
        party: aranyok[party] * orszagos_eredmenyek.get(party, 0)
        for party in parties
    })

    # Korrigálás, ha több mint 100%
    row_sums = pred_szazalek_df.sum(axis=1)
    faktor = pd.Series(1.0, index=row_sums.index)
    overshoot = row_sums > 100
    faktor[overshoot] = 100.0 / row_sums[overshoot]
    pred_szazalek_df = pred_szazalek_df.mul(faktor, axis=0)

    return None