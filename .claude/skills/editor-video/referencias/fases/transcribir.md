> Las órdenes `kit.py …` se lanzan así, desde la carpeta del proyecto: `py "<carpeta de la skill>/motor/herramientas/kit.py" …` (ver SKILL.md). Donde pone `brand.json` y `marca/` son los de la marca en uso, compartidos por todos sus proyectos: `kit.py proyecto` dice dónde están.

# Transcribir

**Idioma:** responde siempre en español de España, también en los resúmenes y cuando algo falle (aunque el error salga en inglés).

```
kit.py transcribir <video>
```

- Motor: en Mac con chip Apple, `mlx-whisper` (usa la GPU, muy rápido). En Windows, Linux o Mac
  Intel, `faster-whisper` en el procesador (más lento: cuenta 1 minuto de proceso por cada 2-4
  de vídeo con el modelo turbo).
- Modelo: `"transcripcion.modelo"` en `brand.json`. `turbo` (el bueno, 1,6 GB la primera vez)
  o `small` (más ligero, se equivoca más con nombres propios).
- El `"glosario"` se le pasa a Whisper como pista: pon ahí marcas y nombres que se dicen mucho.
- **Alineador** (`alinear.py`, en español): Whisper pone el texto, pero sitúa cada palabra con 0,2-0,5 s
  de error. Después, un wav2vec2 CTC en local (onnxruntime, 355 MB en `modelos/` del entorno, Apache-2.0) encaja
  cada palabra en el audio al centésimo; sale la fase «alinear» y «N de N palabras encajadas». Es lo que
  hace que la palabra del subtítulo se ilumine justo cuando se dice. Si falla, se quedan los de Whisper.

## Qué genera (en `trabajo/<video>/`)

| Archivo | Para qué |
|---|---|
| `palabras.json` | Cada palabra con inicio, fin y seguridad (`p`). Lo usan los subtítulos |
| `transcripcion.txt` | Frases con su minuto y sus números de palabra, para leerla tú |
| `audio.wav` | El audio a 16 kHz que se ha transcrito |
| `origen.json` | Tamaño, fps, duración y orientación del vídeo original |

## Tu parte: revisar el texto

Lee `transcripcion.txt` entera. El script también lista las «palabras dudosas». Si una está mal
(«Cloud Code» en vez de «Claude Code»), añádela a `"correcciones"` de `brand.json` y relanza:
tarda segundos y se aplica también en los siguientes vídeos. Las correcciones pueden ser de
varias palabras a una («Cloud Markdown» → «CLAUDE.md»).

No corrijas el estilo de cómo habla la persona: solo errores de transcripción.
