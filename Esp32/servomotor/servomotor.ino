#include "ESP32Servo.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

Servo Traquea;
Servo servoIzq;
Servo servoDer;
int TraqueaPin = 18;
int servoIzqPin = 32;
int servoDerPin = 33;

int memoriaDireccion = 0; // Variable para almacenar la última dirección recibida

TaskHandle_t TaskHandle_servoMovement = NULL;

void moveServos(void * parameter) {
    int direction = (int)parameter;

    // Movimiento hacia derecha (cuando direction == 6)
    if (direction == 6 && memoriaDireccion != 6) {
        Traquea.write(80);
        delay(500);
        Traquea.write(70);
        Serial.println("Girando izquierdo hacia adelante");
        servoIzq.writeMicroseconds(1345);
        Serial.println("Girando derecho hacia atras");
        servoDer.writeMicroseconds(1663);
        delay(1000);
        
    }
    // Movimiento en la dirección contraria (cuando direction == 4)
    else if (direction == 4 && memoriaDireccion != 4) {
        Traquea.write(80);
        delay(500);
        Traquea.write(70);
        Serial.println("Girando izquierdo hacia atras");
        servoIzq.writeMicroseconds(1663);
        Serial.println("Girando derecho hacia adelante");
        servoDer.writeMicroseconds(1345);
        delay(1000);
    }
    else if (direction == 8 && memoriaDireccion != 8) {
        Serial.println("Girando izquierdo hacia abajo");
        servoIzq.writeMicroseconds(1345);
        Serial.println("Girando derecho hacia abajo");
        servoDer.writeMicroseconds(1345);
        Traquea.write(100);
        delay(300);
        Traquea.write(90);
    }
    else if (direction == 2 && memoriaDireccion != 2) {
        Serial.println("Girando izquierdo hacia abajo");
        servoIzq.writeMicroseconds(1663);
        Serial.println("Girando derecho hacia abajo");
        servoDer.writeMicroseconds(1663);
        Traquea.write(60);
        delay(300);
    }else if (direction == 5 && memoriaDireccion != 5)
    {
        switch (memoriaDireccion)
        {
        case 2:
            Serial.println("Regresando de arriba a centro");
            servoIzq.writeMicroseconds(1345);
            servoDer.writeMicroseconds(1345);
            Traquea.write(80);
            delay(150);
            Traquea.write(70);
            break;
        case 8:
            Serial.println("Regresando de abajo a centro");
            servoIzq.writeMicroseconds(1663);
            servoDer.writeMicroseconds(1663);
            Traquea.write(80);
            delay(150);
            Traquea.write(70);
            break;
        case 4:
            Serial.println("Regresando de derecha a centro");
            servoIzq.writeMicroseconds(1663);
            servoDer.writeMicroseconds(1345);
            Traquea.write(80);
            delay(500);
            Traquea.write(70);
            break;
        case 6:
            Serial.println("Regresando de izquierda a centro");
            servoIzq.writeMicroseconds(1345);
            servoDer.writeMicroseconds(1663);
            Traquea.write(80);
            delay(500);
            Traquea.write(70);
            break;
        default:
            Serial.println("Ya en centro, no se necesita mover");
            break;
        }

        
        Serial.println("Centrando cabeza");
        servoIzq.writeMicroseconds(1500);
        servoDer.writeMicroseconds(1500);
        Traquea.write(100);
        delay(300);
        Traquea.write(90);
    }
    
    
    memoriaDireccion = direction; // Actualizamos la última dirección recibida
    Serial.println("Deteniendo ambos servos");
    servoIzq.writeMicroseconds(1500);
    servoDer.writeMicroseconds(1500);

    Serial.println("Movimiento completado. Eliminando tarea.");
    vTaskDelete(NULL); // Elimina la tarea actual
}

void setup() {
    Serial.begin(115200);
    servoIzq.attach(servoIzqPin);
    servoDer.attach(servoDerPin);
    Traquea.attach(TraqueaPin);
    Serial.println("Servo listo. Esperando comandos '2', '4', '6', '8'...");
}

void loop() {
    if (Serial.available()) {
        char command = Serial.read();

        if (command == '4') {
            if (TaskHandle_servoMovement == NULL) {
                Serial.println("Comando '4' recibido. Creando tarea para servos...");
                xTaskCreatePinnedToCore(
                    moveServos,
                    "servo_fwd",
                    2048,
                    (void*)4, // Pasamos el argumento 1 para movimiento hacia adelante
                    1,
                    &TaskHandle_servoMovement,
                    0);
            } else {
                Serial.println("La tarea ya esta activa. Espere a que termine.");
            }
        } else if (command == '6') {
            if (TaskHandle_servoMovement == NULL) {
                Serial.println("Comando '6' recibido. Creando tarea para servos (reverso)...");
                xTaskCreatePinnedToCore(
                    moveServos,
                    "servo_rev",
                    2048,
                    (void*)6, // Pasamos el argumento 6 para movimiento reverso
                    1,
                    &TaskHandle_servoMovement,
                    0);
            } else {
                Serial.println("La tarea ya esta activa. Espere a que termine.");
            }
        } else if (command == '8') {
            if (TaskHandle_servoMovement == NULL) {
                Serial.println("Comando '8' recibido. Creando tarea para servos (reverso)...");
                xTaskCreatePinnedToCore(
                    moveServos,
                    "servo_up",
                    2048,
                    (void*)8, // Pasamos el argumento 8 para movimiento hacia arriba
                    1,
                    &TaskHandle_servoMovement,
                    0);
            } else {
                Serial.println("La tarea ya esta activa. Espere a que termine.");
            }
        } else if (command == '2') {
            if (TaskHandle_servoMovement == NULL) {
                Serial.println("Comando '2' recibido. Creando tarea para servos (reverso)...");
                xTaskCreatePinnedToCore(
                    moveServos,
                    "servo_down",
                    2048,
                    (void*)2, // Pasamos el argumento 2 para movimiento hacia abajo
                    1,
                    &TaskHandle_servoMovement,
                    0);
            } else {
                Serial.println("La tarea ya esta activa. Espere a que termine.");
            }
        }else if (command == '5'){
            if (TaskHandle_servoMovement == NULL) {
                Serial.println("Comando '5' recibido. Creando tarea para servo (centrar)...");
                xTaskCreatePinnedToCore(
                    moveServos,
                    "servo_center",
                    2048,
                    (void*)5, // Pasamos el argumento 2 para movimiento hacia abajo
                    1,
                    &TaskHandle_servoMovement,
                    0);
            } else {
                Serial.println("La tarea ya esta activa. Espere a que termine.");
            }
        }
         else {
            Serial.println("Comando no reconocido.");
        }
    }
    
    // Si la tarea terminó y se eliminó, restablecemos el handle
    if (TaskHandle_servoMovement != NULL && eTaskGetState(TaskHandle_servoMovement) == eDeleted) {
        TaskHandle_servoMovement = NULL;
    }

    delay(10);
}