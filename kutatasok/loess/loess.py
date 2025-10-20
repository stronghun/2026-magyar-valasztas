import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
import warnings
import re

warnings.filterwarnings("ignore", category=np.exceptions.RankWarning)

def kozvelemeny_grafikon(
    csv_fajl: str = "de.csv",

    # X és Y tengely meghatározása
    mettol: str = None,
    meddig: str = None,
    y_hatarok: tuple = (0, 40),
    y_offset_negativ: float = -2,

    # Küszöb
    valasztasi_kuszob: float = 5,
    kuszob_vastagsag: float = 1.5,
    kuszob_szin: str = "#666666bb",

    valasztasi_eredmenyek: list = None, 

    # Loess, pontok beállítása
    loess_szigor: float = 0.25,
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

    def loess(x, y, xnew, span, degree=2):
        x, y, xnew = np.asarray(x), np.asarray(y), np.asarray(xnew)
        n = len(x)
        if n < degree + 2:
            return np.full(len(xnew), np.nan)
        k = max(int(span * n), degree + 1)
        ynew = np.empty(len(xnew))
        for i, xi in enumerate(xnew):
            dists = np.abs(x - xi)
            idx_sort = np.argsort(dists)
            h = dists[idx_sort[k - 1]]
            if h == 0:
                if np.all(x == xi):
                    ynew[i] = np.mean(y)
                    continue
                h = np.max(dists[dists > 0]) if np.any(dists > 0) else 1e-6
            u = dists / h
            w = np.where(u < 1, (1 - u**3)**3, 0)
            dx = x - xi
            X = np.ones((n, degree + 1))
            for d in range(1, degree + 1):
                X[:, d] = dx ** d
            W = np.diag(w)
            try:
                beta = np.linalg.solve(X.T @ W @ X, X.T @ W @ y)
                ynew[i] = beta[0]
            except np.linalg.LinAlgError:
                sum_w = np.sum(w)
                ynew[i] = np.sum(w * y) / sum_w if sum_w > 0 else np.nan
        return ynew
    
    # Adatok beolvasása, ellenőrzése
    df = pd.read_csv(csv_fajl, encoding="utf-8")
    all_parties = [c.strip() for c in df.columns if c.strip().lower() != "polldate" and not c.startswith("Unnamed")]
    df["date"] = pd.to_datetime(df["polldate"])

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
    ax.axhline(valasztasi_kuszob, color=kuszob_szin, linestyle="--", linewidth=kuszob_vastagsag)

    # Pontok, trendvonalak
    for party, color in filtered_dict.items():
        pdata = df_long[df_long["party"] == party].dropna(subset=["value"]).sort_values("date")
        if len(pdata) < 3:
            continue
        ax.scatter(
            pdata["date"], pdata["value"],
            s=pont_meret, color=color,
            alpha=pont_atlatszosag, edgecolor="white", linewidth=0.6
        )
        x = (pdata["date"] - pdata["date"].min()).dt.days.values
        y = pdata["value"].values
        x_dense = np.linspace(min(x), max(x), 500)
        y_smooth = loess(x, y, x_dense, loess_szigor)
        date_dense = pdata["date"].min() + pd.to_timedelta(x_dense, unit="D")
        ax.plot(date_dense, y_smooth, color=color,
                linewidth=trend_vastagsag, label=party)
        
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
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))
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
    "SPD": "#EB001F",
    "Union": "#000000",
    "Grüne": "#64A12D",
    "FDP": "#FFED00",
    "AfD": "#009EE0",
    "Linke": "#BE3075",
    "BSW": "#792350",
    "FW": "#F7A800"
}

valasztasi_eredmenyek = [
    {
        "datum": "2021-09-26",
        "adatok": {"SPD": 25.7, "Union": 24.1, "Grüne": 14.8, "FDP": 11.5, "AfD": 10.3, "Linke": 4.9}
    },
    {
        "datum": "2025-02-23",
        "adatok": {"SPD": 22.3, "Union": 27.5, "Grüne": 15.0, "AfD": 17.1, "BSW": 5.6}
    }
]

kozvelemeny_grafikon(
    csv_fajl="de.csv",
    mettol="2021-10-01",
    meddig="2025-03-01",
    y_hatarok=(0, 40),
    y_offset_negativ=-2,
    valasztasi_kuszob=5,
    kuszob_vastagsag=1.8,
    loess_szigor=0.09,
    pont_meret=30,
    pont_atlatszosag=0.45,
    trend_vastagsag=2.6,
    eredmeny_meret_szorzo=2.5,      
    eredmeny_atlatszosag_szorzo=1.0, 
    racs_szin="white",
    racs_vastagsag=1.5,
    racs_alvonal_szin="#ffffffaa",
    racs_alvonal_vastagsag=0.6,
    racs_lathato=True,
    partok_es_szinek=partok_es_szinek,
    valasztasi_eredmenyek=valasztasi_eredmenyek,
    kimenet="test"
)

