# Formato de las vistas .vw de SQX (lo observado)

Fuente: un `live.vw` real del usuario (SQX 144), más la versión ampliada que él mismo confirmó que carga. Todo lo que sigue es observación, no documentación oficial.

## Estructura

```xml
<View name="live" originalName="live">
  <Columns>
    <Column class="ReturnDDRatio" name="Ret/DD Ratio" sampleType="127" direction="0" plType="10" resultType="main" confidenceLevel="50" market="1" subresult="30" showMainResult="true"/>
    ...
  </Columns>
</View>
```

- Saltos de línea CRLF, sangría de 2 espacios por nivel, `<Column .../>` autocerrada y sin espacio antes de `/>`.
- Un único `<Columns>` dentro de `<View>`; ninguna columna tenía elementos hijos.
- El orden de las columnas es el orden en el que se ven en el databank.

## Atributos de cada columna

| Atributo | Valores vistos | Notas |
|---|---|---|
| `class` | ver lista abajo | Identifica la métrica. Dos columnas pueden compartir clase si cambia `sampleType`. |
| `name` | texto libre | Es lo que se ve en la cabecera. Se puede cambiar sin tocar la clase. |
| `sampleType` | `127`, `41`, `10` | Ver abajo. |
| `direction` | `0` | Igual en todas. |
| `plType` | `10` | Igual en todas. |
| `resultType` | `main` | Igual en todas. |
| `confidenceLevel` | `50` | Igual en todas. |
| `market` | `1` | Igual en todas. |
| `subresult` | `30` | Igual en todas. |
| `showMainResult` | `true` | Igual en todas. |

Los atributos que valen lo mismo en todas las columnas se copian de una columna existente al crear una nueva; no se sabe qué hace cada uno ni qué otros valores admite.

## sampleType

- `127`: lo que el usuario llama **full** (periodo completo) en esta vista.
- `41`: lo que el usuario llama **ISV1**. Ya existía así en su columna Ret/DD Ratio.
- `10`: usado solo por la columna `Symbol`.

No se sabe el significado interno de estos números (podrían ser una combinación de periodos, pero no está confirmado) ni qué valor corresponde a otros periodos (OOS, ISV2...). Para cualquier otro periodo, pide un `.vw` con esa columna ya configurada en SQX y lee el valor de ahí.

## Clases vistas

Métricas que se duplican por periodo: `ReturnDDRatio`, `NetProfit`, `NetProfitInPct`, `DrawdownPct`, `Fitness`, `NumberOfTrades`, `WinningPct`, `ProfitFactor`, `AvgConsecWins`, `AvgConsecLosses`, `MaxConsecWins`, `MaxConsecWonsP80`, `MaxConsecLosses`, `MaxConsecLosesP80`, `WinLossRatio`, `AvgWin`, `AvgLoss`, `AvgBarsInTrade`.

Columnas que la herramienta no duplica por defecto (no son una métrica por periodo): `EntryIndicators`, `MiniEquityChart`, `Symbol`, `DateGenerated`. Si el usuario quiere duplicar alguna de estas, no hay base para saber si SQX lo admite; avisa y haz la prueba sobre una copia.

Esta lista es solo lo que había en la vista del usuario. SQX tiene más columnas; no inventes sus nombres de clase.

## Convención de nombres

`Nombre (full)` y `Nombre (ISV1)`, como el usuario pidió (por ejemplo `Ret/DD Ratio (full)` y `Ret/DD Ratio (ISV1)`). La herramienta quita un sufijo `(full)` o `(ISVn)` previo antes de añadir el nuevo.

## Lo que no se sabe

- Dónde está exactamente la carpeta de vistas en la instalación del usuario (pregúntale; él ya la usa).
- Qué hace SQX si encuentra un `.vw` inválido: en el caso visto, una vista que no cargó simplemente no apareció en la lista, sin aviso en pantalla.
- Si SQX distingue entre CRLF y LF al leer vistas.
- Si el nombre del archivo debe coincidir con `name` y `originalName` dentro del XML (en el ejemplo coinciden: `live`).
