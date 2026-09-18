# core/facial.py
#
# Responsabilidad: toda la lógica de lectura e interpretación de la cara.
# Recibe landmarks y blendshapes de MediaPipe y produce valores listos
# para enviar al ESP32 o guardar en el estado del robot.
#
# NO conoce el estado del robot ni el ESP32 directamente.
# Devuelve un diccionario con los resultados para que callbacks.py
# decida qué hacer con ellos.
#
# Estructura interna:
#   ProcesadorFacial          ← clase principal, punto de entrada
#   ├── _ProcesadorOjos       ← geometría del iris, oclusión, calibración
#   └── _ProcesadorExpresion  ← blendshapes (mandíbula, mejillas)

import math
import traceback
from utils.filtroPromedio import FiltroEstabilidad


# =============================================================================
# ÍNDICES DE LANDMARKS FACEMESH (478 puntos)
# =============================================================================
# Referencia visual: imagen facemesh adjunta al proyecto.
#
# IRIS (solo disponibles en el modelo full, no en el lite):
#   468 → centro iris izquierdo   473 → centro iris derecho
#   469 → iris izq top             474 → iris der top
#   471 → iris izq bottom          476 → iris der bottom
#
# MARCO OJO IZQUIERDO (puntos fijos del hueso orbitario, no del párpado):
#   226 → esquina exterior (sien)
#   244 → esquina interior (nariz)
#   223 → referencia superior fija
#   230 → referencia inferior fija
#
# MARCO OJO DERECHO:
#   446 → esquina exterior (sien)
#   464 → esquina interior (nariz)
#   444 → referencia superior fija
#   450 → referencia inferior fija
#
# Por qué puntos fijos en vez del párpado:
#   El párpado se mueve al abrir/cerrar el ojo, lo que desplaza el marco
#   de referencia y hace que el iris parezca "arriba" cuando el ojo se
#   entrecierra. Los puntos del hueso orbitario son estables.
#
# BLENDSHAPES USADOS (índices en la lista):
#   25 → jawOpen       (apertura mandíbula)
#   44 → mouthSmileLeft
#   45 → mouthSmileRight

# ── Iris ─────────────────────────────────────────────────────────────────────
_IRIS_IZQ        = 468
_IRIS_DER        = 473
_IRIS_IZQ_TOP    = 469
_IRIS_IZQ_BOT    = 471
_IRIS_DER_TOP    = 474
_IRIS_DER_BOT    = 476

# ── Marco ojo izquierdo ───────────────────────────────────────────────────────
_OJO_IZQ_EXT = 226
_OJO_IZQ_INT = 244
_OJO_IZQ_SUP = 223
_OJO_IZQ_INF = 230

# ── Marco ojo derecho ─────────────────────────────────────────────────────────
_OJO_DER_EXT = 446
_OJO_DER_INT = 464
_OJO_DER_SUP = 444
_OJO_DER_INF = 450

# ── Oclusión ──────────────────────────────────────────────────────────────────
# Si apertura_ojo < diámetro_iris × FACTOR_OCLUSION → lectura no fiable.
_FACTOR_OCLUSION = 0.6

# ── Calibración ───────────────────────────────────────────────────────────────
_FRAMES_CAL = 40   # Frames mirando al frente para calibrar el reposo


# =============================================================================
# RESULTADO ESTANDARIZADO
# =============================================================================
# ProcesadorFacial.procesar() devuelve siempre este diccionario.
# Los valores None indican que no hay dato fiable en este frame.

