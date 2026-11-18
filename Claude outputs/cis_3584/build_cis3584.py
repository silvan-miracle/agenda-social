"""CIS 3584 (preelectoral 29-N-2026, avance de resultados) -> CSVs en el formato de las variables comunes del dashboard.
Uso: python3 -I build_cis3584.py <excel> <carpeta_salida>   (antes: parse_cis3584.py)"""
import sys, os, pandas as pd, numpy as np
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
m = pd.read_pickle('marg.pkl'); c = pd.read_pickle('cruces.pkl')
ESTUDIO, FECHA, CAMPO = '3584', '2026-11', '2026-10-07/2026-10-30'

# --- 1. Agrupación de partidos al esquema del dashboard ---
def grupo_partido(cat):
    c_ = cat.strip()
    if c_ == 'PSOE': return 'PSOE'
    if c_ == 'PP': return 'PP'
    if c_ == 'VOX': return 'VOX'
    if c_.startswith('Frente Amplio'): return 'Sumar'            # sucesor de Sumar -> ver nota de ruptura
    if c_ == 'Podemos': return 'Podemos'
    if c_ == 'Se Acabó la Fiesta': return 'Se Acabó la Fiesta'
    if c_ in ('En blanco', 'Voto nulo'): return 'Voto en blanco/nulo'
    if c_ in ('No votaría', 'Ninguno'): return 'No votaría/Ninguno'
    if c_ in ('No sabe todavía', 'N.S.'): return 'No sabe'
    if c_ == 'N.C.': return 'No contesta'
    return 'Otros partidos'
MED = {'3R': 'intencion_directa', '5a': 'voto_simpatia'}

def n_row(g):  # n ponderada de cada grupo (fila (N))
    return g[g.categoria == '(N)'].set_index('grupo').valor

# --- 2. Total nacional ---
rows = []
for q, med in MED.items():
    d = m[(m.pregunta == q) & (~m.categoria.isin(['(N)']))].copy()
    d['grupo_dashboard'] = d.categoria.map(grupo_partido)
    for _, r in d.iterrows():
        rows.append(dict(estudio=ESTUDIO, fecha=FECHA, medida=med, categoria_original=r.categoria, grupo_dashboard=r.grupo_dashboard, valor=round(r.valor, 3), n_total=45074))
tot = pd.DataFrame(rows)
tot.to_csv(f'{out}/cis3584_voto_total.csv', index=False, encoding='utf-8-sig')
res = tot.groupby(['medida', 'grupo_dashboard']).valor.sum().round(2).unstack(0)
print(res); print('suma', res.sum().round(2).to_dict())

# --- 3. Voto x perfil (misma lógica que cis_votosim_perfiles: % del grupo sobre el total del grupo) ---
LAB = {  # cruce 'Ocupación' -> situación laboral agregada
 'Jubilado o pensionista (anteriormente ha trabajado)': 'Jubilado/a o pensionista', 'Estudiante': 'Estudiante',
 'Trabajo doméstico no remunerado': 'Trabajo doméstico no remunerado', 'Otra situación inactiva': 'Otra situación inactiva', 'Parados/as': 'Parado/a', 'N.C.': 'N.C.'}
def laboral(g): return LAB.get(g, 'Trabaja' if g not in ('TOTAL',) else 'TOTAL')
def tramo_ideo(g):
    if g in ('TOTAL', 'N.S.', 'N.C.'): return g
    k = int(g.split()[0]); return 'Izquierda (1-4)' if k <= 4 else 'Centro (5-6)' if k <= 6 else 'Derecha (7-10)'
