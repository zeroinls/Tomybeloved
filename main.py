"""
Jardín de puntos: animación romántica de flores
------------------------------------------------
Ramos de tres peonías, tres tulipanes y tres liliums formados por miles de
puntos de colores que viajan, se juntan y florecen, rodeadas de
aguamarinas, citrinos, amatistas y zafiros, sobre un lago
con flores de loto flotando y una pareja de cisnes.

Requisitos:   pip install pygame
Ejecutar:     python main.py            (en tu computador)
En la web:    pip install pygbag
              pygbag carpeta_del_proyecto   ->  abre http://localhost:8000

Controles:
  ESPACIO / →   siguiente flor
  ←             flor anterior
  M             pausar / reanudar la música
  S             guardar captura (flor.png)
  ESC           salir
"""
import asyncio
import math
import random
import sys

import pygame

# ---------------------------------------------------------------------------
# Personaliza aquí
# ---------------------------------------------------------------------------
ANCHO, ALTO = 1000, 760
FPS = 60
EN_LA_WEB = sys.platform == "emscripten"     # True cuando corre en el navegador (pygbag)
N_PUNTOS = 9000 if EN_LA_WEB else 15000      # en el navegador Python es más lento: menos puntos
DETALLE = 3.0                # multiplica los puntos de cada pétalo, hoja y tallo
BRILLO = 0.25                # fracción de puntos que titilan como luces
SEGUNDOS_POR_FLOR = 10
DURACION_FLORECER = 4.5      # segundos que tarda un ramo en crecer y abrirse
MENSAJE = "Cada una de estas flores es para ti"
DEDICATORIA = ["Estas flores jamás se marchitarán.",      # texto de arriba, una línea por elemento
               "Al igual que mi amor por ti, florecen eternamente."]

FONDO = (8, 6, 22)

# ---------------------------------------------------------------------------
# MÚSICA DE FONDO: copia tu canción en la misma carpeta que main.py con
# alguno de estos nombres. Se usa el primero que encuentre.
#   - "cancion.ogg"  -> funciona en el computador y en el navegador (recomendado)
#   - "cancion.mp3"  -> funciona en el computador; en el navegador puede fallar
# ---------------------------------------------------------------------------
CANCIONES = ["cancion.ogg", "cancion.mp3"]
VOLUMEN = 0.6                # de 0.0 (silencio) a 1.0 (máximo)
LAGO_Y = ALTO - 145          # altura de la superficie del lago
VELOCIDAD_CISNES = 22        # píxeles por segundo
CADA_CUANTO_PAJAROS = (7, 14)  # segundos entre una bandada y la siguiente (mínimo, máximo)

FLORES = [
    ("Peonía", "un amor que florece en capas"),
    ("Tulipán", "la declaración de un amor perfecto"),
    ("Lilium", "devoción pura"),
]


