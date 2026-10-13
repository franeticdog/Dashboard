> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# Planificar los beats

**Idioma:** responde siempre en español de España, también en los resúmenes y cuando algo falle (aunque el error salga en inglés).

```
kit.py plan borrador <video>     # rótulo + transiciones en los cambios de plano
# tú eliges un recurso para cada frase en trabajo/<video>/plan.json
kit.py plan tabla <video>        # resuelve tiempos y enseña la tabla
kit.py plan aprobar <video>      # SOLO tras el OK del usuario
```

La lista completa de recursos y sus campos está en `fases/animar.md`.

**Sigue la plantilla activa** (la enseña `plan borrador`; `kit.py estilo ver <nombre>`): su ritmo
(un recurso cada X s, más seguido en el gancho), sus recursos preferidos y los que evita, y sus
subtítulos. `plan tabla` avisa si queda un hueco demasiado largo o usas algo que evita. El
borrador también sugiere los logos de `marca/logos/` que se nombran (úsalos con `logos`) y avisa
de las palabras que disparan un sonido de marca (suenan solas, no hace falta ponerlas).

## Qué recurso para qué frase

| Lo que se dice | Recurso |
|---|---|
| Se nombra la herramienta protagonista | `logos` (uno, grande y en 3D) |
| Una idea fuerte, lo que está mal, la promesa | `palabra` |
| «No es X, es Y», «antes X, ahora Y» con palabras | `tachado` |
| Antes y ahora como situación | `barrido` |
| La cifra del vídeo (una vez) | `golpe3d` |
| Una cifra o un tiempo | `contador` |
| Pasos, un orden, «primero… después…» | `fases` |
| Una orden o lo que hace Claude | `terminal` |
| Empieza un bloque nuevo | `capitulo` |
| Presentación | `rotulo` |
| Un apunte corto mientras van los subtítulos («Datos recibidos», una lista corta) | `etiqueta` |
| Una frase importante que no tiene gráfico | `subtitulo` |
| Algo que se puede enseñar (una bandeja, una web, un producto) | `broll` |
| El mensaje clave, a toda pantalla | `pantalla` (texto + SVG) |
| «Acércate aquí», un golpe de énfasis sin gráfico | `zoom` (o `"camara"` en el beat) |

## Subtítulos: solo en los momentos

Ya no son continuos. La columna «Subtítulo» dice sí o no por cada beat:
- **No** en todo recurso que ya dice algo con palabras (`palabra`, `tachado`, `logos`, `golpe3d`,
  `contador`, `fases`, `terminal`, `capitulo`): nunca subtítulo y gráfico diciendo lo mismo.
- **Sí** en `barrido` y `subtitulo` (frases fuertes sin gráfico). El `rotulo`, no (se pide con `"con_subtitulo": true`).
- Se puede forzar con `"subtitulo": true/false` en el beat. Fuera de los beats, no hay subtítulos.
- Si el usuario los quiere **en todo el vídeo**, pon `"subtitulos": "siempre"` en `plan.json` (manda sobre la
  plantilla). Entonces «no» en un beat significa que ese recurso los aparta mientras está; para que sigan
  durante un gráfico, `"subtitulo": true` en ese beat. Con subtítulos siempre, los apuntes van mejor con
  `etiqueta` (texto pequeño) que con `palabra` (frase grande que repetiría lo mismo).

## Ritmo y limpieza

- Un recurso en pantalla cada vez, con aire entre dos (0,2 s o más).
- En el hook, uno nuevo cada 2-4 s; después, más espaciado. Nunca el mismo dos veces seguidas.
- Menos es más: si un recurso no suma, fuera.

## Cómo se escribe un beat

```json
{"id": "p1", "tipo": "palabra", "cuando": "utilizando mal", "texto": "Lo estás utilizando", "clave": "mal", "duracion": 1.6}
{"id": "t1", "tipo": "tachado", "inicio": 5.6, "duracion": 1.8, "texto": "Lo digo yo", "nueva": "Anthropic",
 "cuando_tacha": "lo dice", "cuando_nueva": "Anthropic"}
{"id": "l1", "tipo": "logos", "cuando": "Claude Opus 5.5", "duracion": 1.9,
 "items": [{"logo": "claude", "nombre": "Claude", "clave": "Opus 5.5"}]}
```

- `cuando`: la frase **literal** de `transcripcion_cortada.txt` (`"desde"` si se repite). Para
  probar: `kit.py plan buscar <video> "frase"`.
- `terminal`: el `cuando` del beat y el de su primera línea, en la misma frase (la terminal no
  debe quedarse vacía más de medio segundo).
- Un «sí» en Subtítulo solo sale si una frase entera cabe en el tramo del beat: si la tabla
  avisa, alarga la duración o márcalo «no».
- Logos que ya vienen en `marca/logos/`: `claude`, `hyperframes`, `d-ia`. Otros se bajan solos.
- Textos cortos, sacados de lo que se dice, y **sintagmas completos**: la tabla avisa si un texto
  acaba en «de», «que», «y», «como», «para»… **Nunca una cifra que no esté en la transcripción.**

- `broll` y `pantalla` tapan la cámara: que no coincidan con una `palabra` por detrás (la tabla
  lo avisa). Con subtítulos «siempre», el B-roll los mantiene y la pantalla los aparta.
- `tachado`: el `cuando` en la palabra vieja (sale cuando se dice, no antes), el tachón en
  `cuando_tacha` y la nueva en `cuando_nueva`; cada palabra de `nueva` entra sola cuando se dice.
  La duración, hasta que se acaba de decir la nueva y un poco más: la salida empieza 0,38 s antes
  del final. Si justo después entra una `pantalla`, que dure hasta su entrada + 0,26 s: el círculo
  lo tapa entero, sin hueco (la tabla no lo cuenta como solape).

Enseña la tabla tal cual (con «Recurso» y «Subtítulo») y **espera el OK**.
