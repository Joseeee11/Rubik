#include "ESP32Servo.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

Servo servoIzq;
int servoIzqPin = 32;

TaskHandle_t TaskHandle_servoMovement = NULL;

void moveServos(void * parameter) {
    int direction = (int)parameter;

    // Movimiento hacia adelante (cuando direction == 4)
    if (direction >= 500 && direction <= 2500) {
        servoIzq.writeMicroseconds(direction);
        delay(500);
        
    }
    Serial.println("Deteniendo servo");
    servoIzq.writeMicroseconds(1500);
    Serial.println("Movimiento completado. Eliminando tarea.");
    vTaskDelete(NULL); // Elimina la tarea actual
}

void setup() {
    Serial.begin(115200);
    servoIzq.attach(servoIzqPin);
    Serial.println("Servo listo. Esperando comandos entre 500 y 2500 ...");
}

void loop() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        int comandInt = command.toInt(); // Convertir String a int
        if (comandInt >= 500 && comandInt <= 2500) {
            if (TaskHandle_servoMovement == NULL) {
                Serial.println("Comando recibido "+ String(comandInt) +". Creando tarea para servos...");
                xTaskCreatePinnedToCore(
                    moveServos,
                    "moverServo360",
                    2048,
                    (void*)comandInt, // Pasamos el argumento 1 para movimiento hacia adelante
                    1,
                    &TaskHandle_servoMovement,
                    0);
            } else {
                Serial.println("La tarea ya esta activa. Espere a que termine.");
            }
        }
    }
    
    // Si la tarea terminó y se eliminó, restablecemos el handle
    if (TaskHandle_servoMovement != NULL && eTaskGetState(TaskHandle_servoMovement) == eDeleted) {
        TaskHandle_servoMovement = NULL;
    }
    delay(10);
}