"""Biblioteca de recursos del kit (versión 4, identidad «dia-editorial»).

Lenguaje propio de D-IA: cine editorial. Instrument Serif con la palabra clave en cursiva
coral, Archivo para lo estructural, JetBrains Mono para números y órdenes. Coral #D97757 sobre
crema #F2EDE3, grano fino y luz cálida. Sin cajas detrás de los textos.

| Recurso     | Para qué frase                                   | Qué se ve |
|-------------|--------------------------------------------------|-----------|
| palabra     | Una idea fuerte                                  | Frase editorial grande POR DETRÁS de la persona, a un lado: serif crema y la clave en cursiva coral subrayada |
| tachado     | Se corrige o se sustituye algo («antes X, ahora Y») | Una palabra se tacha con trazo coral y entra la correcta en cursiva |
| logos       | Se nombran herramientas                          | Logos reales en 3D, en fila editorial o uno protagonista, con su nombre en serif |
| golpe3d     | La cifra o la palabra del clip (una vez)          | Texto en 3D con luz de canto coral y su remate en serif |
| contador    | Se dice una cifra o un tiempo                     | Contador en mono que corre hasta la cifra, con su unidad en serif |
| fases       | Se enumeran pasos                                 | Cabezal que avanza por una línea con fases numeradas que se encienden al decirlas |
| terminal    | Se habla de una orden o de lo que hace Claude     | Terminal de Claude Code que se escribe sola |
| barrido     | Antes y después                                   | El plano se parte con un deslizador: a un lado «antes» apagado, al otro «ahora» |
| cine        | Momento solemne                                   | Bandas finas de cine y viñeta |
| capitulo    | Empieza un bloque                                 | Título de capítulo tipo créditos: «01 · Transcribe» |
| luz         | Cambio de bloque                                  | Destello cálido de película (0,5 s) |
| rotulo      | Presentación                                      | Nombre en serif, @ en mono y una línea coral |
| etiqueta    | Un apunte corto que acompaña a los subtítulos     | Texto pequeño a un lado: antetítulo en mono, frase corta (clave en cursiva) o lista con ticks |
| subtitulo   | Una frase que merece subtítulo sin gráfico        | Solo subtítulos en ese tramo |
| broll       | Se habla de algo que se puede enseñar             | Imagen o vídeo de recurso a pantalla completa (marca/broll/ o captura local de una web) |
| pantalla    | Un mensaje que merece toda la pantalla            | Pantalla completa con texto en serif y un SVG (icono, logo o dibujo) |
| zoom        | «Acércate cuando digo X»                          | Solo cámara: acercar, alejar o golpe de zoom |
"""
from __future__ import annotations

import re
from pathlib import Path

from comun import FORMATOS, MARCA, ruta_proyecto

ESCENAS: tuple = ()
# por defecto, qué recursos dejan pasar los subtítulos (los que no dicen nada con palabras)
SUBTITULO_DEFECTO = {"barrido": True, "cine": True, "luz": True, "rotulo": True, "subtitulo": True, "broll": True,
                     "etiqueta": True}


def lleva_subtitulo(b: dict, defecto: bool = False) -> bool:
    """Si el beat lleva subtítulo. En el rótulo, «subtitulo» es la línea del @, así que ahí manda
    «con_subtitulo» (no por defecto: el nombre ya está en pantalla)."""
    if b.get("tipo") == "rotulo":
        return bool(b.get("con_subtitulo", False))
    return bool(b.get("subtitulo", SUBTITULO_DEFECTO.get(b.get("tipo"), defecto)))
TERMINALES = {"de", "del", "que", "y", "o", "en", "para", "como", "con", "a", "al", "el", "la", "los",
              "las", "un", "una", "por", "su", "sus"}


def esc(t: str) -> str:
    import html
    return html.escape(t or "", quote=True)


def letras(t: str) -> str:
    return "".join(f'<span class="l">{esc(ch) if ch != " " else "&nbsp;"}</span>' for ch in t)


def palabras_html(t: str, bid: str, pref: str, desde: int = 0) -> str:
    return "".join(f'<span class="w" id="{bid}-{pref}{desde + k}">{esc(w)}</span> '
                   for k, w in enumerate(t.split()))


