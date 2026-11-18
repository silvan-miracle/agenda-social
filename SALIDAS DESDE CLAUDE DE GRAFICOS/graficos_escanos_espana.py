# ==============================================================================
# Script:   graficos_escanos_espana.py
# Objetivo: Escaños por territorio en España: los de las generales de 2023 y el
#           reparto estimado 2026 (promedio de encuestas + elasticidad provincial)
# Inputs:   escanos_2023_provincial.csv (Interior, vía dashboard),
#           proyeccion_voto_escanos_provincial_2026-11-04.csv
# Outputs:  espana_escanos_territorio.png y su CSV
# ==============================================================================
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Patch

C23, C26, OUT, SERIF, LOGO = sys.argv[1:6]

# 0. Estilo Matiz (igual que graficos_escanos.py) -----------------------------
fm.fontManager.addfont(SERIF)
SANS, SERIFF = "Inter", "Instrument Serif"
TINTA, SUBTLE, GRID = "#1A1A1A", "#5A6B6C", "#EEEBE3"
NARANJA = "#FF723C"
COL = {"PSOE": "#E5393B", "PP": "#1E73C4", "Vox": "#8BC34A",
       "Izq": "#6A2C91", "ERC": "#F2B01E", "Junts": "#20A39E",
       "EH Bildu": "#4FB5AE", "PNV": "#1B7A3D", "Otros": "#A8A396"}
plt.rcParams.update({"font.family": SANS, "text.color": TINTA})


def aclarar(hexcol, f=0.62):
    """Mezcla un color con blanco: columna clara = resultado de 2023."""
    c = np.array(matplotlib.colors.to_rgb(hexcol))
    return tuple(c + (1 - c) * f)


def firma_logo(fig, ancho_in=1.9, derecha=0.985, abajo=0.016):
    """Logo de Silván & Miracle abajo a la derecha, como en Matiz."""
    img = plt.imread(LOGO)
    w = ancho_in / fig.get_figwidth()
    h = ancho_in * img.shape[0] / img.shape[1] / fig.get_figheight()
    lax = fig.add_axes([derecha - w, abajo, w, h])
    lax.imshow(img, alpha=0.9)
    lax.axis("off")


# 1. Datos: 2023 real y 2026 estimado, agrupados en 9 categorías -------------
M23 = {"PSOE": "PSOE", "PP": "PP", "Vox": "Vox", "Podemos / UP / Sumar": "Izq",
       "ERC": "ERC", "CiU / Junts": "Junts", "HB / Amaiur / EH Bildu": "EH Bildu",
       "PNV": "PNV", "BNG": "Otros", "Coalición Canaria": "Otros", "UPN": "Otros"}
M26 = {"PSOE": "PSOE", "PP": "PP", "Vox": "Vox", "Sumar": "Izq", "Podemos": "Izq",
       "Frente Amplio": "Izq", "ERC": "ERC", "Junts": "Junts",
       "EH Bildu": "EH Bildu", "PNV": "PNV", "BNG": "Otros", "CCa": "Otros",
       "UPN": "Otros", "SALF": "Otros"}
ORDEN = list(COL)

d23 = pd.read_csv(C23)
d23["p"] = d23.linea.map(M23)
JUEGO = d23.drop_duplicates("provincia").set_index("provincia").escanos_provincia
E23 = (d23.dropna(subset=["p"]).groupby(["provincia", "p"]).escanos_2023.sum()
          .unstack(fill_value=0).reindex(columns=ORDEN, fill_value=0))

d26 = pd.read_csv(C26)
d26 = d26[d26.partido != "Otros"].copy()
d26["p"] = d26.partido.map(M26)
E26 = (d26.groupby(["provincia", "p"]).escanos_proyectados.sum()
          .unstack(fill_value=0).reindex(columns=ORDEN, fill_value=0))

# Comprobación: cada provincia reparte todos sus escaños en ambos casos
assert (E23.sum(axis=1) == JUEGO.reindex(E23.index)).all()
assert (E26.sum(axis=1) == JUEGO.reindex(E26.index)).all()
E23.loc["España"], E26.loc["España"] = E23.sum(), E26.sum()
JUEGO["España"] = int(JUEGO.sum())
assert JUEGO["España"] == 350

# 2. Gráfico ------------------------------------------------------------------
ETIQ = {"PSOE": "PSOE", "PP": "PP", "Vox": "Vox",
        "Izq": "Sumar / Podemos\n/ F. Amplio", "ERC": "ERC", "Junts": "Junts",
        "EH Bildu": "EH Bildu", "PNV": "EAJ-PNV", "Otros": "BNG, CCa\ny UPN"}
