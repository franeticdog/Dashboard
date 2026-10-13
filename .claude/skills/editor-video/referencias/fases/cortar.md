> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# Cortar

**Idioma:** responde siempre en español de España, también en los resúmenes y cuando algo falle (aunque el error salga en inglés).

Dos pasos, con tu criterio en medio:

```
kit.py cortar analizar <video>
# tú revisas y ajustas trabajo/<video>/cortes.json
kit.py cortar aplicar <video>
```

## Lo que detecta el script

- **Silencios** de más de `cortes.silencio_min` segundos (0,55 por defecto), por el audio y por
  los huecos entre palabras. Deja `cortes.margen` (0,12 s) de aire a cada lado.
- **Muletillas** sueltas: «eh», «em», «mmm».
- **Tomas repetidas**: una frase y, justo después, otra que empieza igual. Quita la primera.
- **Frases a medias** (en `"revisar"`): acaban en «de», «que», «y»… y luego hay pausa.

## Tu parte: leer y decidir

Lee `transcripcion.txt` con `cortes.json` al lado. El script no entiende el sentido; tú sí.

- Repetición con otras palabras («lo que quiero decir es… bueno, lo que os quiero contar es…»):
  quita la primera versión. Añade a `"quitar"`:
  `{"palabras": [120, 131], "motivo": "toma repetida"}`.
- Frases de `"revisar"`: si se retoman bien después, pásalas a `"quitar"`. Si no, déjalas.
- Arranques en falso al principio («vale, ¿grabando? vale») y despedidas fuera de guion: fuera.
- No quites nada que cambie el sentido. En la duda, se queda.

## Qué genera

- `cortado.mp4`: el vídeo limpio. Con `cortes.zoom_en_cortes` a `true`, un tramo sí y otro no
  entra con un zoom del 8 %, que disimula el salto del corte como hacen los editores. El zoom va
  anclado a un tercio desde arriba (la altura de la cara), así la cara no salta en cada corte.
- `palabras_cortado.json` y `transcripcion_cortada.txt`: los tiempos ya reajustados al vídeo
  cortado. Desde aquí, todas las fases trabajan sobre el vídeo cortado.
