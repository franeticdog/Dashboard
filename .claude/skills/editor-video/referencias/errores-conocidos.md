# Errores conocidos y cómo se resolvieron

Anotados durante el montaje y la prueba real del kit (28-sep-2026) y durante la subida de
acabado de la versión 2 (29-sep-2026).

## Resueltos

| # | Fallo | Causa | Solución en el kit |
|---|---|---|---|
| 1 | Whisper escribía «Clotopus», «clot» con el modelo `small` | Modelo pequeño y sin pistas | Modelo `turbo` por defecto + `glosario` como pista + `correcciones` en `brand.json` |
| 2 | A partir del segundo 26 la transcripción salía sin puntos ni mayúsculas | `condition_on_previous_text=False` | Se deja el valor por defecto de Whisper |
| 3 | «5.5» salía como «5 .5» en subtítulos | Whisper parte el número en dos tokens | Los tokens que llegan sin espacio delante se pegan a la palabra anterior |
| 4 | «Cloud Markdown» no se corregía a «CLAUDE.md» | Las correcciones solo iban palabra a palabra | Correcciones de varias palabras a una, conservando tiempos y puntuación |
| 5 | «este» se cortaba como muletilla | Estaba en la lista de muletillas, pero es una palabra normal | Lista de muletillas solo con sonidos: eh, em, mmm… |
| 6 | La palabra iluminada del subtítulo se pegaba a la siguiente («comoestabas») | Escalado al 107 % de la palabra activa | Solo cambia de color; más espacio entre palabras |
| 7 | En vertical, los textos destacados tapaban ojos y boca | Posición «arriba», pensada para horizontal | En vertical los destacados van solos bajo la barbilla y los subtítulos más abajo |
| 8 | En vertical, logo con nombre y rótulo chocaban arriba | No caben los dos en 1080 px | En vertical el logo va solo con el monograma |
| 9 | El monograma salía «D·» | Iniciales de «D-IA · El Campamento» | Si la primera palabra es una sigla corta (D-IA) se usa entera |
| 10 | Rótulo y destacado a la izquierda a la vez | El plan no lo comprobaba | `plan tabla` avisa de ese choque y de destacados del mismo lado que se pisan |
| 11 | Destacado de la izquierda rozaba la cara en horizontal | Tarjeta de 760 px | Ancho máximo 580 px y letra de 66 px |
| 12 | Render de dos formatos: 88 s para 47 s de vídeo | Se hacían uno detrás de otro | Se renderizan a la vez: 50 s |
| 13 | Error de Python al construir el logo | Concatenación de f-strings sin `+` | Corregido y cubierto por la prueba de `/comprobar` |

| 14 | El detector de caras de MediaPipe se cerraba de golpe en Mac («Service is unavailable») | Una pieza del detector exige la GPU de Metal | La cara sale del mismo segmentador que recorta a la persona (clase «piel de la cara» + pelo). Un solo modelo |
| 15 | HyperFrames rechazaba la capa: animar `letterSpacing` salta a píxeles enteros | La regla de HyperFrames solo admite transformaciones | Las entradas de «tracking» se hacen con escala horizontal y desenfoque |
| 16 | «Missing window.__timelines registration» | El motor iba en un .js aparte y el revisor no lo lee | El motor se escribe dentro del HTML |
| 17 | El énfasis plano salía como un bloque de color | `background-clip: text` en el padre no recorta letras animadas por separado | El degradado va en cada letra |
| 18 | Palabras cortas («KIT», «MAL») salían tan grandes que se cortaban por arriba | El tamaño solo miraba el ancho | Se limita también la altura de las mayúsculas |
| 19 | En vertical el texto «por detrás» tapaba los ojos | El recorte miraba el cuadrado de abajo del fotograma y no veía la cara | La ventana del recorte se centra en la cara |
| 20 | En vertical el texto por detrás no se leía (la cabeza ocupa casi todo el ancho) | Misma colocación que en horizontal | En vertical va como la cabecera de una portada de revista: encima de la cabeza, con el pelo tapando el pie de las letras |
| 21 | Un «whoosh» sonaba tan alto como la voz | El volumen se medía en el arranque del efecto, que es silencioso | Se mide el tramo más fuerte (60 ms) de cada efecto |
| 22 | Dos graves a la vez al empezar (logo y primer énfasis) | Nada limitaba la densidad | Nunca más de dos sonidos a la vez y nunca el mismo pegado |
| 23 | El nombre de la marca junto al logo se cortaba en el borde derecho | Ancho del texto estimado a ojo | El logo se ancla por la derecha |
| 24 | El logo en grande chocaba con el primer énfasis | Los dos arriba a la vez | Si coinciden, el logo entra ya pequeño; en vertical espera a un hueco sin énfasis |

