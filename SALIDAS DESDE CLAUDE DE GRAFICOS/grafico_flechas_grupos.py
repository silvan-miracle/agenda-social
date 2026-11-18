# ==============================================================================
# Script:   grafico_flechas_grupos.py
# Objetivo: Gráfico de trayectorias curvas (estilo NYT) del margen izquierda-derecha
#           por grupo en tres momentos del CIS: sep-2019, jun-2023, oct-2026
# Inputs:   barómetros CIS 3261 (sep-19), 3410 (jun-23), 3582 (oct-26)
# Outputs:  grupos_flechas_cis.png y su CSV
# ==============================================================================
import sys
import re
import unicodedata
import numpy as np
import pandas as pd
import pyreadstat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb
from matplotlib.patches import Polygon

SCRIPTS, CISDIR, OUT, LOGO = sys.argv[1:5]
sys.path.insert(0, SCRIPTS)
from cis_comun import leer   # nombres canónicos de las preguntas comunes (en 2019 el CIS las llamaba P1, P2…)

# 0. Estilo -------------------------------------------------------------------
for f in fm.findSystemFonts():
    if "inter" in f.lower() and "display" not in f.lower():
        fm.fontManager.addfont(f)
SERIF_TTF = "/mnt/skills/examples/canvas-design/canvas-fonts/InstrumentSerif-Regular.ttf"
fm.fontManager.addfont(SERIF_TTF)
plt.rcParams["font.family"] = "Inter"   # sustituta de PP Neue Montreal
TEAL, NAR, CREMA, INK, GRIS = "#014550", "#FF723C", "#F3EFE4", "#1A1A1A", "#8A8678"
C_IZQ, C_DER = "#8E2C48", "#014550"   # púrpura = tramo en el lado de la izquierda; naranja = lado de la derecha
GRIS_CLARO = "#B9B4A5"

# 1. Momentos, bloques y variables de cada barómetro ---------------------------
# (archivo, año, variable de clase, de estudios, de recuerdo de voto 2019 o None)
MOM = {"sep. 2019": ("2019/3261_2019-09", 2019, "P45", "P35A", "P36"),
       "jun. 2023": ("2023/3410_2023-06", 2023, "CLASESUB", "NIVELESTENTREV", "RELIGION"),
       "oct. 2026": ("2026/3582_2026-10", 2026, "CLASESUB", "NIVELESTENTREV", "RELIGION")}
M1, M2, M3 = list(MOM)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# Bloques como en «Promedio de encuestas», salvo que Ciudadanos cuenta en la derecha
# (en 2019 pesaba ~13 %: sin él el margen de entonces no sería comparable). En 2019 se
# suman las marcas de izquierda que el CIS desglosaba y Navarra Suma cuenta como UPN.
IZQ = {"psoe", "podemos", "unidas podemos", "sumar", "movimiento sumar", "frente amplio",
       "erc", "eh bildu", "bng", "iu", "en comu podem", "compromis", "equo"}
DER = {"pp", "ciudadanos", "vox", "se acabo la fiesta", "upn", "na"}
NOVAL = {"voto nulo", "nulo", "en blanco", "no votaria", "ninguno", "no sabe todavia", "n s", "n c"}


def clase(l):
    n = norm(l)
    return "izq" if n in IZQ else ("der" if n in DER else ("nada" if n in NOVAL else "otro"))


def etiquetas_recuerdo(lab):
    """Recuerdo de voto 2019 -> grupo (solo los partidos grandes y la abstención)."""
    g = {}
    for k, v in lab.items():
        n = norm(v)
        if n == "psoe": g[k] = "PSOE"
        elif n == "pp": g[k] = "PP"
        elif n == "vox": g[k] = "Vox"
        elif n in ("c s", "cs"): g[k] = "Ciudadanos"
        elif n in ("unidas podemos", "up", "en comu podem", "en comun up"): g[k] = "Unidas Podemos"
        elif n == "no voto": g[k] = "No votó"
    return g


