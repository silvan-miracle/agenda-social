# ==============================================================================
# Script:   graficos_euskadi.py
# Objetivo: Dos gráficos con estética Matiz sobre las elecciones generales en
#           Euskadi: (1) partido ganador y sus escaños 1977-2026 (2026 =
#           estimación Sociómetro) y (2) estimación 2026 por territorio frente
#           al resultado de las generales de 2023.
# Inputs:   datos/generales_euskadi_1977_2023.csv (Interior, vía dashboard)
#           PDF «Hauteskunde Orokorrak: Boto-aurreikuspena» (oct. 2026),
#           transcrito a mano en la sección 2 (pp. 5-8 del PDF)
# Outputs:  PNG en la carpeta de salida
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
COL = {"PSOE": "#E5393B", "PNV": "#1B7A3D", "EH Bildu": "#4FB5AE",
       "PP": "#1E73C4", "Podemos": "#6A2C91", "Vox": "#8BC34A",
       "Izq": "#6A2C91", "Otros": "#C9C5B8"}
plt.rcParams.update({"font.family": SANS, "text.color": TINTA,
                     "axes.edgecolor": GRID, "axes.labelcolor": SUBTLE})


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


def aclarar(hexcol, f=0.62):
    """Mezcla un color con blanco: columna clara = resultado de 2023."""
    c = np.array(matplotlib.colors.to_rgb(hexcol))
    return tuple(c + (1 - c) * f)


def cabecera(fig, titulo, subt, pie, x0=0.045):
    """Título (Inter medium), subtítulo (Instrument Serif) y pie de fuente."""
    fig.text(x0, 0.965, titulo, fontsize=19, fontweight=500, va="top")
    fig.text(x0, 0.918, subt, fontsize=15, family=SERIFF, color=SUBTLE, va="top")
    fig.text(x0, 0.018, pie, fontsize=8.6, color=SUBTLE, va="bottom",
             linespacing=1.45)
    firma_logo(fig)


# 1. Datos de Interior: agregado de Euskadi -----------------------------------
d = pd.read_csv(CSV)
EUSK = (d.groupby(["eleccion", "linea"], sort=False)
          .agg(v=("votos", "sum"), e=("escanos", "sum")).reset_index())
VAL = (d.drop_duplicates(["eleccion", "provincia"])
         .groupby("eleccion", sort=False)
         .agg(val=("votos_validos", "sum"), juego=("escanos_provincia", "sum")))
EUSK = EUSK.join(VAL, on="eleccion")
EUSK["pct"] = 100 * EUSK.v / EUSK.val

# Partido ganador = más escaños; si hay empate, el más votado (criterio Matiz)
gan = []
for el, g in EUSK.groupby("eleccion", sort=False):
    g = g.sort_values(["e", "pct"], ascending=False)
    empate = (g.e.iloc[0] == g.e.iloc[1])
    gan.append(dict(eleccion=el, linea=g.linea.iloc[0], esc=int(g.e.iloc[0]),
                    juego=int(g.juego.iloc[0]), pct=g.pct.iloc[0],
                    empate=empate, estimacion=False))
gan = pd.DataFrame(gan)
NOMBRE = {"PNV": "PNV", "PSOE": "PSOE", "HB / Amaiur / EH Bildu": "EH Bildu",
          "Podemos / UP / Sumar": "Podemos / UP / Sumar"}
gan["partido"] = gan.linea.map(NOMBRE)
gan["color"] = gan.partido.map({"PNV": COL["PNV"], "PSOE": COL["PSOE"],
                                "EH Bildu": COL["EH Bildu"],
                                "Podemos / UP / Sumar": COL["Podemos"]})

# 2. Estimación Sociómetro oct. 2026 (PDF, pp. 5-8) ---------------------------
# % sobre votos válidos: PSOE, PNV, EH Bildu, PP, Frente Amplio, Vox, Podemos,
# Otros+Blancos. Escaños de Euskadi: PSOE 5, PNV 4, EH Bildu 7, PP 2 (18).
EST = pd.DataFrame({
    "PSOE":      {"Euskadi": 24.7, "Araba": 27.9, "Bizkaia": 25.0, "Gipuzkoa": 22.8},
    "PNV":       {"Euskadi": 21.9, "Araba": 15.1, "Bizkaia": 24.7, "Gipuzkoa": 20.3},
    "EH Bildu":  {"Euskadi": 29.1, "Araba": 23.7, "Bizkaia": 25.9, "Gipuzkoa": 36.9},
    "PP":        {"Euskadi": 12.6, "Araba": 19.7, "Bizkaia": 13.0, "Gipuzkoa": 8.8},
    "FA":        {"Euskadi": 4.0,  "Araba": 4.3,  "Bizkaia": 4.1,  "Gipuzkoa": 3.6},
    "Vox":       {"Euskadi": 4.8,  "Araba": 4.7,  "Bizkaia": 4.8,  "Gipuzkoa": 4.8},
    "Podemos":   {"Euskadi": 1.5,  "Araba": 2.7,  "Bizkaia": 1.1,  "Gipuzkoa": 1.5},
    "Otros":     {"Euskadi": 1.4,  "Araba": 1.9,  "Bizkaia": 1.4,  "Gipuzkoa": 1.3},
})
SUMA = EST.sum(axis=1)
assert (SUMA.sub(100).abs() < 0.25).all(), SUMA   # control: ~100 % por redondeo

