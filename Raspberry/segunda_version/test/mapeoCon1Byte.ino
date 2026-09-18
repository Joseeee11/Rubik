#include <ESP32Servo.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"

#define NUM_MOTORES 16 // Ajusta esto al número real de motores que envías

// Estructura para configurar cada servo en el ESP32
struct ServoConfig {
  uint8_t pin;
  int pwm_min;
  int pwm_max;
  float grados_a_pwm_factor; // Precalculado en el setup()
};

// ServoConfig hombro =  { 0, 150, 600, 0}; // pin 0, min 150, max 600
ServoConfig OjoIzqVert = { 0,  26,  42, 0}
ServoConfig OjoIzqHori = { 0,  16,  28, 0}
ServoConfig ParpIzqSup = { 0,   6,  42, 0}
ServoConfig ParpIzqInf = { 0,  10,  30, 0}

ServoConfig OjoDerVert = { 0,  16,  46, 0}
ServoConfig OjoDerHori = { 0,   6,  24, 0}
ServoConfig ParpDerSup = { 0,  10,  44, 0}
ServoConfig ParpDerInf = { 0, 170, 150, 0}

// Función rápida para mapear durante la ejecución
int calcularPWM(ServoConfig& motor, uint8_t angulo_solicitado) {
  // Capa de seguridad básica (asumiendo que Python envía 0-180)
  if (angulo_solicitado > 180) angulo_solicitado = 180;
  
  // Mapeo lineal rápido usando el factor precalculado
  return motor.pwm_min + (angulo_solicitado * motor.grados_a_pwm_factor);
}

// Cola de FreeRTOS para pasar los ángulos de forma segura entre tareas
QueueHandle_t colaAngulos;

// Máquina de estados para la lectura Serial
enum EstadoSerial { ESPERANDO_AA, ESPERANDO_55, LEYENDO_DATOS };

void TareaRecibirSerial(void *pvParameters) {
    EstadoSerial estado = ESPERANDO_AA;
    uint8_t indice = 0;
    uint8_t buffer_angulos[NUM_MOTORES];

    for (;;) {
        // Leemos todos los bytes que estén disponibles en el buffer del ESP32
        while (Serial.available() > 0) {
            uint8_t byteRecibido = Serial.read();

            switch (estado) {
                case ESPERANDO_AA:
                    if (byteRecibido == 0xAA) {
                        estado = ESPERANDO_55;
                    }
                    break;

                case ESPERANDO_55:
                    if (byteRecibido == 0x55) {
                        // Sincronización exitosa, preparamos para leer los ángulos
                        estado = LEYENDO_DATOS;
                        indice = 0;
                    } else if (byteRecibido != 0xAA) {
                        // Falsa alarma, volvemos a buscar el primer byte
                        estado = ESPERANDO_AA; 
                    }
                    break;

                case LEYENDO_DATOS:
                    buffer_angulos[indice] = byteRecibido;
                    indice++;

                    // ¿Ya recibimos todos los motores?
                    if (indice >= NUM_MOTORES) {
                        // Enviamos la lista completa a la tarea de motores
                        // El "0" significa que no bloquearemos si la cola está llena
                        xQueueOverwrite(colaAngulos, &buffer_angulos);
                        
                        // Reiniciamos el estado para el próximo paquete
                        estado = ESPERANDO_AA; 
                    }
                    break;
            }
        }
        
        // Liberamos CPU: Si no hay datos, dormimos la tarea 5 milisegundos
        // Esto es VITAL en FreeRTOS para que otras tareas (como el I2C del PCA9685) funcionen.
        vTaskDelay(pdMS_TO_TICKS(5)); 
    }
}

void TareaControlMotores(void *pvParameters) {
    uint8_t angulos_actuales[NUM_MOTORES];

    for (;;) {
        // Esperamos indefinidamente hasta que lleguen nuevos datos por la cola
        if (xQueueReceive(colaAngulos, &angulos_actuales, portMAX_DELAY)) {
            
            // ¡Nuevos ángulos recibidos! 
            for (int i = 0; i < NUM_MOTORES; i++) {
                uint8_t angulo_objetivo = angulos_actuales[i];
                
                // AQUI ENTRA TU CAPA DE SEGURIDAD
                // angulo_objetivo ya está entre 0-180 gracias a Python,
                // pero aquí verificas los límites físicos de PWM.
                // int pwm = calcularPWM(motor[i], angulo_objetivo);
                // PCA.setPWM(pin, 0, pwm);
            }
        }
    }
}

void setup() {
    Serial.begin(921600); // Mismo baudrate que en tu Python

    // Creamos una cola con capacidad para 1 solo array de ángulos
    colaAngulos = xQueueCreate(1, sizeof(uint8_t) * NUM_MOTORES);

    // Creamos las tareas de FreeRTOS
    // La tarea de motores tiene prioridad más alta (2) que la lectura (1)
    xTaskCreatePinnedToCore(TareaControlMotores, "ControlMotores", 2048, NULL, 2, NULL, 1);
    xTaskCreatePinnedToCore(TareaRecibirSerial, "LecturaSerial", 2048, NULL, 1, NULL, 0);

    // configurar servos:
    
    hombro.grados_a_pwm_factor = (hombro.pwm_max - hombro.pwm_min) / 180.0;
}

void loop() {
    // Vacío. Todo se maneja en las tareas de FreeRTOS.
}