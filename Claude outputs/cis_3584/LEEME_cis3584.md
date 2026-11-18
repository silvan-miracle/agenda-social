# CIS 3584 (preelectoral 29-N-2026): cómo entra en el dashboard (12-11-2026) — integrado y probado en copia de trabajo, SIN subir (Ainara: Commit + Push)

## Integración hecha (agenda-social-datos)
- `cis_avances/3584_2026-11_avance.xlsx` (el Excel) y **`scripts/32_cis_preelectoral.py`** (nuevo): lee el Excel y AÑADE el estudio 3584 (fecha 2026-11) a `cis_intencion_directa.csv`, `cis_votosim_perfiles.csv`, `cis_transferencias.csv`, `cis_preferencia_presidente.csv`, `cis_aprobacion_lideres.csv`, `cis_ideologia.csv` y `cis_ideologia_distribucion.csv`, con el mismo esquema. Si llega el .sav del 3584 a `cis/2026/`, el paso se salta solo (el estudio ya está).
- `herramientas/construir.py`: llama al paso 32 justo después del 16b (no obligatorio: si falla, la web sale con el 3582 como último). Debe ir después del 16b porque este necesita el microdato del último barómetro.
- `dashboard/build_dashboard.py`: aprobación de líderes con último y anterior dato de CADA líder (Yolanda Díaz no está en el 3584 y se queda con su dato de oct-26, con su fecha); «El viaje de cada perfil» ignora los estudios sin generación (sigue abriendo en 3582); `DATA.cis_avance` con el aviso del 3584.
- `dashboard/cis_voto.js` (notas de perfil y de transferencias: añaden el aviso) y `dashboard/cis_lideres.js` (fechas por líder).
- Probado con una copia de trabajo: pasos 01–31 + build sin errores; sintaxis JS correcta; sumas 100; el Total de perfiles coincide con el nacional; las transferencias y la ideología tienen las mismas categorías que oct-26. Vista previa: `agenda-social/Claude outputs/dashboard_previa_2026-11-12_cis3584.html` (comprobada solo por datos y sintaxis, no visualmente: el navegador integrado no abre archivos locales).
- Efecto visible: la transferencia de voto y el histograma de ideología pasan a mostrar el 3584; el aviso aparece en las notas.

## Qué es el archivo
- `multi_A.xlsx` = **avance de resultados** del estudio 3584/0, preelectoral de las generales del 29-N. **Son tablas, no microdatos**: marginales nacionales, 19 CCAA, provincias y cruces por sexo, edad, estudios, recuerdo de voto 2023, ocupación, clase, ideología y religiosidad.
- 45.074 entrevistas CATI, **campo 7–30 oct 2026** (el barómetro 3582 fue 1–6 oct). Error ±0,5 %. Ponderado con PESO (las n de los cruces son ponderadas).

## Decisión de entrada (a confirmar)
1. **Entra como un punto más de las series CIS (2026-11), con aviso en las notas**, no en el promedio de encuestas. Matiza la decisión del 03-11 (estudios electorales de 2019 fuera de las series): este se muestra, aunque no es un barómetro; si prefieres dejarlo fuera como los de 2019, basta con borrar el Excel de `cis_avances/` o añadirlo a la exclusión.
2. **fecha = 2026-11** (CIS de noviembre, el último), con el campo (7–30 oct) en el tooltip. Alternativa: 2026-10 (por campo), pero chocaría con el 3582.
3. Cuando salga el **.sav**, reprocesarlo por el pipeline normal y retirar estas filas.
4. El CIS oficial sigue **fuera del promedio de encuestas** (regla del 02-11). Su estimación (PSOE 33,3 · PP 25,5 · VOX 18,4 · FA 4,7 sobre voto válido; PSOE 134–143 escaños) queda en `cis3584_estimacion_oficial.csv` solo como referencia.

## Variables comunes (y CSV)
| Variable del dashboard | Pregunta 3584 | CSV | Estado |
|---|---|---|---|
| Intención directa (INTENCIONGR) | P3R | `cis3584_voto_total.csv` | comparable, con ruptura de Sumar/Podemos |
| Voto + simpatía (VOTOSIMG) | P5a | `cis3584_voto_total.csv` | ídem |
| Voto por perfil (sexo, edad, estudios, clase, situación laboral, ideología, religiosidad, recuerdo 2023) | P3R/P5a × cruces | `cis3584_voto_x_perfil.csv` | comparable |
| Transferencias recuerdo 2023 → voto | RV EG23 × P3R/P5a | `cis3584_transferencias.csv` | comparable; n mucho mayor |
| Ideología (autoubicación 1–10, media por votante) | C3 × P5a | `cis3584_ideologia.csv` | comparable |
| Valoración de líderes | P10/P10a | `cis3584_lideres.csv` | comparable (verificado con el .sav del 3582: misma definición); sin Yolanda Díaz |
| Preferencia de presidente | P11R | `cis3584_pref_presidente.csv` | comparable |
| Indecisos | «No sabe todavía» en P3R × perfiles | dentro de `voto_x_perfil` (partido = No sabe) | comparable |

**No existen en este estudio**: problemas principales, situación económica, estado civil, hábitat, generación (la edad viene en 7 tramos y los de 18–24/25–34 cortan la Gen Z), Yolanda Díaz en la valoración. En esos gráficos el 3584 simplemente no aporta punto.