# 3. Gráfico 1: partido ganador y escaños -------------------------------------
LAB = {"2019 (abr)": "2019\n(abr)", "2019 (nov)": "2019\n(nov)"}
x = np.arange(len(gan) + 1)
fig, ax = plt.subplots(figsize=(13, 7.2), dpi=200)
fig.subplots_adjust(left=0.045, right=0.985, top=0.80, bottom=0.20)

# Columna clara de fondo = escaños en juego en Euskadi en cada elección
juego = list(gan.juego) + [18]
ax.bar(x, juego, width=0.78, color="#F3EFE4", zorder=1)
for xi, j in zip(x, juego):
    ax.text(xi, j + 0.25, str(j), ha="center", va="bottom", fontsize=8.5,
            color=SUBTLE)

# Columnas del partido ganador (1977-2023)
ax.bar(x[:-1], gan.esc, width=0.78, color=gan.color, zorder=2)
for xi, r in zip(x[:-1], gan.itertuples()):
    ax.text(xi, r.esc - 0.35, str(r.esc), ha="center", va="top", color="#fff",
            fontsize=13, fontweight=700, zorder=3)
    ax.text(xi, 0.35, ("†" if r.empate else ""), ha="center", va="bottom",
            color="#fff", fontsize=11, fontweight=700, zorder=3)

# Columna 2026 = estimación Sociómetro (rayada, para distinguirla del dato real)
ax.bar(x[-1], 7, width=0.78, color=aclarar(COL["EH Bildu"], .55),
       edgecolor=COL["EH Bildu"], hatch="////", linewidth=1.4, zorder=2)
ax.text(x[-1], 7 - 0.35, "7", ha="center", va="top", fontsize=13,
        fontweight=700, color=TEAL, zorder=3,
        bbox=dict(boxstyle="round,pad=0.18", fc="#fff", ec="none", alpha=.9))
ax.axvline(x[-1] - 0.5, color=SUBTLE, lw=1, ls=(0, (4, 3)), zorder=0)

# Ejes
ax.set_xticks(x)
ax.set_xticklabels([LAB.get(e, e) for e in gan.eleccion] + ["2026"],
                   fontsize=10.5, color=SUBTLE)
ax.text(x[-1], -2.35, "(estimación\nSociómetro)", ha="center", va="top",
        fontsize=8.8, color=TEAL, fontweight=600, linespacing=1.2)
ax.set_ylim(0, 23)
ax.set_yticks(range(0, 23, 5))
ax.tick_params(axis="x", length=0, pad=6)
ax.tick_params(axis="y", length=0, labelsize=10.5, labelcolor=SUBTLE)
ax.yaxis.grid(True, color=GRID, lw=1)
ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#DCD8CC")
ax.set_ylabel("Escaños", fontsize=10.5, color=SUBTLE)

# Leyenda (solo partidos que ganan alguna vez)
hand = [Patch(fc=COL[k], label=k) for k in
        ["PNV", "PSOE", "EH Bildu", "Podemos"]]
hand[3].set_label("Podemos / UP / Sumar")
hand += [Patch(fc="#F3EFE4", label="Escaños en juego en Euskadi"),
         Patch(fc=aclarar(COL["EH Bildu"], .55), ec=COL["EH Bildu"],
               hatch="////", label="Estimación (no es resultado)")]
ax.legend(handles=hand, loc="upper center", bbox_to_anchor=(0.5, 1.115),
          ncol=6, frameon=False, fontsize=10, handlelength=1.1,
          columnspacing=1.6)

cabecera(fig, "Partido ganador en Euskadi y sus escaños",
         "Escaños del partido con más escaños en cada elección general, "
         "1977-2023, y estimación del Sociómetro para 2026",
         "Fuente: Ministerio del Interior (1977-2023) y Sociómetro (Gabinete de "
         "Prospección Sociológica, Gobierno Vasco), trabajo de campo 20-23 oct. 2026, "
         "n = 3.485.\n"
         "Partido ganador = más escaños; si hay empate (†: 1982, 1996, 2000, 2004 y "
         "2023, donde PSOE, PNV y EH Bildu empatan a 5), el más votado. "
         "EH Bildu incluye HB y Amaiur.")
fig.savefig(f"{OUT}/euskadi_partido_ganador_escanos.png", facecolor="#fff")
plt.close(fig)

# 4. Gráfico 2: estimación 2026 por territorio frente a 2023 ------------------
# 2023 por territorio (% sobre votos válidos); «Izq» = Podemos / UP / Sumar
d23 = d[d.eleccion == "2023"].copy()
M23 = {"PSOE": "PSOE", "PNV": "PNV", "HB / Amaiur / EH Bildu": "EH Bildu",
       "PP": "PP", "Podemos / UP / Sumar": "Izq", "Vox": "Vox"}