def _resultado_vacio():
    return {
        # Ojos
        "ojo_horizontal":   None,   # "izquierda" | "centro" | "derecha"
        "ojo_vertical":     None,   # "arriba"    | "centro" | "abajo"
        "ojo_desviacion_H": None,   # float centrado en 0
        "ojo_desviacion_V": None,   # float centrado en 0  ← None hasta calibrar + cambio real
        "ojo_ratio_H_izq":  None,   # float 0..1 (raw, para debug)
        "ojo_ratio_H_der":  None,
        "ojo_ratio_V":      None,
        "ojo_ocluido_izq":  False,
        "ojo_ocluido_der":  False,
        "calibrado":        False,
        # Expresión
        "boca":             None,   # float 0..1
        "mejillaIzq":       None,
        "mejillaDer":       None,
    }


# =============================================================================
# CLASE PÚBLICA
# =============================================================================

class ProcesadorFacial:
    """
    Punto de entrada único para toda la lógica facial.

    Uso en callbacks.py:
        self.facial = ProcesadorFacial()
        ...
        resultado = self.facial.procesar(landmarks, blendshapes)
        if resultado["ojo_horizontal"] == "derecha":
            ...
    """

    def __init__(self):
        self._ojos      = _ProcesadorOjos()
        self._expresion = _ProcesadorExpresion()

    def procesar(self, landmarks: list, blendshapes: list) -> dict:
        """
        Recibe los landmarks y blendshapes de un frame y devuelve
        el diccionario de resultados estandarizado.
        Nunca lanza excepciones hacia afuera.
        """
        resultado = _resultado_vacio()
        try:
            self._ojos.procesar(landmarks, resultado)
            self._expresion.procesar(blendshapes, resultado)
        except IndexError:
            print(
                "[facial] IndexError: no se encontraron puntos de iris (468-477).\n"
                "         Verifica que usas 'face_landmarker.task' completo, no el lite."
            )
        except Exception as e:
            print(f"[facial] Error inesperado: {e}")
            traceback.print_exc()
        return resultado

    def resetear_calibracion(self):
        """Recalibra el reposo del iris. Llama desde la UI."""
        self._ojos.resetear_calibracion()


# =============================================================================
# PROCESADOR DE OJOS (privado)
# =============================================================================

