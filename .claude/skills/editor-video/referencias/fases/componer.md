> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# Componer

**Idioma:** responde siempre en español de España, también en los resúmenes y cuando algo falle (aunque el error salga en inglés).

```
kit.py componer <video> [--formato horizontal|vertical]
kit.py componer <video> --formato vertical --desde 12.4 --hasta 48.1 --nombre reel1
```

Por cada fotograma, en este orden:

1. **Cámara**. Encuadre (el vertical sigue a la persona plano a plano; en un tutorial de pantalla,
   centra la pantalla), un ken burns del 3 % por plano, un empuje suave del 5 % cuando entra un
   énfasis (hacia la cara, nunca mareante) y un «látigo» con desenfoque de zoom en las transiciones.
2. **Profundidad**. En cada énfasis por detrás: recorta a la persona con MediaPipe (máscara
   ajustada a los bordes y suavizada en el tiempo, sin parpadeo), pone el texto 3D entre el fondo
   y la persona, oscurece y desenfoca un poco el fondo para que ella destaque, y mezcla los últimos
   fotogramas del texto al entrar y salir (desenfoque de movimiento). Borde limpio: nada de
   contorno, halo ni brillo alrededor de la persona.
2b. **Antes / ahora**: con `barrido`, a un lado del deslizador el plano se apaga y pierde el color.
3. **Cristal** (solo en los estilos con tarjetas): desenfoca e ilumina el vídeo allí donde la capa
   tiene un panel.
4. **La capa animada** encima, una viñeta muy suave y un grano fino de película. Los dos se quitan
   con `"vineta": false` y `"grano": false` en `brand.json` (el grano cuesta nitidez al comprimir: si el
   usuario nota el vídeo «pixelado» o «con un filtro», es lo primero que se quita).
1a. **Luz de relleno** (`"luz_cara"` en `plan.json`, o en `brand.json` para todos los vídeos; 0,2 es
   «un poco más», 0,35 ya se nota mucho): aclara a la persona, sobre todo la cara, solo dentro de su
   silueta (el fondo no se toca), en sombras y medios tonos y sin cambiar el color. Para la persona a
   contraluz o en sombra con un fondo luminoso. Solo hace falta volver a componer, no animar.
1b. **B-roll**: en sus tramos, la foto o el vídeo de recurso tapan la cámara (la voz sigue), con
   zoom lento y un fundido desenfocado de 0,22 s al entrar y salir.
5. **Sonido**: la voz, los efectos sintetizados en su segundo exacto (nunca más de dos a la vez),
   los **sonidos de marca** (`marca/sonidos/mapa.json`: «dinero» → caja.wav; mandan sobre los
   efectos) y la **música de cama**: la de `marca/musica/` si hay (bucle, fundidos y ducking: baja
   unos 9 dB mientras hablas), o la cama sintetizada del kit si se pide. Todo a unos -16 LUFS.
   `brand.json` `"musica"`: `"auto"` (de serie: la tuya si la hay), `true`, `false` o un archivo.

- Cámara según la plantilla: ken burns, empujes, **golpes de zoom** (entran en 0,08 s y sueltan en
  0,3 s) y transición `latigo`, `desenfoque` (estela lateral) o `corte`. Los zooms pedidos por
  frase (`zoom`, `"camara"`) se suman. `"zooms"` en `plan.json` ajusta los de la plantilla para un
  vídeo: `{"ken_burns": 0}` deja la cámara fija entre cortes.
- Si el usuario nota «zooms desprolijos» (acercar y volver a abrir): quita los beats `zoom` y los
  `"camara"` del plan y pon `"zooms": {"ken_burns": 0}`. Queda solo el acercamiento de los cortes
  (anclado a la altura de la cara), que es un único movimiento y se lee como cambio de plano.
- `"encuadre_vertical"` en `plan.json`: `"auto"` (sigue a la persona) o un número de 0 a 1.
- Salida H.264 + AAC, 30 fps, en la carpeta de finales: `<video>-<formato>.mp4` (CRF 17, `slow`; el
  reencuadre de cámara es bicúbico para no ablandar la imagen).
- Tarda como un vídeo en tiempo real (47 s de clip: unos 45 s por formato, con 9 énfasis).
- Si algún texto de la capa tapa ojos o boca, lo avisa con el segundo exacto y queda apuntado para
  `verificar`.