def grupos(df, anio, ccls, cest, crec, lab_rec):
    e, s = df.EDAD, df.SEXO
    nac = anio - e
    gen = pd.Series(np.select([nac >= 1997, nac >= 1981, nac >= 1965],
                              ["Generación Z", "Millennials", "Generación X"], "Boomers y mayores"), index=df.index)
    T = [("Todos", "Todos los votantes", pd.Series(True, index=df.index))]
    for g in ["Generación Z", "Millennials", "Generación X", "Boomers y mayores"]:
        T += [("Generación y sexo", f"{g}: hombres", (gen == g) & (s == 1)),
              ("Generación y sexo", f"{g}: mujeres", (gen == g) & (s == 2))]
    c = df[ccls]
    cl = ([("Alta y media-alta", [1, 2]), ("Media-media", [3]), ("Media-baja", [4]),
           ("Trabajadora y baja", [5, 6, 8, 9, 10])] if anio == 2019 else
          [("Alta y media-alta", [1]), ("Media-media", [2]), ("Media-baja", [3]),
           ("Trabajadora y baja", [4, 5])])
    T += [("Clase social subjetiva", n, c.isin(v)) for n, v in cl]
    es = df[cest]
    T += [("Nivel de estudios", "Hasta primaria", es.isin([1, 2])),
          ("Nivel de estudios", "ESO y FP básica", es.isin([3, 4])),
          ("Nivel de estudios", "Bachillerato y FP", es.isin([5, 6, 7])),
          ("Nivel de estudios", "Universitarios", es.between(8, 15))]
    rel = df[crec]   # mismos códigos en los tres barómetros
    T += [("Religiosidad", "Católicos practicantes", rel == 1),
          ("Religiosidad", "Católicos no practicantes", rel == 2),
          ("Religiosidad", "Agnósticos, indiferentes y ateos", rel.isin([4, 5, 6]))]
    return T


# 2. Cálculo ------------------------------------------------------------------
filas = []
for etq, (arch, anio, ccls, cest, crec) in MOM.items():
    df, m = leer(f"{CISDIR}/{arch}.sav", ["PESO", "VOTOSIMG", "SEXO", "EDAD"])
    extra = [ccls, cest, crec]
    dx, mx = pyreadstat.read_sav(f"{CISDIR}/{arch}.sav", usecols=extra, user_missing=True,
                                 apply_value_formats=False)
    for c_ in extra:
        df[c_] = dx[c_].values
    m.variable_value_labels.update({c_: mx.variable_value_labels.get(c_, {}) for c_ in extra})
    w = df["PESO"].fillna(1.0)   # 2019 viene sin ponderar (PESO vacío)
    cl = df.VOTOSIMG.map({k: clase(v) for k, v in m.variable_value_labels["VOTOSIMG"].items()})
    ok = cl.isin(["izq", "der", "otro"])   # base: quienes citan un partido
    for var, g, mk in grupos(df, anio, ccls, cest, crec, None):
        mm = mk & ok
        W = w[mm].sum()
        filas.append(dict(momento=etq, variable=var, grupo=g,
                          izq=w[mm & (cl == "izq")].sum() / W * 100, der=w[mm & (cl == "der")].sum() / W * 100,
                          n_validos=int(mm.sum())))
r = pd.DataFrame(filas)
r["margen"] = r.izq - r.der
p = r.pivot_table(index=["variable", "grupo"], columns="momento", values=["margen", "n_validos"], sort=False)
p.columns = [f"{a}_{b}" for a, b in p.columns]
p = p.reset_index()
p.to_csv(f"{OUT}/grupos_flechas_cis_datos.csv", index=False, encoding="utf-8-sig")
pd.set_option("display.width", 220)
print(p.round(1).to_string())


# 3. Trazo curvo (como el del NYT: sale del punto, da la vuelta en el 2.º momento y vuelve con flecha) --
def bezier(p0, p1, p2, p3, k=60):
    t = np.linspace(0, 1, k)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * (t ** 2) * p2 + (t ** 3) * p3


