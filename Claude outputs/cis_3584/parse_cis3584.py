"""Lee el Excel de avance del CIS 3584 (preelectoral 2026) y lo convierte a formato largo.
Salida: una fila por pregunta x categoría x grupo (cruce) con %, y n ponderada del grupo."""
import sys, re, openpyxl, pandas as pd

F = sys.argv[1]
wb = openpyxl.load_workbook(F, read_only=True, data_only=True)

def clean(s):
    return re.sub(r'\s+', ' ', str(s).replace('_x000D_', ' ')).strip() if s is not None else None

def parse_marginal(ws):
    rows = list(ws.iter_rows(values_only=True)); out = []; i = 0
    while i < len(rows):
        a = rows[i][0]
        if a and str(a).startswith('Pregunta '):
            q = str(a).replace('Pregunta ', '').strip(); texto = clean(rows[i+1][0]); j = i+2
            cols = ['valor']
            if rows[j][0] in (None, '') and any(c is not None for c in rows[j][1:]):
                cols = [clean(c) for c in rows[j][1:] if c is not None]; j += 1
            while j < len(rows):
                r = rows[j]
                if r[0] is None and all(c is None for c in r): j += 1; break
                lab = clean(r[0])
                if lab and lab.startswith('(N)'):
                    for k, c in enumerate(cols):
                        out.append(dict(pregunta=q, texto=texto, categoria='(N)', col=c, valor=r[1+k]))
                elif lab and lab not in ('Media', 'Desviación típica', 'N'):
                    for k, c in enumerate(cols):
                        out.append(dict(pregunta=q, texto=texto, categoria=lab, col=c, valor=r[1+k]))
                elif lab in ('Media', 'Desviación típica', 'N'):
                    out.append(dict(pregunta=q, texto=texto, categoria=lab, col=cols[0], valor=r[1]))
                j += 1
            i = j
        else: i += 1
    return pd.DataFrame(out)

def parse_cruce(ws):
    rows = list(ws.iter_rows(values_only=True)); out = []; i = 0
    cruce = clean(rows[3][1])
    while i < len(rows):
        a = rows[i][0]
        if a and str(a).startswith('Pregunta '):
            q = a.replace('Pregunta ', '').strip(); texto = clean(rows[i+1][0]); j = i+2
            # fila de título de grupo + cabecera
            while j < len(rows) and not (rows[j][0] == '' and rows[j][1] == 'TOTAL'): j += 1
            hdr = [clean(c) for c in rows[j][1:]]; j += 1
            while j < len(rows):
                r = rows[j]; lab = clean(r[0])
                if lab is None and all(c is None for c in r): break
                for k, g in enumerate(hdr):
                    if g is None: continue
                    out.append(dict(pregunta=q, texto=texto, categoria=lab, grupo=g, valor=r[1+k]))
                j += 1
            i = j
        else: i += 1
    d = pd.DataFrame(out); d['cruce'] = cruce; return d

marg = parse_marginal(wb['Resultados total nacional'])
cruces = {n: parse_cruce(wb[n]) for n in ['Sexo','Edad','Nivel de estudios','RV EG23','Ocupación','Clase social','Escala de ideología','Religiosidad']}
marg.to_pickle('/home/claude/work/marg.pkl'); pd.concat(cruces.values()).to_pickle('/home/claude/work/cruces.pkl')
print(marg.pregunta.nunique(), {k: (len(v), v.pregunta.nunique(), v.grupo.nunique()) for k, v in cruces.items()})
