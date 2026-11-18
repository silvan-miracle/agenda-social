# ==============================================================================
# Script:   graficos_indecisos.py
# Objetivo: Comparar el «No sabe» a un mes de las elecciones generales: 2023
#           (trabajo de campo 20-23 jun. 2023, generales del 23-J) frente a la
#           previsión de oct. 2026 (20-23 oct.). Estética Matiz.
# Inputs:   datos/generales_euskadi_1977_2023.csv (solo para ponderar Euskadi
#           por el censo), PDFs del Gabinete de Prospección Sociológica
#           (23tef6_aurreikuspena.pdf y eb0aa319-26sv90_aurreikuspenak.pdf)
# Outputs:  euskadi_indecisos_1_mes.png y su CSV
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
plt.rcParams.update({"font.family": SANS, "text.color": TINTA})


def firma_logo(fig, ancho_in=1.9, derecha=0.985, abajo=0.016):
    """Logo de Silván & Miracle abajo a la derecha, como en Matiz."""
    img = plt.imread(LOGO)
    w = ancho_in / fig.get_figwidth()
    h = ancho_in * img.shape[0] / img.shape[1] / fig.get_figheight()
    lax = fig.add_axes([derecha - w, abajo, w, h])
    lax.imshow(img, alpha=0.9)
    lax.axis("off")


def coma(x, d=1):
    """Número con coma decimal (formato español)."""
    return f"{x:.{d}f}".replace(".", ",")


# 1. Datos: «No sabe» (% sobre la muestra, intención directa) -----------------
# 2023: PDF 23tef6, pp. 2-4 (n = 400 / 603 / 450). 2026: PDF oct. 2026, pp. 5-7
# (n = 800 / 1.485 / 1.200).
NS = pd.DataFrame({"anio2023": {"Araba": 21.0, "Bizkaia": 21.4, "Gipuzkoa": 21.6},
                   "anio2026": {"Araba": 30.3, "Bizkaia": 26.4, "Gipuzkoa": 27.2}})

# Euskadi: los PDFs no dan el «No sabe» del conjunto. Se pondera por el censo
# de 2023 de cada territorio (el mismo peso en las dos fechas, para que la
# diferencia no dependa de los pesos).
d = pd.read_csv(CSV)
cen = (d[d.eleccion == "2023"].drop_duplicates("provincia")
         .set_index("provincia").censo)
cen.index = cen.index.str.replace("Araba/Álava", "Araba")
w = (cen / cen.sum()).reindex(NS.index)
NS.loc["Euskadi"] = (NS.mul(w, axis=0)).sum()
NS = NS.loc[["Euskadi", "Araba", "Bizkaia", "Gipuzkoa"]]
NS["dif_pp"] = NS.anio2026 - NS.anio2023

# 2. Gráfico ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 7.2), dpi=200)
fig.subplots_adjust(left=0.07, right=0.97, top=0.78, bottom=0.23)
x = np.array([0, 1.3, 2.3, 3.3])         # hueco tras Euskadi (dato derivado)
bw = 0.36
C23, C26 = "#B8C9CB", TEAL
for xi, (t, r) in zip(x, NS.iterrows()):
    ax.bar(xi - bw / 2 - .01, r.anio2023, bw, color=C23, zorder=2)
    ax.bar(xi + bw / 2 + .01, r.anio2026, bw, color=C26, zorder=2)
    ax.text(xi - bw / 2 - .01, r.anio2023 + .5, coma(r.anio2023) + " %",
            ha="center", va="bottom", fontsize=11, color=SUBTLE)
    ax.text(xi + bw / 2 + .01, r.anio2026 + .5, coma(r.anio2026) + " %",
            ha="center", va="bottom", fontsize=12, fontweight=700)
    ax.text(xi, 35.2, f"+{coma(r.dif_pp)} pp".replace("+-", "−"),
            ha="center", va="bottom", fontsize=11.5, fontweight=700,
            color=NARANJA)
ax.axvline(0.65, color="#DCD8CC", lw=1, ls=(0, (4, 3)), zorder=0)
ax.set_xticks(x)
ax.set_xticklabels(["Euskadi*", "Araba", "Bizkaia", "Gipuzkoa"], fontsize=12.5)
ax.set_ylim(0, 40)
ax.set_yticks(range(0, 41, 10))
ax.set_yticklabels([f"{v} %" for v in range(0, 41, 10)])
ax.tick_params(axis="x", length=0, pad=8)
ax.tick_params(axis="y", length=0, labelsize=10.5, labelcolor=SUBTLE)
ax.tick_params(axis="x", labelcolor=TINTA)
ax.yaxis.grid(True, color=GRID, lw=1)
ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#DCD8CC")
ax.legend(handles=[Patch(fc=C23, label="Un mes antes de las generales de 2023 (20-23 jun.)"),
                   Patch(fc=C26, label="Oct. 2026 (20-23 oct.)")],
          loc="upper left", bbox_to_anchor=(-0.005, 1.14), ncol=1,
          frameon=False, fontsize=11, handlelength=1.1)

fig.text(0.07, 0.965, "Indecisos un mes antes de las elecciones generales",
         fontsize=19, fontweight=500, va="top")
fig.text(0.07, 0.915, "% de la muestra que responde «No sabe» a la intención "
         "directa de voto, Euskadi 2023 y 2026", fontsize=15, family=SERIFF,
         color=SUBTLE, va="top")
fig.text(0.07, 0.018,
         "Fuente: Sociómetro (Gabinete de Prospección Sociológica, Gobierno Vasco). "
         "2023: n = 1.453 (400 Araba, 603 Bizkaia, 450 Gipuzkoa). 2026: n = 3.485 "
         "(800, 1.485, 1.200).\n"
         "Intención directa sin ajustar, % sobre la muestra. pp = puntos porcentuales.\n"
         "Los cuestionarios y la muestra no son idénticos (cuotas y ponderación distintas "
         "en 2026): la comparación es orientativa.\n"
         "*Euskadi: media de los tres territorios ponderada por el censo de 2023 "
         "(dato propio, no publicado).",
         fontsize=8.6, color=SUBTLE, va="bottom", linespacing=1.45)
firma_logo(fig, derecha=0.97)
fig.savefig(f"{OUT}/euskadi_indecisos_1_mes.png", facecolor="#fff")
NS.round(1).reset_index(names="territorio").to_csv(
    f"{OUT}/euskadi_indecisos_1_mes_datos.csv", index=False, encoding="utf-8-sig")
print(NS.round(2), w.round(3))
