// Coreografía de la capa (GSAP, una sola línea de tiempo en pausa, apta para HyperFrames).
// Los tiempos llegan ya calculados desde Python (window.CAPA): cada palabra clave entra en el
// segundo exacto en que se dice. Aquí solo se decide CÓMO se mueve cada cosa.
(function () {
  const C = window.CAPA;
  const tl = gsap.timeline({ paused: true });
  const $ = (id) => document.getElementById(id);
  const ENFOQUE = "expo.out";
  const est = C.estilo || "cristal";
  const energia = est === "energia";

  // --------------------------------------------------------------- piezas comunes
  function entradaVidrio(id, t, lado) {
    const giro = lado === "izquierda" ? 16 : lado === "derecha" ? -16 : 0;
    tl.fromTo("#" + id + "-v",
      { autoAlpha: 0, scale: 0.86, y: 26, rotationY: giro * 1.6, filter: "blur(22px)" },
      { autoAlpha: 1, scale: 1, y: 0, rotationY: giro * 0.35, filter: "blur(0px)", duration: 0.75, ease: ENFOQUE },
      t);
    if ($(id + "-halo")) {
      tl.fromTo("#" + id + "-halo", { autoAlpha: 0, scale: 0.7 }, { autoAlpha: 1, scale: 1, duration: 0.9, ease: "power2.out" }, t + 0.05);
    }
    if ($(id + "-br")) {
      tl.fromTo("#" + id + "-br", { xPercent: -130, autoAlpha: 1 }, { xPercent: 330, autoAlpha: 1, duration: 1.05, ease: "power2.inOut" }, t + 0.32);
    }
  }
  function flotar(id, t0, t1, lado) {
    // respiración muy leve mientras está en pantalla: nada se queda congelado
    const dur = Math.max(0.5, t1 - t0 - 1.2);
    const giro = lado === "izquierda" ? 16 : lado === "derecha" ? -16 : 0;
    tl.fromTo("#" + id + "-v", { rotationY: giro * 0.35, y: 0 },
      { rotationY: giro * 0.12, y: -6, duration: dur, ease: "sine.inOut", immediateRender: false }, t0 + 0.8);
  }
  function salidaVidrio(id, t1) {
    tl.to("#" + id + "-v", { autoAlpha: 0, scale: 0.95, y: -18, filter: "blur(14px)", duration: 0.38, ease: "power2.in" }, t1 - 0.4);
    if ($(id + "-halo")) tl.to("#" + id + "-halo", { autoAlpha: 0, duration: 0.3 }, t1 - 0.4);
  }
  function numero(el, t, hasta) {
    const obj = { v: 0 };
    tl.fromTo(obj, { v: 0 }, { v: hasta, duration: Math.min(0.9, 0.35 + hasta * 0.03), ease: "power3.out",
      onUpdate: () => { el.textContent = String(Math.round(obj.v)); } }, t);
  }
  function palabraClave(sel, t) {
    tl.fromTo(sel, { scale: 1.32, filter: "blur(6px)" }, { scale: 1, filter: "blur(0px)", duration: 0.55, ease: "back.out(2.2)" }, t);
    const sub = document.querySelector(sel + " .subraya path");
    if (sub) {
      tl.fromTo(sub, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut" }, t + 0.12);
    }
  }

  // --------------------------------------------------------------- tipos de pieza
  const TIPOS = {
    logo(b) {
      const id = b.id;
      tl.fromTo("#" + id + "-v", { autoAlpha: 0, scaleX: 0.2, filter: "blur(10px)" },
        { autoAlpha: 1, scaleX: 1, filter: "blur(0px)", duration: 0.7, ease: ENFOQUE, transformOrigin: b.origen }, b.t0 + b.abre);
      tl.fromTo("#" + id + " .marca .l", { autoAlpha: 0, x: -10, filter: "blur(6px)" },
        { autoAlpha: 1, x: 0, filter: "blur(0px)", duration: 0.5, stagger: 0.022, ease: ENFOQUE }, b.t0 + b.abre + 0.18);
      tl.fromTo("#" + id + "-br", { xPercent: -130, autoAlpha: 1 }, { xPercent: 330, autoAlpha: 1, duration: 1.1, ease: "power2.inOut" }, b.t0 + b.abre + 0.5);
      tl.to("#" + id + " .marca .l", { autoAlpha: 0, x: 8, duration: 0.25, stagger: { each: 0.01, from: "end" }, ease: "power2.in" }, b.t1 - 0.62);
      tl.to("#" + id + "-v", { autoAlpha: 0, scaleX: 0.3, duration: 0.4, ease: "power3.in", transformOrigin: b.origen }, b.t1 - 0.45);
    },
    rotulo(b) {
      const id = b.id;
      sombra(id, b.t0, b.t1);
      entradaVidrio(id, b.t0, "izquierda");
      tl.fromTo("#" + id + "-b", { scaleY: 0 }, { scaleY: 1, duration: 0.55, ease: ENFOQUE }, b.t0 + 0.2);
      tl.fromTo("#" + id + " .nombre .l", { autoAlpha: 0, y: 22, rotationX: -70, filter: "blur(8px)" },
        { autoAlpha: 1, y: 0, rotationX: 0, filter: "blur(0px)", duration: 0.6, stagger: 0.025, ease: ENFOQUE }, b.t0 + 0.22);
      tl.fromTo("#" + id + "-h", { autoAlpha: 0, scaleX: 1.35, transformOrigin: "0% 50%", filter: "blur(6px)" },
        { autoAlpha: 1, scaleX: 1, filter: "blur(0px)", duration: 0.8, ease: ENFOQUE }, b.t0 + 0.5);
      flotar(id, b.t0, b.t1, "izquierda");
      salidaVidrio(id, b.t1);
    },
    destacado(b) {
      const id = b.id;
      entradaVidrio(id, b.t0, b.lado);
      if ($(id + "-k")) {
        tl.fromTo("#" + id + "-k", { autoAlpha: 0, scaleX: 1.45, transformOrigin: "0% 50%", filter: "blur(5px)" },
          { autoAlpha: 1, scaleX: 1, filter: "blur(0px)", duration: 0.7, ease: ENFOQUE }, b.t0 + 0.12);
      }
      if ($(id + "-i")) {
        tl.fromTo("#" + id + "-i", { autoAlpha: 0, scale: 0.4, rotation: -25 }, { autoAlpha: 1, scale: 1, rotation: 0, duration: 0.6, ease: "back.out(2)" }, b.t0 + 0.28);
        const trazo = document.querySelector("#" + id + "-i path");
        if (trazo) tl.fromTo(trazo, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.45, ease: "power2.out" }, b.t0 + 0.42);
      }
      b.palabras.forEach((p, k) => {
        const sel = "#" + id + "-p" + k;
        tl.fromTo(sel, { autoAlpha: 0, y: 30, filter: "blur(10px)" },
          { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.5, ease: ENFOQUE }, p.t);
        if (p.num != null) numero(document.querySelector(sel + " .num"), p.t, p.num);
        if (p.clave) palabraClave(sel, p.t);
      });
      flotar(id, b.t0, b.t1, b.lado);
      salidaVidrio(id, b.t1);
    },
    lista(b) {
      const id = b.id;
      entradaVidrio(id, b.t0, b.lado);
      if ($(id + "-k")) {
        tl.fromTo("#" + id + "-k", { autoAlpha: 0, scaleX: 1.45, transformOrigin: "0% 50%" }, { autoAlpha: 1, scaleX: 1, duration: 0.6, ease: ENFOQUE }, b.t0 + 0.1);
      }
      b.items.forEach((it, k) => {
        const f = "#" + id + "-f" + k;
        tl.fromTo(f, { autoAlpha: 0, x: 30, filter: "blur(8px)" }, { autoAlpha: 1, x: 0, filter: "blur(0px)", duration: 0.5, ease: ENFOQUE }, it.t);
        tl.fromTo(f + " .check", { scale: 0.3 }, { scale: 1, duration: 0.5, ease: "back.out(2.4)" }, it.t + 0.08);
        const trazo = document.querySelector(f + " .check path");
        tl.fromTo(trazo, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.35, ease: "power2.out" }, it.t + 0.2);
      });
      flotar(id, b.t0, b.t1, b.lado);
      salidaVidrio(id, b.t1);
    },
    herramienta(b) {
      const id = b.id;
      entradaVidrio(id, b.t0, b.lado);
      tl.fromTo("#" + id + "-n", { autoAlpha: 0, x: 20, filter: "blur(8px)" }, { autoAlpha: 1, x: 0, filter: "blur(0px)", duration: 0.6, ease: ENFOQUE }, b.t0 + 0.35);
      tl.fromTo("#" + id + "-s", { autoAlpha: 0, scaleX: 1.4, transformOrigin: "0% 50%" }, { autoAlpha: 1, scaleX: 1, duration: 0.7, ease: ENFOQUE }, b.t0 + 0.5);
      flotar(id, b.t0, b.t1, b.lado);
      salidaVidrio(id, b.t1);
    },
    transicion(b) {
      tl.fromTo("#" + b.id + "-h", { xPercent: 0, autoAlpha: 0 }, { xPercent: 420, autoAlpha: 1, duration: 0.62, ease: "power2.inOut" }, b.t0);
      tl.to("#" + b.id + "-h", { autoAlpha: 0, duration: 0.2 }, b.t0 + 0.45);
    },
    // ============================================================ biblioteca «dia-editorial» (v4)
    tachado(b) {
      const id = b.id;
      sombra(id, b.t0, b.t1);
      if ($(id + "-k")) tl.fromTo("#" + id + "-k", { autoAlpha: 0, x: -12 }, { autoAlpha: 1, x: 0, duration: 0.5, ease: ENFOQUE }, b.t0);
      tl.fromTo("#" + id + "-v", { autoAlpha: 0, y: 24, filter: "blur(10px)" }, { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.6, ease: ENFOQUE }, b.t0 + 0.05);
      const tacha = document.querySelector("#" + id + " .tacha path");
      tl.fromTo(tacha, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.34, ease: "power2.inOut" }, b.tacha);
      tl.to("#" + id + "-v .txt", { opacity: 0.45, duration: 0.3 }, b.tacha + 0.2);
      // la frase nueva entra palabra a palabra, cada una en el segundo en que se dice
      (b.palabras || []).forEach((t, k) => {
        tl.fromTo("#" + id + "-n" + k + " .l", { autoAlpha: 0, y: 26, filter: "blur(8px)" },
          { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.45, stagger: 0.016, ease: ENFOQUE }, t);
      });
      tl.to("#" + id, { autoAlpha: 0, y: -12, filter: "blur(8px)", duration: 0.35, ease: "expo.in" }, b.t1 - 0.38);
    },
    logos(b) {
      sombra(b.id, b.t0, b.t1);
      b.items.forEach((it, k) => {
        const el = $(b.id + "-c" + k);
        if (el && el.tagName === "IMG") {
          // logos planos (plantilla sin 3D): misma entrada por enfoque, con algo de escala
          tl.fromTo(el, { autoAlpha: 0, scale: 0.86, y: 18, filter: "blur(10px)" },
            { autoAlpha: 1, scale: 1, y: 0, filter: "blur(0px)", duration: 0.6, ease: ENFOQUE }, it.t);
          tl.to(el, { autoAlpha: 0, scale: 0.94, filter: "blur(8px)", duration: 0.32, ease: "power2.in" }, b.t1 - 0.36);
        }
        tl.fromTo("#" + b.id + "-c" + k, { filter: "blur(6px)" }, { filter: "blur(0px)", duration: 0.7, ease: ENFOQUE }, it.t);
        tl.fromTo("#" + b.id + "-t" + k, { autoAlpha: 0, y: 14, filter: "blur(6px)" },
          { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.6, ease: ENFOQUE }, it.t + 0.25);
      });
      tl.to("#" + b.id + " .nombre-logo", { autoAlpha: 0, duration: 0.3 }, b.t1 - 0.4);
    },
    golpe3d(b) {
      sombra(b.id, b.t0, b.t1);
      tl.fromTo("#" + b.id + "-r .l", { autoAlpha: 0, y: 26, filter: "blur(8px)" },
        { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.6, stagger: 0.03, ease: ENFOQUE }, b.t0 + 0.35);
      tl.to("#" + b.id + "-r", { autoAlpha: 0, duration: 0.3 }, b.t1 - 0.35);
    },
    contador(b) {
      const id = b.id;
      sombra(id, b.t0, b.t1);
      if ($(id + "-k")) tl.fromTo("#" + id + "-k", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.4 }, b.t0);
      tl.fromTo("#" + id + "-n", { autoAlpha: 0, y: 20, filter: "blur(10px)" }, { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.5, ease: ENFOQUE }, b.t0);
      const el = $(id + "-n");
      const obj = { v: 0 };
      let fin = 0, esTiempo = b.formato === "tiempo";
      if (esTiempo) { const [m, s] = b.hasta.split(":").map(Number); fin = m * 60 + s; } else { fin = parseFloat(b.hasta); }
      const pinta = () => {
        const v = Math.round(obj.v);
        el.textContent = esTiempo ? String(Math.floor(v / 60)).padStart(2, "0") + ":" + String(v % 60).padStart(2, "0") : String(v);
      };
      pinta();
      tl.fromTo(obj, { v: 0 }, { v: fin, duration: Math.max(0.5, b.t_final - b.t0 - 0.1), ease: "power3.out", onUpdate: pinta }, b.t0 + 0.1);
      tl.fromTo("#" + id + "-u", { autoAlpha: 0, x: -10 }, { autoAlpha: 1, x: 0, duration: 0.5, ease: ENFOQUE }, b.t_final - 0.1);
      tl.to("#" + id, { autoAlpha: 0, filter: "blur(8px)", duration: 0.35, ease: "expo.in" }, b.t1 - 0.38);
    },
    fases(b) {
      const id = b.id;
      sombra(id, b.t0, b.t1);
      tl.fromTo("#" + id + "-l", { scaleX: 0, transformOrigin: "0% 50%" }, { scaleX: 1, duration: 0.7, ease: ENFOQUE }, b.t0);
      tl.fromTo("#" + id + " .fase", { autoAlpha: 0, y: 16 }, { autoAlpha: 0.55, y: 0, duration: 0.5, stagger: 0.06, ease: ENFOQUE }, b.t0 + 0.2);
      b.items.forEach((it, k) => {
        tl.to("#" + id + "-f" + k, { autoAlpha: 1, duration: 0.25 }, it.t);
        tl.fromTo("#" + id + "-f" + k + " .punto-f", { scale: 0.6 }, { scale: 1, backgroundColor: C.colores.principal, duration: 0.35, ease: "back.out(2.5)" }, it.t);
        tl.to("#" + id + "-c", { x: (b.x1 - b.x0) * (k + 0.5) / b.n, duration: 0.45, ease: "power3.inOut" }, it.t - 0.15);
      });
      tl.fromTo("#" + id + "-c", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.3 }, b.t0 + 0.2);
      tl.to("#" + id, { autoAlpha: 0, duration: 0.35 }, b.t1 - 0.38);
    },
    terminal(b) {
      const id = b.id;
      sombra(id, b.t0, b.t1);
      tl.fromTo("#" + id + "-w", { autoAlpha: 0, y: 30, scale: 0.96, filter: "blur(10px)" },
        { autoAlpha: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.6, ease: ENFOQUE }, b.t0);
      const cur = $(id + "-cur");
      b.lineas.forEach((ln, k) => {
        const el = $(id + "-l" + k);
        const txt = el.getAttribute("data-texto");
        const obj = { n: 0 };
        const vel = Math.min(0.9, 0.035 * txt.length);
        tl.fromTo(obj, { n: 0 }, { n: txt.length, duration: vel, ease: "none",
          onUpdate: () => { el.textContent = txt.slice(0, Math.round(obj.n)); } }, ln.t);
      });
      const proxy = { u: 0 };
      tl.fromTo(proxy, { u: 0 }, { u: 1, duration: b.t1 - b.t0, ease: "none",
        onUpdate: () => { cur.style.opacity = Math.floor(proxy.u * (b.t1 - b.t0) * 2.4) % 2 ? "0" : "1"; } }, b.t0);
      tl.to("#" + id + "-w", { autoAlpha: 0, y: -16, filter: "blur(8px)", duration: 0.35, ease: "expo.in" }, b.t1 - 0.38);
    },
    barrido(b) {
      const id = b.id;
      const W = C.W;
      tl.fromTo("#" + id + "-g", { x: -40 }, { x: W * 0.62, duration: b.corte - b.t0, ease: "power2.inOut" }, b.t0);
      tl.to("#" + id + "-g", { x: W * 0.38, duration: Math.max(0.4, b.t1 - b.corte - 0.4), ease: "power2.inOut" }, b.corte);
      tl.fromTo("#" + id + "-a", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.4 }, b.t0 + 0.2);
      tl.fromTo("#" + id + "-d", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.4 }, b.t0 + 0.3);
      tl.to("#" + id, { autoAlpha: 0, duration: 0.3 }, b.t1 - 0.3);
    },
    cine(b) {
      tl.fromTo("#" + b.id + "-a", { yPercent: -100 }, { yPercent: 0, duration: 0.7, ease: "power3.out" }, b.t0);
      tl.fromTo("#" + b.id + "-b", { yPercent: 100 }, { yPercent: 0, duration: 0.7, ease: "power3.out" }, b.t0);
      tl.to("#" + b.id + "-a", { yPercent: -100, duration: 0.5, ease: "expo.in" }, b.t1 - 0.5);
      tl.to("#" + b.id + "-b", { yPercent: 100, duration: 0.5, ease: "expo.in" }, b.t1 - 0.5);
    },
    capitulo(b) {
      const id = b.id;
      sombra(id, b.t0, b.t1);
      tl.fromTo("#" + id + "-n", { autoAlpha: 0, x: -20 }, { autoAlpha: 1, x: 0, duration: 0.5, ease: ENFOQUE }, b.t0);
      tl.fromTo("#" + id + "-s", { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: ENFOQUE }, b.t0 + 0.15);
      tl.fromTo("#" + id + "-t .l", { autoAlpha: 0, y: 20, filter: "blur(8px)" }, { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.55, stagger: 0.03, ease: ENFOQUE }, b.t0 + 0.25);
      tl.to("#" + id, { autoAlpha: 0, filter: "blur(8px)", duration: 0.35, ease: "expo.in" }, b.t1 - 0.38);
    },
    etiqueta(b) {
      // texto pequeño de apoyo: el punto se enciende, el antetítulo entra de lado, la frase sube letra
      // a letra, cada tick se dibuja al decirlo y la línea se traza; sale desenfocándose hacia arriba
      const id = b.id, s = b.lado === "derecha" ? -1 : 1;
      // en una lista, el velo llega con el primer punto: antes solo está el antetítulo
      sombra(id, b.items && b.items.length ? b.items[0].t - 0.25 : b.t0, b.t1);
      if ($(id + "-k")) {
        tl.fromTo("#" + id + " .etq-punto", { scale: 0 }, { scale: 1, duration: 0.4, ease: "back.out(3)" }, b.t0);
        tl.fromTo("#" + id + "-k", { autoAlpha: 0, x: -24 * s, filter: "blur(6px)" },
          { autoAlpha: 1, x: 0, filter: "blur(0px)", duration: 0.5, ease: ENFOQUE }, b.t0 + 0.05);
      }
      if ($(id + "-t")) {
        tl.fromTo("#" + id + "-t .l", { autoAlpha: 0, y: 26, filter: "blur(8px)" },
          { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.5, stagger: 0.018, ease: ENFOQUE }, b.t0 + 0.14);
      }
      (b.items || []).forEach((it, k) => {
        const f = "#" + id + "-f" + k;
        tl.fromTo(f, { autoAlpha: 0, x: -22 * s, filter: "blur(6px)" },
          { autoAlpha: 1, x: 0, filter: "blur(0px)", duration: 0.45, ease: ENFOQUE }, it.t);
        tl.fromTo(f + " .etq-check path", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.35, ease: "power2.out" }, it.t + 0.1);
      });
      if ($(id + "-l")) tl.fromTo("#" + id + "-l", { scaleX: 0 }, { scaleX: 1, duration: 0.6, ease: ENFOQUE }, b.t0 + 0.3);
      const fuera = ["-k", "-t", "-fs", "-l"].map((x) => $(id + x)).filter(Boolean);
      tl.to(fuera, { autoAlpha: 0, y: -10, filter: "blur(8px)", duration: 0.32, ease: "expo.in" }, b.t1 - 0.36);
    },
    pantalla(b) {
      const id = b.id;
      tl.fromTo("#" + id + "-f", { scale: 0 }, { scale: 1, duration: 0.36, ease: "expo.out" }, b.t0);
      if ($(id + "-k")) tl.fromTo("#" + id + "-k", { autoAlpha: 0, y: 14 }, { autoAlpha: 1, y: 0, duration: 0.4, ease: ENFOQUE }, b.t0 + 0.12);
      if ($(id + "-s")) {
        tl.fromTo("#" + id + "-s", { autoAlpha: 0, scale: 0.6, y: 40, rotation: -8, filter: "blur(14px)" },
          { autoAlpha: 1, scale: 1, y: 0, rotation: 0, filter: "blur(0px)", duration: 0.6, ease: "back.out(1.8)" }, b.t0 + 0.14);
        tl.fromTo("#" + id + "-s", { scale: 1 }, { scale: 1.04, duration: Math.max(0.4, b.t1 - b.t0 - 0.9), ease: "none", immediateRender: false }, b.t0 + 0.74);
      }
      tl.fromTo("#" + id + " .l1 .l", { autoAlpha: 0, y: 60, filter: "blur(12px)" },
        { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.5, stagger: 0.02, ease: ENFOQUE }, b.t0 + 0.24);
      tl.fromTo("#" + id + " .l2 .l", { autoAlpha: 0, y: 50, scale: 1.2, filter: "blur(12px)" },
        { autoAlpha: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.55, stagger: 0.03, ease: ENFOQUE }, b.t0 + 0.46);
      // sale limpio: el contenido se desenfoca y el círculo se cierra hacia el centro
      tl.to("#" + id + " .pant-svg, #" + id + " .pant-txt, #" + id + " .pant-kicker", { autoAlpha: 0, filter: "blur(10px)", duration: 0.16, ease: "power2.in" }, b.t1 - 0.26);
      tl.to("#" + id + "-f", { scale: 0, duration: 0.22, ease: "expo.in" }, b.t1 - 0.23);
    },
    luz(b) {
      tl.fromTo("#" + b.id + "-f", { autoAlpha: 0, x: -300, scale: 0.8 }, { autoAlpha: 1, x: 200, scale: 1.1, duration: (b.t1 - b.t0) * 0.5, ease: "power2.out" }, b.t0);
      tl.to("#" + b.id + "-f", { autoAlpha: 0, x: 500, duration: (b.t1 - b.t0) * 0.5, ease: "expo.in" }, b.t0 + (b.t1 - b.t0) * 0.5);
    },
  };
  function sombra(id, t0, t1) {
    if (!$(id + "-sh")) return;
    tl.fromTo("#" + id + "-sh", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.5 }, t0);
    tl.to("#" + id + "-sh", { autoAlpha: 0, duration: 0.4 }, t1 - 0.4);
  }
  (C.beats || []).forEach((b) => TIPOS[b.tipo] && TIPOS[b.tipo](b));

  // --------------------------------------------------------------- subtítulos
  (C.subs || []).forEach((g, gi) => {
    const lin = "#s" + gi + "l";
    tl.fromTo(lin, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.01 }, g.t0);
    g.w.forEach((w, k) => {
      const sel = "#s" + gi + "w" + k;
      tl.fromTo(sel, { autoAlpha: 0, y: 16, filter: "blur(7px)", scale: 0.92 },
        { autoAlpha: 1, y: 0, filter: "blur(0px)", scale: 1, duration: 0.2, ease: "power3.out" }, Math.max(g.t0, w.t - 0.05));
      const fin = k + 1 < g.w.length ? g.w[k + 1].t : g.t1;
      if (energia) {
        tl.fromTo(sel + " .caja", { opacity: 0, scaleX: 0.6 }, { opacity: 1, scaleX: 1, duration: 0.12, ease: "power3.out" }, w.t);
        tl.fromTo(sel, { color: C.colores.texto }, { color: C.colores.panel, duration: 0.05, immediateRender: false }, w.t);
        tl.to(sel + " .caja", { opacity: 0, duration: 0.08 }, Math.max(w.t + 0.1, fin - 0.02));
        tl.to(sel, { color: w.clave ? C.colores.principal : C.colores.texto, duration: 0.06 }, Math.max(w.t + 0.1, fin - 0.02));
      } else {
        // la palabra que se dice se ilumina; solo color: si crece, una palabra larga se pega a la de al lado
        tl.fromTo(sel, { color: w.clave ? C.colores.principal : C.colores.texto },
          { color: C.colores.principal, duration: 0.12, ease: "power2.out", immediateRender: false }, w.t);
        tl.to(sel, { color: w.clave ? C.colores.principal : C.colores.texto, duration: 0.22, ease: "power2.out" }, Math.max(w.t + 0.12, fin - 0.02));
      }
    });
    tl.to(lin, { autoAlpha: 0, y: -10, filter: "blur(6px)", duration: 0.14, ease: "expo.in" }, g.t1 - 0.14);
  });

  // la duración manda el atributo data-duration de la raíz
  tl.to({}, { duration: 0.001 }, Math.max(0, C.dur - 0.001));
  window.__timelines["capa"] = tl;
})();