PRINC = ["PSOE", "PP", "Vox", "Izq"]  # siempre se muestran, aunque sean 0
TERR = ["España", "Madrid", "Barcelona", "Salamanca"]
fig, axs = plt.subplots(2, 2, figsize=(13, 9.2), dpi=200,
                        gridspec_kw={"width_ratios": [1.55, 1]})
fig.subplots_adjust(left=0.05, right=0.985, top=0.80, bottom=0.16,
                    hspace=0.42, wspace=0.10)
LOG = []
for ax, t in zip(axs.flat, TERR):
    # Partidos con escaños en 2023 o 2026 en el territorio (más los 4 principales)
    cats = [k for k in ORDEN
            if k in PRINC or E23.loc[t, k] > 0 or E26.loc[t, k] > 0]
    xs = np.arange(len(cats))
    w = 0.38
    top = max(E23.loc[t, cats].max(), E26.loc[t, cats].max())
    fs = 8.8 if len(cats) > 6 else 10.5
    for xi, k in zip(xs, cats):
        a, b = int(E23.loc[t, k]), int(E26.loc[t, k])
        LOG.append(dict(territorio=t, partido=ETIQ[k].replace("\n", " "),
                        escanos_2023=a, escanos_est_2026=b, dif=b - a))
        ax.bar(xi - w / 2 - .01, a, w, color=aclarar(COL[k]), zorder=2)
        ax.bar(xi + w / 2 + .01, b, w, color=COL[k], zorder=2)
        ax.text(xi - w / 2 - .01, a + top * .02, str(a), ha="center",
                va="bottom", fontsize=fs, color=SUBTLE)
        ax.text(xi + w / 2 + .01, b + top * .02, str(b), ha="center",
                va="bottom", fontsize=fs + 1, fontweight=700)
        if b != a:
            ax.text(xi, top * 1.2, f"{'+' if b > a else '−'}{abs(b - a)}",
                    ha="center", va="bottom", fontsize=11, fontweight=700,
                    color=NARANJA)
    ax.set_title(f"{t} ({int(JUEGO[t])} escaños)", loc="left", fontsize=13.5,
                 fontweight=500, pad=8)
    ax.set_xticks(xs)
    ax.set_xticklabels([ETIQ[k] for k in cats], fontsize=8.0 if len(cats) > 6 else 8.4, color=SUBTLE,
                       linespacing=1.15)
    ax.set_ylim(0, max(top * 1.45, 2.4))
    paso = 1 if top <= 7 else (2 if top <= 16 else (5 if top <= 40 else 20))
    ax.set_yticks(range(0, int(top) + 1, paso))
    ax.tick_params(axis="x", length=0, pad=4)
    ax.tick_params(axis="y", length=0, labelsize=9.5, labelcolor=SUBTLE)
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#DCD8CC")

fig.legend(handles=[Patch(fc=aclarar("#5A6B6C"), label="Escaños actuales (generales 2023)"),
                    Patch(fc="#5A6B6C", label="Reparto estimado, promedio de encuestas nov. 2026")],
           loc="upper left", bbox_to_anchor=(0.05, 0.875), ncol=2,
           frameon=False, fontsize=10.5, handlelength=1.1, columnspacing=2)
fig.text(0.05, 0.965, "Escaños por territorio: los actuales y los estimados",
         fontsize=19, fontweight=500, va="top")
fig.text(0.05, 0.918, "Escaños de cada partido en el Congreso en España, Madrid, "
         "Barcelona y Salamanca: resultado de 2023 y estimación de 2026",
         fontsize=15, family=SERIFF, color=SUBTLE, va="top")
fig.text(0.05, 0.018,
         "Fuente: Ministerio del Interior (2023) y estimación propia a partir del promedio de encuestas a 1 de noviembre de 2026.\n"
         "Voto provincial = cuota nacional × ratio histórico provincia/España (generales 2011-2023, más peso a 2019 y 2023), reajustado a 100 %;\n"
         "reparto por D'Hondt con umbral del 3 %, listas separadas. «Sumar / Podemos / F. Amplio»: Sumar + Podemos en 2023; los tres en 2026.\n"
         "+/− = diferencia de escaños entre 2026 y 2023. Estimación puntual, no es un resultado.",
         fontsize=8.6, color=SUBTLE, va="bottom", linespacing=1.45)
firma_logo(fig)
fig.savefig(f"{OUT}/espana_escanos_territorio.png", facecolor="#fff")
pd.DataFrame(LOG).to_csv(f"{OUT}/espana_escanos_territorio_datos.csv",
                         index=False, encoding="utf-8-sig")
print(E23.loc["España"].to_dict(), E26.loc["España"].to_dict())