PERFILES = {'CRUCE POR SEXO': ('sexo', lambda g: g), 'CRUCE POR EDAD': ('edad', lambda g: g), 'CRUCE POR ESTUDIOS': ('estudios', lambda g: g),
            'CRUCE POR IDENTIFICACIÓN SUBJETIVA': ('clase_social', lambda g: g), 'CRUCE POR POBLACIÓN ACTIVA': ('situacion_laboral', laboral),
            'CRUCE POR ESCALA': ('ideologia_tramos', tramo_ideo), 'CRUCE POR RELIGIOSIDAD': ('religiosidad', lambda g: g),
            'CRUCE POR PARTICIPACIÓN': ('recuerdo_voto_2023', lambda g: g)}
rows = []; filas_ideo = []
for key, (var, fmap) in PERFILES.items():
    cx = c[c.cruce.str.startswith(key)]
    for q, med in MED.items():
        d = cx[cx.pregunta == q]; N = n_row(d)
        d = d[d.categoria != '(N)'].copy(); d['gd'] = d.categoria.map(grupo_partido); d['gr'] = d.grupo.map(fmap)
        d['n'] = d.grupo.map(N); d['w'] = d.valor * d.n
        g = d.groupby(['gr', 'gd']).agg(w=('w', 'sum')).reset_index()
        nn = d.drop_duplicates('grupo').groupby('gr').n.sum()
        g['valor'] = g.w / g.gr.map(nn); g['n_grupo'] = g.gr.map(nn)
        for _, r in g.iterrows():
            rows.append(dict(estudio=ESTUDIO, fecha=FECHA, medida=med, variable=var, grupo=r.gr, partido=r.gd, valor=round(r.valor, 3), n_grupo=round(r.n_grupo, 1), flag_n_pequena='*' if r.n_grupo < 250 else ''))
    if var == 'sexo': pass
perf = pd.DataFrame(rows); perf = perf[perf.n_grupo >= 1]   # fuera grupos vacíos (p. ej. edad N.C.)
perf.to_csv(f'{out}/cis3584_voto_x_perfil.csv', index=False, encoding='utf-8-sig')
chk = perf[(perf.medida == 'voto_simpatia')].groupby(['variable', 'grupo']).valor.sum().round(1)
print('sumas perfil (debe 100):', chk.describe()[['min', 'max']].to_dict())

# --- 4. Transferencias: recuerdo 2023 (origen) -> intención (destino); % vertical de cada columna ---
cx = c[c.cruce.str.startswith('CRUCE POR PARTICIPACIÓN')]; rows = []
for q, med in MED.items():
    d = cx[(cx.pregunta == q)]; N = n_row(d); d = d[(d.categoria != '(N)') & (d.grupo != 'TOTAL')]
    for _, r in d.iterrows():
        rows.append(dict(estudio=ESTUDIO, fecha=FECHA, medida=med, origen_recuerdo_2023=r.grupo, destino_original=r.categoria, destino_dashboard=grupo_partido(r.categoria), valor=round(r.valor, 3), n_origen=round(N[r.grupo], 1), flag_n_pequena='*' if N[r.grupo] < 250 else ''))
tr = pd.DataFrame(rows); tr.to_csv(f'{out}/cis3584_transferencias.csv', index=False, encoding='utf-8-sig')
print('transf PSOE->', tr[(tr.medida == 'voto_simpatia') & (tr.origen_recuerdo_2023 == 'PSOE')].groupby('destino_dashboard').valor.sum().round(1).to_dict())

