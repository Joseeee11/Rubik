// =============================================================================
// Zoe_freeRTOS.ino
// =============================================================================
//
// PROTOCOLO DE COMUNICACIÓN SERIAL (desde Python):
//   [ 0xAA ]      [ 0x55 ] [ angulo_0 ][ angulo_1 ] ... [ angulo_N-1 ]
//   └─ Header (2 bytes) ─┘ └────── 1 byte por motor (0-180) ─────────┘
//
//   - 1 byte por motor: uint8_t, rango 0-180 (Python lo garantiza).
//   - El ESP32 mapea ese ángulo a un pulso PWM real según los límites
//     físicos de cada servo (pwm_min / pwm_max en ServoConfig).
//
//
// DEPENDENCIAS (instalar en Arduino IDE / PlatformIO):
//   - ESP32Servo  (por Kevin Harrington)
//   - Arduino-ESP32 board package
//
// COMPATIBILIDAD PCA9685 (futuro):
//   Busca los bloques marcados con [PCA9685] para saber dónde
//   hacer los cambios cuando tengas la placa.
//   Librería necesaria: Adafruit PWM Servo Driver Library
//
// =============================================================================

#include <ESP32Servo.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

// =============================================================================
// CONFIGURACIÓN GLOBAL — AJUSTA AQUÍ
// =============================================================================

// los puertos I2C son:

// SDA = GPIO 21
// SCL = GPIO 22

// Número de motores que Python envía en cada paquete.
// Debe coincidir exactamente con NUM_MOTORES en services/esp32.py
#define NUM_MOTORES 16

// Baudrate — debe coincidir con BAUD_RATE en services/esp32.py
#define BAUDRATE 921600

// Bytes de sincronización del header
#define HEADER_1 0xAA
#define HEADER_2 0x55

// =============================================================================
// ESTRUCTURA DE CONFIGURACIÓN DE SERVO
// =============================================================================
//
// pwm_min / pwm_max: pulsos en unidades del oscilador interno del ESP32.
//   Con ESP32Servo, los valores son microsegundos (µs).
//   Servo estándar: 500µs (0°) a 2500µs (180°).
//   Ajusta por servo para compensar variaciones mecánicas.
//
// grados_a_pwm_factor: precalculado en setup(), no editar a mano.
//
// [PCA9685] Cuando uses la PCA9685, pwm_min/pwm_max pasarán a ser
//   cuentas de 12 bits (0-4095). El factor se calcula igual.
//   Valor típico: 150 (0°) a 600 (180°) para un servo estándar a 50Hz.

struct ServoConfig {
  uint8_t pin;       // Pin GPIO del ESP32 (ignorado con PCA9685, usa canal)
  int     pwm_min;   // Pulso mínimo en µs (corresponde a 0°)
  int     pwm_max;   // Pulso máximo en µs (corresponde a 180°)
  float   factor;    // Precalculado: (pwm_max - pwm_min) / 180.0
  Servo   servo;     // Objeto de la librería ESP32Servo // Cuidao al usar PCA9685 esto queda inutil
};

// =============================================================================
// DECLARACIÓN DE MOTORES
// =============================================================================
//
// Orden: el índice en este array debe coincidir con el índice que Python
// asigna en callbacks.py (MOTOR_OJO_H = 0, MOTOR_OJO_V = 1, etc.)
//
// Formato: { pin_GPIO, pwm_min_us, pwm_max_us, 0 }
//          El último 0 es el factor, se calcula en setup().
//
// IMPORTANTE: pwm_min puede ser MAYOR que pwm_max si el servo
// está montado al revés (ver ParpDerInf como ejemplo).

