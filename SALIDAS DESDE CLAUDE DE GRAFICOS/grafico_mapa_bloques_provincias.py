# ==============================================================================
# Script:   grafico_mapa_bloques_provincias.py
# Objetivo: Mapa de España por provincias: dónde va mejor cada bloque en las
#           últimas generales (23J 2023) y cómo cambió respecto a nov. 2019
# Inputs:   datos/generales_provincias.csv, config/provincias_espana.geojson
# Outputs:  mapa_bloques_provincias_23J.png, mapa_bloques_provincias_datos.csv
# Uso:      python grafico_mapa_bloques_provincias.py CSV GEOJSON SALIDA_DIR
# ==============================================================================
import sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib import font_manager as fm

CSV, GEO, OUT, LOGO = sys.argv[1:5]

# 0. Estilo (paleta del resto de gráficos del proyecto) ------------------------
fuentes = {f.name for f in fm.fontManager.ttflist}
plt.rcParams["font.family"] = "Inter" if "Inter" in fuentes else "DejaVu Sans"
SERIF = "Instrument Serif"
# Tokens del dashboard Matiz (template.html): Inter + Instrument Serif, tarjeta blanca con borde
TEAL, NAR, INK, MUT, GRID = "#014550", "#FF723C", "#1A1A1A", "#5A6B6C", "#DCD8CC"
SIN_DATO, BORDE = "#DCD8CC", "#FFFFFF"
SERIF_TTF = "/mnt/skills/examples/canvas-design/canvas-fonts/InstrumentSerif-Regular.ttf"
fm.fontManager.addfont(SERIF_TTF)

# 1. Datos: margen izquierda − derecha en % de votos válidos -------------------
# Mismos bloques que el resto del proyecto (gráfico de flechas por provincia)
IZQ = ["PSOE", "Podemos / UP / Sumar", "ERC", "HB / Amaiur / EH Bildu", "BNG"]
DER = ["PP", "Vox", "Cs", "UPN"]
d = pd.read_csv(CSV)
d = d[d.eleccion.isin(["2019-11", "2023-07"])].copy()
d["bloque"] = d.linea.map(lambda l: "izq" if l in IZQ else ("der" if l in DER else "otros"))
p = d.pivot_table(index=["cod", "provincia"], columns=["eleccion", "bloque"],
                  values="pct_validos", aggfunc="sum").fillna(0)
m = pd.DataFrame({"cod": [i[0] for i in p.index], "provincia": [i[1] for i in p.index]})
for e, s in [("2019-11", "19"), ("2023-07", "23")]:
    m["izq_" + s] = p[(e, "izq")].values
    m["der_" + s] = p[(e, "der")].values
m["margen_19"] = m.izq_19 - m.der_19      # >0: ventaja de la izquierda
m["margen_23"] = m.izq_23 - m.der_23
m["cambio"] = m.margen_23 - m.margen_19   # >0: se mueve hacia la izquierda
m.round(2).to_csv(f"{OUT}/mapa_bloques_provincias_datos.csv", index=False)
M = m.set_index("cod")
n_izq, n_der = int((m.margen_23 > 0).sum()), int((m.margen_23 < 0).sum())