class Ctx:
    def __init__(self, formato, palabras, marca, estilo, zonas_fn, proyecto, duracion, video, acento, pl=None):
        self.formato = formato
        self.W, self.H = FORMATOS[formato]
        self.vert = formato == "vertical"
        self.palabras = palabras
        self.marca = marca
        self.e = estilo
        self.zonas = zonas_fn
        self.proyecto = proyecto
        self.duracion = duracion
        self.video = video
        self.acento = acento
        self.pl = pl or {}
        self.escala = float(self.pl.get("textos", {}).get("escala", 1.0))
        self.tres_d = bool(self.pl.get("tres_d", {}).get("logos", True))

    def cuando(self, frase, desde, defecto):
        if not frase:
            return defecto
        from plan import buscar_frase
        r = buscar_frase(self.palabras, frase, max(0.0, desde))
        return r[0] if r else defecto

    def cara(self, t0, t1):
        return self.zonas(t0, t1).get("cara")

    def lado_libre(self, t0, t1, preferido=None):
        """Lado con más sitio (horizontal) y su caja [x0, x1] libre."""
        c = self.cara(t0, t1)
        if not c:
            return (preferido or "derecha"), (self.W * 0.55, self.W - 96)
        izq, der = c[0] - 96, self.W - 96 - c[2]
        # El lado pedido por el usuario se respeta mientras quepa algo (300 px)
        lado = preferido if preferido in ("izquierda", "derecha") and (izq if preferido == "izquierda" else der) > 300 \
            else ("izquierda" if izq > der else "derecha")
        return lado, ((96, c[0] - 50) if lado == "izquierda" else (c[2] + 50, self.W - 96))

    def bajo_barbilla(self, t0, t1):
        c = self.cara(t0, t1)
        return min(max((c[3] + 70) if c else 1080, 900), 1180)


def construir(tipo, b, bid, t0, t1, ctx):
    fn = globals().get("r_" + tipo)
    return fn(b, bid, t0, t1, ctx) if fn else {}


def _clip(bid, t0, t1, clase, estilo="", pista=3):
    return (f'<div class="clip {clase}" id="{bid}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" '
            f'data-track-index="{pista}" style="{estilo}">')


def _sombra_lado(bid, lado, vert):
    """Sombra suave (no caja) que baja el plató detrás del texto lateral."""
    if vert:
        return f'<div class="sombra-lado abajo" id="{bid}-sh"></div>'
    return f'<div class="sombra-lado {lado}" id="{bid}-sh"></div>'


def _posicion_lateral(ctx, t0, t1, preferido, ancho_min=560):
    if ctx.vert:
        y = ctx.bajo_barbilla(t0, t1)
        return f"left:96px;right:96px;top:{y:.0f}px;text-align:center", "centro"
    lado, (x0, x1) = ctx.lado_libre(t0, t1, preferido)
    c = ctx.cara(t0, t1)
    yc = ((c[1] + c[3]) / 2) if c else ctx.H * 0.42
    ancho = max(ancho_min, x1 - x0)
    if lado == "izquierda":
        return f"left:{x0:.0f}px;width:{ancho:.0f}px;top:{yc - 150:.0f}px", lado
    return f"left:{x0:.0f}px;width:{ancho:.0f}px;top:{yc - 150:.0f}px", lado


def _tiempos(ctx, items, t0, clave="cuando", paso=0.35):
    out, prev = [], t0
    for k, it in enumerate(items):
        frase = it.get(clave) if isinstance(it, dict) else None
        t = ctx.cuando(frase, prev - 0.2, prev + paso if k else t0 + 0.1)
        t = max(t - 0.05, prev + 0.12 if k else t0)
        out.append(round(t, 3))
        prev = t
    return out


# ------------------------------------------------------------------ tachado
def _tiempos_frase(ctx, texto, desde, hasta, primero):
    """Segundo en que se dice cada palabra de «texto», en orden y dentro de [desde, hasta). La que no
    se dice tal cual entra 0,2 s después de la anterior."""
    from plan import norm
    dichas = [w for w in ctx.palabras if desde <= w["s"] < hasta]
    out, j = [], 0
    for tok in texto.split():
        n, t = norm(tok).strip(), None
        for k in range(j, len(dichas)):
            if n and norm(dichas[k]["w"]).strip() == n:
                t, j = dichas[k]["s"], k + 1
                break
        out.append(t if t is not None else (out[-1] + 0.2 if out else primero))
    return out