# ---------------------------------------------------------------------------
# Utilidades de color
# ---------------------------------------------------------------------------
def mezclar(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def variar(c, cant=14):
    return tuple(max(0, min(255, v + random.uniform(-cant, cant))) for v in c)


def aclarar(c, t):
    return mezclar(c, (255, 255, 255), t)


# ---------------------------------------------------------------------------
# Primitivas de puntos: cada una agrega tuplas (x, y, color) a la lista
# ---------------------------------------------------------------------------
def ancho_perfil(u, perfil):
    """Ancho relativo del pétalo a lo largo de su eje (u: 0 base -> 1 punta)."""
    if perfil == "redondo":      # peonía: ancho y redondeado
        return math.sin(math.pi * u) ** 0.5
    if perfil == "copa":         # tulipán: se ensancha arriba y cierra redondo
        return math.sin(math.pi * u ** 0.65) ** 0.55
    if perfil == "punta":        # lilium, loto, hojas: termina en punta
        return math.sin(math.pi * u ** 0.8)
    return math.sin(math.pi * u)


def petalo(pts, cx, cy, ang, largo, ancho, n, c_base, c_punta,
           perfil="punta", curva=0.0, borde=0.3, manchas=0, color_manchas=(140, 15, 70)):
    """Pétalo que nace en (cx, cy) y apunta en el ángulo `ang` (0 = arriba)."""
    dx, dy = math.sin(ang), -math.cos(ang)      # eje del pétalo
    px, py = math.cos(ang), math.sin(ang)       # perpendicular

    def a_pantalla(x, y):
        return cx + x * px + y * dx, cy + x * py + y * dy

    for _ in range(int(n * DETALLE)):
        u = random.random()
        w = ancho_perfil(u, perfil)
        en_borde = random.random() < borde
        v = random.choice((-1, 1)) * random.uniform(0.85, 1.0) if en_borde else random.uniform(-1, 1)
        x = v * w * ancho + curva * u * u * largo
        y = u * largo
        color = mezclar(c_base, c_punta, u ** 0.9)
        if en_borde:
            color = aclarar(color, 0.25)        # bordes más luminosos
        X, Y = a_pantalla(x, y)
        pts.append((X, Y, variar(color, 10)))

    # pintitas típicas del lilium
    for _ in range(int(manchas * DETALLE)):
        u = random.uniform(0.08, 0.45)
        v = random.uniform(-0.45, 0.45)
        x = v * ancho_perfil(u, perfil) * ancho + curva * u * u * largo
        X, Y = a_pantalla(x, u * largo)
        pts.append((X, Y, variar(color_manchas, 10)))


def disco(pts, cx, cy, r, n, c_centro, c_borde, sy=1.0):
    """Disco relleno (sy < 1 lo aplana en elipse)."""
    for _ in range(int(n * DETALLE)):
        a = random.uniform(0, 2 * math.pi)
        d = math.sqrt(random.random())
        pts.append((cx + math.cos(a) * r * d, cy + math.sin(a) * r * d * sy,
                    variar(mezclar(c_centro, c_borde, d), 12)))


def tallo(pts, x0, y0, x1, y1, curv, n, grosor=3, color=(60, 140, 75)):
    """Curva de Bézier cuadrática de (x0, y0) a (x1, y1)."""
    mx, my = (x0 + x1) / 2 + curv, (y0 + y1) / 2
    for _ in range(int(n * DETALLE)):
        t = random.random()
        bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1
        by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1
        pts.append((bx + random.uniform(-grosor, grosor), by, variar(color, 15)))


def hoja(pts, cx, cy, ang, largo, ancho, n, curva=0.0):
    petalo(pts, cx, cy, ang, largo, ancho, n, (40, 110, 60), (110, 190, 100),
           perfil="punta", curva=curva, borde=0.25)


# ---------------------------------------------------------------------------
# Las flores
# ---------------------------------------------------------------------------
def etiquetar(pts, desde, etiqueta):
    """Marca los puntos agregados desde `desde` para la animación de florecer."""
    for i in range(desde, len(pts)):
        if len(pts[i]) < 4:
            pts[i] = pts[i][:3] + (etiqueta,)


def base_tallo(cx):
    """Los tallos nacen juntos del lago, como un ramo."""
    return ANCHO / 2 + (cx - ANCHO / 2) * 0.45


def punto_tallo(x0, y0, x1, y1, curv, t):
    mx, my = (x0 + x1) / 2 + curv, (y0 + y1) / 2
    return ((1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1,
            (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t * t * y1)


# Colores de cada peonía: (color base, color punta) por capa, de afuera hacia adentro
PEONIA_ROSADA = [((255, 150, 195), (255, 215, 232)), ((250, 120, 175), (255, 190, 215)),
                 ((240, 90, 155), (255, 160, 195)), ((225, 65, 135), (250, 130, 175)),
                 ((205, 45, 115), (240, 100, 155))]
PEONIA_CASI_BLANCA = [((255, 230, 238), (255, 250, 252)), ((252, 218, 230), (255, 243, 247)),
                      ((248, 205, 220), (255, 235, 242)), ((242, 188, 208), (253, 224, 235)),
                      ((232, 168, 195), (248, 210, 226))]
PEONIA_FUCSIA = [((240, 60, 170), (255, 145, 212)), ((230, 40, 160), (250, 115, 198)),
                 ((215, 25, 145), (245, 88, 182)), ((195, 15, 130), (235, 62, 166)),
                 ((170, 10, 115), (220, 40, 150))]


class Capas:
    """Ordena las partes de una flor de atrás hacia adelante y borra los puntos que quedan
    tapados por un pétalo de más adelante. Así cada pétalo conserva una silueta limpia."""

    def __init__(self):
        self.capas = []   # (polígono o None, lista de puntos, etiqueta)
        self.etiqueta = None

    def nueva(self, poligono=None):
        pts = []
        self.capas.append((poligono, pts, self.etiqueta))
        return pts

    def resultado(self):
        mapa = pygame.Surface((ANCHO, ALTO))
        mapa.fill((0, 0, 0))
        for i, (poli, _, _) in enumerate(self.capas, start=1):
            if poli:
                color = (i & 255, (i >> 8) & 255, 0)
                pygame.draw.polygon(mapa, color, poli)
                pygame.draw.polygon(mapa, color, poli, 4)   # contorno oscuro sobre lo de atrás
        visibles = []
        for i, (_, pts, etiqueta) in enumerate(self.capas, start=1):
            for x, y, c in pts:
                xi, yi = int(x), int(y)
                if 0 <= xi < ANCHO and 0 <= yi < ALTO:
                    r, g, _, _ = mapa.get_at((xi, yi))
                    if r + (g << 8) > i:       # lo tapa un pétalo de más adelante
                        continue
                visibles.append((x, y, c, etiqueta))
        return visibles


def petalo_ovalo(capas, cx, cy, ang, a, b, c_base, c_punta, volantes=6, densidad=0.13):
    """Pétalo redondeado centrado en (cx, cy). `ang` indica hacia dónde mira su punta
    (0 = arriba); `a` es su largo en esa dirección y `b` su ancho. La base queda en sombra
    y el borde de la punta, ondulado y luminoso."""
    fase = random.uniform(0, 6.28)
    ux, uy = math.sin(ang), -math.cos(ang)     # hacia la punta
    vx, vy = -uy, ux                           # hacia el costado

    def radio(th):                             # th = 0 apunta a la punta del pétalo
        ondas = 1 + 0.07 * math.sin(th * volantes + fase) * max(0.0, math.cos(th))
        return ondas

    def pos(th, d):
        p, q = math.cos(th) * a * d, math.sin(th) * b * d
        return cx + p * ux + q * vx, cy + p * uy + q * vy

    silueta = [pos(2 * math.pi * j / 32, radio(2 * math.pi * j / 32) * 0.985) for j in range(32)]
    general = capas.etiqueta
    if general and general[0] == "flor":      # base del pétalo y hacia dónde se abre
        capas.etiqueta = general[:5] + (cx - ux * a, cy - uy * a, ang)
    pts = capas.nueva(silueta)
    capas.etiqueta = general

    for _ in range(int(math.pi * a * b * densidad * DETALLE / 3) + 10):
        th = random.uniform(0, 2 * math.pi)
        d = math.sqrt(random.random()) * radio(th)
        t = (math.cos(th) * d + 1) / 2            # 0 en la base, 1 en la punta
        color = mezclar(c_base, c_punta, t)
        if t < 0.35:
            color = tono(color, 0.5 + t * 1.4)    # sombra de la copa
        pts.append((*pos(th, d), variar(color, 4)))

    for _ in range(int((a + b) * 3.4 * DETALLE / 3) + 10):              # borde
        th = random.uniform(0, 2 * math.pi)
        punta = math.cos(th)
        if punta < -0.2 and random.random() < 0.7:
            continue                               # la base casi sin borde: queda más limpia
        d = radio(th) * random.uniform(0.95, 1.0)
        col = aclarar(c_punta, 0.55) if punta > 0 else mezclar(c_base, c_punta, 0.6)
        pts.append((*pos(th, d), variar(col, 5)))


def una_peonia(capas, cx, cy, e, paleta):
    """Peonía vista de lado: corona atrás, domo de pétalos en copa al centro y un tazón
    de pétalos grandes adelante, como en una ilustración."""
    k = 1.4 * e
    bx, by = base_tallo(cx), LAGO_Y + 15
    tope, curv = cy + 100 * k, (bx - cx) * 0.3 - 30 * e
    capas.etiqueta = ("tallo", bx, by, cx, tope)
    verde = capas.nueva()
    tallo(verde, bx, by, cx, tope, curv, int(200 * e) + 40, 3.5 * e + 0.5)
    for t, ang, largo in ((0.2, -1.0, 150), (0.36, 1.1, 140)):
        hx, hy = punto_tallo(bx, by, cx, tope, curv, t)
        hoja(verde, hx, hy, ang, largo * e, 37 * e, int(210 * e) + 20, curva=0.15 if ang < 0 else -0.15)

    capas.etiqueta = ("flor", cx, cy + 20 * k, bx, by, cx, cy + 20 * k, 0.0)
    corona, lados, falda, domo_atras, domo, centro = (paleta[3], paleta[2], paleta[2],
                                                     paleta[1], paleta[0], paleta[4])

    # 1. corona: pétalos ondulados que asoman por detrás
    for i in range(7):
        th = -1.25 + 2.5 * i / 6
        petalo_ovalo(capas, cx + math.sin(th) * 62 * k, cy + 8 * k - math.cos(th) * 62 * k, th,
                     50 * k, 36 * k, *corona, volantes=7)
    # 2. pétalos laterales
    for lado in (-1, 1):
        th = lado * 1.85
        petalo_ovalo(capas, cx + math.sin(th) * 72 * k, cy + 10 * k - math.cos(th) * 72 * k, th,
                     48 * k, 36 * k, *lados, volantes=7)
    # 3. pequeños pétalos rizados del centro
    for dx in (-16, 16, 0):
        petalo_ovalo(capas, cx + dx * k, cy - 40 * k, dx * 0.02, 18 * k, 14 * k, *centro, volantes=5)
    # 4. domo: filas de pétalos en forma de copa, de atrás hacia adelante
    filas = [(cy - 18 * k, 3, 30 * k, 20 * k, 24 * k, domo_atras),
             (cy + 2 * k, 4, 48 * k, 24 * k, 26 * k, domo),
             (cy + 24 * k, 3, 44 * k, 28 * k, 32 * k, domo)]
    for y, cuantos, abierto, alto, ancho, (c1, c2) in filas:
        for i in range(cuantos):
            x = cx - abierto + 2 * abierto * i / (cuantos - 1)
            n1, n2 = (tono(c1, 0.9), tono(c2, 0.94)) if i % 2 else (c1, c2)
            petalo_ovalo(capas, x, y, (x - cx) / abierto * 0.35, alto, ancho, n1, n2, volantes=5)
    # 5. tazón: pétalos grandes que abrazan la flor por abajo
    for x, y, th, alto, ancho in ((-52, 58, -2.45, 42, 54), (52, 58, 2.45, 42, 54), (0, 70, math.pi, 40, 62)):
        petalo_ovalo(capas, cx + x * k, cy + y * k, th, alto * k, ancho * k, *falda, volantes=8)


def peonia():
    capas = Capas()
    for cx, cy, e, paleta in ((320, ALTO / 2 - 15, 0.62, PEONIA_CASI_BLANCA),
                              (685, ALTO / 2 - 5, 0.6, PEONIA_FUCSIA),
                              (500, ALTO / 2 - 80, 0.8, PEONIA_ROSADA)):
        una_peonia(capas, cx, cy, e, paleta)
    return capas.resultado()


# Colores de cada tulipán: (base, punta, punta de los pétalos de atrás)
TULIPAN_ROSA = ((255, 215, 225), (240, 100, 152), (185, 55, 112))
TULIPAN_CREMA = ((238, 230, 190), (255, 250, 232), (222, 210, 172))
TULIPAN_MORADO = ((195, 145, 225), (125, 40, 175), (80, 20, 125))


def un_tulipan(pts, cx, cy, e, paleta):
    n0 = len(pts)
    bx, by = base_tallo(cx), LAGO_Y + 15
    curv = 25 * e
    tallo(pts, bx, by, cx, cy, curv, int(300 * e) + 40, 3 * e + 0.5)
    hojas = []
    if cx <= ANCHO / 2:
        hojas.append((0.05, -0.45, 260, 46, 0.18))
    if cx >= ANCHO / 2:
        hojas.append((0.15, 0.40, 230, 40, -0.2))
    for t, ang, largo, ancho, curva in hojas:
        hx, hy = punto_tallo(bx, by, cx, cy, curv, t)
        hoja(pts, hx, hy, ang, largo * e, ancho * e, int(380 * e) + 30, curva=curva)

    etiquetar(pts, n0, ("tallo", bx, by, cx, cy))
    n1 = len(pts)
    amarillo, rojo, rojo_osc = paleta   # base, punta, punta oscura
    # pétalos de atrás (más oscuros) y luego los de adelante
    for ang, largo, ancho in [(-0.32, 185, 60), (0.32, 185, 60), (0.0, 205, 58)]:
        n_p = len(pts)
        petalo(pts, cx, cy, ang, largo * e, ancho * e, int(420 * e) + 20,
               mezclar(amarillo, rojo_osc, 0.4), rojo_osc, perfil="copa", curva=-ang * 0.25)
        etiquetar(pts, n_p, ("flor", cx, cy, bx, by, cx, cy, ang))
    for ang, largo, ancho in [(-0.13, 190, 66), (0.15, 188, 64)]:
        n_p = len(pts)
        petalo(pts, cx, cy, ang, largo * e, ancho * e, int(520 * e) + 20, amarillo, rojo,
               perfil="copa", curva=ang * 0.2)
        etiquetar(pts, n_p, ("flor", cx, cy, bx, by, cx, cy, ang))
    etiquetar(pts, n1, ("flor", cx, cy, bx, by, cx, cy, 0.0))


def tulipan():
    pts = []
    for cx, cy, e, paleta in ((355, ALTO / 2 + 75, 0.78, TULIPAN_CREMA),
                              (645, ALTO / 2 + 90, 0.75, TULIPAN_MORADO),
                              (500, ALTO / 2 + 15, 0.95, TULIPAN_ROSA)):
        un_tulipan(pts, cx, cy, e, paleta)
    return pts


# Colores de cada lilium: (centro, punta, pintitas)
LILIUM_BLANCO_ROSADO = ((242, 115, 168), (255, 250, 252), (150, 20, 80))
LILIUM_NARANJO_AMARILLO = ((255, 225, 60), (245, 90, 10), (130, 35, 10))   # centro amarillo, puntas naranjo fuerte
LILIUM_AMARILLO_ROSADO = ((252, 215, 70), (248, 145, 182), (185, 55, 90))


def un_lilium(pts, cx, cy, e, paleta):
    n0 = len(pts)
    bx, by = base_tallo(cx), LAGO_Y + 15
    curv = (bx - cx) * 0.2
    tallo(pts, bx, by, cx, cy, curv, int(260 * e) + 40, 3 * e + 0.5)
    for t, ang in ((0.3, -0.9), (0.5, 0.9)):
        hx, hy = punto_tallo(bx, by, cx, cy, curv, t)
        hoja(pts, hx, hy, ang, 200 * e, 30 * e, int(160 * e) + 20, curva=0.12 if ang < 0 else -0.12)

    etiquetar(pts, n0, ("tallo", bx, by, cx, cy))
    n1 = len(pts)
    giro = random.uniform(-0.25, 0.25)
    for i in range(6):
        ang = 2 * math.pi * i / 6 + giro + random.uniform(-0.05, 0.05)
        exterior = i % 2 == 0          # sépalos y pétalos alternados
        n_p = len(pts)
        petalo(pts, cx, cy, ang,
               (215 if exterior else 200) * e, (46 if exterior else 54) * e, int(360 * e) + 20,
               paleta[0], paleta[1], perfil="punta",
               curva=0.12 if exterior else -0.08, borde=0.28, manchas=int(30 * e) + 4,
               color_manchas=paleta[2])
        etiquetar(pts, n_p, ("flor", cx, cy, bx, by, cx, cy, ang))

    for i in range(6):                  # estambres
        ang = 2 * math.pi * i / 6 + math.pi / 6 + giro
        largo = random.uniform(85, 100) * e
        pasos = int(28 * DETALLE * e) + 4
        for j in range(pasos):
            s = j / pasos
            curva = 10 * e * s * s
            x = cx + math.sin(ang) * largo * s + math.cos(ang) * curva
            y = cy - math.cos(ang) * largo * s + math.sin(ang) * curva
            pts.append((x, y, variar(mezclar((200, 235, 180), (255, 250, 230), s), 8)))
        tx = cx + math.sin(ang) * largo + math.cos(ang) * 10 * e
        ty = cy - math.cos(ang) * largo + math.sin(ang) * 10 * e
        disco(pts, tx, ty, 7 * e, int(30 * e) + 5, (230, 110, 40), (160, 60, 25), sy=0.6)
    disco(pts, cx, cy, 9 * e, int(50 * e) + 5, (220, 250, 200), (150, 200, 130))   # pistilo
    etiquetar(pts, n1, ("flor", cx, cy, bx, by, cx, cy, 0.0))


def lilium():
    pts = []
    for cx, cy, e, paleta in ((315, ALTO / 2 + 25, 0.6, LILIUM_NARANJO_AMARILLO),
                              (685, ALTO / 2 + 40, 0.58, LILIUM_AMARILLO_ROSADO),
                              (500, ALTO / 2 - 45, 0.76, LILIUM_BLANCO_ROSADO)):
        un_lilium(pts, cx, cy, e, paleta)
    return pts


def loto_flotante(e):
    """Flor de loto con su nenúfar, a escala `e`. Origen = punto donde toca el agua."""
    pts = []
    disco(pts, 0, 4 * e, 115 * e, int(380 * e) + 30, (40, 120, 70), (90, 175, 95), sy=0.25)
    blanco, rosa, rosa_fuerte = (255, 240, 245), (245, 140, 180), (225, 80, 140)
    for ang in [-1.35 + 2.7 * i / 6 for i in range(7)]:              # capa exterior
        petalo(pts, 0, 0, ang, 150 * e * (0.75 + 0.25 * math.cos(ang)), 50 * e, int(190 * e) + 15,
               blanco, rosa, perfil="punta", curva=-ang * 0.08)
    for ang in [-0.95 + 1.9 * i / 4 for i in range(5)]:              # capa media
        petalo(pts, 0, 0, ang, 185 * e, 48 * e, int(230 * e) + 15, blanco, rosa,
               perfil="punta", curva=-ang * 0.1)
    disco(pts, 0, -55 * e, 26 * e, int(120 * e) + 8, (255, 220, 90), (225, 175, 60), sy=0.45)
    for ang in (-0.38, 0.0, 0.38):                                   # capa interior
        petalo(pts, 0, 0, ang, 175 * e, 44 * e, int(240 * e) + 15, (255, 248, 250), rosa_fuerte,
               perfil="punta", curva=-ang * 0.15)
    return pts


GENERADORES = [peonia, tulipan, lilium]


def ajustar(pts, n):
    """Lleva cualquier lista de puntos a exactamente n, conservando el orden de dibujo."""
    if len(pts) >= n:
        idx = sorted(random.sample(range(len(pts)), n))
        return [pts[i] for i in idx]
    idx = sorted(random.choices(range(len(pts)), k=n))
    return [(pts[i][0] + random.uniform(-1.5, 1.5), pts[i][1] + random.uniform(-1.5, 1.5)) + tuple(pts[i][2:])
            for i in idx]


# ---------------------------------------------------------------------------
# Sistema de partículas
# ---------------------------------------------------------------------------
class Particulas:
    RESORTE = 0.022
    AMORTIGUACION = 0.87

    def __init__(self, n):
        self.n = n
        self.x = [random.uniform(0, ANCHO) for _ in range(n)]
        self.y = [random.uniform(0, ALTO) for _ in range(n)]
        self.vx = [0.0] * n
        self.vy = [0.0] * n
        self.col = [list(variar((180, 160, 220), 40)) for _ in range(n)]
        self.tx, self.ty, self.tcol = self.x[:], self.y[:], [tuple(c) for c in self.col]
        self.brilla = [random.random() < BRILLO for _ in range(n)]
        self.fase = [random.uniform(0, 2 * math.pi) for _ in range(n)]

    def nueva_forma(self, pts, explosion=True):
        """Asigna la nueva flor. Cada punto guarda su posición final y cómo llega a ella:
        los tallos crecen desde el lago y los pétalos se abren desde un capullo."""
        cx, cy = ANCHO / 2, ALTO / 2
        n = self.n
        self.fx, self.fy = [0.0] * n, [0.0] * n
        self.modo, self.par = [0] * n, [0.0] * n            # modo: 0 fijo, 1 tallo, 2 flor
        self.ox, self.oy, self.bx, self.by = [0.0] * n, [0.0] * n, [0.0] * n, [0.0] * n
        self.px, self.py, self.pang = [0.0] * n, [0.0] * n, [0.0] * n   # base y ángulo de su pétalo
        self.edad = 0.0
        for i, p in enumerate(pts):
            x, y, c = p[:3]
            self.fx[i], self.fy[i] = x, y
            etiqueta = p[3] if len(p) > 3 else None
            if etiqueta and etiqueta[0] == "tallo":
                _, bx, by, topx, topy = etiqueta
                self.modo[i] = 1
                self.ox[i], self.oy[i] = bx, by
                self.par[i] = min(1.0, max(0.02, (by - y) / max(1.0, by - topy)))
            elif etiqueta and etiqueta[0] == "flor":
                _, ox, oy, bx, by, px, py, ang = etiqueta
                self.modo[i] = 2
                self.ox[i], self.oy[i], self.bx[i], self.by[i] = ox, oy, bx, by
                self.px[i], self.py[i], self.pang[i] = px, py, ang
                # los pétalos exteriores (más abiertos) se abren primero; el centro, al final
                self.par[i] = 0.75 * (1 - min(1.0, abs(ang) / math.pi)) + random.uniform(0, 0.06)
            self.tx[i], self.ty[i], self.tcol[i] = x, y, c
            if explosion:   # pequeño estallido radial antes de reagruparse
                dx, dy = self.x[i] - cx, self.y[i] - cy
                d = math.hypot(dx, dy) or 1
                f = random.uniform(4, 11)
                self.vx[i] += dx / d * f + random.uniform(-3, 3)
                self.vy[i] += dy / d * f + random.uniform(-3, 3)

    def florecer(self):
        """Mueve los destinos de los puntos según cuánto ha avanzado el florecimiento."""
        edad = self.edad
        g = min(1.0, edad / (DURACION_FLORECER * 0.38))          # crecimiento del tallo
        inicio = DURACION_FLORECER * 0.32                         # cuándo empiezan a abrirse
        tramo = DURACION_FLORECER * 0.5
        fx, fy, ox, oy, par, modo = self.fx, self.fy, self.ox, self.oy, self.par, self.modo
        px, py, pang = self.px, self.py, self.pang
        tx, ty = self.tx, self.ty
        for i in range(self.n):
            m = modo[i]
            if m == 1:
                f = par[i]
                r = 1.0 if f <= g else g / f
                tx[i] = ox[i] + (fx[i] - ox[i]) * r
                ty[i] = oy[i] + (fy[i] - oy[i]) * r
            elif m == 2:
                p = (edad - inicio - par[i] * tramo * 0.6) / tramo
                p = 0.0 if p < 0 else (1.0 if p > 1 else p)
                q = p - 1
                s = 1 + 2.4 * q * q * q + 1.4 * q * q        # 0 -> 1 con un pequeño rebote
                # en el capullo cada pétalo está cerrado hacia arriba; al abrirse gira sobre su base
                ang = pang[i]
                giro = (ang * 0.1 - ang) * (1 - s)
                largo = 0.45 + 0.55 * s
                dx, dy = fx[i] - px[i], fy[i] - py[i]
                co, si = math.cos(giro), math.sin(giro)
                abre = 0.3 + 0.7 * s                           # las bases se separan del centro
                x = ox[i] + (px[i] - ox[i]) * abre + (dx * co - dy * si) * largo
                y = oy[i] + (py[i] - oy[i]) * abre + (dx * si + dy * co) * largo
                if g < 1:                                      # el capullo sube con el tallo
                    x += (self.bx[i] - ox[i]) * (1 - g)
                    y += (self.by[i] - oy[i]) * (1 - g)
                tx[i], ty[i] = x, y

    def actualizar(self, t, dt=1 / 60):
        if hasattr(self, "edad") and self.edad <= DURACION_FLORECER + 0.2:
            self.florecer()
        if hasattr(self, "edad"):
            self.edad += dt
        k, amort = self.RESORTE, self.AMORTIGUACION
        for i in range(self.n):
            ty = self.ty[i]
            # la brisa mueve más las partes altas que la base
            brisa = math.sin(t * 1.2 + ty * 0.006) * 3.0 * (1 - ty / ALTO)
            self.vx[i] = (self.vx[i] + (self.tx[i] + brisa - self.x[i]) * k) * amort
            self.vy[i] = (self.vy[i] + (ty - self.y[i]) * k) * amort
            self.x[i] += self.vx[i]
            self.y[i] += self.vy[i]
            c, tc = self.col[i], self.tcol[i]
            c[0] += (tc[0] - c[0]) * 0.04
            c[1] += (tc[1] - c[1]) * 0.04
            c[2] += (tc[2] - c[2]) * 0.04

    def dibujar(self, sup, t):
        fill = sup.fill
        for i in range(self.n):
            c = self.col[i]
            x, y = int(self.x[i]), int(self.y[i])
            if self.brilla[i]:
                b = 0.5 + 0.5 * math.sin(t * 3 + self.fase[i])
                if b > 0.6:   # halo suave cuando la luz está en su punto más alto
                    fill(mezclar(FONDO, c, 0.45), (x - 2, y - 2, 5, 5))
                fill(aclarar(c, 0.55 * b), (x - 1, y - 1, 3, 3))
            else:
                fill(c, (x, y, 2, 2))



# ---------------------------------------------------------------------------
# Piedras preciosas a los costados
# ---------------------------------------------------------------------------
PIEDRAS = {  # nombre: (color, talla)
    "aguamarina": ((105, 215, 228), "brillante"),
    "citrino": ((250, 175, 40), "prisma"),
    "amatista": ((158, 88, 218), "corazon"),
    "zafiro": ((45, 80, 220), "oval"),
}

GEMAS = [  # (piedra, x, y, tamaño)
    ("amatista", 100, 205, 34), ("aguamarina", 170, 325, 26),
    ("zafiro", 80, 440, 28), ("citrino", 160, 540, 26),
    ("zafiro", 900, 205, 30), ("citrino", 830, 320, 26),
    ("amatista", 905, 440, 27), ("aguamarina", 840, 545, 28),
]


def contorno_talla(talla, n=32):
    """Silueta de la piedra en coordenadas unitarias (radio ~1, y hacia abajo)."""
    if talla == "prisma":      # cristal largo de seis caras con punta triangular
        w = 0.42
        return [(-w, 1.25), (-w, -0.45), (0, -1.25), (w, -0.45), (w, 1.25)]
    if talla == "esmeralda":   # rectángulo con esquinas cortadas
        w, h, c = 0.75, 1.05, 0.25
        return [(-w + c, -h), (w - c, -h), (w, -h + c), (w, h - c),
                (w - c, h), (-w + c, h), (-w, h - c), (-w, -h + c)]
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        if talla == "brillante":
            pts.append((math.sin(t), -math.cos(t)))
        elif talla == "oval":
            pts.append((0.78 * math.sin(t), -1.1 * math.cos(t)))
        elif talla == "pera":       # gota con la punta hacia arriba
            pts.append((0.85 * math.sin(t) * math.sin(t / 2), -1.1 * math.cos(t) + 0.2))
        elif talla == "corazon":
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts.append((x / 15, -y / 15 - 0.15))
    return pts


def dentro(x, y, poli):
    adentro = False
    j = len(poli) - 1
    for i in range(len(poli)):
        xi, yi = poli[i]
        xj, yj = poli[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            adentro = not adentro
        j = i
    return adentro


def tono(c, luz):
    if luz <= 1:
        return tuple(v * luz for v in c)
    return aclarar(c, min(1.0, luz - 1))


def linea(lista, a, b, color, n=None):
    if n is None:   # densidad según el largo de la línea
        n = int(math.hypot(b[0] - a[0], b[1] - a[1]) / 2.2) + 2
    for k in range(n):
        s = k / max(1, n - 1)
        lista.append((a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s, variar(color, 8)))


def gema(talla, tam, color):
    """Puntos (dx, dy, color) de una piedra tallada, relativos a su centro."""
    borde = [(x * tam, y * tam) for x, y in contorno_talla(talla)]
    mesa = [(x * 0.5, y * 0.5) for x, y in borde]
    xs, ys = [p[0] for p in borde], [p[1] for p in borde]
    area = abs(sum(borde[i][0] * borde[i - 1][1] - borde[i - 1][0] * borde[i][1]
                   for i in range(len(borde)))) / 2
    escalonada = talla == "esmeralda"
    prisma = talla == "prisma"
    w, cara, tope = 0.42 * tam, 0.45 * 0.42 * tam, -0.45 * tam   # medidas del prisma
    pts = []

    objetivo = int(area * 0.16)
    while len(pts) < objetivo:
        x, y = random.uniform(min(xs), max(xs)), random.uniform(min(ys), max(ys))
        if not dentro(x, y, borde):
            continue
        if prisma:       # tres caras visibles: izquierda, frente y derecha
            luz = 0.72 if x < -cara else (0.58 if x > cara else 1.0)
            if y < tope - 0.12 * tam * (1 - abs(x) / w):
                luz *= 1.15                               # caras de la punta
            luz *= 1 + 0.3 * (-y / (1.25 * tam))          # más luz hacia la punta
        elif escalonada:   # escalones concéntricos
            rel = max(abs(x) / (0.75 * tam), abs(y) / (1.05 * tam))
            luz = 0.7 + 0.3 * (int(rel * 4) % 2)
        else:            # facetas radiales alternadas
            sector = int((math.atan2(y, x) + math.pi) / (2 * math.pi) * 12)
            luz = 0.72 + 0.3 * (sector % 2)
        luz *= 1 + 0.35 * (-(x + y) / (tam * 1.5))   # luz que viene de arriba a la izquierda
        if not prisma and dentro(x, y, mesa):
            luz *= 1.12
        pts.append((x, y, variar(tono(color, luz), 10)))

    claro = aclarar(color, 0.55)
    for i in range(len(borde)):                       # contorno brillante
        linea(pts, borde[i - 1], borde[i], claro, 5 if len(borde) > 8 else None)
    if prisma:
        quiebre = tope - 0.12 * tam
        arista = aclarar(color, 0.35)
        for sx in (-1, 1):
            linea(pts, (sx * cara, 1.25 * tam), (sx * cara, quiebre), arista)
            linea(pts, (sx * cara, quiebre), (0, -1.25 * tam), arista)
            linea(pts, (sx * w, tope), (sx * cara, quiebre), arista)
    elif escalonada:
        for f in (0.72, 0.45):
            interior = [(x * f, y * f) for x, y in borde]
            for i in range(len(interior)):
                linea(pts, interior[i - 1], interior[i], aclarar(color, 0.35), 10)
        for i in (0, 2, 4, 6):
            linea(pts, borde[i], (borde[i][0] * 0.45, borde[i][1] * 0.45), aclarar(color, 0.3), 6)
    else:
        for i in range(len(mesa)):                    # la mesa (cara superior)
            linea(pts, mesa[i - 1], mesa[i], aclarar(color, 0.4), 3)
        for i in range(0, len(borde), 4):             # aristas de las facetas
            linea(pts, mesa[i], borde[i], aclarar(color, 0.3), 8)
    return pts


class Gemas:
    RESORTE = 0.03
    AMORTIGUACION = 0.85

    def __init__(self):
        self.centros, self.fases, self.indices = [], [], []
        self.dx, self.dy, self.col, self.gid = [], [], [], []
        for g, (nombre, cx, cy, tam) in enumerate(GEMAS):
            color, talla = PIEDRAS[nombre]
            ini = len(self.dx)
            for dx, dy, c in gema(talla, tam, color):
                self.dx.append(dx)
                self.dy.append(dy)
                self.col.append(c)
                self.gid.append(g)
            self.indices.append((ini, len(self.dx)))
            self.centros.append((cx, cy))
            self.fases.append(random.uniform(0, 2 * math.pi))
        n = len(self.dx)
        self.x = [random.uniform(0, ANCHO) for _ in range(n)]
        self.y = [random.uniform(0, ALTO) for _ in range(n)]
        self.vx, self.vy = [0.0] * n, [0.0] * n
        self.brilla = [random.random() < 0.2 for _ in range(n)]
        self.fase_pt = [random.uniform(0, 2 * math.pi) for _ in range(n)]
        self.destellos = []   # [x, y, vida]
        self.imagenes = None  # cuando ya están armadas, cada piedra se dibuja como imagen
        self.t_armado = 6.0

    def _hornear(self):
        """Pasa cada piedra ya armada a una imagen: se dibuja mucho más rápido."""
        self.imagenes = []
        for ini, fin in self.indices:
            xs, ys = self.dx[ini:fin], self.dy[ini:fin]
            x0, y0 = int(min(xs)) - 3, int(min(ys)) - 3
            sup = pygame.Surface((int(max(xs)) - x0 + 4, int(max(ys)) - y0 + 4), pygame.SRCALPHA)
            for i in range(ini, fin):
                if not self.brilla[i]:
                    sup.fill(self.col[i], (int(self.dx[i]) - x0, int(self.dy[i]) - y0, 2, 2))
            self.imagenes.append((sup, x0, y0, [i for i in range(ini, fin) if self.brilla[i]]))

    def actualizar(self, t, dt):
        self.flote = flote = [math.sin(t * 0.9 + f) * 5 for f in self.fases]
        if self.imagenes is None and t > self.t_armado:
            self._hornear()
        k, amort = self.RESORTE, self.AMORTIGUACION
        rango = range(len(self.dx)) if self.imagenes is None else ()
        for i in rango:
            g = self.gid[i]
            cx, cy = self.centros[g]
            self.vx[i] = (self.vx[i] + (cx + self.dx[i] - self.x[i]) * k) * amort
            self.vy[i] = (self.vy[i] + (cy + self.dy[i] + flote[g] - self.y[i]) * k) * amort
            self.x[i] += self.vx[i]
            self.y[i] += self.vy[i]
        for g, (ini, fin) in enumerate(self.indices):      # nuevos destellos
            if random.random() < 0.03:
                i = random.randrange(ini, fin)
                cx, cy = self.centros[g]
                self.destellos.append([cx + self.dx[i], cy + self.dy[i] + flote[g], 1.0])
        for d in self.destellos:
            d[2] -= dt * 1.8
        self.destellos = [d for d in self.destellos if d[2] > 0]

    def dibujar(self, sup, t):
        fill = sup.fill
        if self.imagenes is not None:
            for g, (img, x0, y0, brillantes) in enumerate(self.imagenes):
                cx, cy = self.centros[g]
                cy += self.flote[g]
                sup.blit(img, (cx + x0, cy + y0))
                for i in brillantes:
                    b = 0.5 + 0.5 * math.sin(t * 2.5 + self.fase_pt[i])
                    fill(aclarar(self.col[i], 0.6 * b), (int(cx + self.dx[i]), int(cy + self.dy[i]), 2, 2))
        for i in (range(len(self.dx)) if self.imagenes is None else ()):
            c = self.col[i]
            x, y = int(self.x[i]), int(self.y[i])
            if self.brilla[i]:
                b = 0.5 + 0.5 * math.sin(t * 2.5 + self.fase_pt[i])
                fill(aclarar(c, 0.6 * b), (x, y, 2, 2))
            else:
                fill(c, (x, y, 2, 2))
        for x, y, vida in self.destellos:   # estrellitas de luz
            b = math.sin(vida * math.pi)
            largo = 3 + 9 * b
            col = (255, 255, 255)
            pygame.draw.line(sup, col, (x - largo, y), (x + largo, y))
            pygame.draw.line(sup, col, (x, y - largo), (x, y + largo))
            d = largo * 0.4
            pygame.draw.line(sup, (200, 200, 230), (x - d, y - d), (x + d, y + d))
            pygame.draw.line(sup, (200, 200, 230), (x - d, y + d), (x + d, y - d))



# ---------------------------------------------------------------------------
# El lago
# ---------------------------------------------------------------------------
CELESTE, AZUL_PROFUNDO = (130, 205, 245), (22, 55, 145)


class Lago:
    def __init__(self):
        alto = ALTO - LAGO_Y
        self.fondo = pygame.Surface((ANCHO + 8, alto), pygame.SRCALPHA)
        for _ in range(int(3200 * DETALLE / 3)):
            y = random.uniform(0, alto)
            p = y / alto
            c = variar(mezclar(CELESTE, AZUL_PROFUNDO, p ** 0.7), 18)
            a = int(255 * min(1.0, y / 14))      # orilla difusa
            largo = random.randint(2, 4 + int(5 * (1 - p)))
            self.fondo.fill((*map(int, c), a), (random.uniform(0, ANCHO + 8), y, largo, 1 + (p > 0.5)))
        # reflejos que se mueven sobre el agua
        self.reflejos = [[random.uniform(0, ANCHO), LAGO_Y + 4 + (alto - 8) * random.random() ** 1.3,
                          random.randint(3, 9), random.uniform(0, 6.28), random.uniform(-8, 8)]
                         for _ in range(420)]

    def dibujar(self, sup, t, dt):
        sup.blit(self.fondo, (-4 + math.sin(t * 0.5) * 3, LAGO_Y))
        fill = sup.fill
        for r in self.reflejos:
            r[0] = (r[0] + r[4] * dt) % ANCHO
            b = math.sin(t * 1.8 + r[3])
            if b > 0.1:
                fill(aclarar(CELESTE, 0.55 * b), (int(r[0]), int(r[1]), r[2], 1))


# ---------------------------------------------------------------------------
# Flores de loto flotando en el lago
# ---------------------------------------------------------------------------
LOTOS = [  # (x, cuánto más abajo del borde del lago, escala)
    (130, 26, 0.32), (430, 20, 0.28), (730, 24, 0.30),       # al fondo
    (65, 118, 0.5), (935, 112, 0.46),                         # adelante
]


class Lotos:
    def __init__(self):
        self.items = []
        for x, prof, e in LOTOS:
            pts = loto_flotante(e)
            reflejo = [(px + random.uniform(-2, 2), -py * 0.5 + 6 * e, mezclar(c, (70, 120, 200), 0.6))
                       for px, py, c in pts if py < -8 * e and random.random() < 0.3]
            todos = pts + reflejo
            x0 = int(min(p[0] for p in todos)) - 2
            y0 = int(min(p[1] for p in todos)) - 2
            sup = pygame.Surface((int(max(p[0] for p in todos)) - x0 + 4,
                                  int(max(p[1] for p in todos)) - y0 + 4), pygame.SRCALPHA)
            for px, py, c in reflejo:
                sup.fill((*map(int, c), 95), (int(px) - x0, int(py) - y0, 2, 2))
            for px, py, c in pts:
                sup.fill((*map(int, c), 255), (int(px) - x0, int(py) - y0, 2, 2))
            self.items.append((sup, x + x0, LAGO_Y + prof, y0, prof, random.uniform(0, 6.28)))

    def dibujar(self, sup, t, delante):
        """delante=False dibuja los del fondo (detrás de los cisnes); True, los de adelante."""
        for img, x, y, y0, prof, fase in self.items:
            if (prof > 100) == delante:
                sup.blit(img, (x, y + y0 + math.sin(t * 0.8 + fase) * 1.5))


# ---------------------------------------------------------------------------
# La pareja de cisnes
# ---------------------------------------------------------------------------
def cisne(escala, fase, semilla):
    """Un cisne mirando a la derecha. Origen = punto de flotación. Devuelve (x, y, color, alfa)."""
    rnd = random.Random(semilla)
    s = escala
    blanco, sombra = (250, 250, 255), (175, 185, 215)
    pts = []

    cuerpo = [(-1.0, -0.42), (-0.8, -0.2), (-0.45, -0.42), (-0.05, -0.5), (0.35, -0.42),
              (0.68, -0.25), (0.85, -0.04), (0.7, 0.02), (-0.6, 0.02), (-0.92, -0.14)]
    cuerpo = [(x * s, y * s) for x, y in cuerpo]
    xs, ys = [p[0] for p in cuerpo], [p[1] for p in cuerpo]
    total = 0
    while total < int(s * s * 0.42):
        x, y = rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys))
        if dentro(x, y, cuerpo):
            c = mezclar(blanco, sombra, (y / s + 0.5) / 0.55)
            pts.append((x, y, variar(c, 6), 255))
            total += 1
    for k in range(4):                                  # plumas del ala
        x0, x1 = (-0.85 + 0.1 * k) * s, (0.4 - 0.08 * k) * s
        for j in range(40):
            u = j / 39
            x = x0 + (x1 - x0) * u
            y = (-0.2 - 0.04 * k - 0.16 * math.sin(math.pi * u)) * s
            pts.append((x, y, (200, 208, 230), 255))

    # cuello en S (curva de Bézier cúbica) que se mece con `fase`
    mx, my = 0.05 * math.sin(fase), 0.03 * math.cos(fase)
    p0, p1 = (0.55, -0.35), (1.0, -0.55)
    p2, p3 = (0.28 + mx, -1.0 + my), (0.55 + mx, -1.35 + my)
    for _ in range(int(s * 10)):
        t = rnd.random()
        bx = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0]
        by = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]
        g = (0.11 - 0.05 * t) * rnd.uniform(-1, 1)
        pts.append(((bx + g) * s, (by + g * 0.4) * s, variar(mezclar(blanco, sombra, 0.25 + g * 2), 6), 255))
    hx, hy = p3[0] * s, p3[1] * s
    for _ in range(int(s * 1.6)):                       # cabeza
        a, d = rnd.uniform(0, 6.28), math.sqrt(rnd.random()) * 0.1 * s
        pts.append((hx + math.cos(a) * d, hy + math.sin(a) * d * 0.85, variar(blanco, 5), 255))
    for _ in range(int(s * 1.2)):                       # pico naranjo
        u, v = rnd.random(), rnd.uniform(-1, 1)
        x = hx + (0.07 + 0.24 * u) * s
        y = hy + (0.0 + 0.11 * u + v * 0.04 * (1 - u)) * s
        pts.append((x, y, variar((240, 125, 40), 10), 255))
    for _ in range(int(s * 0.4)):                       # base negra del pico
        pts.append((hx + rnd.uniform(0.04, 0.09) * s, hy + rnd.uniform(-0.03, 0.04) * s, (25, 20, 30), 255))
    pts.append((hx + 0.02 * s, hy - 0.03 * s, (20, 20, 30), 255))   # ojo

    # reflejo en el agua
    reflejo = []
    for x, y, c, _ in pts:
        if rnd.random() < 0.35:
            reflejo.append((x + rnd.uniform(-2, 2), -y * 0.55 + 0.04 * s, mezclar(c, (70, 120, 200), 0.55), 110))
    return reflejo + pts


