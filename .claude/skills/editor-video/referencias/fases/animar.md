> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# Animar

**Idioma:** responde siempre en español de España, también en los resúmenes y cuando algo falle (aunque el error salga en inglés).

```
kit.py animar <video> [--formato horizontal|vertical] [--plantilla <nombre>]
```

La **plantilla activa** (`estilos/<nombre>.json`, `fases/estilo.md`) manda en subtítulos
(`momentos`, `siempre` o `nunca`), tamaño de textos, acento, logos en 3D o planos y frases por
detrás o delante. Sale en la primera línea: «Plantilla: …».

- Lee `plan.json` (aprobado), `palabras_cortado.json`, `persona.json` y `brand.json`.
- Renderiza `capa-<formato>.mov` (ProRes 4444 con transparencia) y, por cada frase por detrás,
  `detras-<formato>-<id>.mov`. Deja en `eventos-<formato>.json` sonidos, cámara y barridos.
- Como mucho 4 renders a la vez.

## Principio (lo que manda)

**Lo más limpio y dinámico posible, de máxima calidad.** Ante la duda, menos elementos y mejor
ejecutados. Un recurso en pantalla cada vez, mucho aire, entradas con energía (expo, nada lento
ni flotante), y cada elemento entra, cuenta algo y sale limpio. Cero adornos: nada de
partículas, destellos gratuitos, rejillas decorativas, marcos ni efectos sobre la silueta.

## Identidad «dia-editorial» (estilo por defecto)

- **Tipos:** Instrument Serif (la palabra clave en *cursiva* coral), Archivo estructural,
  JetBrains Mono para cifras y órdenes.
- **Color:** coral `#D97757` (el único acento) más crema `#F2EDE3`. El color de otras marcas,
  solo dentro de sus logos. Grano fino de película en todo el vídeo.
- **Sin cajas:** el texto se sostiene con sombra suave; si va a un lado, una sombra sin bordes
  baja el plató de ese lado.
- **La máscara de la persona** solo sirve para poner texto POR DETRÁS, con borde limpio: nunca
  contorno, halo ni brillo alrededor del cuerpo.
- **Sin logo animado de marca ni cierre de marca.**
- **Subtítulos solo en los momentos que lo piden** (columna «Subtítulo» del plan). Nunca a la
  vez que un gráfico que dice lo mismo.

## La biblioteca

Código: `herramientas/recursos.py` (HTML y tiempos), `herramientas/capa/motor.js` (coreografía,
una función por recurso), `herramientas/capa/motor3d.js` (3D) y `herramientas/capa/capa.css`.

| Recurso (`tipo`) | Cuándo | Qué se ve | Campos |
|---|---|---|---|
| `palabra` | Una idea fuerte | Frase en serif crema con la clave en cursiva coral subrayada. En horizontal, POR DETRÁS de la persona y a un lado (la cabeza solo roza el arranque); en vertical, bajo la barbilla | `texto`, `clave` |
| `tachado` | Se corrige algo («no lo digo yo, lo dice X») | La palabra se tacha con trazo coral y entra la correcta en cursiva, cada palabra cuando se dice. La firma de la casa. Con `escala` por debajo de 0,8 va pequeño, a la altura del pecho, con la letra de las etiquetas (la última palabra de `nueva`, en cursiva de acento) y un velo suave | `texto`, `nueva`, `cuando_tacha`, `cuando_nueva`, `escala` |
| `logos` | Se nombran herramientas | Logos reales en 3D (extrusión media, bisel fino, metal 0,6, canto coral, relleno frío), uno protagonista o en fila, con su nombre en serif | `items: [{logo, nombre, clave, cuando, color, gradiente}]` |
| `golpe3d` | La cifra o palabra del clip (una vez) | Texto extruido crema con canto coral, entra de 1,25 a 1; remate en serif cursiva | `texto`, `remate` |
| `contador` | Se dice una cifra o un tiempo | Número en mono que corre hasta la cifra, con su unidad en cursiva coral | `hasta` («10» o «10:00»), `unidad`, `cuando_cifra` |
| `fases` | Se enumeran pasos | Línea de puntos con fases numeradas; el cabezal salta a cada una al decirla | `items: [{texto, cuando}]` |
| `terminal` | Una orden, lo que hace Claude | Terminal de Claude Code que se escribe sola | `lineas: [{texto, cuando}]`, `titulo` |
| `barrido` | Antes y después | Deslizador que parte el plano: «antes» apagado y sin color, «ahora» vivo | `antes`, `despues`, `cuando_ahora` |
| `capitulo` | Empieza un bloque | Créditos: «01 · Transcribe» | `numero`, `texto` |
| `subtitulo` | Frase que merece subtítulo sin gráfico | Solo subtítulos en ese tramo | `cuando`, `duracion` |
| `rotulo` | Presentación | Nombre en serif, @ en mono coral y una línea fina | `titulo`, `subtitulo` |
| `etiqueta` | Un apunte corto que acompaña a los subtítulos | Texto pequeño a un lado, a la altura del pecho: antetítulo en mono con un punto de acento, la frase en la tipografía de la marca con la clave en cursiva de acento y una línea fina; con `items`, lista con ticks que se marcan al decirlos. Sin caja: un velo suave detrás para que se lea en fondos claros | `kicker`, `texto`, `clave`, `items: [{texto, cuando}]`, `posicion` |
| `lista` | Puntos sueltos (mejor `fases`) | Ticks sin caja | `items` |
| `broll` | Se habla de algo que se puede enseñar | Foto o vídeo a pantalla completa, con zoom lento; entra y sale con un fundido desenfocado de 0,22 s. La voz sigue y los subtítulos también | `archivo` (de `marca/broll/`) o `web` (se captura en local), `movimiento` (`acercar`, `alejar`, `derecha`, `izquierda`, `quieto`), `ajuste` (`auto`, `cubrir`, `entero`), `desde_s` (vídeos) |
| `pantalla` | Un mensaje que merece toda la pantalla | Fondo de tu panel que se abre en círculo, un SVG grande y la frase en serif con la clave en cursiva de acento | `texto`, `clave`, `kicker`, y uno de: `icono` (`tabler:key`, licencia MIT), `logo` (de `marca/logos/`), `svg` (ruta o `<svg>…</svg>` que escribes tú) |
| `zoom` | «Acércate cuando digo X» | Solo cámara, sin gráfico | `modo` (`acercar`, `alejar`, `golpe`), `zoom` (0,05 a 0,15), `duracion` |

