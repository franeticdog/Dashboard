> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# /editor-video reels $ARGUMENTS

> **Idioma:** responde siempre en español de España, también en los resúmenes de cada fase, en el resumen final y cuando algo falle (aunque el error salga en inglés).

Saca clips verticales cortos (20 a 60 s) de un vídeo de la carpeta de brutos. **No hace falta
haber pasado antes por `/editor-video editar`**: si falta algo, lo haces tú aquí, sin preguntar nada técnico.

Antes de nada, `kit.py proyecto`: si falta el entorno o la carpeta aún no tiene marca, sigue «Al empezar» de SKILL.md (con una sola marca guardada, el proyecto se prepara solo).

## 0 · Preparar el vídeo (solo si hace falta)

Si NO existe `trabajo/<video>/palabras_cortado.json`, haz las fases 1 y 2 de `/editor-video editar`:

```
kit.py transcribir <video>
kit.py cortar analizar <video>
kit.py cortar aplicar <video>
```

Igual que en `/editor-video editar`: corrige en `brand.json` las palabras mal transcritas y decide los
cortes leyendo el texto. Resume en una línea («de X s a Y s»).

## 1 · Elegir los momentos

Lee `trabajo/<video>/transcripcion_cortada.txt`. Busca fragmentos que se entiendan solos:

- empiezan con una frase que engancha (una afirmación fuerte, una pregunta, un «el error
  es…»), nunca con «y», «pues» o «entonces»,
- acaban al final de una frase, con la idea cerrada,
- duran entre 20 y 60 segundos,
- mejor con la persona a cámara: en un tramo de grabación de pantalla el vertical se ve peor.

Por defecto, uno por cada 2-3 minutos de vídeo, máximo 5. Si el usuario dice cuántos, esos.
Calcula `inicio` y `fin` con `kit.py plan buscar <video> "frase"`.

## 2 · El plan (un solo OK)

- **Si ya hay un plan aprobado** (`plan.json` con `"aprobado": true`, de un `/editor-video editar` anterior):
  se reutiliza. Los reels cogen las piezas que caen dentro de su tramo.
- **Si no lo hay**: `kit.py plan borrador <video>`, y en
  `trabajo/<video>/plan.json` pon `"formatos": ["vertical"]`, quita el `rotulo` y elige un
  recurso para las frases que importan **solo dentro de los tramos elegidos**, con la skill
  `planificar`. Apunta cada reel en `"reels"`:
  `{"cuando": "<primera frase>", "duracion": <fin - inicio>, "titulo": "reel1: <de qué va>"}`.

Luego `kit.py plan tabla <video>` y enseña la tabla tal cual (sale una
fila «Reel» por cada momento, con su tramo) junto a esta otra:
| # | De | A | Duración | Empieza con… | Por qué funciona solo |

Pregunta **una sola vez**: «¿Te valen estos reels y lo que sale en cada uno?». **Espera el OK.**
Si pide cambios, edita `plan.json` y vuelve a enseñar las tablas. Con el OK (y solo si el plan
no estaba ya aprobado): `kit.py plan aprobar <video>`.

Los reels usan su plantilla (`"plantilla_reels"` en `brand.json`, de serie `reels-dinamico`:
más ritmo, golpes de zoom y subtítulos cortos todo el rato). Para otra: añade
`--plantilla <nombre>` a `animar`. Si hay música en `marca/musica/`, entra sola con ducking.

Si pide más dinamismo («añade motion graphics, B-roll, pantallas completas, zoom in y zoom out,
transiciones limpias»), añade al plan beats `broll`, `pantalla` y `zoom` dentro del tramo del
reel (`fases/animar.md`, «Pedirlo hablando»), enseña la tabla y, con el OK, vuelve a producir.

## 3 · Producir cada reel

Para cada uno (nombre `reel1`, `reel2`…), con los segundos del paso 1:

```
kit.py animar <video> --formato vertical --desde <inicio> --hasta <fin> --nombre reel1
kit.py componer <video> --formato vertical --desde <inicio> --hasta <fin> --nombre reel1
kit.py verificar <video> --formato vertical --nombre reel1
```

Mira la `hoja.jpg` de cada uno (`trabajo/<video>/capturas/reel1-vertical/`) antes de darlo por
bueno, con la misma lista de `fases/verificar.md`.

## 4 · Entregar

En español de España: lista de rutas con la duración de cada reel, cuánto ha tardado la máquina
(`kit.py tiempos <video>`) y una frase de gancho para el texto de la
publicación (sacada de lo que se dice en el clip, sin inventar).