ServoConfig motores[NUM_MOTORES] = {
  // idx   pin   min  max factor  // Nombre
  /* 0 */ { 13,  500, 2500, 0 },  // OjoIzqHori
  /* 1 */ { 12,  500, 2500, 0 },  // OjoIzqVert
  /* 2 */ { 14,  500, 2500, 0 },  // ParpIzqSup
  /* 3 */ { 27,  500, 2500, 0 },  // ParpIzqInf
  /* 4 */ { 26,  500, 2500, 0 },  // OjoDerHori
  /* 5 */ { 25,  500, 2500, 0 },  // OjoDerVert
  /* 6 */ { 33,  500, 2500, 0 },  // ParpDerSup
  /* 7 */ { 32,  500, 2500, 0 },  // ParpDerInf (invertido: min>max)
  /* 8 */ { 15,  500, 2500, 0 },  // (libre)
  /* 9 */ { 2,   500, 2500, 0 },  // (libre)
  /* 10 */{ 4,   500, 2500, 0 },  // (libre)
  /* 11 */{ 16,  500, 2500, 0 },  // (libre)
  /* 12 */{ 17,  500, 2500, 0 },  // (libre)
  /* 13 */{ 5,   500, 2500, 0 },  // (libre)
  /* 14 */{ 18,  500, 2500, 0 },  // (libre)
  /* 15 */{ 19,  500, 2500, 0 },  // (libre)
};

// =============================================================================
// FUNCIÓN DE MAPEO DE ÁNGULO A PWM
// =============================================================================

int calcularPWM(ServoConfig& motor, uint8_t angulo) {
  // Python garantiza 0-180, pero por seguridad lo forzamos.
  if (angulo > 180) angulo = 180;
  // Mapeo lineal. Funciona igual con factor negativo (servo invertido).
  return motor.pwm_min + (int)(angulo * motor.factor);
}

// =============================================================================
// [PCA9685] FUNCIÓN EQUIVALENTE PARA LA PLACA DE EXPANSIÓN
// =============================================================================
// Descomenta y adapta cuando tengas la PCA9685.
//
// #include <Adafruit_PWMServoDriver.h>
// Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(0x40); // dirección I2C
//
// // Llama a esto en setup():
// // pca.begin();
// // pca.setPWMFreq(50);  // 50Hz estándar para servos
//
// void moverServoPCA(uint8_t canal, ServoConfig& motor, uint8_t angulo) {
//   if (angulo > 180) angulo = 180;
//   int cuentas = motor.pwm_min + (int)(angulo * motor.factor);
//   // pwm_min/pwm_max deben estar en cuentas 12-bit (ej: 150-600)
//   pca.setPWM(canal, 0, cuentas);
// }

// =============================================================================
// COLA DE FREERTOS
// =============================================================================
//
// xQueueOverwrite: si la cola ya tiene un paquete que no fue procesado,
// lo sobreescribe con el más reciente. Esto es correcto para control
// en tiempo real: nos interesa el estado ACTUAL, no el historial.
// Capacidad 1: siempre hay exactamente un estado "pendiente de aplicar".

QueueHandle_t colaAngulos;

// =============================================================================
// TAREA 1: LECTURA SERIAL (Core 0)
// =============================================================================
//
// Prioridad baja (1). Solo lee bytes y los deposita en la cola.
// No toca los servos nunca.
//
// Máquina de estados:
//   ESPERANDO_AA → ESPERANDO_55 → LEYENDO_DATOS → ESPERANDO_AA

enum EstadoSerial { ESPERANDO_AA, ESPERANDO_55, LEYENDO_DATOS };

