import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
import warnings
import re
from scipy.interpolate import make_interp_spline
from statsmodels.nonparametric.smoothers_lowess import lowess

warnings.filterwarnings("ignore", category=np.exceptions.RankWarning)

def kozvelemeny_grafikon(
    csv_fajl: str = "de.csv",
    csv_elvalaszto: str = ',',

    # X és Y tengely meghatározása
    mettol: str = None,
    meddig: str = None,
    y_hatarok: tuple = (0, 40),
    y_offset_negativ: float = -2,

    # Küszöb
    valasztasi_kuszob: float = 5,
    kuszob_stilus: str = ":",
    kuszob_vastagsag: float = 1.5,
    kuszob_szin: str = "#666666bb",

    valasztasi_eredmenyek: list = None, 

    # LOESS
    loess_szigor: float = 0.25,
    loess_fok: int = 1,
    loess_pontok: int = 300,
    partonkenti_loess: dict = None,

    # Loess, pontok beállítása
    pont_meret: float = 20,
    pont_atlatszosag: float = 0.4,
    trend_vastagsag: float = 2.5,

    # Eredménypontok beállítása
    eredmeny_meret_szorzo: float = 2.0,
    eredmeny_atlatszosag_szorzo: float = 1.0,

    # Egyéb beállítások
    szelesseg: int = 18,
    magassag: int = 8,
    racs_szin: str = "white",
    racs_vastagsag: float = 1.2,
    racs_lathato: bool = True,
    racs_alvonal_szin: str = "#ffffffaa",
    racs_alvonal_vastagsag: float = 0.6,
    fix_vonalak: list = None,


    # Kizárt időszak adott párt esetében
    kizart_idoszakok: dict = None,

    # Kutatócégekre szűrés
    szurt_intezmenyek: list = None,

    # Pártok
    partok_es_szinek: dict = None,
    kimenet: str = None

):
    # Stílusbeállítások
    plt.style.use("ggplot")
    plt.rcParams.update({
        "axes.facecolor": "#f2f2f2",
        "figure.facecolor": "white",
        "grid.color": racs_szin,
        "grid.linewidth": racs_vastagsag,
        "axes.edgecolor": "#bbbbbb",
        "axes.grid": racs_lathato,
        "axes.axisbelow": True,
    })

    def loess(x, y, xnew, span=0.3, degree=1, robust=True, iterations=2):
        x, y, xnew = np.asarray(x), np.asarray(y), np.asarray(xnew)
        n = len(x)
        if n < degree + 2:
            return np.full(len(xnew), np.nan)

        k = max(int(span * n), degree + 1)

        def local_fit(xi, y, x, w):
            X = np.vstack([np.ones_like(x)] + [(x - xi) ** d for d in range(1, degree + 1)])
            W = np.diag(w)
            beta, *_ = np.linalg.lstsq(W @ X.T, W @ y, rcond=None)
            return beta[0]

        yfit = np.zeros_like(y)
        for i, xi in enumerate(x):
            dists = np.abs(x - xi)
            idx = np.argsort(dists)
            h = dists[idx[k - 1]]
            u = dists / h if h > 0 else np.zeros_like(dists)
            w = np.where(u < 1, (1 - u**3)**3, 0)
            yfit[i] = local_fit(xi, y, x, w)

        if robust:
            resid = np.abs(y - yfit)
            s = np.median(resid)
            if s == 0:
                s = np.mean(resid) + 1e-6
            robustness = (1 - (resid / (6 * s))**2) ** 2
            robustness[resid > 6 * s] = 0

            for _ in range(iterations):
                yfit = np.zeros_like(y)
                for i, xi in enumerate(x):
                    dists = np.abs(x - xi)
                    idx = np.argsort(dists)
                    h = dists[idx[k - 1]]
                    u = dists / h if h > 0 else np.zeros_like(dists)
                    w = np.where(u < 1, (1 - u**3)**3, 0) * robustness
                    yfit[i] = local_fit(xi, y, x, w)

        ynew = np.zeros_like(xnew)
        for i, xi in enumerate(xnew):
            dists = np.abs(x - xi)
            idx = np.argsort(dists)
            h = dists[idx[k - 1]]
            u = dists / h if h > 0 else np.zeros_like(dists)
            w = np.where(u < 1, (1 - u**3)**3, 0)
            ynew[i] = local_fit(xi, y, x, w)

        return ynew

    def loess2(x, y, xnew, span, degree=1):
        fitted = lowess(y, x, frac=span, it=3, delta=0.0, is_sorted=True, return_sorted=True)
        x_fit, y_fit = fitted[:, 0], fitted[:, 1]
        return np.interp(xnew, x_fit, y_fit)
    
    # Adatok beolvasása, ellenőrzése
    df = pd.read_csv(csv_fajl, encoding="utf-8", sep=csv_elvalaszto)
    all_parties = [c.strip() for c in df.columns if c.strip().lower() != "polldate" and not c.startswith("Unnamed")]
    df["date"] = pd.to_datetime(df["polldate"])

    # Kutatókra szűrés
    if szurt_intezmenyek and "polling_firm" in df.columns:
        eredeti_sorok = len(df)
        df = df[df["polling_firm"].isin(szurt_intezmenyek)]
        print(f"Csak a következő intézetek maradtak: {', '.join(szurt_intezmenyek)} "
              f"({len(df)}/{eredeti_sorok} sor)")
    elif szurt_intezmenyek and "polling_firm" not in df.columns:
        print("Figyelmeztetés: 'polling_firm' oszlop nem található, "
              "de 'szurt_intezmenyek' meg van adva → szűrés kihagyva.")
    

    filtered_dict = {p: c for p, c in partok_es_szinek.items() if p in all_parties}
    if len(filtered_dict) < len(partok_es_szinek):
        missing = set(partok_es_szinek.keys()) - set(filtered_dict.keys())
        print(f"Hiányzik a fájlból: {', '.join(missing)}")

    df = df[["date"] + list(filtered_dict.keys())]

    start_date = pd.to_datetime(mettol) if mettol else df["date"].min()
    end_date = pd.to_datetime(meddig) if meddig else df["date"].max()
    df_visible = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    # Ha nincsen az adott intervallumban adat
    if df_visible.empty:
        df_visible = df.copy()

    # Táblázatot átalakítjuk
    df_long = pd.melt(df_visible, id_vars=["date"], value_vars=list(filtered_dict.keys()),
                      var_name="party", value_name="value")
    df_long["party"] = pd.Categorical(df_long["party"], categories=list(filtered_dict.keys()))

    # Plot
    fig, ax = plt.subplots(figsize=(szelesseg, magassag))
    ax.axhline(valasztasi_kuszob, color=kuszob_szin, linestyle=kuszob_stilus, linewidth=kuszob_vastagsag)

    # Pontok, trendvonalak
    for party, color in filtered_dict.items():
        pdata = df_long[df_long["party"] == party].dropna(subset=["value"]).sort_values("date")

        # Kizárt időszakok
        excluded_ranges = []
        if kizart_idoszakok and party in kizart_idoszakok:
            for (start, end) in kizart_idoszakok[party]:
                start = pd.to_datetime(start)
                end = pd.to_datetime(end)
                excluded_ranges.append((start, end))
                pdata = pdata[~((pdata["date"] >= start) & (pdata["date"] <= end))]

        if len(pdata) < 3:
            continue

        # Pontok (kizárt időszakok nélkül)
        ax.scatter(
            pdata["date"], pdata["value"],
            s=pont_meret, color=color,
            alpha=pont_atlatszosag, edgecolor="white", linewidth=0.6
        )

        segments = []
        segment_start = pdata["date"].min()
        segment_end = pdata["date"].max()

        if not excluded_ranges:
            segments = [(segment_start, segment_end)]
        else:
            excluded_ranges = sorted(excluded_ranges, key=lambda x: x[0])
            current_start = segment_start
            for (start, end) in excluded_ranges:
                if start > current_start and start <= segment_end:
                    segments.append((current_start, start - pd.Timedelta(days=1)))
                current_start = end + pd.Timedelta(days=1)

            if segments:
                last_end = segments[-1][1]
                if last_end < segment_end:
                    segments.append((last_end + pd.Timedelta(days=1), segment_end))
            else:
                if segment_start < segment_end:
                    segments.append((segment_start, segment_end))

        #  Külön trendvonalak húzása a kizárt időszakok által elvágott ponthalmazokra
        for (seg_start, seg_end) in segments:
            seg_data = pdata[(pdata["date"] >= seg_start) & (pdata["date"] <= seg_end)]
            if len(seg_data) < 3:
                continue
            x = (seg_data["date"] - seg_data["date"].min()).dt.days.values
            y = seg_data["value"].values
            x_dense = np.linspace(min(x), max(x), loess_pontok)

            if partonkenti_loess and party in partonkenti_loess:
                span = partonkenti_loess[party].get("loess_szigor", loess_szigor)
                fok = partonkenti_loess[party].get("loess_fok", loess_fok)
            else:
                span = loess_szigor
                fok = loess_fok

            y_smooth = loess(x, y, x_dense, span, degree=fok)
           
            date_dense = seg_data["date"].min() + pd.to_timedelta(x_dense, unit="D")
            ax.plot(date_dense, y_smooth, color=color, linewidth=trend_vastagsag, label=None)

        ax.plot([], [], color=color, linewidth=trend_vastagsag, label=party)

        
    # Választási eredménypontok
    if valasztasi_eredmenyek:
        for valasztas in valasztasi_eredmenyek:
            datum = pd.to_datetime(valasztas["datum"])
            for party, result in valasztas["adatok"].items():
                if party in filtered_dict:
                    ax.scatter(
                        datum, result,
                        s=pont_meret * eredmeny_meret_szorzo,
                        color=filtered_dict[party],
                        alpha=min(pont_atlatszosag * eredmeny_atlatszosag_szorzo, 1.0),
                        linewidth=0,
                        marker="D",
                        zorder=10
                    )
    if fix_vonalak:
        for vonal in fix_vonalak:
            datum = pd.to_datetime(vonal.get("datum"))
            szin = vonal.get("szin", "#000000")
            vastagsag = vonal.get("vastagsag", 1.5)
            stilus = vonal.get("stilus", "--")
            ax.axvline(
                x=datum,
                color=szin,
                linewidth=vastagsag,
                linestyle=stilus,
                alpha=0.8,
                zorder=1
            )

    # Tengelyek
    ymin = y_hatarok[0] + y_offset_negativ
    ymax = y_hatarok[1]
    ax.set_ylim(ymin, ymax)
    ax.set_xlim(start_date, end_date)

    # Kerekít + '%'
    def y_fmt(val, pos):
        return f"{int(val)}%" if val >= 0 else ""
    ax.yaxis.set_major_formatter(FuncFormatter(y_fmt))

    # Kisebb rácsok megjelenítése
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(which="minor", color=racs_alvonal_szin, linewidth=racs_alvonal_vastagsag, linestyle="-")

    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=14, labelspacing=0.8)
    ax.tick_params(axis="x", labelsize=11)
    ax.tick_params(axis="y", labelsize=12)

    plt.tight_layout()
    plt.savefig(f"{kimenet}.svg", bbox_inches="tight", pad_inches=0.05)

    # SVG elmentése
    with open(f"{kimenet}.svg", "r", encoding="utf-8") as f:
        svg = f.read()
    svg = re.sub(r'width="[\d\.]+pt"', 'width="100%"', svg)
    svg = re.sub(r'height="[\d\.]+pt"', 'height="100%"', svg)
    if 'preserveAspectRatio' not in svg:
        svg = svg.replace('<svg ', '<svg preserveAspectRatio="xMidYMid meet" ', 1)
    with open(f"{kimenet}_full.svg", "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"{kimenet}.svg elmentve")



# Futtatás

partok_es_szinek = {
    "TISZA": "#112866",
    "Fidesz": "#FF6A00",
    "Dobrev Klára Pártja": "#0067AA",
    "Mi Hazánk": "#688D1B",
    "MKKP": "#808080",
    "Momentum": "#8E6FCE",
    "MSZP": "#CC0000",
    "Párbeszéd": "#39B54A",
    "Jobbik": "#047B60",
    "LMP": "#54B586",
    "Mindenki Magyarországa": "#001166",
    "Második Reformkor": "#F1DB7B",
    "Nép Pártján": "#023854",
    "Szociáldemokrata-zöld koalíció": "#6BC4FF",
    "Egyéb": "#505050"
}

valasztasi_eredmenyek = [
    {
        "datum": "2024-06-09",
        "adatok": {"Fidesz": 44.34, "TISZA": 29.86, "Szociáldemokrata-zöld koalíció": 8.15, "Mi Hazánk": 6.79, "Momentum": 3.70, "MKKP": 3.60, "Jobbik": 1.01, "LMP": 0.88, "Második Reformkor": 0.68, "Mindenki Magyarországa": 0.65}
    }
]

kizart_idoszakok = {
    "Dobrev Klára Pártja": [("2024-03-28", "2024-06-16")],
    "MSZP": [("2024-03-28", "2024-06-16")],
    "Párbeszéd": [("2024-03-28", "2024-06-16")],
    "Egyéb": [("2022-03-28", "2024-06-16")],
    "Nép Pártján": [("2024-06-09", "2026-12-12")],
    "MSZP": [("2024-06-09", "2026-12-12")],
    "Párbeszéd": [("2024-06-09", "2026-12-12")],
    "LMP": [("2024-06-09", "2026-12-12")],
    "Második Reformkor": [("2024-06-09", "2026-12-12")],
    "Mindenki Magyarországa": [("2024-06-09", "2026-12-12")],
    "Jobbik": [("2024-06-09", "2026-12-12")],
}

partonkenti_loess = {
    "Szociáldemokrata-zöld koalíció": {"loess_szigor": 1, "loess_fok": 1},
}

fix_vonalak = [
    {"datum": "2022-04-04", "szin": "#999999", "vastagsag": 1.5, "stilus": "-"},
    {"datum": "2026-04-12", "szin": "#999999", "vastagsag": 1.5, "stilus": "-"},
]


narancsos_kutatok= ["Nézőpont", "Társadalomkutató", "Századvég", "Századvég/McLaughlin", "Real-PR 93"]
narancsmentes_kutatok= ["21 Kutató", "Medián", "Publicus", "ZRI", "IDEA", ""]

kozvelemeny_grafikon(
    csv_fajl="hu.csv",
    csv_elvalaszto=";",
    mettol="2022-05-04",
    meddig="2026-05-12",
    y_hatarok=(0, 65),
    y_offset_negativ=-2,
    valasztasi_kuszob=5,
    kuszob_stilus="--",
    kuszob_vastagsag=2.2,
    kuszob_szin="#999999",
    pont_meret=30,
    pont_atlatszosag=0.45,
    trend_vastagsag=3,
    eredmeny_meret_szorzo=3.0,      
    eredmeny_atlatszosag_szorzo=1, 
    racs_szin="white",
    racs_vastagsag=1.5,
    racs_alvonal_szin="#ffffffaa",
    racs_alvonal_vastagsag=0.6,
    racs_lathato=True,
    partok_es_szinek=partok_es_szinek,
    kizart_idoszakok=kizart_idoszakok,
    szurt_intezmenyek=None,
    valasztasi_eredmenyek=valasztasi_eredmenyek,
    loess_szigor=0.70,
    loess_fok=1,
    loess_pontok=2500,
    partonkenti_loess=None,
    fix_vonalak=fix_vonalak,
    kimenet="test"
)