def trayectoria(ax, y, xs, span, lane=0.27, cx=0.0, lw=3.0):
    """Devuelve (punto del 2.º momento, punta). El tramo se pinta púrpura a un lado de cx y naranja al otro."""
    x0, x1, x2 = xs
    A = np.array
    yA, yB = y + lane, y - lane
    s1 = np.sign(x1 - x0) or 1
    s2 = np.sign(x2 - x1) or s1
    seg1, seg2 = abs(x1 - x0), abs(x2 - x1)
    dmax = 0.075 * span                     # cuánto sobresale la curva: más espacio = vuelta más redonda
    if seg2 < 1.0:                           # casi sin cambio: esquina redondeada y flecha hacia abajo
        r = 0.045 * span
        r = min(r, 0.8 * seg1) if seg1 > 0.5 else r
        c = bezier(A([x1 - s1 * r, yA]), A([x1, yA]), A([x1, yA]), A([x1, yA - 0.2]), k=30)
        pts = np.vstack([[x0, yA], c, [x1, yB + 0.17]])
        L = np.r_[0, np.cumsum(np.hypot(*(pts[1:] - pts[:-1]).T))]
        t = np.linspace(0, L[-1], 700)
        P = np.c_[np.interp(t, L, pts[:, 0]), np.interp(t, L, pts[:, 1])]
        seg = np.stack([P[:-1], P[1:]], axis=1)
        cols = [C_IZQ if (a_[0] + b_[0]) / 2 < cx else C_DER for a_, b_ in seg]
        ax.add_collection(LineCollection(seg, colors=cols, linewidths=lw, capstyle="round", joinstyle="round", zorder=3))
        colf = C_IZQ if x1 < cx else C_DER
        hw = 0.012 * span
        ax.add_patch(Polygon([[x1, yB - 0.02], [x1 - hw, yB + 0.2], [x1 + hw, yB + 0.2]], closed=True,
                             color=colf, zorder=4, lw=0))
        return (x1, y), (x1, yB), s1
    if s1 != s2 and min(seg1, seg2) >= 0.9:   # giro: «U» con el vértice en x1
        d = min(dmax, 0.8 * seg1, 0.8 * seg2)
        c = bezier(A([0.0, yA]), A([s1 * 1.55 * d, yA]), A([s1 * 1.55 * d, yB]), A([0.0, yB]))
        c[:, 0] += x1 - (c[:, 0].max() if s1 > 0 else c[:, 0].min())   # el vértice de la «U» cae justo en x1
        ap2 = c[0, 0]
        pts = np.vstack([[x0, yA], [ap2, yA], c, [x2, yB]])
    else:                                    # mismo sentido (o cambio mínimo): «S» suave
        w = max(min(0.45 * seg1, 0.95 * seg2, 0.07 * span), 0.1)
        c = bezier(A([x1 - s1 * w, yA]), A([x1, yA]), A([x1, yB]), A([x1 + s2 * w, yB]))
        pts = np.vstack([[x0, yA], c, [x2, yB]])
    # Densificar y pintar por lado
    L = np.r_[0, np.cumsum(np.hypot(*(pts[1:] - pts[:-1]).T))]
    t = np.linspace(0, L[-1], 700)
    P = np.c_[np.interp(t, L, pts[:, 0]), np.interp(t, L, pts[:, 1])]
    seg = np.stack([P[:-1], P[1:]], axis=1)
    cols = [C_IZQ if (a_[0] + b_[0]) / 2 < cx else C_DER for a_, b_ in seg]
    ax.add_collection(LineCollection(seg, colors=cols, linewidths=lw, capstyle="round", joinstyle="round", zorder=3))
    direc = np.sign(x2 - pts[-2][0]) or -s1
    hl = min(0.032 * span, max(0.8 * abs(x2 - (pts[-2][0] if len(pts) > 2 else x1)), 0.5))
    colf = C_IZQ if x2 < cx else C_DER
    fin = (x2, yB)
    ax.add_patch(Polygon([[fin[0] + direc * 0.15, fin[1]], [fin[0] - direc * hl, fin[1] + 0.15],
                          [fin[0] - direc * hl, fin[1] - 0.15]], closed=True, color=colf, zorder=4, lw=0))
    return (x1, y), fin, direc