class Cisnes:
    FOTOGRAMAS = 12
    PAREJA = [  # (escala, cuánto más abajo del borde del lago flota, adelanto en x)
        (54, 55, 85),   # el que va un poco más atrás en el paisaje (más chico)
        (64, 88, 0),
    ]

    def __init__(self):
        self.cuadros = []   # por cisne: lista de (superficie, ox, oy)
        for k, (escala, _, _) in enumerate(self.PAREJA):
            cuadros = []
            for f in range(self.FOTOGRAMAS):
                pts = cisne(escala, 2 * math.pi * f / self.FOTOGRAMAS, semilla=7 + k)
                ox, oy = int(1.15 * escala), int(1.55 * escala)
                sup = pygame.Surface((int(2.5 * escala), int(2.4 * escala)), pygame.SRCALPHA)
                for x, y, c, a in pts:
                    sup.fill((*map(int, c), a), (int(x) + ox, int(y) + oy, 2, 2))
                cuadros.append((sup, ox, oy))
            self.cuadros.append(cuadros)
        self.inicio = -2 * max(e for e, _, _ in self.PAREJA) - 80
        self.x = self.inicio

    def dibujar(self, sup, t, dt):
        self.x += VELOCIDAD_CISNES * dt
        if self.x > ANCHO + 2 * max(e for e, _, _ in self.PAREJA):   # salieron: vuelven a empezar
            self.x = self.inicio
        f = int(t * 3) % self.FOTOGRAMAS
        for k, (escala, prof, adelanto) in enumerate(self.PAREJA):
            x = self.x + adelanto
            y = LAGO_Y + prof + math.sin(t * 1.6 + k) * 1.5
            for d in range(4, 70, 3):                   # estela en forma de V
                b = 1 - d / 70
                if b * (0.6 + 0.4 * math.sin(t * 4 - d * 0.3)) > 0.25:
                    col = aclarar(CELESTE, 0.5 * b)
                    for lado in (-1, 1):
                        sup.fill(col, (int(x - 0.95 * escala - d), int(y + lado * d * 0.13 + 1), 2, 1))
            img, ox, oy = self.cuadros[k][f]
            sup.blit(img, (int(x) - ox, int(y) - oy))



