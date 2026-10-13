# Avisos de terceros (NOTICE)

El código de este kit (carpeta `herramientas/`, `CLAUDE.md`, las órdenes de `.claude/commands/`
y las skills de `.claude/skills/`) es original de D-IA · El Campamento y se publica con
licencia MIT (ver `LICENSE`).

El kit **no incluye** código de terceros dentro del zip. Las piezas siguientes las descarga e
instala `/empezar` en tu ordenador, cada una con su propia licencia:

| Pieza | Para qué | Licencia | Cómo llega |
|---|---|---|---|
| HyperFrames (HeyGen), github.com/heygen-com/hyperframes | Animaciones en HTML renderizadas a vídeo | Apache-2.0 | `npm install` (versión fijada en `package.json`) |
| Skills oficiales de HyperFrames | Guía para retocar animaciones con Claude | Apache-2.0 | `npx skills add heygen-com/hyperframes` (opcional) |
| Chrome Headless Shell | Navegador con el que HyperFrames dibuja los fotogramas | BSD-3-Clause (Chromium) y otras | Lo descarga `hyperframes browser ensure` |
| GSAP 3 (GreenSock / Webflow) | Motor de las animaciones | Licencia estándar «no charge» de GSAP (gsap.com/standard-license): gratuita, también para uso comercial | `npm install`; se copia a la carpeta de trabajo en cada render |
| FFmpeg | Cortar, componer y codificar | LGPL-2.1+ o GPL-2+, según la compilación | La instalas tú o Homebrew/winget |
| mlx-whisper (Apple ML Explore) | Transcripción en Mac con chip Apple | MIT | `pip install` en `.venv` |
| faster-whisper (SYSTRAN) | Transcripción en Windows, Linux y Mac Intel | MIT | `pip install` en `.venv` |
| Modelos Whisper (OpenAI), conversiones de mlx-community | El modelo de transcripción | MIT | Se descargan de Hugging Face la primera vez |
| Three.js (mrdoob y colaboradores) | Las piezas en 3D real (logo, énfasis por detrás) | MIT | `npm install` (versión fijada en `package.json`); se copia a la carpeta de trabajo en cada render |
| fontkit (foliojs) | Convierte tu tipografía al formato del texto 3D | MIT | `npm install` |
| MediaPipe (Google) | Encuentra la cara y recorta a la persona para poner textos por detrás | Apache-2.0 | `pip install` en `.venv` |
| Modelo «selfie multiclass 256x256» de MediaPipe | El recorte de la persona (y la cara) | Apache-2.0 (tarjeta del modelo de Google) | Se descarga a `modelos/` la primera vez |
| OpenCV (opencv-contrib-python, llega con MediaPipe) | Composición fotograma a fotograma y ajuste fino del borde de la máscara | Apache-2.0 | `pip install` |
| NumPy | Cálculo de fotogramas y síntesis de sonido | BSD-3-Clause | `pip install` |
| Tipografías de Google Fonts: Instrument Serif, Archivo, JetBrains Mono (y Sora, Inter, Inter Tight, Newsreader, Archivo Black para los estilos alternativos) | Rótulos, subtítulos, énfasis y estilos | SIL Open Font License 1.1 | Se descargan a `marca/fuentes/` |
| Logos de herramientas del set «logos» de Iconify (Gil Barbara) | El logo 3D de una herramienta que nombras | CC0-1.0 (los dibujos); las marcas siguen siendo de sus dueños: úsalos solo para referirte a esa herramienta | Se descargan a `marca/logos/` solo cuando un beat los pide |

## Logos

Los logos de herramientas que salen en 3D son marcas de sus dueños: el kit solo los usa para
referirse a esa herramienta. Dentro del zip, en `marca/logos/`, van tres: `claude.svg` (del set
«logos» de Iconify, CC0), `hyperframes.svg` (la forma del logo de HyperFrames, de HeyGen) y
`d-ia.svg` (de D-IA). Los demás se leen de `marca/logos/` (los que pongas tú) o se bajan del set
«logos» de Iconify (CC0) cuando un beat los pide.

## Sonido

Todos los efectos (aire, graves, paso de aire, clic, subida de tensión), la cama musical
opcional y la caja registradora de ejemplo (`marca/sonidos/caja.wav`) **los sintetiza el propio
kit** (`herramientas/sonido.py`, con NumPy). No hay muestras de terceros dentro del kit ni se
descarga ninguna: no hay licencias de audio que revisar. Son obra original de D-IA y van con la
licencia MIT del kit.

Lo que tú dejes en `marca/musica/`, `marca/sonidos/`, `marca/logos/` y `marca/broll/` es tuyo y
es cosa tuya que tengas derecho a usarlo (música con licencia para redes, logos solo para
referirte a su marca).

## B-roll

El kit **no descarga imágenes de stock ni usa APIs de pago**. El B-roll sale de tus archivos
(`marca/broll/`), de capturas de webs que nombras, hechas en tu ordenador con el navegador
sin ventana que ya instala HyperFrames (Chrome Headless Shell), o de imágenes que Claude dibuja
en HTML/SVG. Una captura de una web sigue siendo contenido de esa web: úsala para referirte a
ella. Los iconos de las pantallas completas se bajan del set Tabler de Iconify (licencia MIT)
cuando un beat los pide.

## Plantillas aprendidas con /estilo

`/estilo` guarda principios y ritmo de una referencia (cada cuánto entra un recurso, si hay
subtítulos, tamaños, zooms, transiciones). No guarda ni reutiliza sus fotogramas, tipografías
exclusivas, colores de marca, logos, música ni textos. Los fotogramas analizados se quedan en
`trabajo/_estilos/` y se pueden borrar.

## Ideas de otros proyectos (sin copiar código)

- **Barty-Bart/motion-graphics** (MIT, © 2026 Bart): de su flujo tomamos tres ideas, escritas
  desde cero aquí: enseñar el plan en una tabla y esperar el OK antes de renderizar, no inventar
  cifras en pantalla y revisar hojas de fotogramas antes de entregar. No se ha copiado código,
  fuentes ni iconos de ese repositorio.
- **Nate Herk** (vídeo sobre edición con Claude): el orden de cinco pasos (transcribir, cortar,
  planificar beats, skills reutilizables, bucle de verificación) y la idea de zooms sutiles y
  sonido en cada animación.
- **Principios de edición** (ritmo, un recurso por frase, un solo acento, sin cajas): tomados como
  criterio general del oficio, sin copiar el lenguaje visual, los recursos ni los assets de
  ningún canal. La identidad visual del kit («dia-editorial») es propia de D-IA.
- **Proyecto Motion de D-IA** (propio): lenguaje visual (entradas por enfoque, barrido de luz
  único, extrusión 3D con canto, «aire + grave» en cada golpe, nunca más de dos sonidos a la vez).
- **cth9191/motion-design**: revisado y descartado. No tiene licencia publicada y su flujo
  depende de generación de pago en Higgsfield. No se ha usado nada.

Los textos de licencia completos de cada pieza se instalan junto a ella (por ejemplo,
`node_modules/hyperframes/LICENSE`).