def r_tachado(b, bid, t0, t1, ctx):
    pos, lado = _posicion_lateral(ctx, t0, t1, b.get("posicion"))
    escala = float(b.get("escala", 1.0))
    tam = int((186 if not ctx.vert else 150) * ctx.escala * escala)
    pequeno = escala < 0.8 and not ctx.vert
    if pequeno:  # tachado pequeño: a la altura del pecho, con la letra y el margen de las etiquetas
        c = ctx.cara(t0, t1)
        y = min((c[3] + 110) if c else ctx.H * 0.45, ctx.H - 470)
        pos = f"{'left' if lado == 'izquierda' else 'right'}:120px;top:{y:.0f}px"
    t_tacha = ctx.cuando(b.get("cuando_tacha"), t0, t0 + 0.9)
    t_tacha = max(t_tacha, t0 + 0.55)
    t_nueva = ctx.cuando(b.get("cuando_nueva"), t_tacha, t_tacha + 0.35)
    t_nueva = max(t_nueva - 0.05, t_tacha + 0.3)
    # la frase nueva entra palabra a palabra, cada una cuando se dice (0,06 s antes: lo que tarda en enfocarse)
    nueva = (b.get("nueva") or "").split()
    entradas = []
    for k, t in enumerate(_tiempos_frase(ctx, " ".join(nueva), t_nueva - 0.1, t1, t_nueva + 0.05)):
        t = max(t - 0.06, entradas[-1] + 0.12 if entradas else t_nueva)
        entradas.append(round(min(t, t1 - 0.6), 3))
    # en el pequeño, como en las etiquetas: la última palabra es la clave, en cursiva de acento
    pals = " ".join(f'<span class="nw{" clave" if pequeno and k == len(nueva) - 1 else ""}" id="{bid}-n{k}">'
                    f'{letras(w)}</span>' for k, w in enumerate(nueva))
    kicker = f'<div class="kicker-ed" id="{bid}-k">{esc(b["etiqueta"])}</div>' if b.get("etiqueta") else ""
    sombra = f'<div class="velo" id="{bid}-sh"></div>' if pequeno else _sombra_lado(bid, lado, ctx.vert)
    html = (_clip(bid, t0, t1, "r r-tachado" + (f" peq {lado}" if pequeno else ""), pos + f";--t-ed:{tam}px")
            + sombra + kicker +
            f'<div class="vieja" id="{bid}-v"><span class="txt">{esc(b.get("texto", ""))}</span>'
            f'<svg class="tacha" viewBox="0 0 100 10" preserveAspectRatio="none"><path pathLength="1" '
            f'd="M1 6 C 30 3, 60 8, 99 4"/></svg></div>'
            f'<div class="nueva" id="{bid}-n">{pals}</div></div>')
    return {"html": html, "js": {"tipo": "tachado", "id": bid, "t0": t0, "t1": t1, "tacha": round(t_tacha, 3),
                                 "nueva": round(t_nueva, 3), "palabras": entradas},
            "sonidos": [{"t": t0, "sonido": "aire", "db": -8}, {"t": t_tacha, "sonido": "whoosh", "dur": 0.35, "db": -6},
                        {"t": (entradas[0] if entradas else t_nueva) + 0.05, "sonido": "sub", "db": -8}]}


# ------------------------------------------------------------------ logos (3D)
# acabado por defecto de los logos que viajan en marca/logos (el beat puede cambiarlo con color/gradiente)
LOGO_DEFECTO = {"hyperframes": {"gradiente": ["#49DB6C", "#08E4F4"]}}


def _clave_logo(it: dict) -> str:
    return re.sub(r"[^a-z0-9-]", "", str(it.get("logo", "")).lower().replace(" ", "-"))