class _ProcesadorOjos:
    """
    Calcula la posición del iris dentro del marco óseo del ojo.
    Maneja oclusión, calibración y filtros de estabilidad.
    """

    def __init__(self):
        self.filtro_H_izq = FiltroEstabilidad(frames_confirmacion=3)
        self.filtro_H_der = FiltroEstabilidad(frames_confirmacion=3)
        self.filtro_V     = FiltroEstabilidad(frames_confirmacion=3)

        # Tolerancias (cuánto debe cambiar la ratio para considerarse un cambio real)
        self._tol_H = 0.04
        # ── FIX 1: tolerancia V más fina que la H ─────────────────────────────
        # El iris se mueve menos verticalmente que horizontalmente porque
        # el párpado recorta antes el marco. Tolerancia más baja = más sensible.
        self._tol_V = 0.02   # era 0.04

        # Umbrales de clasificación (en desviación respecto al reposo)
        self.UMBRAL_H        =  0.12
        self.UMBRAL_V_ARRIBA = -0.03
        self.UMBRAL_V_ABAJO  =  0.03

        # Última lectura fiable (se mantiene durante oclusión)
        self._ultima_H_izq = 0.5
        self._ultima_H_der = 0.5
        self._ultima_V     = 0.5

        # Calibración
        self._cal_frames   = 0
        self._cal_H_izq    = 0.0
        self._cal_H_der    = 0.0
        self._cal_V        = 0.0
        self._calibrado    = False
        self._reposo_H_izq = 0.5
        self._reposo_H_der = 0.5
        self._reposo_V     = 0.5

        # ── FIX 2: última desviación V confirmada por el filtro ───────────────
        # Solo se emite al ESP32 cuando el filtro confirma un cambio real.
        self._ultima_desv_V_confirmada: float | None = None
        self._ultima_desv_H_confirmada: float | None = None

    # ── Entrada principal ─────────────────────────────────────────────────────

    def procesar(self, landmarks: list, resultado: dict):
        """Escribe los campos de ojo en el diccionario resultado."""

        # 1. Extraer landmarks
        iris_izq = landmarks[_IRIS_IZQ]
        iris_der = landmarks[_IRIS_DER]

        marco_izq = (
            landmarks[_OJO_IZQ_EXT],
            landmarks[_OJO_IZQ_INT],
            landmarks[_OJO_IZQ_SUP],
            landmarks[_OJO_IZQ_INF],
        )
        marco_der = (
            landmarks[_OJO_DER_EXT],
            landmarks[_OJO_DER_INT],
            landmarks[_OJO_DER_SUP],
            landmarks[_OJO_DER_INF],
        )

        # 2. Radio del iris (para detectar oclusión)
        radio_izq = _dist2d(landmarks[_IRIS_IZQ_TOP], landmarks[_IRIS_IZQ_BOT]) / 2
        radio_der = _dist2d(landmarks[_IRIS_DER_TOP], landmarks[_IRIS_DER_BOT]) / 2

        # 3. Apertura del ojo (distancia entre referencias sup e inf del marco)
        ext_izq, int_izq, sup_izq, inf_izq = marco_izq
        ext_der, int_der, sup_der, inf_der = marco_der

        apertura_izq = abs(inf_izq.y - sup_izq.y)
        apertura_der = abs(inf_der.y - sup_der.y)

        # 4. Detectar oclusión
        ocluido_izq = apertura_izq < (radio_izq * 2 * _FACTOR_OCLUSION)
        ocluido_der = apertura_der < (radio_der * 2 * _FACTOR_OCLUSION)

        resultado["ojo_ocluido_izq"] = ocluido_izq
        resultado["ojo_ocluido_der"] = ocluido_der

        # Si ambos ojos ocluidos (parpadeo completo) → no actualizar nada
        if ocluido_izq and ocluido_der:
            return

        # 5. Calcular ratios geométricas
        ratio_H_izq = self._ratio_H_izq(iris_izq, ext_izq, int_izq, ocluido_izq)
        ratio_H_der = self._ratio_H_der(iris_der, ext_der, int_der, ocluido_der)
        ratio_V     = self._ratio_V(
            iris_izq, iris_der,
            sup_izq, inf_izq,
            sup_der, inf_der,
            ocluido_izq, ocluido_der,
        )

        # 6. Auto-calibración
        self._calibrar(ratio_H_izq, ratio_H_der, ratio_V)
        resultado["calibrado"] = self._calibrado

        # ── FIX 3: no emitir nada al ESP32 hasta que la calibración termine ──
        # Antes, desv_V se escribía siempre (incluso con reposo_V=0.5 incorrecto),
        # provocando movimientos erráticos durante los primeros 40 frames.
        if not self._calibrado:
            return

        # 7. Desviación respecto al reposo (0 = centro)
        desv_H_izq = self._reposo_H_izq - ratio_H_izq   # izq: ratio baja al mirar derecha
        desv_H_der = self._reposo_H_der - ratio_H_der   # der: ratio baja al mirar derecha
        desv_H     = (desv_H_izq + desv_H_der) / 2
        desv_V     = ratio_V - self._reposo_V            # positivo = abajo

        # 8. Clasificar
        dir_H = self._clasificar_H(desv_H)
        dir_V = self._clasificar_V(desv_V)

        # 9. Escribir resultado
        # Los ratios raw siempre (útil para debug)
        resultado["ojo_ratio_H_izq"]  = ratio_H_izq
        resultado["ojo_ratio_H_der"]  = ratio_H_der
        resultado["ojo_ratio_V"]      = ratio_V

        # ── FIX 4: desviacion_V solo se emite cuando el filtro confirma cambio ─
        # Antes: desv_V se escribía en resultado SIEMPRE, sin pasar por el filtro.
        # Eso hacía que callbacks.py enviara al servo cada frame ruidoso.
        # Ahora: el filtro decide si hay un cambio real; si no lo hay, resultado
        # queda con None y callbacks.py no mueve el servo ese frame.
        h_cambio = False
        if not ocluido_izq and self.filtro_H_izq.a_y_v_float_valor(ratio_H_izq, tolerancia=self._tol_H):
            h_cambio = True
        if not ocluido_der and self.filtro_H_der.a_y_v_float_valor(ratio_H_der, tolerancia=self._tol_H):
            h_cambio = True
        if h_cambio:
            resultado["ojo_horizontal"]   = dir_H
            resultado["ojo_desviacion_H"] = desv_H
            self._ultima_desv_H_confirmada = desv_H

        if self.filtro_V.a_y_v_float_valor(ratio_V, tolerancia=self._tol_V):
            resultado["ojo_vertical"]     = dir_V
            resultado["ojo_desviacion_V"] = desv_V          # ← solo en cambio confirmado
            self._ultima_desv_V_confirmada = desv_V

        # Debug (comenta este bloque cuando ya no lo necesites)
        # self._debug(ratio_H_izq, ratio_H_der, desv_H, desv_V,
        #             dir_H, dir_V, ocluido_izq, ocluido_der,
        #             apertura_izq, radio_izq)

    # ── Cálculo de ratios ─────────────────────────────────────────────────────

    def _ratio_H_izq(self, iris, ext, int_, ocluido) -> float:
        """
        ratio_H ojo izquierdo:
          0.0 → iris en esquina exterior (mira a la izquierda)
          1.0 → iris en esquina interior (mira a la derecha)
        """
        if ocluido:
            return self._ultima_H_izq
        ancho = int_.x - ext.x
        if abs(ancho) < 1e-4:
            return self._ultima_H_izq
        ratio = _clamp((iris.x - ext.x) / ancho)
        self._ultima_H_izq = ratio
        return ratio

    def _ratio_H_der(self, iris, ext, int_, ocluido) -> float:
        """
        ratio_H ojo derecho (espejado respecto al izquierdo):
          0.0 → iris en esquina exterior (mira a la derecha)
          1.0 → iris en esquina interior (mira a la izquierda)
        El signo se invierte en el cálculo de desv_H para que ambos
        apunten en la misma dirección.
        """
        if ocluido:
            return self._ultima_H_der
        ancho = ext.x - int_.x
        if abs(ancho) < 1e-4:
            return self._ultima_H_der
        ratio = _clamp((iris.x - int_.x) / ancho)
        self._ultima_H_der = ratio
        return ratio

    def _ratio_V(self, iris_izq, iris_der,
                 sup_izq, inf_izq,
                 sup_der, inf_der,
                 ocluido_izq, ocluido_der) -> float:
        """
        ratio_V (promedio de los ojos disponibles):
          0.0 → iris arriba del marco
          1.0 → iris abajo del marco
          0.5 → centro
        """
        validas = []
        if not ocluido_izq:
            alto = inf_izq.y - sup_izq.y
            if abs(alto) > 1e-4:
                validas.append(_clamp((iris_izq.y - sup_izq.y) / alto))
        if not ocluido_der:
            alto = inf_der.y - sup_der.y
            if abs(alto) > 1e-4:
                validas.append(_clamp((iris_der.y - sup_der.y) / alto))

        if not validas:
            return self._ultima_V
        ratio = sum(validas) / len(validas)
        self._ultima_V = ratio
        return ratio

    # ── Calibración ───────────────────────────────────────────────────────────

    def _calibrar(self, ratio_H_izq: float, ratio_H_der: float, ratio_V: float):
        if self._calibrado:
            return
        self._cal_frames += 1
        self._cal_H_izq  += ratio_H_izq
        self._cal_H_der  += ratio_H_der
        self._cal_V      += ratio_V
        if self._cal_frames >= _FRAMES_CAL:
            self._reposo_H_izq = self._cal_H_izq / self._cal_frames
            self._reposo_H_der = self._cal_H_der / self._cal_frames
            self._reposo_V     = self._cal_V     / self._cal_frames
            self._calibrado    = True
            print(
                f"[facial] Calibración completa:\n"
                f"  reposo_H_izq={self._reposo_H_izq:.4f}\n"
                f"  reposo_H_der={self._reposo_H_der:.4f}\n"
                f"  reposo_V    ={self._reposo_V:.4f}"
            )

    def resetear_calibracion(self):
        self._cal_frames = self._cal_H_izq = self._cal_H_der = self._cal_V = 0
        self._calibrado  = False
        self._reposo_H_izq = self._reposo_H_der = self._reposo_V = 0.5
        self._ultima_desv_V_confirmada = None
        self._ultima_desv_H_confirmada = None
        print("[facial] Calibración reiniciada — mira al frente")

    # ── Clasificadores ────────────────────────────────────────────────────────

    def _clasificar_H(self, desv: float) -> str:
        if desv > self.UMBRAL_H:
            return "derecha"
        if desv < -self.UMBRAL_H:
            return "izquierda"
        return "centro"

    def _clasificar_V(self, desv: float) -> str:
        if desv > self.UMBRAL_V_ABAJO:
            return "abajo"
        if desv < self.UMBRAL_V_ARRIBA:
            return "arriba"
        return "centro"

    # ── Debug ─────────────────────────────────────────────────────────────────

    def _debug(self, rH_izq, rH_der, dH, dV, dir_H, dir_V,
               ocl_izq, ocl_der, apertura, radio):
        print("─" * 60)
        if not self._calibrado:
            print(f"  [Calibrando {self._cal_frames}/{_FRAMES_CAL}]")
        print(f"  ratioH_izq={rH_izq:.3f}  ratioH_der={rH_der:.3f}")
        print(f"  desv_H={dH:+.4f} ({dir_H})   desv_V={dV:+.4f} ({dir_V})")
        print(f"  ocluido_izq={ocl_izq}  ocluido_der={ocl_der}")
        print(f"  apertura_izq={apertura:.4f}  radio_iris={radio:.4f}")


