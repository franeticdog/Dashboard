> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md).

# /editor-video empezar · Puesta en marcha

> **Idioma:** responde siempre en español de España, también en los resúmenes de cada fase, en el resumen final y cuando algo falle (aunque el error salga en inglés).

Son dos cosas distintas, y casi siempre solo hace falta la segunda:

1. **El equipo**, una sola vez por ordenador: instalar el entorno. `kit.py proyecto` lo dice
   («Entorno: … (instalado)» o «SIN INSTALAR»).
2. **El proyecto**, en cada carpeta nueva de trabajo: qué marca usa, y sus carpetas `brutos/` y
   `finales/`.

Empieza siempre con `kit.py proyecto`.

## 1 · El proyecto y su marca

**Si la carpeta ya es un proyecto** (`kit.py proyecto` enseña su marca): enséñale en dos líneas
lo que tiene guardado la marca y pregúntale si lo cambia o lo deja. Si lo deja, ve a la
instalación (o termina, si ya está instalado).

**Si no lo es**, mira las marcas guardadas con `kit.py proyecto marcas`:

- **Una encaja** (el usuario la nombra, o solo hay una y no dice otra cosa):
  `kit.py proyecto nuevo <marca>`. Díselo en una línea: «Uso tu marca Grupo Nergia. Si este
  vídeo es de otra marca, dímelo.»
- **Hay varias y no sabes cuál**: pregúntalo en una línea (o si es una nueva).
- **Es una marca nueva**, o no hay ninguna guardada: `kit.py proyecto crear-marca <nombre-corto>`
  crea `marcas/<nombre>/` (su `brand.json`, copia del de ejemplo, y su carpeta `marca/`) y la
  carpeta de trabajo pasa a usarla. Haz los tres bloques de preguntas de abajo y rellena ese
  `brand.json` (la orden dice dónde está). La marca queda guardada para todos sus proyectos.

Los tres bloques, **de uno en uno** (no preguntes el siguiente hasta tener la respuesta del
anterior). Si el usuario dice «usa los de ejemplo» o «lo que tú veas», deja el de ejemplo,
cambia solo lo que te haya dicho y salta a la instalación.

**Si el entorno está SIN INSTALAR, mientras esperas su primera respuesta lanza ya la
instalación en segundo plano** (abajo): no depende de las respuestas y así se gana tiempo. Solo
el paso 6 (tipografías) y el 7 (prueba) usan la marca; si cambia la tipografía, relanza al final
`kit.py instalar`, que salta todo lo que ya está hecho.

### Bloque 1 · Tú y tu canal

> Para los rótulos: ¿qué nombre quieres que salga en pantalla, cuál es tu @ o el nombre de tu
> canal, y cómo se llama tu marca o tu empresa?

### Bloque 2 · Tu identidad visual

> ¿Qué colores usa tu marca? Con el principal y uno de acento me vale. Puedes darme el código
> (#2fe39a) o decírmelo con palabras («verde menta y dorado»). ¿Qué tipografía usáis? Si no lo
> sabes, pongo una limpia. ¿Tienes logo? Si lo tienes, arrástralo aquí o dime dónde está.

- Si describe el color con palabras, elige tú un código razonable y díselo.
- Las tipografías tienen que estar en Google Fonts (fonts.google.com). Si da una que no está,
  propón la más parecida que sí esté.
- Si hay logo, cópialo a la carpeta `marca/` de la marca (PNG o SVG, mejor con fondo
  transparente) y pon en `"logo"` su ruta empezando por `marca/`, por ejemplo `"marca/logo.png"`.
  Sin logo se usan sus iniciales.

### Bloque 3 · Tus carpetas

> ¿Dónde vas a dejar los vídeos grabados y dónde quieres los terminados? Si te da igual, cada
> proyecto tendrá sus carpetas `brutos` y `finales`. Y dos cosas más: ¿en qué idioma hablas en
> los vídeos? ¿Hay nombres o marcas que digas mucho y que un transcriptor podría escribir mal?

- Las palabras que diga van al `"glosario"` de `"transcripcion"`, que ayuda a Whisper.
- `"brutos"` y `"finales"` con un nombre suelto son carpetas dentro de cada proyecto. Con una
  ruta completa, todos los proyectos de esa marca usan la misma.

### Guardar la marca

Escribe el `brand.json` de la marca con la misma estructura que el de ejemplo y las respuestas.
Enséñale un resumen de cuatro líneas: nombre, colores, tipografía, carpetas.

## 2 · Instalación (solo con el entorno SIN INSTALAR, o si ha cambiado la tipografía)

```
kit.py instalar
```

- Todo va al entorno de la skill (en este equipo, `D:\DatosFranco\EditorVideo\entorno`): Python
  con Whisper y MediaPipe, HyperFrames con su navegador, los modelos y lo que se descarga para
  instalar. Las tipografías de la marca, a su carpeta `marca/fuentes`.
- Es idempotente: lo que ya está instalado se salta. Se puede relanzar sin miedo.
- Cada pieza se prueba con un comando real: ffmpeg, Node 22+, HyperFrames con su navegador,
  Whisper con su modelo, las tipografías y un render de prueba de un segundo.
- Si Homebrew (Mac) o winget (Windows) están disponibles, instala ffmpeg y Node solos.
- En Windows, si acaba con el código 2, pide al usuario que cierre y abra Claude Code, y
  relanza `/editor-video empezar`: seguirá donde lo dejó.
- Si un paso falla, el propio mensaje dice cómo arreglarlo. Hazlo tú si puedes; si hace falta
  el usuario (por ejemplo, instalar Homebrew), explícaselo en una frase.

Mientras corre, cuenta en una línea en qué paso va (en español). Al terminar, di cuánto ha
tardado y:
«Listo. Deja un vídeo en la carpeta de brutos (o en esta misma carpeta) y escribe
`/editor-video editar nombre-del-video`. Si vas a grabar en directo, lanza antes
`/editor-video comprobar`.» Y en una línea más: «Tus assets van en la carpeta `marca/` de tu
marca (<ruta>): música en `musica/`, sonidos en `sonidos/`, logos en `logos/` y B-roll en
`broll/`. Valen para todos tus proyectos. Si ves una edición que te gusta, pásamela con
`/editor-video estilo`.»
