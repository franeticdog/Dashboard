> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# /editor-video comprobar · Modo ensayo

> **Idioma:** responde siempre en español de España, también en los resúmenes de cada fase, en el resumen final y cuando algo falle (aunque el error salga en inglés).

Es lo que se lanza **cuando algo no funciona**: revisa todo lo que hace falta para editar y
dice qué falta. No instala nada.

```
kit.py comprobar
```

(Para revisar sin ensayo: `--rapido`.)

Revisa, sin instalar nada: ffmpeg, Node, HyperFrames y su navegador, Whisper, MediaPipe,
Three.js, `brand.json`, colores, logo, tipografías, plantillas, música, sonidos y logos de
`marca/`, que se pueda escribir en las carpetas y el espacio en disco (5 GB libres).
Después hace un **ensayo general**: coge 8 segundos del vídeo de `demo/` y lo pasa por las seis
fases, con la carpeta de finales del ensayo aparte para no ensuciar la tuya.

Cuando acabe, resume así:

- **Todo en verde**: «Todo listo. El ensayo completo ha tardado X s. Puedes grabar tranquilo.»
- **Algo en rojo**: di qué pieza falla, en llano, y arréglalo. Casi siempre basta con relanzar
  `kit.py instalar`, que salta lo que ya está bien. Luego repite
  `/editor-video comprobar` hasta verlo todo en verde.

Abre también `trabajo/ensayo/capturas/horizontal/hoja.jpg` y confirma en una línea que las
animaciones se ven con la marca correcta (colores, nombre, logo).
