# core/expresiones.py
#
# Catálogo de expresiones y miradas de Zoé.
# Los valores de ángulo están calibrados a partir de caraFases.py.
#
# Convención de ángulos:
#   180 = Feliz / Levantado / Arriba / Abierto
#   90  = Neutro / Centro / Descanso
#   0   = Triste / Caído / Abajo / Cerrado
#
# ── MAPA DE MOTORES ──────────────────────────────────────────────────────────
# Ojos y párpados:
#   0  → OjoIzqVert      4  → OjoDerVert
#   1  → OjoIzqHori      5  → OjoDerHori
#   2  → ParpIzqSup      6  → ParpDerSup
#   3  → ParpIzqInf      7  → ParpDerInf
#
# Expresión facial:
#   8  → CejaIzq         12 → CejaDer
#   9  → FrenteNarizIzq  13 → FrenteNarizDer
#   10 → MejillaIzq      14 → MejillaDer
#   11 → LabioSup        15 → Mandibula
# ─────────────────────────────────────────────────────────────────────────────

from services.esp32 import ConexionESP32, NUM_MOTORES

# =============================================================================
# ÍNDICES (por nombre, para legibilidad)
# =============================================================================

M_OJO_IZQ_V      = 0
M_OJO_IZQ_H      = 1
M_PARP_IZQ_SUP   = 2
M_PARP_IZQ_INF   = 3
M_OJO_DER_V      = 4
M_OJO_DER_H      = 5
M_PARP_DER_SUP   = 6
M_PARP_DER_INF   = 7
M_CEJA_IZQ       = 8
M_FRENTE_NAR_IZQ = 9
M_MEJILLA_IZQ    = 10
M_LABIO_SUP      = 11
M_CEJA_DER       = 12
M_FRENTE_NAR_DER = 13
M_MEJILLA_DER    = 14
M_MANDIBULA      = 15

# Nombres de motores para que la IA pueda referenciarlos
NOMBRES_MOTORES = {
    "ojo_izq_vertical":    M_OJO_IZQ_V,
    "ojo_izq_horizontal":  M_OJO_IZQ_H,
    "parpado_izq_sup":     M_PARP_IZQ_SUP,
    "parpado_izq_inf":     M_PARP_IZQ_INF,
    "ojo_der_vertical":    M_OJO_DER_V,
    "ojo_der_horizontal":  M_OJO_DER_H,
    "parpado_der_sup":     M_PARP_DER_SUP,
    "parpado_der_inf":     M_PARP_DER_INF,
    "ceja_izq":            M_CEJA_IZQ,
    "frente_nariz_izq":    M_FRENTE_NAR_IZQ,
    "mejilla_izq":         M_MEJILLA_IZQ,
    "labio_sup":           M_LABIO_SUP,
    "ceja_der":            M_CEJA_DER,
    "frente_nariz_der":    M_FRENTE_NAR_DER,
    "mejilla_der":         M_MEJILLA_DER,
    "mandibula":           M_MANDIBULA,
}

# =============================================================================
# EXPRESIONES PREDEFINIDAS
# Cada expresión es un dict {motor_idx: ángulo}.
# Los motores no listados se mantienen en su valor actual.
# =============================================================================