| 25 | Los recursos nuevos no aparecían en pantalla | Sus tiempos ya eran del vídeo y se les volvía a sumar el inicio del clip | Los recursos llevan tiempos absolutos y no se desplazan |
| 26 | El contorno de luz rellenaba a la persona entera de color | La resta de la máscara dejaba luz también por dentro | Solo se ilumina por fuera de la silueta |
| 27 | La segunda línea corta del texto por detrás («MAL») quedaba tapada por la cabeza | Iba centrada debajo de la primera | Si la segunda es corta, van en la misma línea; en vertical, siempre en una |
| 28 | En vertical las tarjetas de referencia pisaban los subtítulos | Huecos pensados para horizontal | Huecos propios del vertical, por encima de los subtítulos |
| 29 | Paleta de muchos colores | Cada énfasis cogía un color | Un solo color de acento (`color_enfasis`) más el blanco; varios colores solo con `"multicolor": true` |

| 30 | La edición se parecía demasiado a la de un vídeo de referencia | Se copiaron sus recursos uno a uno | Versión 4: de la referencia solo quedan los principios; lenguaje visual propio («dia-editorial») y fuera los recursos reconocibles |
| 31 | Frases por detrás tapadas por la cabeza («UTILIZ_DO») | Centradas en la cara | Van a un lado, alineadas al borde de fuera: la cabeza solo roza el arranque |
| 32 | Subtítulo y gráfico diciendo lo mismo a la vez | Subtítulos continuos | Subtítulos solo en los beats marcados con «sí» |
| 33 | Fotogramas hechos papilla en el látigo | Pasos grandes y 0,32 s de duración | 8 pasos de 0,018 con pesos decrecientes, 0,25 s como mucho |
| 34 | En vertical, el compositor fallaba sin frases por detrás | El recortador no existía y se reiniciaba igual | Se comprueba antes |

| 35 | Los logos de HyperFrames y D-IA no salían (y el de Claude necesitaba internet) | Los SVG oficiales no viajaban en el zip y el set de Iconify no tiene esos dos | `marca/logos/` trae `claude.svg`, `hyperframes.svg` (con su degradado `#49DB6C → #08E4F4` por defecto) y `d-ia.svg` |
| 36 | `/reels` sobre un bruto sin editar se paraba («el plan todavía no está aprobado») | `animar` pide un plan aprobado y la orden daba por hecho un `/editar` anterior | `/reels` prepara solo lo que falte (transcribir, cortar, plan de los tramos) y pide un único OK |
| 37 | Subtítulo a trozos («no es Claude» sin el «Y no,») | Las frases se partían en cada coma y los trozos de menos de 3 palabras se tiraban | Un trozo corto se une al siguiente; la tabla avisa si un «sí» no va a enseñar subtítulo |
| 38 | El rótulo salía con «Subtítulo: sí» pero nunca lo enseñaba | El campo `subtitulo` del rótulo es la línea del @ y se leía como «sí» | En el rótulo manda `con_subtitulo` (no por defecto) |
| 39 | Las capturas de un reel solo enseñaban subtítulos, no las piezas | `verificar` no sabía qué tramo era el del reel | `animar` apunta el tramo y `verificar` captura cada pieza del reel |
| 40 | `kit.py tiempos` daba 164 s para una pasada de 130 s | Sumaba los dos formatos, que se componen a la vez | Los formatos en paralelo cuentan una vez |
| 41 | En vertical, con camiseta blanca, el rótulo y las fases casi no se leían | Crema sobre blanco con una sombra pensada para ropa oscura | En vertical, sombra de texto más densa y el plató más bajo detrás (sin cajas) |

Los fallos 35 a 41 salieron de la prueba del 29-sep-2026 con un bruto nuevo (camiseta blanca, gorra),
no el de la demo.

Los fallos 6 a 11, 17 a 24, 25 a 28 y 31 a 34 los encontró el propio bucle de verificación: salían en las hojas de
capturas y se corrigieron antes de dar la demo por buena. Es el paso que no hay que saltarse.

