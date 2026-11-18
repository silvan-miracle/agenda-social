# ==============================================================================
# Script:   grafico_flechas_provincias.py
# Objetivo: Gráfico de flechas (estilo NYT) del cambio de margen izquierda-derecha
#           por provincia: generales 2023 -> estimación 2026
# Inputs:   datos/margen_provincias_2023_2026.csv
# Outputs:  espana_flechas_provincias.png
# ==============================================================================
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

CSV, OUT, SERIF, LOGO = sys.argv[1:5]

# 0. Estilo (el de la previsualización de perfiles) ----------------------------
for f in fm.findSystemFonts():
    if "inter" in f.lower() and "display" not in f.lower():
        fm.fontManager.addfont(f)
fm.fontManager.addfont(SERIF)
plt.rcParams["font.family"] = "Inter"
TEAL, NAR, CREMA, INK, GRIS = "#014550", "#FF723C", "#F3EFE4", "#1A1A1A", "#8A8678"

# 1. Datos: España + provincias agrupadas por comunidad -----------------------
d = pd.read_csv(CSV)
d["ccaa"] = d.ccaa.replace({"": "Ceuta y Melilla", "Ceuta": "Ceuta y Melilla", "Melilla": "Ceuta y Melilla"}).fillna("Ceuta y Melilla")
w = d.escanos  # peso de cada provincia: escaños en juego (aprox. peso electoral)
# España: se pondera por votos; como aproximación robusta, por escaños de 2023
esp = dict(provincia="España", margen_pre=12.3, margen_2023=2.23, margen_2026=-10.41)  # media ponderada por votos válidos
tam = d.groupby("ccaa").agg(esc=("escanos", "sum"), np_=("provincia", "count"))
multi = tam[(tam.np_ > 1) & (tam.index != "Ceuta y Melilla")].sort_values("esc", ascending=False).index
uni = tam[(tam.np_ == 1)].sort_values("esc", ascending=False).index
filas = [("g", "España", esp)]
# Comunidades pluriprovinciales, cada una con su cabecera
for c in multi:
    filas.append(("h", c, None))
    for r in d[d.ccaa == c].sort_values("margen_2026").itertuples():
        filas.append(("r", r.provincia, dict(margen_pre=r.margen_pre, margen_2023=r.margen_2023, margen_2026=r.margen_2026)))
# Comunidades de una sola provincia, juntas bajo una cabecera común
filas.append(("h", "Una sola provincia", None))
for c in uni:
    r = d[d.ccaa == c].iloc[0]
    filas.append(("r", r.provincia, dict(margen_pre=r.margen_pre, margen_2023=r.margen_2023, margen_2026=r.margen_2026)))
filas.append(("h", "Ceuta y Melilla", None))
for r in d[d.ccaa == "Ceuta y Melilla"].sort_values("margen_2026").itertuples():
    filas.append(("r", r.provincia, dict(margen_pre=r.margen_pre, margen_2023=r.margen_2023, margen_2026=r.margen_2026)))
n = len(filas)

