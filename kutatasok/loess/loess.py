import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=np.exceptions.RankWarning)

def kozvelemeny_grafikon(
    csv_fajl: str = "de.csv",
    kezdo_datum: str = "2021-09-26",
    kovetkezo_valasztas: str = "2025-02-23",
    valasztasi_kuszob: float = 5,
    loess_szigor: float = 0.25,
    pont_meret: float = 20,
    pont_atlatszosag: float = 0.4,
    trend_vastagsag: float = 2.5,
    y_hatarok=(-5, 40),
    szelesseg: int = 18,
    magassag: int = 8,
    mettol: str = None,
    meddig: str = None,
    racs_szin: str = "white",
    racs_vastagsag: float = 1.2,
    racs_lathato: bool = True
):
    # Stílusbeállítások
    plt.style.use("ggplot")
    plt.rcParams.update({
        "axes.facecolor": "#f2f2f2",
        "figure.facecolor": "white",
        "grid.color": racs_szin,
        "grid.linestyle": "-",
        "grid.linewidth": racs_vastagsag,
        "axes.edgecolor": "#bbbbbb",
        "axes.grid": racs_lathato,
        "axes.axisbelow": True,
    })

    part_szin = [
        "#EB001F",  # SPD
        "#000000",  # CDU/CSU
        "#64A12D",  # Greens
        "#FFED00",  # FDP
        "#009EE0",  # AfD
        "#BE3075",  # Left
        "#F7A800",  # BSW
        "#792350"   # FW / Others
    ]

    def loess(x, y, xnew, span, degree=2):
        return None