## Limitaciones que siguen ahí

- **En vertical, la frase «por detrás» va delante**, bajo la barbilla: la cabeza ocupa casi todo
  el ancho y por detrás no se leería. El efecto de profundidad es de horizontal.
- **El efecto «por detrás» es sutil a propósito**: la frase va a un lado y la persona solo tapa
  el arranque. Si se quiere más profundidad, la frase se come la cabeza y deja de leerse.
- **El sonido no se ha revisado a oído.** Los efectos se sintetizan con criterio (aire en agudos,
  grave con cuerpo, nada en la banda de la voz) y se han medido por bandas y niveles, pero nadie
  los ha escuchado todavía con cascos. Si alguno molesta: `"nivel_efectos": 0.6` en `brand.json`
  (o `0` para quitarlos) y se vuelve a componer, sin volver a animar.
- **Tarda más que la versión 1.** Cada énfasis es un render 3D aparte y el montaje es fotograma a
  fotograma con recorte de la persona. Cifras en `TIEMPOS.md`.
- **El recorte de la persona es de un modelo ligero** (256x256): con poca luz, pelo muy rizado o
  fondo del mismo color que la ropa, el borde puede comerse o dejar un poco de fondo. Se suaviza
  en el tiempo para que no parpadee. Si un énfasis se ve raro, cambia su color o pon
  `"estilo": "plano"` en ese beat.
- **En grabaciones de pantalla** el «por detrás» se queda por detrás solo de la persona que salga
  (la miniatura de la cámara); sobre la pantalla el texto va delante.
- **Mediapipe en Windows** está escrito y pensado, pero la prueba se hizo solo en Mac con chip M.
- **La capa de animaciones pesa mucho** (ProRes 4444 con transparencia): unos 350 MB por cada
  47 s y formato, más unos 20 MB por énfasis. Borra `trabajo/` cuando entregues.
- **Vertical desde horizontal recorta el centro de la persona** (sigue a la cara plano a plano).
  Para tutoriales de pantalla, mejor solo horizontal.
- **Ropa clara en vertical.** Con camiseta blanca los textos bajo la barbilla se leen, pero peor que
  con ropa oscura, sobre todo las fases que aún no han llegado (van atenuadas a propósito). Para
  reels, mejor ropa oscura o lisa.
- **Una mano delante de la frase «por detrás» se come letras** (es el efecto: la persona tapa el
  texto). Si la mano tapa la palabra clave, cambia esa frase de lado.
- **La demo es un tramo de un vídeo ya publicado**, no un bruto: casi no hay cortes que hacer.
- **Si Whisper se equivoca en una palabra dudosa**, el script la lista, pero lo decide Claude
  leyendo la transcripción.

## 42 · «Esa frase, al otro lado» no movía la frase por detrás (29-sep-2026)
**Síntoma:** en el plan se ponía `"posicion": "izquierda"` a una frase por detrás y seguía saliendo a la derecha (el lado con más sitio). **Arreglo:** `construir_editorial` y `lado_libre` (animar.py, recursos.py) respetan el lado pedido si caben al menos 300 px; si no se pide, elige solo el lado con más sitio. Probado en el ensayo: «Menos de un céntimo» pasa a la izquierda y la mano ya no se come la «d».

## Versión 5 (29-sep-2026): lo que salió en la grabación real y en la prueba del kit nuevo