EXPRESIONES: dict[str, dict[int, int]] = {

    "neutral": {
        M_OJO_IZQ_V:      90, M_OJO_IZQ_H:      90,
        M_PARP_IZQ_SUP:   90, M_PARP_IZQ_INF:   90,
        M_OJO_DER_V:      90, M_OJO_DER_H:      90,
        M_PARP_DER_SUP:   90, M_PARP_DER_INF:   90,
        M_CEJA_IZQ:       90, M_CEJA_DER:       90,
        M_FRENTE_NAR_IZQ: 90, M_FRENTE_NAR_DER: 90,
        M_MEJILLA_IZQ:    90, M_MEJILLA_DER:    90,
        M_LABIO_SUP:      90, M_MANDIBULA:       0,
    },

    # ── Emociones básicas ────────────────────────────────────────────────────

    "feliz": {
        # Mejillas arriba (180), cejas suavemente levantadas (135),
        # labio subido (180), párpados inf suben con la sonrisa (135)
        M_PARP_IZQ_SUP:   90,  M_PARP_IZQ_INF:  135,
        M_PARP_DER_SUP:   90,  M_PARP_DER_INF:  135,
        M_CEJA_IZQ:      135,  M_CEJA_DER:      135,
        M_MEJILLA_IZQ:   180,  M_MEJILLA_DER:   180,
        M_LABIO_SUP:     180,  M_MANDIBULA:      20,
    },

    "triste": {
        # Mejillas caídas (0), labio abajo (0), cejas bajas (45),
        # mirada ligeramente hacia abajo (45), párpados sup bajos (45)
        M_OJO_IZQ_V:      45,  M_OJO_DER_V:     45,
        M_PARP_IZQ_SUP:   45,  M_PARP_IZQ_INF:  90,
        M_PARP_DER_SUP:   45,  M_PARP_DER_INF:  90,
        M_CEJA_IZQ:       45,  M_CEJA_DER:      45,
        M_MEJILLA_IZQ:     0,  M_MEJILLA_DER:    0,
        M_LABIO_SUP:       0,  M_MANDIBULA:      0,
    },

    "enojada": {
        # Cejas muy fruncidas (0), nariz arrugada (0),
        # ojos entrecerrados, labio levantado mostrando tensión
        M_PARP_IZQ_SUP:   45,  M_PARP_IZQ_INF:  135,
        M_PARP_DER_SUP:   45,  M_PARP_DER_INF:  135,
        M_CEJA_IZQ:        0,  M_CEJA_DER:        0,
        M_FRENTE_NAR_IZQ:  0,  M_FRENTE_NAR_DER:  0,
        M_MEJILLA_IZQ:    90,  M_MEJILLA_DER:    90,
        M_LABIO_SUP:     180,  M_MANDIBULA:      10,
    },

    "sorprendida": {
        # Cejas muy arriba (180), ojos muy abiertos (180), boca abierta
        M_OJO_IZQ_V:     130,  M_OJO_DER_V:    130,
        M_PARP_IZQ_SUP:  180,  M_PARP_IZQ_INF:  90,
        M_PARP_DER_SUP:  180,  M_PARP_DER_INF:  90,
        M_CEJA_IZQ:      180,  M_CEJA_DER:      180,
        M_MEJILLA_IZQ:    90,  M_MEJILLA_DER:    90,
        M_LABIO_SUP:      90,  M_MANDIBULA:      60,
    },

    "curiosa": {
        # Cejas muy arriba (180), nariz expandida (180),
        # ojos bien abiertos, mirando ligeramente hacia arriba (140)
        M_OJO_IZQ_V:     140,  M_OJO_DER_V:    140,
        M_PARP_IZQ_SUP:  180,  M_PARP_IZQ_INF:  90,
        M_PARP_DER_SUP:  180,  M_PARP_DER_INF:  90,
        M_CEJA_IZQ:      180,  M_CEJA_DER:      180,
        M_FRENTE_NAR_IZQ:180,  M_FRENTE_NAR_DER:180,
        M_MEJILLA_IZQ:    90,  M_MEJILLA_DER:    90,
        M_LABIO_SUP:      90,  M_MANDIBULA:      10,
    },

    "asustada": {
        # Ojos muy abiertos y mirando arriba, cejas elevadas, boca entreabierta
        M_OJO_IZQ_V:     140,  M_OJO_DER_V:    140,
        M_PARP_IZQ_SUP:  180,  M_PARP_IZQ_INF:  60,
        M_PARP_DER_SUP:  180,  M_PARP_DER_INF:  60,
        M_CEJA_IZQ:      180,  M_CEJA_DER:      180,
        M_MEJILLA_IZQ:    90,  M_MEJILLA_DER:    90,
        M_LABIO_SUP:      90,  M_MANDIBULA:      40,
    },

    "emocionada": {
        # Como feliz pero más intensa: ojos bien abiertos, boca más abierta
        M_OJO_IZQ_V:      90,  M_OJO_DER_V:     90,
        M_PARP_IZQ_SUP:  180,  M_PARP_IZQ_INF:  135,
        M_PARP_DER_SUP:  180,  M_PARP_DER_INF:  135,
        M_CEJA_IZQ:      180,  M_CEJA_DER:      180,
        M_MEJILLA_IZQ:   180,  M_MEJILLA_DER:   180,
        M_LABIO_SUP:     180,  M_MANDIBULA:      50,
    },

    "asco": {
        # Nariz muy arrugada (0), labio subido (180),
        # mejillas algo subidas, ojos muy achinados
        M_PARP_IZQ_SUP:   60,  M_PARP_IZQ_INF:  150,
        M_PARP_DER_SUP:   60,  M_PARP_DER_INF:  150,
        M_CEJA_IZQ:        0,  M_CEJA_DER:        0,
        M_FRENTE_NAR_IZQ:  0,  M_FRENTE_NAR_DER:  0,
        M_MEJILLA_IZQ:   135,  M_MEJILLA_DER:   135,
        M_LABIO_SUP:     180,  M_MANDIBULA:      10,
    },

    "misteriosa": {
        # Ceja izq levantada (180), ceja der fruncida (0),
        # mirada de reojo hacia la derecha, ojos entrecerrados
        M_OJO_IZQ_H:       0,  M_OJO_DER_H:      0,   # reojo derecha
        M_PARP_IZQ_SUP:   60,  M_PARP_IZQ_INF:  120,
        M_PARP_DER_SUP:   60,  M_PARP_DER_INF:  120,
        M_CEJA_IZQ:      180,  M_CEJA_DER:        0,
        M_MEJILLA_IZQ:    90,  M_MEJILLA_DER:    90,
        M_LABIO_SUP:      90,  M_MANDIBULA:       0,
    },

    # ── Acciones puntuales ───────────────────────────────────────────────────

    "parpadeo": {
        # Cierra párpados superiores (0) y los vuelve a abrir — ver GestorExpresiones
        M_PARP_IZQ_SUP:    0,  M_PARP_DER_SUP:   0,
    },

    "guino_izq": {
        # Cierra solo el ojo izquierdo
        M_PARP_IZQ_SUP:    0,  M_PARP_IZQ_INF:  135,
    },

    "guino_der": {
        # Cierra solo el ojo derecho
        M_PARP_DER_SUP:    0,  M_PARP_DER_INF:  135,
    },
}