# ---------------------------------------------------------------------------
# Pájaros que cruzan el cielo
# ---------------------------------------------------------------------------
PLUMAJES = {  # (lomo, pecho, cabeza, alas, pico)
    "azulejo": ((60, 125, 235), (250, 150, 65), (75, 140, 240), (40, 90, 205), (60, 55, 70)),
    "jilguero": ((250, 210, 40), (255, 232, 95), (255, 220, 60), (70, 65, 85), (245, 165, 85)),
    "cardenal": ((222, 40, 52), (240, 70, 70), (232, 48, 58), (170, 25, 42), (250, 155, 65)),
    "turquesa": ((40, 195, 160), (225, 248, 240), (45, 210, 180), (25, 140, 125), (60, 55, 70)),
    "rosado": ((242, 110, 172), (255, 195, 215), (248, 125, 182), (192, 70, 142), (255, 205, 125)),
    "lila": ((150, 110, 232), (232, 212, 255), (165, 122, 242), (110, 80, 202), (255, 195, 115)),
}


def pajaro(escala, aleteo, plumaje, semilla):
    """Pajarito de puntos visto de lado, mirando a la derecha. `aleteo` va de -1 (alas
    abajo) a 1 (alas arriba). Origen = centro del cuerpo. Devuelve (x, y, color)."""
    rnd = random.Random(semilla)
    s = escala
    lomo, pecho, cabeza, alas, pico = PLUMAJES[plumaje]
    pts = []

    def ala(oscuro):
        """Ala redondeada que gira sobre el hombro."""
        ang = -1.45 + aleteo * 0.95            # 0 = arriba; negativo = hacia atrás
        hx, hy = -0.05 * s, -0.22 * s
        ux, uy = math.sin(ang), -math.cos(ang)
        vx, vy = -uy, ux
        base = tono(alas, 0.7) if oscuro else alas
        for _ in range(int(s * s * 0.55)):
            u = rnd.random()
            w = math.sin(math.pi * u ** 0.7) * 0.3 * s
            v = rnd.uniform(-1, 1)
            d = u * 0.9 * s
            col = mezclar(base, aclarar(base, 0.35), u)
            if abs(v) > 0.82 or (not oscuro and 0.3 < u < 0.36):   # borde y franja de plumas
                col = aclarar(base, 0.45)
            pts.append((hx + ux * d + vx * v * w, hy + uy * d + vy * v * w, col))

    ala(oscuro=True)                                    # ala del otro lado, detrás del cuerpo
    for _ in range(int(s * 6)):                         # cola en abanico
        u, v = rnd.random(), rnd.uniform(-1, 1)
        x = (-0.45 - 0.55 * u) * s
        y = (-0.04 + v * (0.05 + 0.13 * u) - 0.1 * u) * s
        pts.append((x, y, mezclar(alas, aclarar(alas, 0.3), u)))
    for _ in range(int(s * s * 1.1)):                   # cuerpo redondo: lomo arriba, pecho abajo
        a, d = rnd.uniform(0, 6.28), math.sqrt(rnd.random())
        x, y = math.cos(a) * d * 0.56 * s, math.sin(a) * d * 0.38 * s
        t = (y / (0.38 * s) + 1) / 2
        pts.append((x, y, mezclar(lomo, pecho, min(1.0, t * 1.4))))
    for _ in range(int(s * s * 0.4)):                   # cabeza
        a, d = rnd.uniform(0, 6.28), math.sqrt(rnd.random()) * 0.28 * s
        pts.append((0.48 * s + math.cos(a) * d, -0.3 * s + math.sin(a) * d, cabeza))
    for _ in range(int(s * 0.8)):                       # pico corto
        u, v = rnd.random(), rnd.uniform(-1, 1)
        pts.append(((0.74 + 0.22 * u) * s, (-0.28 + 0.03 * u + v * 0.06 * (1 - u)) * s, pico))
    ojo = (0.58 * s, -0.36 * s)
    for dx in (0, 1):
        for dy in (0, 1):
            pts.append((ojo[0] + dx, ojo[1] + dy, (25, 20, 35)))
    pts.append((ojo[0] + 1, ojo[1], (255, 255, 255)))  # brillo del ojo
    ala(oscuro=False)                                   # ala cercana, delante del cuerpo
    return pts