# 2. Geometría -----------------------------------------------------------------
geo = json.load(open(GEO, encoding="utf-8"))["features"]
def anillos(g):
    return [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
def centroide(g):
    # Centroide del polígono más grande (evita que las islas arrastren el punto)
    mejor, area_max = None, -1
    for poly in anillos(g):
        xy = np.array(poly[0]); x, y = xy[:, 0], xy[:, 1]
        a = 0.5 * np.sum(x[:-1] * y[1:] - x[1:] * y[:-1])
        if abs(a) > area_max:
            area_max = abs(a)
            cx = np.sum((x[:-1] + x[1:]) * (x[:-1] * y[1:] - x[1:] * y[:-1])) / (6 * a)
            cy = np.sum((y[:-1] + y[1:]) * (x[:-1] * y[1:] - x[1:] * y[:-1])) / (6 * a)
            mejor = (cx, cy)
    return mejor
cent = {f["properties"]["cod"]: centroide(f["geometry"]) for f in geo if f["properties"]["cod"] != 0}

def base(ax, color_fn):
    for f in geo:
        c = f["properties"]["cod"]
        for poly in anillos(f["geometry"]):
            if c == 0:   # recuadro de Canarias: solo el contorno
                ax.add_patch(Polygon(np.array(poly[0]), closed=True, facecolor="none",
                                     edgecolor=MUT, linewidth=0.6))
                continue
            ax.add_patch(Polygon(np.array(poly[0]), closed=True, facecolor=color_fn(c),
                                 edgecolor=BORDE, linewidth=0.6))
    xs = [pt[0] for f in geo for poly in anillos(f["geometry"]) for pt in poly[0]]
    ys = [pt[1] for f in geo for poly in anillos(f["geometry"]) for pt in poly[0]]
    ax.set_xlim(min(xs) - 0.3, max(xs) + 0.3); ax.set_ylim(min(ys) - 0.3, max(ys) + 0.3)
    ax.set_aspect(1 / np.cos(np.radians(40)))   # corrige la deformación de lon/lat
    ax.axis("off")

# 3. Figura con el aspecto de una tarjeta del dashboard -------------------------
from matplotlib.patches import FancyBboxPatch
from matplotlib.image import imread
W, H = 13.2, 8.9
fig = plt.figure(figsize=(W, H), dpi=200, facecolor="white")
# Tarjeta: fondo blanco, borde 1 px #DCD8CC, esquinas casi rectas
fig.add_artist(FancyBboxPatch((0.004, 0.006), 0.992, 0.988, boxstyle="round,pad=0,rounding_size=0.004",
               transform=fig.transFigure, facecolor="none", edgecolor=GRID, linewidth=1.2, zorder=0))
a1 = fig.add_axes([0.03, 0.30, 0.45, 0.50]); a2 = fig.add_axes([0.52, 0.30, 0.45, 0.50])
LIM = 35
cmap = LinearSegmentedColormap.from_list("bloques", [TEAL, "#3E8A93", "#EDE6D3", "#FFA27D", NAR])
norm = Normalize(-LIM, LIM)       # negativo = derecha (teal), positivo = izquierda (naranja)
base(a1, lambda c: cmap(norm(np.clip(M.loc[c, "margen_23"], -LIM, LIM))))
base(a2, lambda c: SIN_DATO)

# Flechas: longitud proporcional al cambio de margen, inclinadas hacia el bloque que gana terreno
ESC = 0.30                        # grados de longitud por punto de cambio
for c, (x, y) in cent.items():
    v = M.loc[c, "cambio"]
    if abs(v) < 0.5:
        a2.scatter([x], [y], s=6, color=MUT, zorder=4); continue
    L = abs(v) * ESC
    dx = -np.sign(v) * L * 0.62   # izquierda = hacia arriba-izquierda
    dy = L * 0.78 / (1 / np.cos(np.radians(40)))
    col = NAR if v > 0 else TEAL
    a2.annotate("", xy=(x + dx / 2, y + dy / 2), xytext=(x - dx / 2, y - dy / 2),
                arrowprops=dict(arrowstyle="-|>,head_width=0.22,head_length=0.5",
                                color=col, lw=1.9, shrinkA=0, shrinkB=0), zorder=5)

# Cabecera de tarjeta: h3 Inter 500 + subtítulo en Instrument Serif
X0 = 0.03
fig.text(X0, 0.955, "Así votó cada provincia el 23J: la derecha gana en %d y la izquierda en %d" % (n_der, n_izq),
         fontsize=17, fontweight="medium", color=INK, ha="left", va="top")
fig.text(X0, 0.915, "Ventaja del bloque de izquierda sobre el de derecha en las últimas generales (julio de 2023) y cambio desde noviembre de 2019.",
         fontsize=14, family=SERIF, color=MUT, ha="left", va="top")
a1.set_title("Dónde le va mejor a cada bloque", fontsize=11, fontweight="medium", color=INK, loc="left", pad=4)
a2.set_title("Hacia dónde se movió desde 2019", fontsize=11, fontweight="medium", color=INK, loc="left", pad=4)

# Leyenda del relleno: barra de color
cax = fig.add_axes([0.03, 0.235, 0.30, 0.013])
cb = fig.colorbar(ScalarMappable(norm, cmap), cax=cax, orientation="horizontal")
cb.outline.set_visible(False); cax.tick_params(length=0, labelsize=8, colors=MUT)
cb.set_ticks([-30, -15, 0, 15, 30]); cb.set_ticklabels(["Der. +30", "+15", "Empate", "Izq. +15", "+30"])
fig.text(0.03, 0.272, "Ventaja de cada bloque, en puntos de voto (23J 2023)", fontsize=8.5, color=INK, ha="left")

# Leyenda de flechas
fig.text(0.52, 0.272, "Cambio de esa ventaja respecto a las generales de nov. 2019", fontsize=8.5, color=INK, ha="left")
fig.text(0.52, 0.235, "◄ gana terreno la izquierda", fontsize=9, color=NAR, fontweight="semibold", ha="left")
fig.text(0.72, 0.235, "gana terreno la derecha ►", fontsize=9, color=TEAL, fontweight="semibold", ha="left")
fig.text(0.52, 0.205, f"Longitud proporcional a los puntos de cambio (la mayor: {abs(m.cambio).max():.0f} puntos, {m.loc[m.cambio.abs().idxmax(), 'provincia']}).",
         fontsize=8, color=MUT, ha="left")

# Nota al pie (foot-note: Inter 11.5 px, color #5A6B6C) y logo de la tarjeta
fig.text(X0, 0.145,
         "Fuente: Ministerio del Interior (resultados del Congreso por provincia, 23J 2023 y 10N 2019). Margen = izquierda − derecha, en % de votos válidos de cada provincia.\n"
         "Izquierda = PSOE + Sumar / Podemos / UP + ERC + EH Bildu + BNG; derecha = PP + Vox + Cs + UPN. Quedan fuera PNV, Junts, CC y otras candidaturas (UPyD, Teruel Existe, ¡Soria ya!…).\n"
         "Por eso en Cataluña, Euskadi, Navarra y Canarias izquierda y derecha no suman 100. Cuenta provincias, no escaños: una provincia pequeña pesa igual que una grande en el titular.\n"
         "Canarias, Ceuta y Melilla, fuera de su posición real.",
         fontsize=7.8, color=MUT, ha="left", va="top", linespacing=1.55)
logo = imread(LOGO)
axl = fig.add_axes([0.80, 0.03, 0.17, 0.17 * (W / H) * logo.shape[0] / logo.shape[1] * (H / W) ])
axl.imshow(logo); axl.axis("off")
fig.savefig(f"{OUT}/mapa_bloques_provincias_23J.png", facecolor="white")
print(n_izq, n_der)