| # | Fallo | Causa | Solución en el kit |
|---|---|---|---|
| 43 | A mitad de la edición, Claude **empezó a contestar en inglés** (visto en la grabación) | Los logs y errores de las herramientas salen en inglés y arrastran | `"language": "spanish"` en `.claude/settings.json`, regla de idioma arriba del todo en `CLAUDE.md` y en cada orden y cada skill, resúmenes finales incluidos |
| 44 | El usuario dejó el vídeo **en otra carpeta** y hubo que buscarlo a mano | `kit.py` solo miraba en `brutos/` | Si no está, lo busca por nombre parecido en `brutos/` y en la raíz del kit, lo usa y avisa («No encuentro X tal cual, pero he encontrado Y») |
| 45 | B-roll, pantallas completas y zooms del segundo reel del directo se hicieron **a mano, fuera del kit** | El kit no tenía esos recursos | Recursos `broll`, `pantalla` y `zoom` (y el campo `camara` en cualquier beat), documentados en la skill `animar` («Pedirlo hablando») |
| 46 | Los reels cogían la plantilla del vídeo largo | La del plan mandaba sobre la de los reels | En reels manda `--plantilla` > `plantilla_reels` > la del plan |
| 47 | Con subtítulos «siempre», el B-roll los apagaba | Se trataba como una pantalla completa | El B-roll mantiene los subtítulos (la voz sigue); la pantalla completa los aparta |
| 48 | Una captura horizontal de B-roll en un reel salía cortada por los lados | Se recortaba para llenar | `ajuste: auto`: si la forma no encaja, va entera sobre un fondo desenfocado de sí misma. Para reels, mejor capturar en móvil (`--movil`) o en vertical |
| 49 | El barrido de luz en los logos 3D no se veía | Una luz direccional sobre una cara plana apenas cambia | Luz puntual cerca del logo que cruza en 0,3 s: reflejo suave que pasa por el bisel |
| 50 | `plan tabla` avisaba de subtítulos que no saldrían aunque la plantilla los pone siempre | El aviso solo tiene sentido en modo «momentos» | Solo avisa en modo «momentos» |

## Limitaciones nuevas

- **Capturas de webs con aviso de cookies**: la captura local sale con el aviso. Si molesta, deja
  tú una captura limpia en `marca/broll/`.
- **PNG sin fondo transparente**: el color de las esquinas se toma como fondo. Con logos sobre
  fondos degradados, mejor un SVG o un PNG transparente.
- **La transición `desenfoque`** (plantillas que la piden) se ha probado con un corte forzado, no
  con un bruto real con varios planos.
- **La música y los sonidos de prueba** del test eran sintéticos; el nivel de la cama (unos 20 dB
  bajo la voz y 9 dB más al hablar) está medido, no escuchado con cascos.

## Instalación en Windows (9-oct-2026)