def r_logos(b, bid, t0, t1, ctx):
    from animar import logo_svg
    items = [it if isinstance(it, dict) else {"logo": it} for it in (b.get("items") or [])]
    n = max(1, len(items))
    vert = ctx.vert
    protagonista = n == 1
    C = (540 if protagonista else 320) if not vert else (460 if protagonista else 300)
    tiempos = _tiempos(ctx, items, t0, paso=0.3)
    if vert:
        y = ctx.bajo_barbilla(t0, t1) - 40
        total = n * C * 0.8
        x0 = (ctx.W - total) / 2
        centros = [(x0 + C * 0.4 + k * C * 0.8, y + C * 0.35) for k in range(n)]
        lado = "centro"
    else:
        lado, (xa, xb) = ctx.lado_libre(t0, t1, b.get("posicion"))
        c = ctx.cara(t0, t1)
        yc = ((c[1] + c[3]) / 2 - 20) if c else ctx.H * 0.4
        paso = min(C * 0.82, (xb - xa) / n)
        x_ini = xa + paso / 2 if lado == "derecha" else xb - paso * (n - 0.5)
        centros = [(x_ini + k * paso, yc) for k in range(n)]
    from animar import logo_png
    import base64
    partes, piezas = [], []
    for k, it in enumerate(items):
        cx, cy = centros[k]
        # un SVG de marca/logos manda; si solo hay PNG, se extruye su silueta con la imagen en la cara
        png = None if (MARCA / "logos" / f"{_clave_logo(it)}.svg").exists() \
            else logo_png(it.get("logo", ""))
        svg = png["svg"] if png else logo_svg(it.get("logo", ""))
        nombre = esc(it.get("nombre") or "")
        rotulo = (f'<div class="nombre-logo" id="{bid}-t{k}" style="left:{cx - 260:.0f}px;top:{cy + C * 0.36:.0f}px">'
                  f'{nombre}{(" <i>" + esc(it["clave"]) + "</i>") if it.get("clave") else ""}</div>')
        if not ctx.tres_d and svg:
            # plantilla con logos planos: la misma entrada, sin 3D
            src = png["textura"] if png else "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
            lado_img = C * 0.56
            partes.append(f'<img class="logo-plano" id="{bid}-c{k}" src="{src}" alt="" style="position:absolute;'
                          f'left:{cx - lado_img / 2:.0f}px;top:{cy - lado_img / 2:.0f}px;width:{lado_img:.0f}px;'
                          f'height:{lado_img:.0f}px;object-fit:contain">' + rotulo)
            continue
        partes.append(f'<canvas id="{bid}-c{k}" width="{C}" height="{C}" style="position:absolute;'
                      f'left:{cx - C / 2:.0f}px;top:{cy - C / 2:.0f}px;width:{C}px;height:{C}px"></canvas>' + rotulo)
        if png:
            partes.append(f'<img id="{bid}-tex{k}" src="{png["textura"]}" alt="" style="display:none">')
        if svg:
            pieza = {"tipo": "marca", "canvas": f"{bid}-c{k}", "w": C, "h": C, "t0": tiempos[k], "t1": t1,
                     "svg": svg, "acento": ctx.acento, "distancia": 6.2 if protagonista else 6.6,
                     "color": it.get("color") or LOGO_DEFECTO.get(_clave_logo(it), {}).get("color"),
                     "gradiente": it.get("gradiente") or LOGO_DEFECTO.get(_clave_logo(it), {}).get("gradiente"),
                     "barrido": bool(ctx.pl.get("tres_d", {}).get("barrido_luz", True))}
            if png:
                pieza.update({"textura": f"{bid}-tex{k}", "colorLado": png["colorLado"],
                              "profundidad": png["profundidad"], "gradiente": None, "color": None})
            piezas.append(pieza)
    html = (_clip(bid, t0, t1, "r r-logos", f"inset:0") + _sombra_lado(bid, lado if not vert else "abajo", vert)
            + "".join(partes) + "</div>")
    son = [{"t": t, "sonido": "aire" if k % 2 == 0 else "tic", "db": -6 if k % 2 == 0 else -2}
           for k, t in enumerate(tiempos)]
    son.append({"t": tiempos[0] + 0.5, "sonido": "sub", "db": -8})
    return {"html": html, "js": {"tipo": "logos", "id": bid, "t0": t0, "t1": t1, "items": [{"t": t} for t in tiempos]},
            "sonidos": son, "piezas3d": piezas}


# ------------------------------------------------------------------ golpe 3D
def r_golpe3d(b, bid, t0, t1, ctx):
    vert = ctx.vert
    pos, lado = _posicion_lateral(ctx, t0, t1, b.get("posicion"))
    Cw, Ch = (720, 420) if not vert else (900, 380)
    if vert:
        y = ctx.bajo_barbilla(t0, t1) - 60
        caja = f"left:{(ctx.W - Cw) / 2:.0f}px;top:{y:.0f}px"
    else:
        lado, (xa, xb) = ctx.lado_libre(t0, t1, b.get("posicion"))
        c = ctx.cara(t0, t1)
        yc = ((c[1] + c[3]) / 2) if c else ctx.H * 0.42
        x = xa if lado == "derecha" else xb - Cw
        caja = f"left:{x:.0f}px;top:{yc - Ch * 0.62:.0f}px"
    remate = esc(b.get("remate") or "")
    html = (_clip(bid, t0, t1, "r r-golpe", caja + f";width:{Cw}px;height:{Ch + 160}px")
            + _sombra_lado(bid, lado if not vert else "abajo", vert)
            + f'<canvas id="{bid}-c" width="{Cw}" height="{Ch}" style="position:absolute;left:0;top:0;width:{Cw}px;height:{Ch}px"></canvas>'
            + f'<div class="remate" id="{bid}-r">{letras(b.get("remate") or "")}</div></div>')
    pieza = {"tipo": "golpe", "canvas": f"{bid}-c", "w": Cw, "h": Ch, "t0": t0, "t1": t1,
             "texto": b.get("texto", ""), "acento": ctx.acento, "escala": 0.82 if vert else 1.0}
    return {"html": html, "js": {"tipo": "golpe3d", "id": bid, "t0": t0, "t1": t1},
            "sonidos": [{"t": t0 - 0.05, "sonido": "whoosh", "dur": 0.5, "db": -3}, {"t": t0 + 0.28, "sonido": "sub", "db": 0}],
            "piezas3d": [pieza], "necesita_fuente": b.get("texto", "")}


