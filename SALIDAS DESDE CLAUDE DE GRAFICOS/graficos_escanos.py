# ==============================================================================
# Script:   graficos_escanos.py
# Objetivo: Escaños por territorio en Euskadi: los de las generales de 2023
#           («lo que hay») y el reparto estimado por el Sociómetro (oct. 2026).
# Inputs:   datos/generales_euskadi_1977_2023.csv (Interior); reparto de
#           escaños 2026 transcrito del PDF de oct. 2026 (pp. 5-8)
# Outputs:  euskadi_escanos_territorio.png y su CSV
# ==============================================================================
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Patch

CSV, OUT, SERIF, LOGO = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

# 0. Estilo Matiz -------------------------------------------------------------
fm.fontManager.addfont(SERIF)
SANS, SERIFF = "Inter", "Instrument Serif"
TINTA, SUBTLE, GRID, TEAL = "#1A1A1A", "#5A6B6C", "#EEEBE3", "#014550"
NARANJA = "#FF723C"
COL = {"PSOE": "#E5393B", "PNV": "#1B7A3D", "EH Bildu": "#4FB5AE",
       "PP": "#1E73C4", "Izq": "#6A2C91", "Vox": "#8BC34A"}
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


# 1. Escaños de 2023 (Interior) -----------------------------------------------
d = pd.read_csv(CSV)
d23 = d[d.eleccion == "2023"].copy()
d23["provincia"] = d23.provincia.replace({"Araba/Álava": "Araba"})
M = {"PSOE": "PSOE", "PNV": "PNV", "HB / Amaiur / EH Bildu": "EH Bildu",
     "PP": "PP", "Podemos / UP / Sumar": "Izq", "Vox": "Vox"}
d23["p"] = d23.linea.map(M)
E23 = (d23.dropna(subset=["p"]).groupby(["provincia", "p"]).escanos.sum()
          .unstack(fill_value=0).reindex(columns=list(M.values()), fill_value=0))
E23.loc["Euskadi"] = E23.sum()
JUEGO = d23.drop_duplicates("provincia").set_index("provincia").escanos_provincia
JUEGO["Euskadi"] = JUEGO.sum()
assert (E23.sum(axis=1) == JUEGO.reindex(E23.index)).all(), E23.sum(axis=1)

# 2. Reparto estimado 2026 (PDF) ----------------------------------------------
# El Frente Amplio, Vox y Podemos no obtienen escaño en ninguna provincia.
E26 = pd.DataFrame(
    {"PSOE": [5, 1, 2, 2], "PNV": [4, 1, 2, 1], "EH Bildu": [7, 1, 3, 3],
     "PP": [2, 1, 1, 0], "Izq": [0, 0, 0, 0], "Vox": [0, 0, 0, 0]},
    index=["Euskadi", "Araba", "Bizkaia", "Gipuzkoa"])
assert (E26.sum(axis=1) == JUEGO.reindex(E26.index)).all(), E26.sum(axis=1)

# 3. Gráfico ------------------------------------------------------------------
CATS = [("PSOE", "PSOE"), ("PNV", "EAJ-PNV"), ("EH Bildu", "EH Bildu"),
        ("PP", "PP"), ("Izq", "Sumar / Podemos\n/ F. Amplio"), ("Vox", "Vox")]
fig, axs = plt.subplots(2, 2, figsize=(13, 9.2), dpi=200)
fig.subplots_adjust(left=0.05, right=0.985, top=0.80, bottom=0.16,
                    hspace=0.42, wspace=0.12)
LOG = []
for ax, t in zip(axs.flat, ["Euskadi", "Araba", "Bizkaia", "Gipuzkoa"]):
    xs = np.arange(len(CATS))
    w = 0.38
    top = max(E23.loc[t].max(), E26.loc[t].max())
    for xi, (k, lab) in zip(xs, CATS):
        a, b = int(E23.loc[t, k]), int(E26.loc[t, k])
        LOG.append(dict(territorio=t, partido=lab.replace("\n", " "),
                        escanos_2023=a, escanos_est_2026=b, dif=b - a))
        ax.bar(xi - w / 2 - .01, a, w, color=aclarar(COL[k]), zorder=2)
        ax.bar(xi + w / 2 + .01, b, w, color=COL[k], zorder=2)
        ax.text(xi - w / 2 - .01, a + top * .02, str(a), ha="center",
                va="bottom", fontsize=10.5, color=SUBTLE)
        ax.text(xi + w / 2 + .01, b + top * .02, str(b), ha="center",
                va="bottom", fontsize=11.5, fontweight=700)
        if b != a:
            ax.text(xi, top * 1.2, f"{'+' if b > a else '−'}{abs(b - a)}",
                    ha="center", va="bottom", fontsize=11, fontweight=700,
                    color=NARANJA)
    ax.set_title(f"{t} ({int(JUEGO[t])} escaños)", loc="left", fontsize=13.5,
                 fontweight=500, pad=8)
    ax.set_xticks(xs)
    ax.set_xticklabels([c[1] for c in CATS], fontsize=8.8, color=SUBTLE,
                       linespacing=1.15)
    ax.set_ylim(0, max(top * 1.45, 2.4))
    ax.set_yticks(range(0, int(top) + 1, 1 if top <= 7 else 2))
    ax.tick_params(axis="x", length=0, pad=4)
    ax.tick_params(axis="y", length=0, labelsize=9.5, labelcolor=SUBTLE)
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#DCD8CC")

fig.legend(handles=[Patch(fc=aclarar("#5A6B6C"), label="Escaños actuales (generales 2023)"),
                    Patch(fc="#5A6B6C", label="Reparto estimado, Sociómetro oct. 2026")],
           loc="upper left", bbox_to_anchor=(0.05, 0.875), ncol=2,
           frameon=False, fontsize=10.5, handlelength=1.1, columnspacing=2)
fig.text(0.05, 0.965, "Escaños por territorio: los actuales y los estimados",
         fontsize=19, fontweight=500, va="top")
fig.text(0.05, 0.918, "Escaños de cada partido en el Congreso por Araba, Bizkaia "
         "y Gipuzkoa: resultado de 2023 y estimación de 2026", fontsize=15,
         family=SERIFF, color=SUBTLE, va="top")
fig.text(0.05, 0.018,
         "Fuente: Ministerio del Interior (2023) y Sociómetro (Gabinete de Prospección "
         "Sociológica, Gobierno Vasco), trabajo de campo 20-23 oct. 2026, n = 3.485.\n"
         "Reparto 2026 por ley D'Hondt sobre la estimación de voto de cada territorio. "
         "«Sumar / Podemos / F. Amplio»: Sumar + Podemos en 2023; Frente Amplio +\n"
         "Podemos en 2026. +/− = diferencia de escaños entre 2026 y 2023.",
         fontsize=8.6, color=SUBTLE, va="bottom", linespacing=1.45)
firma_logo(fig)
fig.savefig(f"{OUT}/euskadi_escanos_territorio.png", facecolor="#fff")
pd.DataFrame(LOG).to_csv(f"{OUT}/euskadi_escanos_territorio_datos.csv",
                         index=False, encoding="utf-8-sig")
print(E23, E26)
