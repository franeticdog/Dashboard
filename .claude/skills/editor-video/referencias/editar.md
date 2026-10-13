> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# /editor-video editar $ARGUMENTS

> **Idioma:** responde siempre en español de España, también en los resúmenes de cada fase, en el resumen final y cuando algo falle (aunque el error salga en inglés).

Edita el vídeo indicado. El primer argumento es el nombre del archivo (dentro de la carpeta de
brutos) o su ruta completa. El segundo, opcional, el formato: `horizontal`, `vertical` o
`ambos`. Si no lo dice, usa el formato del propio vídeo; si el vídeo es horizontal, pregunta
en una línea: «¿Lo saco también en vertical para Reels?». Con `--plantilla <nombre>` se usa
esa plantilla solo en este vídeo (si no, la de `brand.json`; lista: `kit.py estilo lista`).

**Si el vídeo no está donde dice**, `kit.py` lo busca por nombre parecido en `brutos/` y en la
carpeta del proyecto y lo usa (sale un aviso «No encuentro X tal cual, pero he encontrado Y»). Díselo
al usuario en una línea y sigue. Si no encuentra nada parecido, pídele que lo deje en `brutos/`.

Antes de nada, `kit.py proyecto`: si falta el entorno o la carpeta aún no tiene marca, sigue «Al empezar» de SKILL.md (con una sola marca guardada, el proyecto se prepara solo).

En cada fase: di en una línea qué haces, lanza la orden, y resume el resultado con cifras
(segundos, número de cortes, piezas).

## 1 · Transcribir

```
kit.py transcribir <video>
```

Lee `trabajo/<video>/transcripcion.txt` entera. Busca palabras mal transcritas (nombres
propios, marcas, términos del sector). Si hay, añádelas a `"correcciones"` de
`brand.json` (`"lo que pone": "lo que debe poner"`) y relanza la transcripción: tarda
segundos. Detalle en `fases/transcribir.md`.

## 2 · Cortar

```
kit.py cortar analizar <video>
```

Lee `cortes.json` y la transcripción. El script detecta silencios y muletillas, y propone
tomas repetidas y frases a medias. **Tú decides** con la lectura del texto:

- Si la misma idea se dice dos veces seguidas, quita la primera toma (la buena suele ser la
  última). Añade a `"quitar"` un objeto con `"palabras": [desde, hasta]` y un `"motivo"`.
- Las de `"revisar"` son frases que se cortan a medias: quítalas si luego se repiten bien.
- No cortes nada que cambie el sentido. En la duda, se queda.

Después:

```
kit.py cortar aplicar <video>
```

Cuenta «de X s a Y s». Detalle en `fases/cortar.md`.

## 3 · Planificar (espera el OK)

```
kit.py plan borrador <video> [--plantilla <nombre>]
```

El borrador te dice qué pide la plantilla (ritmo, recursos, subtítulos) y qué assets del
usuario encajan: logos de `marca/logos/` que se nombran y palabras con sonido de marca. Abre
`trabajo/<video>/plan.json` y elige un recurso para cada frase (frase editorial por
detrás, tachado, logo 3D, contador, fases, terminal…) y marca qué frases llevan subtítulo, siguiendo la
`fases/planificar.md`: un recurso por idea que importa y subtítulos solo en los momentos clave. Pon en `"formatos"` los que toquen. Luego:

```
kit.py plan tabla <video>
```

Enseña la tabla tal cual y pregunta: **«¿Te vale así o cambio algo?»**. Espera la respuesta.
Si pide cambios, edita `plan.json` y vuelve a enseñar la tabla. Con el OK:

```
kit.py plan aprobar <video>
```

## 4 · Animar

```
kit.py animar <video>
```

Genera la capa de animaciones y los énfasis en 3D con HyperFrames para cada formato. Tarda algo
más de lo que dura el vídeo. Avisa: «Renderizando las animaciones en 3D, tarda algo más de lo que
dura el vídeo».

## 5 · Componer

```
kit.py componer <video>
```

## 6 · Verificar y corregir

```
kit.py verificar <video>
```

Abre con Read la `hoja.jpg` de cada formato y, después, cada captura de una pieza. Sigue la
lista de `fases/verificar.md`. Si algo falla, corrige `plan.json` (posición, duración, texto),
y repite animar, componer y verificar **solo del formato afectado** (`--formato vertical`).
Máximo dos vueltas; si a la segunda sigue mal, entrégalo y di qué queda flojo.

## 7 · Entregar

```
kit.py tiempos <video>
```

Da al usuario:
- la ruta de cada vídeo terminado,
- una línea por formato con duración y lo que lleva,
- la tabla de tiempos («la máquina ha tardado X min»),
- qué has corregido en la verificación, si algo,
- una sugerencia: «¿Saco también reels verticales de este vídeo? Escribe `/editor-video reels <video>`».

Todo el resumen, en español de España. Las capturas de cada pieza están en
`trabajo/<video>/capturas/`: dile que puede mirarlas y decir «esto sí, esto no».