# ------------------------------------------------------------------ contador
def r_contador(b, bid, t0, t1, ctx):
    pos, lado = _posicion_lateral(ctx, t0, t1, b.get("posicion"))
    hasta = str(b.get("hasta", "10"))
    formato = b.get("formato") or ("tiempo" if ":" in hasta else "numero")
    t_final = ctx.cuando(b.get("cuando_cifra"), t0, t0 + 0.9)
    tam = int((190 if not ctx.vert else 170) * ctx.escala)
    html = (_clip(bid, t0, t1, "r r-contador", pos + f";--t-num:{tam}px") + _sombra_lado(bid, lado, ctx.vert)
            + (f'<div class="kicker-ed" id="{bid}-k">{esc(b["etiqueta"])}</div>' if b.get("etiqueta") else "")
            + f'<div class="num" id="{bid}-n">0</div><div class="unidad" id="{bid}-u">{esc(b.get("unidad", ""))}</div></div>')
    return {"html": html, "js": {"tipo": "contador", "id": bid, "t0": t0, "t1": t1, "hasta": hasta, "formato": formato,
                                 "t_final": round(max(t_final, t0 + 0.6), 3)},
            "sonidos": [{"t": t0, "sonido": "aire", "db": -8}, {"t": max(t_final, t0 + 0.6), "sonido": "tic", "db": 2}]}


# ------------------------------------------------------------------ fases
def r_fases(b, bid, t0, t1, ctx):
    vert = ctx.vert
    items = [it if isinstance(it, dict) else {"texto": it} for it in (b.get("items") or [])]
    tiempos = _tiempos(ctx, items, t0 + 0.3, paso=0.5)
    n = max(1, len(items))
    y = (ctx.H - 330) if not vert else ctx.bajo_barbilla(t0, t1) + 40
    x0, x1 = (140, ctx.W - 140) if not vert else (96, ctx.W - 96)
    ancho_f = min(520, (x1 - x0) / n - 16)
    partes = [f'<div class="linea-f" id="{bid}-l" style="left:{x0}px;width:{x1 - x0}px;top:{y}px"></div>']
    for k, it in enumerate(items):
        x = x0 + (x1 - x0) * (k + 0.5) / n
        partes.append(f'<div class="fase" id="{bid}-f{k}" style="left:{x - ancho_f / 2:.0f}px;width:{ancho_f:.0f}px;top:{y - 12}px">'
                      f'<div class="punto-f"></div><div class="num-f">{k + 1:02d}</div>'
                      f'<div class="txt-f">{esc(it.get("texto", ""))}</div></div>')
    partes.append(f'<div class="cabezal-f" id="{bid}-c" style="left:{x0}px;top:{y - 40}px"></div>')
    html = (_clip(bid, t0, t1, "r r-fases", "inset:0") + f'<div class="sombra-lado abajo ancha" id="{bid}-sh"></div>'
            + "".join(partes) + "</div>")
    son = [{"t": t, "sonido": "tic", "db": 0} for t in tiempos] + [{"t": t0, "sonido": "aire", "db": -8}]
    return {"html": html, "js": {"tipo": "fases", "id": bid, "t0": t0, "t1": t1, "items": [{"t": t} for t in tiempos],
                                 "x0": x0, "x1": x1, "n": n},
            "sonidos": son}