def fmt(m):
    return "0" if abs(m) < 0.5 else (f"I+{round(m)}" if m > 0 else f"D+{round(-m)}")


# 4. Gráfico ------------------------------------------------------------------
F = []
d = p[p.variable == "Generación y sexo"]
for g in ["Generación Z", "Millennials", "Generación X", "Boomers y mayores"]:
    F.append(("h", g, None))
    for sx in ["hombres", "mujeres"]:
        q = d[d.grupo == f"{g}: {sx}"].iloc[0]
        F.append(("r", sx.capitalize(), q))
n = len(F)
ROW = 0.62                                   # pulgadas por fila: más aire para que la curva respire
fig = plt.figure(figsize=(9.4, ROW * n + 4.0), dpi=200)
fig.patch.set_facecolor(CREMA)
H = fig.get_figheight()
ax = fig.add_axes([0.25, 1.55 / H, 0.70, (ROW * n) / H])
ax.set_facecolor(CREMA)
tr = ax.get_yaxis_transform()
XLIM = (-50, 30)
span = XLIM[1] - XLIM[0]
for i, (k, nombre, q) in enumerate(F):
    y = -i
    if k == "h":
        ax.text(-0.02, y, nombre, transform=tr, ha="right", va="center", fontsize=11, fontweight=500, color=TEAL)
        if i > 0:
            ax.axhline(y + 0.5, color="#CFCABB", lw=0.8, ls=(0, (1, 2.5)))
        continue
    v = [q[f"margen_{m}"] for m in (M1, M2, M3)]
    xs = [-a for a in v]                       # izquierda a la izquierda
    ns = [q[f"n_validos_{m}"] for m in (M1, M2, M3)]
    mid, fin, direc = trayectoria(ax, y, xs, span)
    c0 = C_IZQ if xs[0] < 0 else C_DER
    c1 = C_IZQ if xs[1] < 0 else C_DER
    ax.scatter([xs[0]], [y + 0.27], s=34, color=c0, edgecolor=CREMA, linewidth=0.8, zorder=6)
    ax.scatter([xs[1]], [y], s=14, color=c1, edgecolor=CREMA, linewidth=0.6, zorder=6)
    ax.text(-0.02, y, nombre + ("*" if min(ns) < 300 else ""), transform=tr, ha="right", va="center",
            fontsize=10.8 if "Todos" in nombre else 9.8, fontweight="bold" if "Todos" in nombre else "normal", color=INK)
    ax.text(fin[0] + direc * 1.1, fin[1], fmt(v[2]), ha="left" if direc > 0 else "right", va="center",
            fontsize=8.6, color=INK, fontweight="bold")
ax.axvline(0, color=INK, lw=1)
ticks = list(range(-50, 31, 10))
ax.set_xticks(ticks)
ax.set_xticklabels(["Izq. +50" if t == -50 else ("Der. +30" if t == 30 else ("0" if t == 0 else f"+{abs(t)}"))
                    for t in ticks], fontsize=8, color=GRIS)
ax.set_xlim(*XLIM)
ax.set_ylim(-n + 0.45, 0.75)
ax.xaxis.tick_top(); ax.tick_params(length=0)
for t_ in ticks:
    ax.axvline(t_, color="#E2DDCF", lw=0.7, zorder=0)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.set_yticks([])
ax.annotate("◄ MÁS BLOQUE DE LA IZQUIERDA", xy=(-1, 1), xycoords=ax.get_xaxis_transform(), xytext=(0, 20), textcoords="offset points",
            fontsize=8.6, fontweight="bold", color=C_IZQ, ha="right", va="bottom")