| # | Fallo | Causa | Solución en el kit |
|---|---|---|---|
| 51 | El modelo de Whisper no se descargaba («Espacio en disco insuficiente») | Se bajaba a la caché del disco del sistema (C:), que estaba casi lleno | El modelo se guarda dentro del kit, en `modelos/huggingface` (`HF_HOME` en `comun.py`) |
| 52 | Whisper fallaba al leer el audio («unexpected keyword argument 'metadata_errors'») | PyAV 19 (29-sep-2026) quitó ese parámetro y faster-whisper 1.2.1 lo sigue usando | El instalador fija `av<19` |
| 53 | El render de prueba se negaba a arrancar («Low disk space: 0.7 GB free at …\Temp») | En Windows, HyperFrames guarda los fotogramas del render en la carpeta temporal del sistema y pide 1 GB libre | Si el disco del sistema tiene menos de 10 GB libres, `comun.py` manda los temporales a `trabajo/_tmp` |
| 54 | `cortar aplicar` fallaba («Unrecognized option 'filter_complex_script'») | ffmpeg 9 quitó esa opción (desde la 7 se escribe `-/filter_complex`) | `cortar.py` mira la versión de ffmpeg y usa la forma que toca |
| 55 | Tras instalar ffmpeg con winget, el kit no lo encontraba hasta reiniciar Claude Code | winget añade ffmpeg al PATH del usuario, pero los procesos ya abiertos no lo ven | `comun.py` lo busca en la carpeta de winget y lo añade al PATH de la sesión |
| 56 | Toda la transcripción salía en minúsculas y sin un punto (vídeo de 40 s con voseo) | La pista a Whisper era solo la lista del glosario («Grupo Nergia, Nergia, Canals.») | En español, la pista es una frase normal con mayúsculas y signos («Hola, ¿qué tal? Hoy te hablo de …»): puntúa bien y acierta más el voseo («tenés», «hacé clic») |
| 57 | La tipografía de la marca (Montserrat) no salía en ningún sitio | El estilo «dia-editorial» fijaba Archivo y no miraba `brand.json` | En «dia-editorial», lo estructural (subtítulos, etiquetas, 3D) usa `tipografia` de `brand.json`; la serif y la mono siguen siendo de la identidad |
| 58 | Subtítulos con una palabra suelta («datos.») o cortados en «tu \| proyecto» | Se agrupaban de max_pal en max_pal sin mirar el sentido | `agrupar` reparte cada frase con el menor coste: trozos de 3-4 palabras, corte en coma, nunca tras artículo o preposición |
| 59 | En exteriores con mucha luz, los textos pequeños (antetítulo, rótulo, @) casi no se leían | Solo llevaban sombra de texto | Un velo radial suave y sin bordes (`.velo`) detrás de etiquetas, rótulo y tachado pequeño; el antetítulo de la etiqueta va en crema |
| 60 | `plan tabla` avisaba de subtítulos que no saldrían con `"subtitulos": "siempre"` en el plan | El aviso miraba el modo de la plantilla, no el del plan | Manda el del plan, igual que en `animar` |
| 61 | Volvía el 6: «avanzardirectamente,» en el subtítulo | La palabra activa crecía al 106-110 % (con rebote) y una palabra larga se comía el espacio | En los estilos sin caja, la palabra que se dice solo cambia de color |
| 62 | Con una lista en `etiqueta`, antes del primer punto se veía una mancha oscura con solo el antetítulo | El velo cubre la lista entera desde el principio | En las listas, el velo entra con el primer punto |
| 63 | Palabras del subtítulo que se iluminaban descompasadas (lo notó el usuario) | Whisper turbo sitúa cada palabra con 0,2-0,5 s de error, unas antes y otras después (medido en los arranques tras silencio: error medio 174 ms) | `alinear.py`: con el texto de Whisper, un wav2vec2 CTC en español (ONNX, onnxruntime, Apache-2.0) encaja cada letra en su trama de 20 ms. Mediana 30 ms y la palabra correcta en cada arranque. Si falla, se quedan los tiempos de Whisper |
| 64 | El vídeo final se veía más blando y «pixelado» que el bruto (el usuario lo llamó «el LUT») | Grano de película (lo que peor comprime) + viñeta + reencuadre bilineal en cada fotograma + CRF 21; intermedio de los cortes en CRF 18 | `"grano": false` y `"vineta": false` en `brand.json`; reencuadre bicúbico; final en CRF 17 `slow`; intermedio en CRF 12 y zoom de los cortes con lanczos |
| 65 | Rectángulo negro sobre la persona desde el segundo 3,5 hasta el final (lo vio `verificar` antes de entregar) | `cv2.ximgproc.guidedFilter` (OpenCV 5, Windows) devuelve a veces NaN en medio cuadro (guía en 0-255: la varianza en coma flotante sale negativa) y el suavizado temporal de la máscara lo arrastra a todos los fotogramas siguientes. Habría roto también los textos por detrás | `persona.filtro_guiado`: el filtro hecho con filtros de caja, guía en 0-1 y varianza ≥ 0; y si una máscara sale no finita, se cae al desenfoque y no contagia a las siguientes |
| 66 | «Zoom-in, zoom-out desprolijos» (lo notó el usuario) | Se sumaban un zoom lento continuo, empujones que acercan en 0,55 s y vuelven a abrir (uno, al acabar el vídeo) y el zoom de los cortes centrado en el cuadro, que hacía saltar la cara en cada corte | El zoom de los cortes, anclado a un tercio desde arriba; `"zooms": {"ken_burns": 0}` en `plan.json` para dejar la cámara fija; y en vídeos así, sin beats `zoom` ni `"camara"` |
| 67 | El tachado «Esperar → Avanzar directamente» se veía desincronizado y duraba poco (lo notó el usuario) | La frase nueva entraba letra a letra seguida, sin mirar cuándo se dice cada palabra; la salida (0,38 s antes del final) empezaba mientras aún se decía «directamente», así que nunca llegaba a verse entera; y la palabra vieja salía 0,4 s antes de decirse | Cada palabra de `nueva` entra en el segundo en que se dice (`_tiempos_frase`); el `cuando` va en la palabra vieja; si detrás viene una `pantalla`, el tachado dura hasta su entrada y el círculo lo tapa (`plan tabla` ya no lo cuenta como solape). El tachado pequeño usa la letra y el margen de las etiquetas |

Nuevo en esta tanda: el recurso `etiqueta` (texto pequeño de apoyo, o lista corta con ticks) y `escala` en el
`tachado`. Pensados para cuando el usuario pide subtítulos en todo el vídeo y, además, textos pequeños en pantalla.
También `"luz_cara"` (luz de relleno sobre la persona, en `componer`): el usuario pidió «un poco más de luz en la
cara» en un exterior a contraluz; con 0,22 la cara sube un 18 % de luminosidad y el cielo no cambia.