terr = {"Euskadi": None, "Araba": "Araba/Álava", "Bizkaia": "Bizkaia",
        "Gipuzkoa": "Gipuzkoa"}
R23 = {}
for t, p in terr.items():
    g = d23 if p is None else d23[d23.provincia == p]
    val = g.drop_duplicates("provincia").votos_validos.sum()
    por = g.groupby("linea").votos.sum()
    r = {M23[k]: 100 * por.get(k, 0) / val for k in M23}
    r["Otros"] = 100 - sum(r.values())          # otros partidos + en blanco
    R23[t] = r

CATS = [("PSOE", "PSOE", "PSOE"), ("PNV", "EAJ-PNV", "PNV"),
        ("EH Bildu", "EH Bildu", "EH Bildu"), ("PP", "PP", "PP"),
        ("Izq", "Sumar / Podemos\n/ F. Amplio", "Izq"), ("Vox", "Vox", "Vox"),
        ("Otros", "Otros\n+ blancos", "Otros")]
fig, axs = plt.subplots(2, 2, figsize=(13, 9.2), dpi=200, sharey=True)
fig.subplots_adjust(left=0.045, right=0.985, top=0.80, bottom=0.135,
                    hspace=0.42, wspace=0.07)
LOG = []
for ax, t in zip(axs.flat, terr):
    xs = np.arange(len(CATS))
    w = 0.38
    for xi, (k, lab, c) in zip(xs, CATS):
        v23 = R23[t][k]
        v26 = (EST.loc[t, "FA"] + EST.loc[t, "Podemos"]) if k == "Izq" \
            else EST.loc[t, k]
        LOG.append(dict(territorio=t, partido=lab.replace("\n", " "),
                        pct_2023=round(v23, 1), pct_est_2026=v26,
                        dif_pp=round(v26 - v23, 1)))
        ax.bar(xi - w / 2 - .01, v23, w, color=aclarar(COL[c]), zorder=2)
        ax.bar(xi + w / 2 + .01, v26, w, color=COL[c], zorder=2)
        ax.text(xi - w / 2 - .01, v23 + .5, coma(v23), ha="center",
                va="bottom", fontsize=7.6, color=SUBTLE)
        ax.text(xi + w / 2 + .01, v26 + .5, coma(v26), ha="center",
                va="bottom", fontsize=8.4, fontweight=700)
    ax.set_title(t if t != "Euskadi" else "Euskadi (suma territorial)",
                 loc="left", fontsize=13.5, fontweight=500, pad=8)
    ax.set_xticks(xs)
    ax.set_xticklabels([c[1] for c in CATS], fontsize=8.6, color=SUBTLE,
                       linespacing=1.15)
    ax.set_ylim(0, 44)
    ax.set_yticks(range(0, 41, 10))
    ax.set_yticklabels([f"{v} %" for v in range(0, 41, 10)])
    ax.tick_params(axis="x", length=0, pad=4)
    ax.tick_params(axis="y", length=0, labelsize=9.5, labelcolor=SUBTLE)
    ax.yaxis.grid(True, color=GRID, lw=1)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#DCD8CC")
for ax in axs[:, 1]:
    ax.tick_params(axis="y", labelleft=False)

fig.legend(handles=[Patch(fc=aclarar("#5A6B6C"), label="Generales 2023 (resultado)"),
                    Patch(fc="#5A6B6C", label="Estimación Sociómetro, oct. 2026")],
           loc="upper left", bbox_to_anchor=(0.045, 0.875), ncol=2,
           frameon=False, fontsize=10.5, handlelength=1.1, columnspacing=2)
cabecera(fig, "Voto previsto en cada territorio frente a las generales de 2023",
         "% sobre votos válidos: resultado de 2023 (columna clara) y estimación "
         "del Sociómetro de octubre de 2026",
         "Fuente: Ministerio del Interior (2023) y Sociómetro (Gabinete de Prospección "
         "Sociológica, Gobierno Vasco), trabajo de campo 20-23 oct. 2026, n = 3.485.\n"
         "«Sumar / Podemos / F. Amplio»: en 2023, Sumar + Podemos; en 2026, Frente "
         "Amplio + Podemos (el Frente Amplio no existía en 2023).\n"
         "«Otros + blancos»: resto de candidaturas y voto en blanco.")
fig.savefig(f"{OUT}/euskadi_estimacion_vs_2023_territorios.png", facecolor="#fff")
plt.close(fig)

pd.DataFrame(LOG).to_csv(f"{OUT}/euskadi_estimacion_vs_2023_datos.csv",
                         index=False, encoding="utf-8-sig")
gan.drop(columns="color").to_csv(f"{OUT}/euskadi_partido_ganador_datos.csv",
                                 index=False, encoding="utf-8-sig")
print(gan[["eleccion", "partido", "esc", "juego", "pct", "empate"]])
print(pd.DataFrame(LOG).query("territorio=='Euskadi'"))