# ------------------------------------------------------------------ terminal
def r_terminal(b, bid, t0, t1, ctx):
    ancho = 900 if not ctx.vert else ctx.W - 192
    if ctx.vert:
        pos = f"left:96px;width:{ancho}px;top:{ctx.bajo_barbilla(t0, t1):.0f}px"
        lado = "centro"
    else:
        lado, (xa, xb) = ctx.lado_libre(t0, t1, b.get("posicion"))
        c = ctx.cara(t0, t1)
        yc = ((c[1] + c[3]) / 2) if c else ctx.H * 0.42
        x = min(max(96, xa if lado == "derecha" else xb - ancho), ctx.W - 96 - ancho)
        # 900 px no caben al lado de la cara: va a la altura del pecho, lejos de la boca
        top = (c[3] + 30) if c else ctx.H * 0.55
        pos = f"left:{x:.0f}px;width:{ancho}px;top:{min(top, ctx.H - 330):.0f}px"
    lineas = b.get("lineas") or []
    tiempos = _tiempos(ctx, [l if isinstance(l, dict) else {"texto": l} for l in lineas], t0 + 0.35, paso=0.8)
    filas = []
    for k, l in enumerate(lineas):
        txt = l.get("texto") if isinstance(l, dict) else str(l)
        orden = txt.startswith("›") or txt.startswith(">")
        filas.append(f'<div class="fila-t{" orden" if orden else ""}" id="{bid}-l{k}" data-texto="{esc(txt)}"></div>')
    html = (_clip(bid, t0, t1, "r r-terminal", pos + f";--t-mono:{34 if not ctx.vert else 40}px")
            + _sombra_lado(bid, lado, ctx.vert)
            + f'<div class="ventana-t" id="{bid}-w"><div class="barra-t"><i></i><i></i><i></i>'
              f'<span>{esc(b.get("titulo") or "claude")}</span></div>'
            + "".join(filas) + f'<span class="cursor-t" id="{bid}-cur"></span></div></div>')
    return {"html": html, "js": {"tipo": "terminal", "id": bid, "t0": t0, "t1": t1, "lineas": [{"t": t} for t in tiempos]},
            "sonidos": [{"t": t0, "sonido": "aire", "db": -8}] + [{"t": t, "sonido": "tic", "db": -4} for t in tiempos]}


# ------------------------------------------------------------------ barrido antes / ahora
def r_barrido(b, bid, t0, t1, ctx):
    t_corte = ctx.cuando(b.get("cuando_ahora"), t0, t0 + (t1 - t0) * 0.45)
    html = (_clip(bid, t0, t1, "r r-barrido", "inset:0", 4)
            + f'<div class="guia-b" id="{bid}-g"><span class="asa-b"></span></div>'
            + f'<div class="etq-b izq" id="{bid}-a">{esc(b.get("antes") or "antes")}</div>'
            + f'<div class="etq-b der" id="{bid}-d">{esc(b.get("despues") or "ahora")}</div></div>')
    return {"html": html, "js": {"tipo": "barrido", "id": bid, "t0": t0, "t1": t1, "corte": round(t_corte, 3)},
            "sonidos": [{"t": t0, "sonido": "whoosh", "dur": 0.6, "db": -6}, {"t": t_corte, "sonido": "whoosh", "dur": 0.5, "db": -4}],
            "barrido": {"t0": t0, "t1": t1, "corte": round(t_corte, 3)}}


# ------------------------------------------------------------------ cine
def r_cine(b, bid, t0, t1, ctx):
    alto = 70 if not ctx.vert else 120
    html = (_clip(bid, t0, t1, "r", "inset:0", 6)
            + f'<div class="banda arriba" id="{bid}-a" style="height:{alto}px"></div>'
            + f'<div class="banda abajo" id="{bid}-b" style="height:{alto}px"></div></div>')
    return {"html": html, "js": {"tipo": "cine", "id": bid, "t0": t0, "t1": t1},
            "sonidos": [{"t": t0, "sonido": "subida", "db": -10}], "vineta": (t0, t1)}


# ------------------------------------------------------------------ capitulo
def r_capitulo(b, bid, t0, t1, ctx):
    y = (ctx.H * 0.70) if not ctx.vert else ctx.bajo_barbilla(t0, t1) + 60
    html = (_clip(bid, t0, t1, "r r-capitulo", f"left:0;right:0;top:{y:.0f}px")
            + f'<div class="sombra-lado abajo ancha" id="{bid}-sh"></div>'
            + f'<span class="num-c" id="{bid}-n">{esc(b.get("numero", "01"))}</span>'
            + f'<span class="sep-c" id="{bid}-s"></span>'
            + f'<span class="txt-c" id="{bid}-t">{letras(b.get("texto", ""))}</span></div>')
    return {"html": html, "js": {"tipo": "capitulo", "id": bid, "t0": t0, "t1": t1},
            "sonidos": [{"t": t0, "sonido": "aire", "db": -6}, {"t": t0 + 0.3, "sonido": "sub", "db": -10}]}