Cualquier beat admite además `"camara": "acercar" | "alejar" | "golpe"` (y `"zoom": 0.1`): el
zoom va con el recurso.

Logos: `marca/logos/<nombre>.svg` o `.png` (el PNG se extruye por su silueta con la imagen en
la cara; mejor con fondo transparente). Al entrar, cada logo 3D lleva un **barrido de luz de 0,3 s**
(un reflejo que cruza el bisel una sola vez); se quita con `"tres_d": {"barrido_luz": false}` en la
plantilla. Los oficiales que da el cliente van ahí y mandan (en la demo:
`claude.svg`, `hyperframes.svg` con su degradado real `#49DB6C → #08E4F4`, `d-ia.svg`). Si falta
uno, se baja del set «logos» de Iconify (CC0). `color` fuerza un color (p. ej. crema para un
logo negro) y `gradiente` aplica un degradado diagonal al material.

## Pedirlo hablando (lo que dice el usuario → lo que pones en el plan)

| Lo que pide | Qué haces |
|---|---|
| «Añade B-roll de recurso», «pon una imagen cuando hablo de X» | Beat `broll` con `archivo` de `marca/broll/`. Si no hay nada que encaje, lo creas tú (abajo) |
| «Pon la web de X cuando la nombro» | Beat `broll` con `"web": "x.com"`: se captura en local con el navegador del kit (en reels, `"movil": true`) |
| «Motion graphics», «una pantalla completa con texto y un icono» | Beat `pantalla` con `texto`, `clave` y `icono` (Tabler) o un `svg` que dibujas tú |
| «Zoom in cuando digo X», «zoom out al final», «golpes de zoom» | Beat `zoom` con `modo` o `"camara"` en el beat de esa frase. Golpes en todo: `zooms.golpes` en la plantilla |
| «Transiciones limpias» | Ya lo son: látigo corto en cada cambio de plano. Más sobrias: plantilla con `transiciones.tipo` `desenfoque` o `corte` |
| «Más dinámico», «máximo dinamismo» | Plantilla `reels-dinamico` (o ritmo más corto), un recurso cada 2-3 s, alternando `palabra`, `contador`, `broll`, `pantalla` y `zoom` |
| «Busca recursos si los necesitas» | Solo local y gratis: `marca/broll/`, capturas de webs nombradas o imágenes que dibujas en HTML/SVG |

Crear B-roll sin APIs de pago:

```
kit.py broll lista                       # lo que hay en marca/broll/
kit.py broll web <url> [--movil]          # captura local de una web
kit.py broll html <archivo.html> [--vertical]  # una imagen que escribes tú
```

Para `broll html`: escribe en `trabajo/_html/<nombre>.html` una ilustración limpia (1920x1080 o,
con `--vertical`, 1080x1920) con los colores de la marca, y conviértela. **Nunca** uses APIs de
pago, bancos de imágenes ni descargas de fotos de terceros. Las webs con aviso de cookies salen
con el aviso: si molesta, pide al usuario una captura suya.

## Añadir un recurso

1. `recursos.py`: `r_<nombre>(b, bid, t0, t1, ctx)` que devuelve `html`, `js` (tiempos absolutos),
   `sonidos` y, si hace falta, `piezas3d` o `barrido`.
2. `motor.js`: la función `<nombre>(b)` dentro de `TIPOS`.
3. Añádelo a `RECURSOS` (`animar.py`), `NOMBRES` y `DUR_DEFECTO` (`plan.py`) y a esta tabla.

## Reglas que no se rompen

- Nada de `Math.random` ni relojes; el 3D se dibuja desde `hf-seek`.
- Solo se animan transformaciones, opacidad y filtros.
- Ningún texto por debajo de 40 px en vertical. Nada a menos de 40 px de la boca.
- Nunca un guion largo en pantalla. Nunca un texto que acabe en «de», «que», «y», «como»…