# 2. Dibujo -------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9.2, 0.205 * n + 2.2), dpi=200)
fig.patch.set_facecolor(CREMA); ax.set_facecolor(CREMA)
tr = ax.get_yaxis_transform()
for i, (k, nombre, v) in enumerate(filas):
    y = -i
    if k == "h":
        ax.text(-0.015, y, nombre, transform=tr, ha="right", va="center",
                fontsize=9.6, fontweight="bold", color=INK)
        ax.axhline(y + 0.5, color="#CFCABB", lw=0.8, ls=(0, (1, 2.5)))
        continue
    a, b, r23 = -v["margen_pre"], -v["margen_2026"], -v["margen_2023"]   # izquierda a la izquierda
    col = NAR if b < a else TEAL
    ax.annotate("", xy=(b, y), xytext=(a, y), arrowprops=dict(
        arrowstyle="-|>,head_width=0.22,head_length=0.45", color=col, lw=2.2,
        shrinkA=0, shrinkB=0))
    ax.scatter([a], [y], s=26, color=col, zorder=5)
    # Resultado real del 23J: rombo hueco de referencia
    ax.scatter([r23], [y], s=22, marker="D", facecolor=CREMA, edgecolor=INK, linewidth=1.0, zorder=6)
    m = v["margen_2026"]
    txt = "Empate" if abs(m) < 0.5 else (f"Izq. +{round(m)}" if m > 0 else f"Der. +{round(-m)}")
    lado = 1 if b >= a else -1
    ax.text(b + lado * 1.2, y, txt, fontsize=7.6, color=INK, va="center",
            ha="left" if lado > 0 else "right")
    resalta = nombre == "Salamanca" or k == "g"
    ax.text(-0.015, y, nombre if k == "g" else "   " + nombre, transform=tr,
            ha="right", va="center", fontsize=8.8 if k != "g" else 10,
            fontweight="bold" if resalta else "normal", color=INK)
ax.axvline(0, color=INK, lw=1)
ticks = [-50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50]
ax.set_xticks(ticks)
ax.set_xticklabels(["Izq. +50", "+40", "+30", "+20", "+10", "0", "Der. +10",
                    "+20", "+30", "+40", "+50"], fontsize=7.6, color=GRIS)
ax.set_xlim(-62, 58)
ax.set_ylim(-n + 0.2, 1.8)
ax.xaxis.tick_top(); ax.tick_params(length=0)
for t in ticks:
    ax.axvline(t, color="#E2DDCF", lw=0.7, zorder=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_yticks([])
ax.text(-1, 1.05, "◄ MÁS IZQUIERDA", fontsize=7.8, fontweight="bold", color=NAR,
        ha="right")
ax.text(1, 1.05, "MÁS DERECHA ►", fontsize=7.8, fontweight="bold", color=TEAL,
        ha="left")
H = fig.get_figheight()
fig.text(0.04, 1 - 0.35 / H, "Cómo se estima que ha cambiado cada provincia: justo antes del 23J y ahora",
         fontsize=16, fontweight="bold", color=TEAL, ha="left", va="top")
fig.text(0.04, 1 - 0.78 / H, "Ventaja del bloque de izquierda sobre el de derecha, en puntos de voto: estimación justo antes del 23J de 2023 y estimación actual",
         fontsize=8.8, color=INK, ha="left", va="top")
fig.text(0.04, 1 - 1.02 / H, "●  justo antes del 23J (CIS, jun. 2023)    ◇  resultado real del 23J    →  hoy (promedio de encuestas, nov. 2026).",
         fontsize=8.2, color=GRIS, ha="left", va="top")
fig.text(0.04, 0.2 / H,
         "Fuente: CIS (barómetro 3410, junio de 2023, voto directo + simpatía), Ministerio del Interior (resultado del 23J) y promedio de encuestas a 1 de noviembre de 2026.\n"
         "Cada momento se reparte por provincias con el ratio histórico de cada partido (el de antes del 23J, solo con generales hasta nov. 2019; el de hoy, hasta 2023, con más peso a 2019 y 2023).\n"
         "Izquierda = PSOE + Sumar / Podemos / Frente Amplio + ERC + EH Bildu + BNG; derecha = PP + Vox + SALF + UPN. Margen = izquierda − derecha, en % de votos válidos.\n"
         "Ojo: el CIS de junio de 2023 daba a la izquierda +12 sobre la derecha y el resultado fue +2, así que parte de la flecha es el sesgo del CIS y no un cambio real. Estimación, no un resultado.",
         fontsize=6.6, color=GRIS, ha="left", va="bottom", linespacing=1.5)
fig.subplots_adjust(left=0.215, right=0.97, top=1 - 1.45 / H, bottom=1.0 / H)
fig.savefig(f"{OUT}/espana_flechas_provincias_pre23J.png", facecolor=CREMA)
print(n)