class Pajaros:
    FOTOGRAMAS = 10
    TAMANOS = (13, 16)

    def __init__(self):
        self.cuadros = {}   # (plumaje, escala, hacia_izquierda) -> lista de superficies
        for plumaje in PLUMAJES:
            for escala in self.TAMANOS:
                cuadros = []
                for f in range(self.FOTOGRAMAS):
                    aleteo = math.sin(2 * math.pi * f / self.FOTOGRAMAS)
                    lado = int(2.6 * escala)
                    sup = pygame.Surface((lado, lado), pygame.SRCALPHA)
                    for x, y, c in pajaro(escala, aleteo, plumaje, semilla=escala):
                        sup.fill((*map(int, c), 255), (int(x) + lado // 2, int(y) + lado // 2, 2, 2))
                    cuadros.append(sup)
                self.cuadros[(plumaje, escala, False)] = cuadros
                self.cuadros[(plumaje, escala, True)] = [pygame.transform.flip(c, True, False) for c in cuadros]
        self.bandada = []           # [x, y_base, velocidad, clave_derecha, fase, ritmo, hacia_izquierda]
        self.proxima = 3.0          # la primera bandada aparece a los 3 segundos

    def nueva_bandada(self):
        izquierda = random.random() < 0.5
        cuantos = random.randint(2, 5)
        y = random.uniform(150, 310)
        vel = random.uniform(60, 90) * (-1 if izquierda else 1)
        inicio = ANCHO + 50 if izquierda else -50
        colores = random.sample(list(PLUMAJES), k=min(cuantos, len(PLUMAJES)))
        for n in range(cuantos):                        # grupo suelto, no en formación
            atraso = n * random.uniform(35, 60)
            self.bandada.append([inicio + (atraso if izquierda else -atraso),
                                 y + random.uniform(-45, 45),
                                 vel * random.uniform(0.92, 1.08),
                                 (colores[n % len(colores)], random.choice(self.TAMANOS)),
                                 random.uniform(0, 1), random.uniform(2.6, 3.4), izquierda])

    def dibujar(self, sup, t, dt):
        self.proxima -= dt
        if self.proxima <= 0:
            self.nueva_bandada()
            self.proxima = random.uniform(*CADA_CUANTO_PAJAROS)
        vivos = []
        for p in self.bandada:
            p[0] += p[2] * dt
            x, y_base, _, (plumaje, escala), fase, ritmo, izquierda = p
            if (x > -80) if izquierda else (x < ANCHO + 80):
                vivos.append(p)
            f = int((t * ritmo + fase) * self.FOTOGRAMAS) % self.FOTOGRAMAS
            img = self.cuadros[(plumaje, escala, izquierda)][f]
            y = y_base + math.sin(t * 2.2 + fase * 6) * 9      # vuelo ondulado de pajarito
            sup.blit(img, (int(x) - img.get_width() // 2, int(y) - img.get_height() // 2))
        self.bandada = vivos


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
async def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Jardín de puntos")

    musica = False
    try:
        pygame.mixer.init()
        for archivo in CANCIONES:
            try:
                pygame.mixer.music.load(archivo)
            except Exception:
                continue                    # no está o no se puede leer: probar el siguiente
            pygame.mixer.music.set_volume(VOLUMEN)
            pygame.mixer.music.play(-1)     # -1 = se repite sin fin
            musica = True
            break
        if not musica:
            print("Sin música: no encontré", " ni ".join(CANCIONES))
    except Exception as error:              # sin audio: la animación sigue igual
        print("Sin música:", error)
    musica_sonando = musica
    reloj = pygame.time.Clock()

    fuente_titulo = pygame.font.SysFont("georgia,garamond,serif", 34, italic=True)
    fuente_sub = pygame.font.SysFont("georgia,garamond,serif", 22, italic=True)
    fuente_msj = pygame.font.SysFont("georgia,garamond,serif", 26, italic=True)

    pantalla.fill(FONDO)
    cargando = fuente_titulo.render("Cultivando las flores...", True, (255, 220, 235))
    pantalla.blit(cargando, (ANCHO / 2 - cargando.get_width() / 2, ALTO / 2 - 20))
    pygame.display.flip()
    await asyncio.sleep(0)      # deja que el navegador muestre el mensaje

    velo = pygame.Surface((ANCHO, ALTO))   # deja estelas suaves
    velo.fill(FONDO)
    velo.set_alpha(55)

    estrellas = [(random.uniform(0, ANCHO), random.uniform(0, ALTO), random.uniform(0, 6.28))
                 for _ in range(110)]

    particulas = Particulas(N_PUNTOS)
    gemas = Gemas()
    lago = Lago()
    lotos = Lotos()
    cisnes = Cisnes()
    pajaros = Pajaros()
    indice = 0
    formas = [ajustar(g(), N_PUNTOS) for g in GENERADORES]   # se calculan una vez al inicio
    particulas.nueva_forma(formas[indice], explosion=False)
    t, t_flor = 0.0, 0.0
    pantalla.fill(FONDO)

    def cambiar(paso):
        nonlocal indice, t_flor
        indice = (indice + paso) % len(GENERADORES)
        particulas.nueva_forma(formas[indice])
        t_flor = 0.0

    while True:
        dt = reloj.tick(FPS) / 1000
        t += dt
        t_flor += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_SPACE, pygame.K_RIGHT):
                    cambiar(1)
                elif ev.key == pygame.K_LEFT:
                    cambiar(-1)
                elif ev.key == pygame.K_m and musica:
                    if musica_sonando:
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                    musica_sonando = not musica_sonando
                elif ev.key == pygame.K_s:
                    pygame.image.save(pantalla, "flor.png")

        if t_flor > SEGUNDOS_POR_FLOR:
            cambiar(1)

        pantalla.blit(velo, (0, 0))

        for ex, ey, fase in estrellas:
            b = 0.5 + 0.5 * math.sin(t * 1.5 + fase)
            v = int(60 + 120 * b)
            pantalla.fill((v, v, min(255, v + 40)), (int(ex), int(ey), 1, 1))

        lago.dibujar(pantalla, t, dt)
        lotos.dibujar(pantalla, t, delante=False)
        pajaros.dibujar(pantalla, t, dt)
        gemas.actualizar(t, dt)
        gemas.dibujar(pantalla, t)
        particulas.actualizar(t, dt)
        particulas.dibujar(pantalla, t)
        cisnes.dibujar(pantalla, t, dt)
        lotos.dibujar(pantalla, t, delante=True)

        # textos con aparición gradual (solo al comenzar: es el mismo para todas las flores)
        alfa = int(255 * min(1.0, max(0.0, (t - 1.5) / 2.0)))
        lineas = [(texto, fuente_titulo, 30 + 44 * n, (255, 220, 235)) for n, texto in enumerate(DEDICATORIA)]
        for texto, fuente, y, color in lineas:
            s = fuente.render(texto, True, color)
            s.set_alpha(alfa)
            pantalla.blit(s, (ANCHO / 2 - s.get_width() / 2, y))

        pygame.display.flip()
        await asyncio.sleep(0)  # necesario para que el navegador pueda dibujar cada cuadro


if __name__ == "__main__":
    asyncio.run(main())
