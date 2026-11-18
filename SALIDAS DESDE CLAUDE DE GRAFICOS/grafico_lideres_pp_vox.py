# ==============================================================================
# Script:   grafico_lideres_pp_vox.py
# Objetivo: Valoración media de los 4 líderes entre quienes votaron al PP en 2023,
#           según se queden en el PP o se pasen a Vox (CIS 3582, oct. 2026)
# Inputs:   cis/2026/3582_2026-10.sav
# Outputs:  lideres_pp_vox.png y lideres_pp_vox_datos.csv
# ==============================================================================
import sys
import numpy as np
import pandas as pd
import pyreadstat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

SAV, OUT, LOGO = sys.argv[1:4]
for f in fm.findSystemFonts():
    if "inter" in f.lower() and "display" not in f.lower():
        fm.fontManager.addfont(f)
fm.fontManager.addfont("/mnt/skills/examples/canvas-design/canvas-fonts/InstrumentSerif-Regular.ttf")
plt.rcParams["font.family"] = "Inter"
TEAL, CREMA, INK, GRIS = "#014550", "#F3EFE4", "#1A1A1A", "#8A8678"
C_PP, C_VOX = "#014550", "#5E8C31"      # se quedan en el PP / se pasan a Vox

# 1. Datos --------------------------------------------------------------------
df, m = pyreadstat.read_sav(SAV, user_missing=True, apply_value_formats=False)
pp23 = df.RECUVOTOG == 2
G = {"Se pasan a Vox": pp23 & (df.VOTOSIMG == 3), "Se quedan en el PP": pp23 & (df.VOTOSIMG == 2)}
LID = [("Pedro Sánchez", "VALORALIDERES_1"), ("Yolanda Díaz", "VALORALIDERES_3"),
       ("Alberto Núñez Feijóo", "VALORALIDERES_2"), ("Santiago Abascal", "VALORALIDERES_4")]
filas = []
for g, mk in G.items():
    for nom, c in LID:
        v, w = df[c][mk], df.PESO[mk]
        ok = v.between(1, 10)               # sin N.S./N.C./N.P.
        mu = (v[ok] * w[ok]).sum() / w[ok].sum()
        var = (w[ok] * (v[ok] - mu) ** 2).sum() / w[ok].sum()
        neff = w[ok].sum() ** 2 / (w[ok] ** 2).sum()
        filas.append(dict(grupo=g, lider=nom, media=mu, ic95=1.96 * np.sqrt(var / neff),
                          n_validos=int(ok.sum()), n_grupo=int(mk.sum())))
r = pd.DataFrame(filas)
r.to_csv(f"{OUT}/lideres_pp_vox_datos.csv", index=False, encoding="utf-8-sig")
print(r.round(2).to_string())

# 2. Gráfico ------------------------------------------------------------------
fig = plt.figure(figsize=(9.4, 7.0), dpi=200)
fig.patch.set_facecolor(CREMA)
H = fig.get_figheight()
ax = fig.add_axes([0.25, 1.4 / H, 0.70, 3.3 / H])
ax.set_facecolor(CREMA)
for i, (nom, _) in enumerate(LID):
    y = -i
    a = r[(r.grupo == "Se quedan en el PP") & (r.lider == nom)].iloc[0]
    b = r[(r.grupo == "Se pasan a Vox") & (r.lider == nom)].iloc[0]
    ax.plot([a.media, b.media], [y, y], color="#CFCABB", lw=4, solid_capstyle="round", zorder=2)
    for q, col in ((a, C_PP), (b, C_VOX)):
        ax.plot([q.media - q.ic95, q.media + q.ic95], [y, y], color=col, lw=1.2, alpha=0.55, zorder=3)
        ax.scatter([q.media], [y], s=120, color=col, edgecolor=CREMA, linewidth=1.2, zorder=5)
    # valores: el más bajo a su izquierda, el más alto a su derecha
    lo, hi = sorted([(a, C_PP), (b, C_VOX)], key=lambda t: t[0].media)
    ax.text(lo[0].media - lo[0].ic95 - 0.15, y, f"{lo[0].media:.1f}".replace(".", ","), ha="right", va="center",
            fontsize=10.5, fontweight=600, color=lo[1])
    ax.text(hi[0].media + hi[0].ic95 + 0.15, y, f"{hi[0].media:.1f}".replace(".", ","), ha="left", va="center",
            fontsize=10.5, fontweight=600, color=hi[1])
    ax.text(-0.02, y, nom, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=10.5,
            fontweight=600 if nom in ("Alberto Núñez Feijóo", "Santiago Abascal") else 400, color=INK)
ax.set_xlim(-0.6, 10.3)
ax.set_ylim(-len(LID) + 0.5, 0.5)
ax.set_xticks(range(1, 11))
ax.set_xticklabels(["1\nMuy mal"] + [str(i) for i in range(2, 10)] + ["10\nMuy bien"], fontsize=8.4, color=GRIS)
ax.xaxis.tick_bottom(); ax.tick_params(length=0, pad=6)
for t in range(1, 11):
    ax.axvline(t, ymin=0, ymax=1, color="#E2DDCF", lw=0.7, zorder=0)
ax.axvline(5, color=INK, lw=0.9, zorder=1)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_yticks([])
nv = int(r[r.grupo == "Se pasan a Vox"].n_grupo.iloc[0]); npp = int(r[r.grupo == "Se quedan en el PP"].n_grupo.iloc[0])
# leyenda propia
fig.text(0.25, 1 - 1.62 / H, "●", color=C_VOX, fontsize=13, va="center")
fig.text(0.275, 1 - 1.62 / H, f"Votaron al PP en 2023 y hoy votarían a Vox ({nv} entrevistas)", fontsize=9.2, va="center", color=INK)
fig.text(0.25, 1 - 1.9 / H, "●", color=C_PP, fontsize=13, va="center")
fig.text(0.275, 1 - 1.9 / H, f"Votaron al PP en 2023 y hoy votarían al PP ({npp} entrevistas)", fontsize=9.2, va="center", color=INK)
fig.text(0.035, 1 - 0.30 / H, "Los votantes del PP que se pasan a Vox\npuntúan a Abascal por encima de Feijóo", fontsize=26,
         family="Instrument Serif", color=TEAL, ha="left", va="top", linespacing=0.95)
fig.text(0.035, 1 - 1.18 / H, "Valoración media de cada líder, de 1 a 10, entre quienes votaron al PP en 2023, según lo que votarían hoy.",
         fontsize=9.2, color="#3A3A36", ha="left", va="top")
fig.text(0.035, 0.22 / H,
         "Fuente: CIS, barómetro 3582 (oct. 2026), ponderado. Intención de voto o, si no la dicen, simpatía; recuerdo de voto en las generales de 2023.\n"
         "Medias sin N.S./N.C. La línea fina de cada punto es el intervalo de confianza al 95 %. Los que se pasan a Vox son una base pequeña: orientativo.",
         fontsize=6.7, color=GRIS, ha="left", va="bottom", linespacing=1.55)
img = plt.imread(LOGO)
w_in = 1.5
lax = fig.add_axes([0.975 - w_in / fig.get_figwidth(), 0.22 / H, w_in / fig.get_figwidth(),
                    w_in * img.shape[0] / img.shape[1] / H])
lax.imshow(img, alpha=0.9); lax.axis("off")
fig.savefig(f"{OUT}/lideres_pp_vox.png", facecolor=CREMA)