void TareaRecibirSerial(void *pvParameters) {
  EstadoSerial estado = ESPERANDO_AA;
  uint8_t indice = 0;
  uint8_t buffer[NUM_MOTORES];

  for (;;) {
    while (Serial.available() > 0) {
      uint8_t b = Serial.read();

      switch (estado) {

        case ESPERANDO_AA:
          if (b == HEADER_1) estado = ESPERANDO_55;
          break;

        case ESPERANDO_55:
          if      (b == HEADER_2) { estado = LEYENDO_DATOS; indice = 0; }
          else if (b != HEADER_1)   estado = ESPERANDO_AA;
          // Si b == HEADER_1 de nuevo, nos quedamos en ESPERANDO_55
          // (podría ser el inicio de un nuevo paquete solapado)
          break;

        case LEYENDO_DATOS:
          buffer[indice++] = b;
          if (indice >= NUM_MOTORES) {
            // Paquete completo: lo mandamos a la tarea de motores.
            // xQueueOverwrite no bloquea y reemplaza el paquete anterior
            // si la tarea de motores aún no lo procesó.
            xQueueOverwrite(colaAngulos, buffer);
            estado = ESPERANDO_AA;
          }
          break;
      }
    }

    // Cede la CPU 5ms. VITAL en FreeRTOS.
    // Si reduces esto aumenta la latencia de respuesta pero consume más CPU.
    vTaskDelay(pdMS_TO_TICKS(5));
  }
}

// =============================================================================
// TAREA 2: CONTROL DE MOTORES (Core 1)
// =============================================================================
//
// Prioridad alta (2). Espera datos en la cola y los aplica a los servos.
// Al tener prioridad mayor, se ejecuta en cuanto llegan datos.

void TareaControlMotores(void *pvParameters) {
  uint8_t angulos[NUM_MOTORES];

  for (;;) {
    // Bloquea hasta que llegue un paquete nuevo (portMAX_DELAY = sin timeout)
    if (xQueueReceive(colaAngulos, angulos, portMAX_DELAY)) {

      for (int i = 0; i < NUM_MOTORES; i++) {
        int pwm = calcularPWM(motores[i], angulos[i]);

        // ── Servo directo ESP32 ────────────────────────────────────────────
        motores[i].servo.writeMicroseconds(pwm);

        // ── [PCA9685] Reemplaza la línea anterior por: ─────────────────────
        // moverServoPCA(i, motores[i], angulos[i]);
        // ──────────────────────────────────────────────────────────────────
      }
    }
  }
}

// =============================================================================
// SETUP
// =============================================================================

void setup() {
  Serial.begin(BAUDRATE);

  // Precalcular factores de mapeo para cada servo.
  // Factor puede ser negativo si pwm_min > pwm_max (servo invertido).
  for (int i = 0; i < NUM_MOTORES; i++) {
    motores[i].factor = (motores[i].pwm_max - motores[i].pwm_min) / 180.0f;
  }

  // Adjuntar servos a sus pines GPIO y definir el rango de pulsos.
  // ESP32Servo necesita el rango explícito para no recortar el movimiento.
  for (int i = 0; i < NUM_MOTORES; i++) {
    int pin_min = min(motores[i].pwm_min, motores[i].pwm_max);
    int pin_max = max(motores[i].pwm_min, motores[i].pwm_max);
    motores[i].servo.attach(motores[i].pin, pin_min, pin_max); // Se usa directamente el ESP32
  }                                                            // Cambia cuando se va usar la PCA9685

  // Cola con capacidad para 1 paquete de ángulos
  colaAngulos = xQueueCreate(1, sizeof(uint8_t) * NUM_MOTORES);

  // Tarea de control en Core 1, prioridad 2 (mayor)
  xTaskCreatePinnedToCore(
    TareaControlMotores, "ControlMotores",
    2048, NULL, 2, NULL, 1
  );

  // Tarea de lectura serial en Core 0, prioridad 1 (menor)
  xTaskCreatePinnedToCore(
    TareaRecibirSerial, "LecturaSerial",
    2048, NULL, 1, NULL, 0
  );

  // [PCA9685] Inicialización de la placa (descomenta cuando la tengas):
  // pca.begin();
  // pca.setPWMFreq(50);
}

// =============================================================================
// LOOP — vacío, FreeRTOS toma el control
// =============================================================================

void loop() {
  // Todo se maneja en las tareas de FreeRTOS.
  // No pongas nada aquí.
  vTaskDelay(portMAX_DELAY);
}