# ------------------------------------------------------------------ etiqueta (texto pequeño)
def r_etiqueta(b, bid, t0, t1, ctx):
    """Texto pequeño de apoyo, sin caja: antetítulo en mono con su punto de acento, una frase corta
    (la clave en cursiva de acento) y una línea fina. Con «items», una lista corta con ticks que se
    encienden al decirlos. A un lado, a la altura del pecho: lejos de la boca y de los subtítulos."""
    from animar import ICONOS
    items = [it if isinstance(it, dict) else {"texto": it} for it in (b.get("items") or [])]
    if ctx.vert:
        lado = "centro"
        pos = f"left:96px;right:96px;top:{ctx.bajo_barbilla(t0, t1):.0f}px"
    else:
        lado, _ = ctx.lado_libre(t0, t1, b.get("posicion"))
        c = ctx.cara(t0, t1)
        alto = 130 + 66 * len(items)
        y = min((c[3] + (60 if items else 130)) if c else ctx.H * 0.42, ctx.H - 300 - alto)
        pos = f"{'left' if lado == 'izquierda' else 'right'}:120px;top:{y:.0f}px"
    kicker = (f'<div class="etq-k" id="{bid}-k"><span class="etq-punto"></span>{esc(b["kicker"])}</div>'
              if b.get("kicker") else "")
    l1, l2 = (b.get("texto") or "").strip(), (b.get("clave") or "").strip()
    frase = ((f'<span class="etq-t1">{letras(l1)}</span>' if l1 else "")
             + ('<span class="l">&nbsp;</span>' if l1 and l2 else "")
             + (f'<span class="etq-t2">{letras(l2)}</span>' if l2 else ""))
    filas = "".join(f'<div class="etq-fila" id="{bid}-f{k}"><svg class="etq-check" viewBox="0 0 24 24">'
                    f'<path pathLength="1" d="{ICONOS["check"]}"/></svg><span>{esc(it.get("texto", ""))}</span></div>'
                    for k, it in enumerate(items))
    tiempos = _tiempos(ctx, items, t0 + 0.35, paso=0.5) if items else []
    html = (_clip(bid, t0, t1, f"r r-etiqueta {lado}", pos)
            + f'<div class="velo" id="{bid}-sh"></div>' + kicker
            + (f'<div class="etq-txt" id="{bid}-t">{frase}</div>' if frase else "")
            + (f'<div class="etq-filas" id="{bid}-fs">{filas}</div>' if filas else "")
            # en una lista la línea no va: quedaría flotando bajo los puntos que aún no han salido
            + ("" if filas else f'<div class="etq-linea" id="{bid}-l"></div>') + "</div>")
    son = [{"t": t0, "sonido": "aire", "db": -10}] + [{"t": t + 0.05, "sonido": "tic", "db": -4} for t in tiempos]
    return {"html": html, "js": {"tipo": "etiqueta", "id": bid, "t0": t0, "t1": t1, "lado": lado,
                                 "items": [{"t": t} for t in tiempos]},
            "sonidos": son}


# ------------------------------------------------------------------ luz cálida
def r_luz(b, bid, t0, t1, ctx):
    t1 = min(t1, t0 + 0.5)
    html = (_clip(bid, t0, t1, "r r-luz", "inset:0", 7) + f'<div class="fuga" id="{bid}-f"></div></div>')
    return {"html": html, "js": {"tipo": "luz", "id": bid, "t0": t0, "t1": t1},
            "sonidos": [{"t": t0 - 0.05, "sonido": "whoosh", "dur": 0.5, "db": -6}]}


# ------------------------------------------------------------------ subtitulo (solo marca el tramo)
def r_subtitulo(b, bid, t0, t1, ctx):
    return {"sonidos": []}


# ------------------------------------------------------------------ zoom (solo cámara)
def r_zoom(b, bid, t0, t1, ctx):
    """«Acércate cuando digo X»: no pinta nada; el movimiento lo hace componer (ver camara_de)."""
    son = [{"t": t0 + 0.08, "sonido": "sub", "db": -10}] if b.get("modo") == "golpe" else []
    return {"sonidos": son}


