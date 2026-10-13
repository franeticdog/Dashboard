# Tiempos reales medidos (versión 5, 29-sep-2026)

Máquina: MacBook con Apple M5 Pro, 24 GB de RAM, fibra. ffmpeg y Node 22 ya estaban instalados y
el modelo de Whisper ya estaba descargado. Todo medido con reloj, desde el zip descomprimido en
una carpeta vacía fuera de iCloud. **Dependerá de tu máquina**: todo lo mueve tu ordenador, y con
otros programas pesados abiertos (la «carga» de macOS va al lado de cada cifra) tarda más.

## Lo que se dice en el vídeo

| Qué | Tiempo |
|---|---|
| Instalar (`/empezar`) | unos **70 s** |
| Comprobar (`/comprobar`, con el ensayo general) | unos **50 s** |
| Editar un fragmento de 30 s en horizontal y vertical | **de 2 a 3 minutos** de máquina |
| Un reel de 25 s | unos **100 s** |
| Regla para un vídeo de 10 minutos | **de 35 a 55 minutos** de máquina (de 3,5 a 5,5 s por segundo de vídeo) |

## 1 · Instalación y comprobación

| Paso | v5 (hoy) | Antes |
|---|---|---|
| `kit.py instalar` desde cero, con las skills oficiales de HyperFrames | **75 s** (carga 7) · 69 s sin las skills | 71 s en la grabación, 72 s en la v4.2 |
| Descarga del modelo de Whisper turbo (1,6 GB), si no está ya en el ordenador | +42 s | medido en la v3 |
| `/comprobar` completo | **56 s** (carga 7-14) | 50 s en la v4.2 |
| · de ellos, el ensayo general con 8 s de vídeo (las seis fases) | **33 s** | 28 s |
| Reparar una pieza que falta (Three.js borrado a propósito): `/comprobar` la marca en rojo y `/empezar` la reinstala | **11 s** | |

## 2 · Editar: un fragmento de 30 s, horizontal y vertical a la vez

Bruto real de la grabación: 30 s de Martín a cámara, **4K** (3840x2160), 30 fps. Plan con 9
recursos (golpe 3D, dos contadores, tres frases por detrás, rótulo, logo 3D y un tramo de
subtítulo).

| Fase | En la grabación (Martín) | v5, plantilla `youtube-editorial` (carga 7 → 21) |
|---|---|---|
| Transcribir (Whisper turbo) | | 3,9 s |
| Cortar (el 4K se recodifica entero) | | 14,7 s |
| Buscar la cara | | 7,0 s |
| Animar: 2 capas + 6 frases por detrás | | 81,9 s |
| Componer los dos formatos a la vez | | 118,9 s |
| Verificar | | 6,0 s |
| **Total de máquina** | **«unos 3 minutos»** | **232 s (3,9 min)** con el ordenador muy cargado |

Con la misma pasada y el ordenador menos cargado (carga 5-11) salió 2,2-2,8 min (v4.2) y, en la
copia de desarrollo de hoy, animar 85 s y componer 76 s. Con la plantilla `reels-dinamico` y los
mismos 30 s en dos formatos (con B-roll, pantalla completa, música y sonidos de marca): animar
78 s y componer 119 s, con carga 14-21.

Lo que más pesa: los logos 3D y las frases por detrás (cada una, un render aparte y el recorte
de la persona fotograma a fotograma). Un bruto en 4K tarda algo más en cortar que uno en 1080p.

## 3 · Reels

| Caso | Tiempo |
|---|---|
| Reel de 25 s de un bruto que ya pasó por `/editar` (animar + componer + verificar, con música de cama, sonido de marca, B-roll y pantalla completa) | **70 s** (carga 21) |
| Reel de 25 s de un bruto de 90 s SIN editar antes (transcribir, cortar, plan, animar, componer, verificar) | **102 s** (v4.2) |

## 4 · Lo nuevo de la v5

| Qué | Tiempo |
|---|---|
| `/estilo` con 3 capturas: preparar la hoja y el borrador | menos de 1 s (más lo que tarda Claude en mirar y rellenar) |
| Captura local de una web para B-roll (`kit.py broll web`) | unos 1-2 s |
| Imagen dibujada por Claude en HTML convertida en B-roll | unos 1 s |

## Lo que no está en la tabla

- **El tiempo de Claude pensando**: leer la transcripción y elegir un recurso para cada frase.
  A ojo, un par de minutos para un fragmento de 30 s.
- **Tu tiempo** revisando la tabla, diciendo «vale», revisando el resultado e iterando.
- `kit.py tiempos <video>` suma las fases de máquina. Los dos formatos se componen a la vez y
  cuentan una sola vez.
- Lo mismo a mano en un programa de edición es trabajo de horas. No está medido: si lo usas,
  dilo como estimación.