# =============================================================================
# MIRADAS — overrides de motores de ojo
# =============================================================================

MIRADAS: dict[tuple, dict[int, int]] = {
    # (horizontal, vertical)
    ("izquierda", "arriba"):  {M_OJO_IZQ_H: 180, M_OJO_DER_H: 180, M_OJO_IZQ_V: 140, M_OJO_DER_V: 140},
    ("izquierda", "centro"):  {M_OJO_IZQ_H: 180, M_OJO_DER_H: 180, M_OJO_IZQ_V:  90, M_OJO_DER_V:  90},
    ("izquierda", "abajo"):   {M_OJO_IZQ_H: 180, M_OJO_DER_H: 180, M_OJO_IZQ_V:  45, M_OJO_DER_V:  45},
    ("centro",    "arriba"):  {M_OJO_IZQ_H:  90, M_OJO_DER_H:  90, M_OJO_IZQ_V: 140, M_OJO_DER_V: 140},
    ("centro",    "centro"):  {M_OJO_IZQ_H:  90, M_OJO_DER_H:  90, M_OJO_IZQ_V:  90, M_OJO_DER_V:  90},
    ("centro",    "abajo"):   {M_OJO_IZQ_H:  90, M_OJO_DER_H:  90, M_OJO_IZQ_V:  45, M_OJO_DER_V:  45},
    ("derecha",   "arriba"):  {M_OJO_IZQ_H:   0, M_OJO_DER_H:   0, M_OJO_IZQ_V: 140, M_OJO_DER_V: 140},
    ("derecha",   "centro"):  {M_OJO_IZQ_H:   0, M_OJO_DER_H:   0, M_OJO_IZQ_V:  90, M_OJO_DER_V:  90},
    ("derecha",   "abajo"):   {M_OJO_IZQ_H:   0, M_OJO_DER_H:   0, M_OJO_IZQ_V:  45, M_OJO_DER_V:  45},
}