## Cómo se ha mapeado
- PSOE, PP, VOX, Podemos, Se Acabó la Fiesta con su nombre. **Frente Amplio → columna «Sumar»** (la sucesora en el bloque izquierda). Resto de partidos (ERC, Bildu, Compromís, Adelante Andalucía, Junts, BNG, PNV, UPC, Ara Més, CCa, UPN-PP, PACMA…) → «Otros partidos». En blanco + nulo → «Voto en blanco/nulo». «No votaría» (P3R) y «Ninguno» (P5a) → «No votaría/Ninguno». Ciudadanos queda dentro de «Democracia 21» (Madrid y Barcelona) → Otros.
- Perfiles: % del grupo sobre el total del grupo, agrupando categorías ponderando por su n. Situación laboral = ocupados (11 categorías de ocupación sumadas), jubilado, parado, estudiante, trabajo doméstico, otra inactiva. Ideología solo en tramos (1–4 / 5–6 / 7–10, más N.S./N.C.); los 10 grupos originales no se exportan. Asterisco si n < 250.
- Media ideológica de votantes: calculada con las columnas de ideología (P(ideología | partido) por Bayes con la n de cada columna). PSOE 2,67 · PP 7,08 · VOX 7,77 · Sumar/FA 2,23 · Podemos 2,10 · SALF 6,69; total 4,65.
- Comprobaciones: suma 100 en todas las medidas; la media ponderada de los grupos de cada cruce reproduce el total nacional (desvío 0,0 pp en las 8 variables); reproduce la columna «voto directo» de la hoja Estimación de Voto.

## Avisos para el dashboard
1. **Ruptura de serie Sumar/Podemos**. «Frente Amplio» recoge Sumar, IU, Más País, Comuns, CHA, Más Madrid, etc.; pero en Comunitat Valenciana, Canarias, Baleares y Cataluña las menciones a FA y **Podemos se suman a Compromís, UPC, Ara Més y ERC**; «Podemos» solo es Podemos donde concurre en solitario. Resultado: Sumar+Podemos baja de 6,7 (oct, sobre total) a 4,2, y parte de esa bajada es esta ruptura, no opinión. Recomiendo marcar Sumar/FA y Podemos con «ruptura de serie» y que el bloque izquierda del 3584 lleve nota («sin los socios regionales de FA/Podemos»).
2. **Salto de oct a nov** (intención directa sobre total, oct → 3584): PSOE 25,3 → 28,7 · PP 14,7 → 17,2 · VOX 11,6 → 15,0 · SALF 1,1 → 1,3 · No sabe 17,3 → 15,8 · No votaría 5,1 → 1,7. En voto+simpatía: PSOE 28,7 → 32,0 · PP 17,0 → 19,2 · VOX 12,2 → 15,8. No se puede separar campaña de cuestionario (el preelectoral pregunta antes por la probabilidad de votar, y hay menos «no votaría»). Nota en el gráfico.
3. **Líderes** (corrección: en la primera versión de esta nota dudé de la comparabilidad; está comprobada). El script 20 define la aprobación sobre quienes conocen al líder, con N.S./N.C. en la base, y el dashboard la muestra como 5–10. Recalculado el 3582 con su .sav: 6–10 = Sánchez 39,2 · Feijóo 18,3 · Abascal 17,7. En el 3584 (misma definición): 42,9 · 28,6 · 26,0; en 5–10: Sánchez 48,1 → 49,9 · Feijóo 31,1 → 38,9 · Abascal 25,3 → 32,6; valoración media 4,4 → 4,6 · 3,4 → 3,9 · 2,9 → 3,4. El salto de Feijóo es grande pero va en línea con el resto (+0,4/+0,5 de media). Colau, Delgado, Rufián y Montero entraron el 21-oct (bases 11.774 · 5.488 · 12.477 · 12.807) y no están en las tarjetas.
4. Tamaños de celda: con 45k casi todos los grupos pasan de 250; los que no: edad N.C., estudios «Otros», recuerdo CCa/UPN. Las n son ponderadas.

## Pendiente
- Ainara: Commit + Push (`cis_avances/`, `scripts/32_…`, `herramientas/construir.py`, `dashboard/build_dashboard.py`, `cis_voto.js`, `cis_lideres.js`); Actions → «Actualizar la web» → comprobar verde y que la transferencia y la ideología muestran el 3584.
- Sin marcador distinto para el punto «Preelectoral» (solo el aviso en las notas): es un cambio de JS en cada gráfico si lo quieres.
- «Evolución del voto» (intención directa y voto+simpatía) está retirada del dashboard por Mikel, pero sus datos ya llevan el 3584.
- Cuando salga el .sav: copiarlo a `cis/2026/3584_2026-11.sav` y retirar el Excel de `cis_avances/` (o dejarlo: el paso se salta); revisar si hay que excluirlo de las series con `config/exclusiones_cis.csv`, como los electorales de 2019.
- Opcional: las hojas por CCAA/provincia y la estimación de escaños provincial (PSOE 134–143, PP 98–106, VOX 57–65…) alimentarían la pestaña «Elecciones generales» (reparto de escaños hoy desactivado, `ESCANOS = False`).
- Scripts reproducibles: `parse_cis3584.py` (Excel → formato largo) y `build_cis3584.py` (CSVs).