# --- 5. Ideología (C3): distribución, media, y media de los votantes de cada partido (voto+simpatía) ---
mi = m[(m.pregunta == 'C3')]; dist = mi.set_index('categoria').valor
rows = [dict(estudio=ESTUDIO, fecha=FECHA, concepto='distribucion', categoria=k, valor=round(v, 3)) for k, v in dist.items() if k not in ('Media', 'Desviación típica', 'N', '(N)')]
rows += [dict(estudio=ESTUDIO, fecha=FECHA, concepto='media_total', categoria='TOTAL', valor=dist['Media'])]
cx = c[c.cruce.str.startswith('CRUCE POR ESCALA')]; d = cx[cx.pregunta == '5a']; N = n_row(d)
d = d[(d.categoria != '(N)') & (d.grupo.str[0].str.isdigit())].copy(); d['gd'] = d.categoria.map(grupo_partido); d['k'] = d.grupo.str.split().str[0].astype(int); d['w'] = d.valor * d.grupo.map(N)
gg = d.groupby(['gd', 'k']).w.sum().reset_index(); mean = gg.groupby('gd').apply(lambda x: (x.k * x.w).sum() / x.w.sum())
nn = gg.groupby('gd').w.sum() / 100
for p in ['PSOE', 'PP', 'VOX', 'Sumar', 'Podemos', 'Se Acabó la Fiesta', 'Otros partidos']:
    rows.append(dict(estudio=ESTUDIO, fecha=FECHA, concepto='media_votantes_voto_simpatia', categoria=p, valor=round(mean[p], 2), n_aprox=round(nn[p])))
ideo = pd.DataFrame(rows); ideo.to_csv(f'{out}/cis3584_ideologia.csv', index=False, encoding='utf-8-sig'); print(ideo[ideo.concepto != 'distribucion'].to_string())

# --- 6. Líderes: valoración 1-10 (P10a), conocimiento (P10) y preferencia presidente (P11R) ---
p10 = m[(m.pregunta == '10')].pivot_table(index='categoria', columns='col', values='valor', aggfunc='first', sort=False)
p10a = m[(m.pregunta == '10a')].pivot_table(index='categoria', columns='col', values='valor', aggfunc='first', sort=False)
rows = []
for l in p10a.index:
    r = p10a.loc[l]; esc = [r[c_] for c_ in r.index if c_[0].isdigit() and c_ not in ('N',)][:10]
    esc = np.array([r[c_] for c_ in ['1 Muy mal', '2', '3', '4', '5', '6', '7', '8', '9', '10 Muy bien']])
    valid = esc.sum()
    rows.append(dict(estudio=ESTUDIO, fecha=FECHA, lider=l, conoce=round(p10.loc[l, 'Conoce'], 2), media=r['Media'], pct_6_10_sobre_quienes_puntuan=round(esc[5:].sum() / valid * 100, 1),
                     pct_6_10_sobre_base_pregunta=round(esc[5:].sum(), 1), pct_1_4=round(esc[:4].sum() / valid * 100, 1), n_base=r['(N)'], n_puntuan=r['N'],
                     aviso='incorporado el 21-oct (base menor)' if l in ('Ada Colau', 'Emilio Delgado', 'Gabriel Rufián', 'Irene Montero') else ''))
ld = pd.DataFrame(rows); ld.to_csv(f'{out}/cis3584_lideres.csv', index=False, encoding='utf-8-sig'); print(ld.to_string())
pr = m[(m.pregunta == '11R') & (m.categoria != '(N)')][['categoria', 'valor']].rename(columns={'categoria': 'lider'}); pr.insert(0, 'fecha', FECHA); pr.insert(0, 'estudio', ESTUDIO)
pr.to_csv(f'{out}/cis3584_pref_presidente.csv', index=False, encoding='utf-8-sig')

# --- 7. Estimación oficial del CIS (solo referencia: el CIS oficial NO entra en el promedio de encuestas) ---
import openpyxl
wb = openpyxl.load_workbook(sys.argv[2], read_only=True, data_only=True); rows = []
for r in list(wb["Estimación de Voto"].iter_rows(values_only=True))[9:31]:
    if r[0] is None: continue
    rows.append(dict(estudio=ESTUDIO, fecha=FECHA, partido=str(r[0]).strip(), voto_directo_sobre_censo=r[1] if isinstance(r[1], (int, float)) else None,
                     estimacion_voto_valido=r[3] if isinstance(r[3], (int, float)) else None, escanos=str(r[4]).strip() if r[4] else None))
pd.DataFrame(rows).to_csv(f'{out}/cis3584_estimacion_oficial.csv', index=False, encoding='utf-8-sig')
