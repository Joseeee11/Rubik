# services/esp32.py
#
# Ubicación en el proyecto:
#   robot_humanoide/
#   └── services/
#       └── esp32.py   ← este archivo
#
# Responsabilidad única: todo lo relacionado con la comunicación serial
# con el ESP32. El resto del sistema nunca importa 'serial' directamente.
#
# Compatibilidad: Windows (COMx) y Linux/Raspberry (/dev/ttyUSBx, /dev/ttyACMx)

import serial
import serial.tools.list_ports
import sys
import time
import logging

# =============================================================================
# PROTOCOLO DE PAQUETE
# =============================================================================
#
# Estructura de cada paquete enviado al ESP32:
#
#   [ 0xAA ][ 0x55 ][ ang_0 ][ ang_1 ] ... [ ang_N-1 ]
#   └── Header 2B ──┘└────── 1 byte por motor (0-180) ──┘
#
# - 1 byte por motor: uint8_t, Python lo fuerza al rango 0-180.
# - El ESP32 mapea ese ángulo a µs según los límites físicos del servo.
# - El header 0xAA 0x55 permite resincronización si hay ruido en el serial.
#
# Para aumentar motores en el futuro:
#   1. Cambia NUM_MOTORES aquí.
#   2. Cambia #define NUM_MOTORES en Zoe_freeRTOS.ino.
#   3. Añade los ServoConfig correspondientes en el array motores[] del .ino.
#   El protocolo no cambia estructuralmente, solo crece el payload.

HEADER      = b'\xAA\x55'
NUM_MOTORES = 16       # Debe coincidir con #define NUM_MOTORES en el .ino
BAUD_RATE   = 921600   # Debe coincidir con Serial.begin() en el .ino

ANGULO_MIN = 0
ANGULO_MAX = 180

# Keywords para auto-detección por nombre de puerto según OS
_KEYWORDS_LINUX   = ["ttyUSB", "ttyACM", "ttyS"]
_KEYWORDS_WINDOWS = ["COM"]

# Chips USB-Serial comunes en módulos ESP32
_CHIPS_CONOCIDOS = ["ch340", "ch341", "cp210", "ft232", "ftdi", "esp32", "silicon labs"]

# El ESP32 resetea al abrir el puerto DTR. Esperamos antes de enviar datos.
_RESET_DELAY_S = 2.0

# Tiempo máximo de espera para una escritura serial (segundos).
# Si la escritura tarda más, se considera error de comunicación.
_WRITE_TIMEOUT_S = 1.0

# Número de reintentos al detectar un error de escritura antes de
# intentar reconectar automáticamente.
_MAX_REINTENTOS_ESCRITURA = 3

# Logger del módulo. Usa el sistema de logging estándar de Python para que
# el nivel de verbosidad se controle desde fuera (logging.INFO / DEBUG).
_log = logging.getLogger(__name__)


# =============================================================================
# EXCEPCIONES PROPIAS
# =============================================================================

class ESP32Error(Exception):
    """Error genérico de comunicación con el ESP32."""

class ESP32ConexionError(ESP32Error):
    """No se pudo abrir o mantener la conexión serial."""

class ESP32EnvioError(ESP32Error):
    """El paquete no se pudo escribir en el puerto serial."""

class ESP32ParametroError(ESP32Error):
    """Los parámetros pasados a un método son inválidos."""


# =============================================================================
# CLASE PRINCIPAL
# =============================================================================

