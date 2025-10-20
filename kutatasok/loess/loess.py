import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
import warnings

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
    partok_es_szinek: dict = None

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