ax.annotate("MÁS BLOQUE DE LA DERECHA ►", xy=(1, 1), xycoords=ax.get_xaxis_transform(), xytext=(0, 20), textcoords="offset points",
            fontsize=8.6, fontweight="bold", color=C_DER, ha="left", va="bottom")

# Cabecera y leyenda-ejemplo (un recorrido de muestra, como la clave del NYT)
fig.text(0.035, 1 - 0.30 / H, "Los hombres jóvenes giran a la derecha;\nlos mayores vuelven a la izquierda", fontsize=31,
         family="Instrument Serif", color=TEAL, ha="left", va="top", linespacing=0.95)
fig.text(0.035, 1 - 1.34 / H, "Diferencia, en puntos, entre el bloque de la izquierda y el de la derecha en la intención de voto (o, si no la dicen, la simpatía)\n"
         "declarada al CIS, por generación y sexo, en tres momentos: sep. 2019, jun. 2023 y oct. 2026.",
         fontsize=9.2, color="#3A3A36", ha="left", va="top", linespacing=1.5)
kax = ax.inset_axes([0.60, 0.035, 0.34, 0.15])   # clave en el hueco libre de la derecha
kax.set_xlim(0, 10); kax.set_ylim(-1.05, 1.05); kax.axis("off"); kax.set_zorder(10)
from matplotlib.patches import Rectangle
kax.add_patch(Rectangle((-0.9, -0.9), 12.4, 2.55, transform=kax.transData, facecolor=CREMA, edgecolor="#CFCABB",
                        lw=0.8, zorder=0, clip_on=False))
kax.text(-0.3, 1.12, "Cómo leerlo", fontsize=7.6, fontweight="bold", color=INK, va="bottom")
mid, fin, direc = trayectoria(kax, 0, [2.0, 8.2, 3.4], 10, lane=0.42, cx=5.6, lw=2.6)
kax.scatter([2.0], [0.42], s=34, color=C_IZQ, edgecolor=CREMA, linewidth=0.8, zorder=6)
kax.scatter([8.2], [0], s=14, color=C_DER, edgecolor=CREMA, linewidth=0.6, zorder=6)
kax.text(1.7, 0.42, "sep. 2019", ha="right", va="center", fontsize=7.6, color=INK)
kax.text(9.3, 0.0, "jun. 2023", ha="left", va="center", fontsize=7.6, color=INK)
kax.text(3.1, -0.42, "oct. 2026", ha="right", va="center", fontsize=7.6, color=INK, fontweight="bold")
fig.text(0.035, 0.22 / H,
         "Fuente: CIS, barómetros 3261 (sep. 2019, sin ponderar), 3410 (jun. 2023) y 3582 (oct. 2026); pregunta «voto + simpatía» (a quien no dice a quién votaría, se le pregunta por qué partido siente más simpatía).\n"
         "Cifra = % que votaría (o simpatiza con) un partido de izquierda − % de derecha (I+11: la izquierda saca 11 puntos más). No cuentan blanco, nulo, no votaría ni NS/NC.\n"
         "Izquierda: PSOE, Sumar / Podemos / Frente Amplio, ERC, EH Bildu, BNG (2019 también IU, En Comú Podem, Compromís, EQUO). Derecha: PP, Cs, Vox, SALF, UPN.\n"
         "Junts, PNV y CCa solo cuentan en la base. Generación por año de nacimiento: Z 1997-2012, Millennials 1981-96, X 1965-80, Boomers ≤1964.\n"
         "* Menos de 300 entrevistas válidas en algún momento.",
         fontsize=6.6, color=GRIS, ha="left", va="bottom", linespacing=1.55)
img = plt.imread(LOGO)
w_in = 1.5
lax = fig.add_axes([0.975 - w_in / fig.get_figwidth(), 0.22 / H, w_in / fig.get_figwidth(),
                    w_in * img.shape[0] / img.shape[1] / H])
lax.imshow(img, alpha=0.9); lax.axis("off")
fig.savefig(f"{OUT}/grupos_flechas_cis.png", facecolor=CREMA)
