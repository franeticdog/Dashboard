// Piezas en 3D real (Three.js, licencia MIT) de la identidad «dia-editorial».
// Dos tipos: «marca» (logo real extruido desde su SVG oficial) y «golpe» (texto extruido, una vez
// por clip). Se dibujan SOLO a partir del tiempo de HyperFrames (hf-seek): nada de relojes.
import * as THREE from "three";
import { Font } from "three/addons/loaders/FontLoader.js";
import { TextGeometry } from "three/addons/geometries/TextGeometry.js";
import { SVGLoader } from "three/addons/loaders/SVGLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const PIEZAS = window.CAPA3D || [];
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const expoOut = (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * clamp(t)));
const suave = (a, b, t) => { const x = clamp((t - a) / (b - a)); return x * x * (3 - 2 * x); };

function renderer(canvas, w, h) {
  const r = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, preserveDrawingBuffer: true,
    premultipliedAlpha: true });
  r.setPixelRatio(1);
  r.setSize(w, h, false);
  r.setClearColor(0x000000, 0);
  r.outputColorSpace = THREE.SRGBColorSpace;
  r.toneMapping = THREE.NeutralToneMapping;
  r.toneMappingExposure = 1.0;
  return r;
}

function escena(r, acento) {
  const e = new THREE.Scene();
  const pm = new THREE.PMREMGenerator(r);
  e.environment = pm.fromScene(new RoomEnvironment(), 0.03).texture;
  e.environmentIntensity = 0.7;
  const clave = new THREE.DirectionalLight(0xfff4e8, 2.2);   // luz principal cálida
  clave.position.set(2, 3, 5);
  e.add(clave);
  const canto = new THREE.DirectionalLight(new THREE.Color(acento), 3.2);  // canto coral
  canto.position.set(-4, 1.5, -2.5);
  e.add(canto);
  const frio = new THREE.DirectionalLight(0x8fb4ff, 1.1);    // relleno frío desde abajo (plató azul)
  frio.position.set(0.5, -4, 2);
  e.add(frio);
  // barrido de luz: una luz blanca que cruza el logo una sola vez al entrar (0,3 s), como un
  // reflejo que pasa por el bisel. Apagada el resto del tiempo.
  const barrido = new THREE.PointLight(0xfff6ee, 0, 0, 2);
  barrido.position.set(-2.4, 0.7, 1.5);
  e.add(barrido);
  e.userData.barrido = barrido;
  return e;
}

function texturaDe(p) {
  // logos en PNG: la imagen real va en la cara del logo extruido (la silueta la saca Python)
  if (!p.textura) return null;
  const img = document.getElementById(p.textura);
  if (!img) return null;
  const tex = new THREE.Texture(img);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  if (img.complete) tex.needsUpdate = true;
  else img.addEventListener("load", () => { tex.needsUpdate = true; });
  return tex;
}

function marcaSVG(svg, p) {
  const datos = new SVGLoader().parse(svg);
  const grupo = new THREE.Group();
  const tex = texturaDe(p);
  const vb = (svg.match(/viewBox="([^"]+)"/) || [])[1];
  const [vx, vy, vw, vh] = vb ? vb.split(/[ ,]+/).map(Number) : [0, 0, 1, 1];
  const prof = p.profundidad || 16;
  for (const path of datos.paths) {
    const fill = path.userData?.style?.fill;
    if (!fill || fill === "none") continue;
    const color = new THREE.Color(p.color || (fill === "currentColor" ? "#F2EDE3" : fill));
    for (const s of SVGLoader.createShapes(path)) {
      const g = new THREE.ExtrudeGeometry(s, { depth: prof, bevelEnabled: true, bevelThickness: prof * 0.1,
        bevelSize: prof * 0.056, bevelSegments: 4, curveSegments: 24 });
      if (tex) {
        // UV de la cara = posición dentro del dibujo (así la imagen cae justo encima de su silueta)
        const pos = g.attributes.position, uv = g.attributes.uv;
        for (let i = 0; i < pos.count; i++) uv.setXY(i, (pos.getX(i) - vx) / vw, 1 - (pos.getY(i) - vy) / vh);
        uv.needsUpdate = true;
      }
      const cara = tex
        ? new THREE.MeshPhysicalMaterial({ color: 0xffffff, map: tex, metalness: 0.15, roughness: 0.38,
            clearcoat: 0.55, clearcoatRoughness: 0.2, transparent: true })
        : new THREE.MeshPhysicalMaterial({ color: p.gradiente ? new THREE.Color("#ffffff") : color,
            metalness: 0.6, roughness: 0.3, clearcoat: 0.6, clearcoatRoughness: 0.2, transparent: true,
            vertexColors: !!p.gradiente });
      const lado = new THREE.MeshPhysicalMaterial({ color: tex ? new THREE.Color(p.colorLado || "#555555")
        : color.clone().multiplyScalar(0.55), metalness: 0.6, roughness: 0.35, transparent: true });
      grupo.add(new THREE.Mesh(g, [cara, lado]));
    }
  }
  const caja = new THREE.Box3().setFromObject(grupo);
  const c = caja.getCenter(new THREE.Vector3());
  const lado = Math.max(caja.max.x - caja.min.x, caja.max.y - caja.min.y);
  if (p.gradiente) {
    // el degradado real de la marca, en diagonal, como color de cada vértice
    const a = new THREE.Color(p.gradiente[0]), b = new THREE.Color(p.gradiente[1]);
    grupo.children.forEach((m) => {
      const pos = m.geometry.attributes.position;
      const col = new Float32Array(pos.count * 3);
      for (let i = 0; i < pos.count; i++) {
        const u = clamp(((pos.getX(i) - caja.min.x) + (caja.max.y - pos.getY(i))) / (2 * lado));
        const k = new THREE.Color().lerpColors(a, b, u);
        col[i * 3] = k.r; col[i * 3 + 1] = k.g; col[i * 3 + 2] = k.b;
      }
      m.geometry.setAttribute("color", new THREE.BufferAttribute(col, 3));
    });
  }
  grupo.position.set(-c.x, -c.y, -c.z);
  const env = new THREE.Group();
  env.add(grupo);
  env.scale.set(2 / lado, -2 / lado, 2 / lado);
  return env;
}