# =============================================================================
# GESTOR DE EXPRESIONES
# =============================================================================

class GestorExpresiones:
    """
    Aplica expresiones y miradas al ESP32.
    Mantiene sincronizado el array de posiciones compartido.
    """

    def __init__(self, esp32: ConexionESP32, posiciones_actuales: list):
        self.esp32 = esp32
        self.posiciones = posiciones_actuales  # referencia compartida

    # ── Primitivas ────────────────────────────────────────────────────────────

    def enviar_motor(self, indice: int, angulo: int):
        """Envía un único motor al ESP32 y actualiza posiciones."""
        angulo = max(0, min(180, angulo))
        self.esp32.enviar_un_motor(indice, angulo, self.posiciones)

    def enviar_todos(self):
        """Envía el array completo de posiciones al ESP32."""
        self.esp32.enviar_angulos(self.posiciones)

    # ── Expresiones ───────────────────────────────────────────────────────────

    def aplicar_expresion(self, nombre: str, intensidad: float = 1.0):
        """
        Aplica una expresión del catálogo EXPRESIONES.
        intensidad ∈ [0.0, 1.0]: interpola desde neutral hasta la expresión completa.
        """
        expr = EXPRESIONES.get(nombre)
        if expr is None:
            print(f"[Expresiones] Expresión desconocida: '{nombre}'")
            return

        neutro = EXPRESIONES["neutral"]

        for idx, angulo_target in expr.items():
            angulo_neutro = neutro.get(idx, 90)
            angulo_final = int(angulo_neutro + (angulo_target - angulo_neutro) * intensidad)
            self.enviar_motor(idx, angulo_final)

        print(f"[Expresiones] '{nombre}' (intensidad={intensidad:.1f})")

    def aplicar_mirada(self, horizontal: str, vertical: str):
        """Mueve los ojos a la dirección indicada."""
        key = (horizontal, vertical)
        overrides = MIRADAS.get(key)
        if overrides is None:
            print(f"[Expresiones] Mirada desconocida: {key}")
            return
        for idx, angulo in overrides.items():
            self.enviar_motor(idx, angulo)
        print(f"[Expresiones] Mirada → {horizontal}/{vertical}")

    def motor_por_nombre(self, nombre_motor: str, angulo: int):
        """
        Mueve un motor específico referenciado por su nombre semántico.
        Ver NOMBRES_MOTORES para la lista completa.
        """
        idx = NOMBRES_MOTORES.get(nombre_motor)
        if idx is None:
            print(f"[Expresiones] Motor desconocido: '{nombre_motor}'")
            return
        self.enviar_motor(idx, angulo)
        print(f"[Expresiones] Motor '{nombre_motor}' (idx={idx}) → {angulo}°")

    def centrar_todo(self):
        """Devuelve todos los motores a 90° (posición de descanso)."""
        for i in range(NUM_MOTORES):
            self.posiciones[i] = 90
        self.enviar_todos()
        print("[Expresiones] Todos los motores centrados")