# ------------------------------------------------------------------ B-roll
def r_broll(b, bid, t0, t1, ctx):
    """Imagen o vídeo de recurso a pantalla completa mientras sigues hablando. La imagen la mueve
    componer (ken burns suave) y entra y sale con un desenfoque corto y limpio."""
    import broll as B
    archivo, clase = B.resolver(b)
    if not archivo:
        return {}
    t0 = t0 + 0.12  # el beat empieza 0,12 s antes de la palabra: el B-roll entra con ella
    mov = b.get("movimiento") or ("acercar" if clase == "imagen" else "quieto")
    return {"broll": {"t0": round(t0, 3), "t1": round(t1, 3), "archivo": str(archivo), "clase": clase,
                      "movimiento": mov, "desde_s": float(b.get("desde_s", 0)), "ajuste": b.get("ajuste", "auto"),
                      "id": bid},
            "tapa": (round(t0, 3), round(t1, 3)),
            "sonidos": [{"t": t0 - 0.12, "sonido": "whoosh", "dur": 0.45, "db": -8}]}


# ------------------------------------------------------------------ pantalla completa
def _svg_de(b, ctx) -> str:
    import re as _re
    from animar import logo_svg
    raw = ""
    if str(b.get("svg", "")).lstrip().startswith("<svg"):
        raw = b["svg"]
    elif b.get("svg"):
        p = Path(str(b["svg"])).expanduser()
        for cand in (p, ruta_proyecto(p), MARCA / p.name, MARCA / "logos" / p.name):
            if cand.exists() and cand.suffix.lower() == ".svg":
                raw = cand.read_text(encoding="utf-8")
                break
    elif b.get("icono") or b.get("logo"):
        raw = logo_svg(b.get("icono") or b.get("logo")) or ""
    raw = _re.sub(r"<script.*?</script>", "", raw, flags=_re.S | _re.I)
    raw = _re.sub(r"<\?xml[^>]*>", "", raw)
    return raw


def r_pantalla(b, bid, t0, t1, ctx):
    """Pantalla completa de marca: fondo del color de tu panel, un SVG (icono, logo o dibujo que
    escribe Claude) y la frase en serif con la clave en cursiva de acento. Entra con un círculo
    que se abre desde el centro y sale cerrándose (0,2 s)."""
    vert = ctx.vert
    svg = _svg_de(b, ctx)
    l1, l2 = (b.get("texto") or "").strip(), (b.get("clave") or "").strip()
    ancho = ctx.W - (192 if vert else 360)
    g1 = int(min(ancho / (max(4, len(l1)) * 0.46), (150 if vert else 150) * ctx.escala)) if l1 else 0
    g2 = int(min(ancho / (max(3, len(l2)) * 0.46), g1 * 1.25 if g1 else 170 * ctx.escala)) if l2 else 0
    lado_svg = (430 if vert else 330) if (l1 or l2) else (620 if vert else 520)
    y_svg = (640 if vert else 170) if (l1 or l2) else (ctx.H - lado_svg) / 2
    y_txt = (y_svg + lado_svg + (70 if vert else 50)) if svg else ctx.H * 0.36
    kick = (f'<div class="pant-kicker" id="{bid}-k" style="top:{(y_svg - 80) if svg else y_txt - 90:.0f}px">'
            f'{esc(b["kicker"])}</div>') if b.get("kicker") else ""
    html = (_clip(bid, t0, t1, "r r-pantalla", "inset:0", 4)
            + f'<div class="pant-fondo" id="{bid}-f"></div>'
            + kick
            + (f'<div class="pant-svg" id="{bid}-s" style="left:{(ctx.W - lado_svg) / 2:.0f}px;top:{y_svg:.0f}px;'
               f'width:{lado_svg}px;height:{lado_svg}px">{svg}</div>' if svg else "")
            + (f'<div class="pant-txt" id="{bid}-t" style="top:{y_txt:.0f}px;--p1:{g1}px;--p2:{g2}px">'
               + (f'<span class="l1">{letras(l1)}</span>' if l1 else "")
               + (f'<span class="l2">{letras(l2)}</span>' if l2 else "") + "</div>" if (l1 or l2) else "")
            + "</div>")
    return {"html": html, "js": {"tipo": "pantalla", "id": bid, "t0": t0, "t1": t1},
            "tapa": (round(t0, 3), round(t1, 3)),
            "sonidos": [{"t": t0 - 0.04, "sonido": "whoosh", "dur": 0.5, "db": -5},
                        {"t": t0 + 0.3, "sonido": "sub", "db": -6}]}
