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

    # Körzeti szavazatszám
    korzeti_szavazok = (df['Népesség'] * reszvetel_szazalek / 100).round().astype(int)
    pred_szavazat_df = pd.DataFrame({
        party: (pred_szazalek_df[party] / 100 * korzeti_szavazok).round().astype(int)
        for party in parties
    })

    # Átszavazás alkalmazása körzetenként
    for idx, korzet in enumerate(df["Körzet"]):
        # Ellenőrizzük, van-e külön szabály adott körzetre
        if korzet in taktikai_atszavazas_korzet:
            atszavazas_szabalyok = taktikai_atszavazas_korzet[korzet]
        else:
            atszavazas_szabalyok = taktikai_atszavazas

        # Alkalmazzuk az átszavazási szabályokat
        for party, (arany, cel_party) in atszavazas_szabalyok.items():
            if party in pred_szavazat_df.columns and cel_party in pred_szavazat_df.columns:
                athelyezendo = int(round(pred_szavazat_df.at[idx, party] * arany))
                pred_szavazat_df.at[idx, party] -= athelyezendo
                pred_szavazat_df.at[idx, cel_party] += athelyezendo
            else:
                print(f"Figyelmeztetés: Érvénytelen párt a körzetben: {korzet}, párt: {party}, cél: {cel_party}")

    # Új százalékok kiszámítása
    total_votes_per_district = pred_szavazat_df.sum(axis=1)
    pred_szazalek_df_adjusted = (pred_szavazat_df.div(total_votes_per_district, axis=0) * 100).round(2)

    # Egyéni győztesek, töredék, kompenzációs értékek
    egyeni_gyoztesek = []
    egyeni_mand = {p: 0 for p in parties}
    toredek = {p: 0 for p in parties}
    komp = {p: 0 for p in parties}
    kulonbsegek = []

    for idx, row in pred_szavazat_df.iterrows():
        winner = row.idxmax()
        runnerup = row.drop(winner).max()
        kulonbseg_szavazat = row[winner] - runnerup
        total_votes = total_votes_per_district[idx]
        kulonbseg_szazalek = (kulonbseg_szavazat / total_votes * 100).round(2)

        egyeni_gyoztesek.append(winner)
        egyeni_mand[winner] += 1
        komp[winner] += int(kulonbseg_szavazat + 1)
        kulonbsegek.append(kulonbseg_szazalek)

        for p in parties:
            if p != winner:
                toredek[p] += int(row[p])

    # Összes szavazó (országosan)
    ossz_szavazo = int(round(reszvetel_szazalek / 100 * total_population))

    # Listás szavazatok számítása a korrigált, 100-as bázisú arányok alapján
    listas_szavazat = {
    p: int(round(pred_szazalek_df_adjusted[p].mean() / 100 * ossz_szavazo)) + kulhoni_szavazatok.get(p, 0)
    for p in parties
    }


    return None