# =============================================================================
# PROCESADOR DE EXPRESIÓN (privado)
# =============================================================================

class _ProcesadorExpresion:
    """
    Lee los blendshapes de expresión facial (mandíbula, mejillas).
    Los blendshapes siguen siendo la mejor fuente para esto porque
    son invariantes a la rotación de la cabeza (MediaPipe los compensa).
    """

    def __init__(self):
        self.filtro_mandibula  = FiltroEstabilidad(frames_confirmacion=5)
        self.filtro_mejillaIzq = FiltroEstabilidad(frames_confirmacion=5)
        self.filtro_mejillaDer = FiltroEstabilidad(frames_confirmacion=5)
        self._tol = 0.15

    def procesar(self, blendshapes: list, resultado: dict):
        mandibula   = blendshapes[25].score
        mejilla_izq = blendshapes[44].score
        mejilla_der = blendshapes[45].score

        if self.filtro_mandibula.a_y_v_float_valor(mandibula, tolerancia=self._tol):
            resultado["boca"] = mandibula

        if self.filtro_mejillaIzq.a_y_v_float_valor(mejilla_izq, tolerancia=self._tol):
            resultado["mejillaIzq"] = mejilla_izq

        if self.filtro_mejillaDer.a_y_v_float_valor(mejilla_der, tolerancia=self._tol):
            resultado["mejillaDer"] = mejilla_der


# =============================================================================
# FUNCIONES AUXILIARES (módulo-privadas)
# =============================================================================

def _dist2d(p1, p2) -> float:
    """Distancia euclidiana en el plano XY entre dos landmarks."""
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Limita un valor al rango [lo, hi]."""
    return max(lo, min(hi, v))