function montar(p) {
  const canvas = document.getElementById(p.canvas);
  const r = renderer(canvas, p.w, p.h);
  const e = escena(r, p.acento || "#D97757");
  const cam = new THREE.PerspectiveCamera(26, p.w / p.h, 0.1, 200);
  const pivote = new THREE.Group();
  let obj;
  if (p.tipo === "marca") {
    obj = marcaSVG(p.svg, p);
  } else {
    const fuente = new Font(p.fuente);
    const g = new TextGeometry(p.texto, { font: fuente, size: 1, depth: 0.35 * 0.72, curveSegments: 14,
      bevelEnabled: true, bevelThickness: 0.02, bevelSize: 0.02, bevelSegments: 4 });
    g.computeBoundingBox();
    g.center();
    const ancho = g.boundingBox.max.x - g.boundingBox.min.x;
    const cara = new THREE.MeshPhysicalMaterial({ color: new THREE.Color("#F2EDE3"), metalness: 0.65, roughness: 0.28,
      clearcoat: 0.8, clearcoatRoughness: 0.12, transparent: true });
    const lado = new THREE.MeshPhysicalMaterial({ color: new THREE.Color(p.acento || "#D97757").multiplyScalar(0.7),
      metalness: 0.65, roughness: 0.3, transparent: true });
    obj = new THREE.Mesh(g, [cara, lado]);
    obj.scale.setScalar((3.4 / ancho) * (p.escala || 1));
  }
  pivote.add(obj);
  e.add(pivote);
  return { p, r, e, cam, pivote };
}

function opacidad(obj, op) {
  obj.traverse((o) => {
    if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { m.opacity = op; });
  });
}

function dibujar(s, t) {
  const p = s.p;
  const u = t - p.t0;
  const dur = p.t1 - p.t0;
  const e = expoOut(u / 0.7);
  const sal = suave(dur - 0.35, dur - 0.02, u);
  if (p.tipo === "marca") {
    // entra con giro Y de 14° a 0 y un leve acercamiento; quieto después (nada flota)
    s.pivote.rotation.set(0, (1 - e) * (14 * Math.PI / 180) + sal * 0.25, 0);
    s.pivote.scale.setScalar(0.9 + 0.1 * e - 0.08 * sal);
    s.pivote.position.set(0, -0.2 * (1 - e), 0);
    // barrido de luz de 0,3 s justo cuando el logo termina de girar (una sola pasada)
    const bz = s.e.userData.barrido;
    if (bz) {
      const k = p.barrido === false ? -1 : (u - 0.34) / 0.3;
      if (k >= 0 && k <= 1) {
        bz.position.set(-2.6 + 5.2 * k, 0.8 - 1.0 * k, 1.9);
        bz.intensity = 13 * Math.sin(Math.PI * k);
      } else {
        bz.intensity = 0;
      }
    }
  } else {
    s.pivote.scale.setScalar(1.25 - 0.25 * e - 0.1 * sal);
    s.pivote.rotation.set(0.08 * (1 - e), -0.12 * (1 - e) + 0.05 * sal, 0);
  }
  opacidad(s.pivote, clamp(u / 0.12) * (1 - sal));
  s.cam.position.set(0, 0, p.distancia || 7);
  s.cam.lookAt(0, 0, 0);
  s.r.render(s.e, s.cam);
}

const montadas = PIEZAS.map(montar);
function todo(t) {
  for (const s of montadas) {
    if (t >= s.p.t0 - 0.001 && t <= s.p.t1 + 0.001) dibujar(s, t);
  }
}
window.addEventListener("hf-seek", (ev) => todo(ev.detail.time));
todo(window.__hfThreeTime || 0);
