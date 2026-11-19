---
name: strategyquant-views
description: 'Crea y modifica vistas (archivos .vw) del databank de StrategyQuant X (SQX): añadir, quitar, renombrar o duplicar columnas de KPIs, por ejemplo mostrar cada métrica en versión (full) y (ISV1) una al lado de la otra. Usar SIEMPRE que el usuario mencione una vista del databank, un archivo .vw, columnas del databank, "ver el KPI de full e ISV1", "añadir columna", "quitar columna" o "ordenar columnas" en SQX, aunque no diga la palabra "vista" ni ".vw".'
---

# Vistas del databank de StrategyQuant X (.vw)

Una vista `.vw` es un XML pequeño que dice qué columnas muestra el databank y con qué periodo se calcula cada una. Esta habilidad sirve para generarlas o modificarlas sin editar a mano 40 líneas casi idénticas. Responde en español, y trabaja con la versión 144 de SQX en Windows, como el resto de proyectos del usuario.

## 1. Parte siempre de una vista real

No escribas el XML de memoria. Pide (o usa si ya está en la conversación) un `.vw` que el usuario haya guardado desde SQX: de él salen los nombres exactos de las clases de columna (`class`) y los valores de `sampleType`. Si el usuario quiere una columna que no aparece en su vista, pídele que la añada una vez en SQX, guarde la vista y te la envíe; así copias la clase y los atributos exactos en vez de inventarlos.

Lee `references/vw-format.md` para el formato, las clases y los valores ya vistos, y lo que NO se sabe.

## 2. Usa la herramienta, no edites a mano

`scripts/sqx_view_tool.py` (solo Python estándar, funciona en tu entorno; el usuario no tiene Python instalado, así que le entregas el `.vw` ya generado y no le pides ejecutar nada).

```
python3 scripts/sqx_view_tool.py list   entrada.vw
python3 scripts/sqx_view_tool.py pair   entrada.vw -o salida.vw
python3 scripts/sqx_view_tool.py add    entrada.vw -o salida.vw --class CLASE --name "Nombre" --sample-type 127 --after-class OtraClase
python3 scripts/sqx_view_tool.py remove entrada.vw -o salida.vw --class CLASE --sample-type 41
python3 scripts/sqx_view_tool.py rename entrada.vw -o salida.vw --class CLASE --sample-type 41 --new-name "Nombre nuevo"
```

Casos habituales:

- **Cada KPI en (full) y (ISV1) lado a lado**: `pair`. Por defecto toma `sampleType` 127 como full y 41 como ISV1, deja `(full)` y `(ISV1)` en el nombre, coloca la gemela justo al lado de la base, no duplica las columnas que no son métricas por periodo (`EntryIndicators`, `MiniEquityChart`, `Symbol`, `DateGenerated`) y respeta los pares que el usuario ya tuviera. Repetirlo no cambia el resultado. Si el usuario usa otros periodos, cambia `--base`, `--twin` y las etiquetas, tras comprobar sus valores en su vista.
- **Otro periodo o etiqueta** (por ejemplo OOS en lugar de ISV1): el valor de `sampleType` hay que sacarlo de un `.vw` suyo con esa columna, no deducirlo.
- **Quitar o renombrar**: `remove` y `rename` exigen un filtro para no tocar todo por error.

## 3. Por qué la herramienta hace lo que hace

- **Escribe en otro archivo (`-o`), nunca sobre el original**: el usuario conserva su vista de partida si algo no le gusta.
- **Conserva CRLF, sangría y orden de atributos del original**: SQX no documenta qué tolera su lector de vistas; copiar el formato exacto del archivo que él mismo escribió es la opción segura. En el caso de `live.vw`, la primera versión (con LF) no apareció en SQX y la regenerada con CRLF sí cargó. No se llegó a confirmar si el CRLF fue la causa, así que mantenlo igualmente.
- **Se niega a reescribir si hay algo que no entiende** (elementos distintos de `<Columns>`, columnas con contenido interno): reescribirlo perdería datos sin avisar.
- **Vuelve a leer lo que acaba de escribir** y comprueba que el número de columnas coincide.

## 4. Cómo entregar el resultado

1. Genera el archivo con la herramienta y comprueba con `list` que el orden y los nombres son los esperados.
2. Entrégalo con el mismo nombre que el original si es una sustitución (el usuario lo copia a su carpeta de vistas de SQX y reinicia SQX), y presenta el archivo con `present_files`.
3. Resume en pocas líneas qué columnas se duplicaron, cuáles se dejaron sin duplicar y por qué. Da el recuento exacto con `list`; no lo estimes de memoria.
4. Di claramente que solo puedes comprobar que el XML es válido y que el formato coincide con el original; que SQX lo acepte lo confirma el usuario al abrirlo.

## 5. Si la vista no aparece en SQX

No puedes verlo desde aquí, así que no afirmes una causa. En este orden:

1. Revisar el log de SQX justo tras arrancarlo.
2. Preguntar si la vista original sí aparecía en la lista (separa "contenido rechazado" de "ubicación o carga").
3. Comprobar saltos de línea y nombre del archivo frente al original.
4. Preparar versiones recortadas (3 o 4 pares) para localizar qué columna provoca el rechazo.