class ConexionESP32:
    """
    Maneja la conexión serial con el ESP32 y el envío de paquetes de ángulos.

    Uso típico:
        esp = ConexionESP32()

        # Auto-conexión (busca el primer ESP32 disponible):
        if esp.conectar_automatico():
            angulos = [90] * NUM_MOTORES   # todos al centro
            esp.enviar_angulos(angulos)
            esp.desconectar()

        # O conexión manual a un puerto específico:
        esp.conectar("COM10")          # Windows
        esp.conectar("/dev/ttyUSB0")   # Linux

    Context manager (cierra automáticamente al salir del bloque):
        with ConexionESP32() as esp:
            esp.conectar_automatico()
            esp.enviar_angulos([90] * NUM_MOTORES)
    """

    def __init__(self):
        self._serial: serial.Serial | None = None
        self._puerto: str | None = None
        self._errores_escritura_consecutivos: int = 0

    # ──────────────────────────────────────────────────────────────────────────
    # CONTEXT MANAGER
    # ──────────────────────────────────────────────────────────────────────────

    def __enter__(self) -> "ConexionESP32":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Cierra la conexión al salir del bloque with, incluso si hubo excepción."""
        self.desconectar()
        return False   # No suprime la excepción original

    # ──────────────────────────────────────────────────────────────────────────
    # CONEXIÓN
    # ──────────────────────────────────────────────────────────────────────────

    def conectar(self, puerto: str) -> bool:
        """
        Abre la conexión serial con el ESP32 en el puerto indicado.
        Cierra cualquier conexión previa de forma segura.

        :param puerto: "COM10" en Windows, "/dev/ttyUSB0" en Linux.
        :return: True si la conexión fue exitosa, False si falló.
        :raises ESP32ConexionError: Si se prefiere manejo por excepción.
        """
        if not puerto:
            _log.error("[ESP32] conectar(): puerto vacío.")
            return False

        self.desconectar()
        try:
            self._serial = serial.Serial(
                port         = puerto,
                baudrate     = BAUD_RATE,
                timeout      = 1,
                write_timeout = _WRITE_TIMEOUT_S,
            )
        except serial.SerialException as e:
            _log.error("[ESP32] No se pudo abrir %s: %s", puerto, e)
            self._serial = None
            return False
        except ValueError as e:
            # serial.Serial lanza ValueError si los parámetros son inválidos
            _log.error("[ESP32] Parámetros inválidos para %s: %s", puerto, e)
            self._serial = None
            return False

        # Vaciar el buffer de entrada: el ESP32 puede haber enviado datos
        # residuales del reset de DTR antes de que Python abra el puerto.
        try:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
        except serial.SerialException as e:
            _log.warning("[ESP32] No se pudo vaciar el buffer en %s: %s", puerto, e)
            # No es fatal; continuamos.

        # El ESP32 hace reset al abrir el puerto por DTR.
        # Esperamos a que el bootloader termine antes de enviar datos.
        time.sleep(_RESET_DELAY_S)

        self._puerto = puerto
        self._errores_escritura_consecutivos = 0
        _log.info("[ESP32] Conectado en %s a %d baudios.", puerto, BAUD_RATE)
        return True

    def conectar_automatico(self) -> bool:
        """
        Busca y conecta automáticamente al primer puerto que parezca un ESP32.

        Estrategia (en orden de prioridad):
          1. Filtra por descripción/fabricante de chips conocidos
             (CH340, CP210x, FT232 — los más comunes en módulos ESP32).
          2. Si no identifica por chip, intenta por keyword de nombre de puerto
             según el sistema operativo (ttyUSB/ttyACM en Linux, COM en Windows).

        :return: True si encontró y conectó correctamente.
        """
        try:
            puertos_info = list(serial.tools.list_ports.comports())
        except Exception as e:
            _log.error("[ESP32] Error al listar puertos: %s", e)
            return False

        if not puertos_info:
            _log.warning("[ESP32] No se encontraron puertos seriales disponibles.")
            return False

        # Paso 1: buscar por chip conocido
        candidatos = [
            p.device for p in puertos_info
            if any(
                chip in (p.description or "").lower() or
                chip in (p.manufacturer or "").lower()
                for chip in _CHIPS_CONOCIDOS
            )
        ]
        if candidatos:
            _log.info("[ESP32] Auto-detect por chip: %s", candidatos[0])
            return self.conectar(candidatos[0])

        # Paso 2: buscar por keyword de nombre
        keywords = _KEYWORDS_LINUX if sys.platform != "win32" else _KEYWORDS_WINDOWS
        for p in puertos_info:
            if any(kw in p.device for kw in keywords):
                _log.info("[ESP32] Auto-detect por keyword: %s", p.device)
                if self.conectar(p.device):
                    return True

        _log.warning("[ESP32] Auto-conexión fallida. Usa conectar(puerto) manualmente.")
        return False

    def reconectar(self) -> bool:
        """
        Intenta reconectar al mismo puerto que estaba en uso.
        Útil cuando el ESP32 se reinicia o el cable se desconecta brevemente.

        :return: True si la reconexión fue exitosa.
        """
        if self._puerto is None:
            _log.error("[ESP32] reconectar(): no hay puerto previo registrado.")
            return False

        _log.info("[ESP32] Intentando reconectar en %s...", self._puerto)
        return self.conectar(self._puerto)

    def desconectar(self):
        """Cierra la conexión de forma segura. Nunca lanza excepciones."""
        if self._serial is not None and self._serial.is_open:
            try:
                self._serial.close()
                _log.info("[ESP32] Conexión cerrada (%s).", self._puerto)
            except serial.SerialException as e:
                _log.warning("[ESP32] Error al cerrar la conexión: %s", e)
        self._serial = None

    @property
    def conectado(self) -> bool:
        """True si la conexión está abierta y lista para enviar."""
        return self._serial is not None and self._serial.is_open

    # ──────────────────────────────────────────────────────────────────────────
    # ENVÍO DE DATOS
    # ──────────────────────────────────────────────────────────────────────────

    def enviar_angulos(self, angulos: list[int]) -> bool:
        """
        Envía las posiciones de TODOS los motores en un solo paquete serial.

        El paquete tiene la estructura:
            HEADER (2B) + angulos (1B × NUM_MOTORES)

        :param angulos: Lista de exactamente NUM_MOTORES enteros (0-180).
                        El índice 0 corresponde al motor 0 en el ESP32.
        :return: True si el envío fue exitoso.

        Ejemplo:
            posiciones = [90] * NUM_MOTORES
            posiciones[0] = 45     # motor 0 a 45°
            esp.enviar_angulos(posiciones)
        """
        # ── Validaciones previas ──────────────────────────────────────────────
        if not self.conectado:
            _log.debug("[ESP32] enviar_angulos(): no hay conexión activa.")
            return False

        if not isinstance(angulos, (list, tuple)):
            _log.error("[ESP32] enviar_angulos(): 'angulos' debe ser list o tuple.")
            return False

        if len(angulos) != NUM_MOTORES:
            _log.error(
                "[ESP32] enviar_angulos(): se esperaban %d ángulos, llegaron %d.",
                NUM_MOTORES, len(angulos)
            )
            return False

        # ── Construir payload ─────────────────────────────────────────────────
        try:
            payload = bytes(
                max(ANGULO_MIN, min(ANGULO_MAX, int(a))) for a in angulos
            )
        except (TypeError, ValueError) as e:
            _log.error("[ESP32] enviar_angulos(): ángulo no convertible a int: %s", e)
            return False

        # ── Envío con gestión de errores ──────────────────────────────────────
        try:
            self._serial.write(HEADER + payload)
            self._errores_escritura_consecutivos = 0   # resetear contador de fallos
            return True

        except serial.SerialTimeoutException:
            # El puerto está abierto pero la escritura tardó más de _WRITE_TIMEOUT_S.
            # Suele indicar que el buffer de salida está lleno (envíos demasiado rápidos)
            # o que el ESP32 no procesa datos (colapsado / desconectado físicamente).
            self._errores_escritura_consecutivos += 1
            _log.warning(
                "[ESP32] Timeout de escritura (#%d consecutivo).",
                self._errores_escritura_consecutivos
            )
            self._intentar_reconexion_si_necesario()
            return False

        except serial.SerialException as e:
            self._errores_escritura_consecutivos += 1
            _log.error(
                "[ESP32] Error de escritura (#%d consecutivo): %s",
                self._errores_escritura_consecutivos, e
            )
            # Puerto físicamente desconectado → marcar como cerrado
            self._serial = None
            self._intentar_reconexion_si_necesario()
            return False

        except OSError as e:
            # OSError puede ocurrir en Linux cuando el dispositivo USB desaparece
            self._errores_escritura_consecutivos += 1
            _log.error("[ESP32] OSError al escribir: %s", e)
            self._serial = None
            self._intentar_reconexion_si_necesario()
            return False

    def enviar_un_motor(self, indice: int, angulo: int, estado_actual: list[int]) -> bool:
        """
        Mueve un solo motor sin cambiar los demás.
        Actualiza estado_actual[indice] in-place para que el llamador
        siempre refleje el estado real.

        :param indice:        Índice del motor (0 a NUM_MOTORES-1).
        :param angulo:        Nuevo ángulo (0-180).
        :param estado_actual: Lista completa de ángulos actuales.
        :return: True si el envío fue exitoso.

        Ejemplo:
            estado = [90] * NUM_MOTORES
            esp.enviar_un_motor(MOTOR_OJO_H, 120, estado)
            # estado[MOTOR_OJO_H] ahora vale 120
        """
        if not isinstance(indice, int) or not (0 <= indice < NUM_MOTORES):
            _log.error(
                "[ESP32] enviar_un_motor(): índice %s fuera de rango (0-%d).",
                indice, NUM_MOTORES - 1
            )
            return False

        if len(estado_actual) != NUM_MOTORES:
            _log.error(
                "[ESP32] enviar_un_motor(): estado_actual tiene %d elementos, se esperaban %d.",
                len(estado_actual), NUM_MOTORES
            )
            return False

        estado_actual[indice] = max(ANGULO_MIN, min(ANGULO_MAX, int(angulo)))
        return self.enviar_angulos(estado_actual)

    # ──────────────────────────────────────────────────────────────────────────
    # RECONEXIÓN AUTOMÁTICA (privado)
    # ──────────────────────────────────────────────────────────────────────────

    def _intentar_reconexion_si_necesario(self):
        """
        Intenta reconectar si se alcanzó el umbral de errores consecutivos.
        Llamado internamente después de cada fallo de escritura.
        """
        if self._errores_escritura_consecutivos >= _MAX_REINTENTOS_ESCRITURA:
            _log.warning(
                "[ESP32] %d errores consecutivos. Intentando reconexión...",
                _MAX_REINTENTOS_ESCRITURA
            )
            if self.reconectar():
                _log.info("[ESP32] Reconexión exitosa.")
            else:
                _log.error("[ESP32] Reconexión fallida. Verifica el cable y el puerto.")

    # ──────────────────────────────────────────────────────────────────────────
    # LISTADO DE PUERTOS
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def listar_puertos() -> list[str]:
        """
        Devuelve los nombres de todos los puertos seriales disponibles.
        Compatible con Windows y Linux.

        :return: ["COM3", "COM10"] en Windows
                 ["/dev/ttyUSB0", "/dev/ttyACM0"] en Linux
        """
        try:
            return [p.device for p in serial.tools.list_ports.comports()]
        except Exception as e:
            _log.error("[ESP32] listar_puertos(): error al enumerar puertos: %s", e)
            return []

    @staticmethod
    def listar_puertos_detalle() -> list[dict]:
        """
        Versión extendida con descripción y fabricante.
        Útil para debug o para mostrar información adicional en la UI.

        :return: Lista de dicts: { "puerto", "descripcion", "fabricante" }
        """
        try:
            return [
                {
                    "puerto":      p.device,
                    "descripcion": p.description  or "—",
                    "fabricante":  p.manufacturer or "—",
                }
                for p in serial.tools.list_ports.comports()
            ]
        except Exception as e:
            _log.error("[ESP32] listar_puertos_detalle(): error: %s", e)
            return []

    # ──────────────────────────────────────────────────────────────────────────
    # CONVERSIÓN DE VALORES SEMÁNTICOS A ÁNGULOS
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def desviacion_a_angulo(desviacion: float, rango: float = 0.4) -> int:
        """
        Convierte una desviación normalizada (de facial.py) a un ángulo 0-180.

        :param desviacion: Float centrado en 0. Ej: -0.4 (izq) a +0.4 (der).
        :param rango:      Valor absoluto máximo esperado de desviacion.
        :return:           Entero 0-180.

        Ejemplo en callbacks.py:
            angulo = ConexionESP32.desviacion_a_angulo(r["ojo_desviacion_H"], rango=0.4)
            self.esp32.enviar_un_motor(self.MOTOR_OJO_IZQ_H, angulo, self.posiciones)
        """
        if rango <= 0:
            _log.warning("[ESP32] desviacion_a_angulo(): rango debe ser > 0, usando 0.4.")
            rango = 0.4
        ratio = (desviacion + rango) / (rango * 2)
        return int(max(0.0, min(1.0, ratio)) * 180)

    @staticmethod
    def score_a_angulo(score: float, angulo_max: float = 180.0) -> int:
        """
        Convierte un blendshape score (0.0-1.0) a ángulo (0-angulo_max).

        :param score:      Float 0.0-1.0 (ej: jawOpen de MediaPipe).
        :param angulo_max: Recorrido máximo del servo en grados.
        :return:           Entero 0-angulo_max.

        Ejemplo (mandíbula con rango físico de 45°):
            angulo = ConexionESP32.score_a_angulo(r["boca"], angulo_max=45)
            self.esp32.enviar_un_motor(self.MOTOR_MANDIBULA, angulo, self.posiciones)
        """
        if angulo_max <= 0:
            _log.warning("[ESP32] score_a_angulo(): angulo_max debe ser > 0, usando 180.")
            angulo_max = 180.0
        return int(max(0.0, min(1.0, float(score))) * angulo_max)
