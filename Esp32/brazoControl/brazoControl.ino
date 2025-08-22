#include <ESP32Servo.h>
#include <Bluepad32.h>


ControllerPtr myControllers[BP32_MAX_GAMEPADS];

int servoPinHombroFrontal = 14;// Pin for the HombroFrontal servo
int servoPinHombroSagital = 27; // Pin for the HombroSagital servo
int servoPinHombroTransversal = 26; // Pin for the HombroTransversal servo
int servoPinBicep = 25; // Pin for the Bicep servo
int servoPinMuneca = 33; // Pin for the Muneca servo
int servoPinMano = 32; // Pin for the Mano servo

int posHombroFrontal = 90; // Initial position for HombroFrontal servo
int posHombroSagital = 90; // Initial position for HombroSagital servo
int posHombroTransversal = 90; // Initial position for HombroTransversal servo
int posBicep = 170; // Initial position for Bicep servo
int posMuneca = 90; // Initial position for Muneca servo
int posMano = 180; // Initial position for Mano servo

Servo HombroFrontal;// Create Servo objects to control servo motors
Servo HombroSagital;
Servo HombroTransversal;
Servo Bicep;
Servo Muneca;
Servo Mano;

// Variables
int modoControl = 0; // 0: Control Raspberry, 1: Control de control general, 2: Control de brazo izquierdo
int last_gyroX = 0;
int last_gyroY = 0;
int last_gyroZ = 0;
int last_accelX = 0;
int last_accelY = 0;
int last_accelZ = 0;

unsigned long powerPressedStart = 0;
bool powerWasPressed = false;

unsigned long modeChangeStart = 0;
bool modeChangeActive = false;

// Umbral de giro
const int UMBRAL_GYRO = 200;
// Umbral de aceleración
const int UMBRAL_ACCEL = 200;

// variables de desarrollo
int maximo_registradoGX= 0;
int maximo_registradoGY= 0;
int maximo_registradoGZ= 0;
int maximo_registradoAX= 0;
int maximo_registradoAY= 0;
int maximo_registradoAZ= 0;


// This callback gets called any time a new gamepad is connected.
// Up to 4 gamepads can be connected at the same time.
void onConnectedController(ControllerPtr ctl) {
    bool foundEmptySlot = false;
    for (int i = 0; i < BP32_MAX_GAMEPADS; i++) {
        if (myControllers[i] == nullptr) {
            Serial.printf("CALLBACK: Controller is connected, index=%d\n", i);
            // Additionally, you can get certain gamepad properties like:
            // Model, VID, PID, BTAddr, flags, etc.
            ControllerProperties properties = ctl->getProperties();
            Serial.printf("Controller model: %s, VID=0x%04x, PID=0x%04x\n", ctl->getModelName().c_str(), properties.vendor_id,
                           properties.product_id);
            myControllers[i] = ctl;
            foundEmptySlot = true;
            break;
        }
    }
    if (!foundEmptySlot) {
        Serial.println("CALLBACK: Controller connected, but could not found empty slot");
    }
}
void onDisconnectedController(ControllerPtr ctl) {
    bool foundController = false;

    for (int i = 0; i < BP32_MAX_GAMEPADS; i++) {
        if (myControllers[i] == ctl) {
            Serial.printf("CALLBACK: Controller disconnected from index=%d\n", i);
            myControllers[i] = nullptr;
            foundController = true;
            break;
        }
    }

    if (!foundController) {
        Serial.println("CALLBACK: Controller disconnected, but not found in myControllers");
    }
}

void dumpGamepad(ControllerPtr ctl) {
    int gyroX = ctl->gyroX();
    int gyroY = ctl->gyroY();
    int gyroZ = ctl->gyroZ();
    int accelX = ctl->accelX();
    int accelY = ctl->accelY();
    int accelZ = ctl->accelZ();

    int showGyroX = (abs(gyroX - last_gyroX) > UMBRAL_GYRO) ? (last_gyroX - gyroX) : 0;
    int showGyroY = (abs(gyroY - last_gyroY) > UMBRAL_GYRO) ? (last_gyroY - gyroY) : 0;
    int showGyroZ = (abs(gyroZ - last_gyroZ) > UMBRAL_GYRO) ? (last_gyroZ - gyroZ) : 0;
    int showAccelX = (abs(accelX - last_accelX) > UMBRAL_ACCEL) ? (last_accelX - accelX) : 0;
    int showAccelY = (abs(accelY - last_accelY) > UMBRAL_ACCEL) ? (last_accelY - accelY) : 0;
    int showAccelZ = (abs(accelZ - last_accelZ) > UMBRAL_ACCEL) ? (last_accelZ - accelZ) : 0;

    
    maximo_registradoAX = max(maximo_registradoAX, abs(accelX));
    maximo_registradoAY = max(maximo_registradoAY, abs(accelY));
    maximo_registradoAZ = max(maximo_registradoAZ, abs(accelZ));

    Serial.printf(
        "Acelerometro(gyro) x:%6d y:%6d z:%6d, giroscopo(accel) x:%6d y:%6d z:%6d,---ESTABLE Acelerometro(gyro) x:%6d y:%6d z:%6d, giroscopo(accel) x:%6d y:%6d z:%6d---DEV maximo acele(gyro) x:%8d y:%8d z:%8d, maximo giro(acce) x:%8d y:%8d z:%8d power  ---",
        showGyroX,
        showGyroY,
        showGyroZ,
        showAccelX,
        showAccelY,
        showAccelZ,
        gyroX,
        gyroY,
        gyroZ,
        accelX,
        accelY,
        accelZ,
        maximo_registradoAX,
        maximo_registradoAY,
        maximo_registradoAZ,
        maximo_registradoGX,
        maximo_registradoGY,
        maximo_registradoGZ
    );

    last_gyroX = gyroX;
    last_gyroY = gyroY;
    last_gyroZ = gyroZ;
    last_accelX = accelX;
    last_accelY = accelY;
    last_accelZ = accelZ;


    // Mostrar estado de L1, L2, R1, R2 por Serial
    Serial.print("L1: ");
    Serial.print((ctl->buttons() & BUTTON_SHOULDER_L) ? "on" : "off");
    Serial.print(" | L2: ");
    Serial.print((ctl->buttons() & BUTTON_TRIGGER_L) ? "on" : "off");
    Serial.print(" | R1: ");
    Serial.print((ctl->buttons() & BUTTON_SHOULDER_R) ? "on" : "off");
    Serial.print(" | R2: ");
    Serial.println((ctl->buttons() & BUTTON_TRIGGER_R) ? "on" : "off");
}


void processGamepad(ControllerPtr ctl) {
    // There are different ways to query whether a button is pressed.
    // By query each button individually:
    //  a(), b(), x(), y(), l1(), etc...

    // Example: Move the HombroFrontal servo based on the left Y axis of the gamepad
    if (modoControl == 1)
    {
        if ((ctl->buttons() & BUTTON_SHOULDER_L) && (ctl->buttons() & BUTTON_SHOULDER_R) && !(ctl->buttons() & BUTTON_TRIGGER_R) && !(ctl->buttons() & BUTTON_TRIGGER_L)){
            // Solo hombros
            if (ctl->axisX() <= -100) {
                posHombroFrontal = posHombroFrontal - (map(ctl->axisX(), -512, -100, 5, 1));
                if (posHombroFrontal < 0) posHombroFrontal = 0; // Limit to minimum position
                HombroFrontal.write(posHombroFrontal);
                Serial.println("HombroFrontal moved to " + String(posHombroFrontal) + " degrees");
            } else if (ctl->axisX() >= 100) {
                posHombroFrontal = posHombroFrontal + (map(ctl->axisX(), 100, 512, 1, 5));
                if (posHombroFrontal > 180) posHombroFrontal = 180; // Limit to maximum position
                HombroFrontal.write(posHombroFrontal);
                Serial.println("HombroFrontal moved to " + String(posHombroFrontal) + " degrees");
            }
            if (ctl->axisY() <= -100) {
                posHombroSagital = posHombroSagital - (map(ctl->axisY(), -512, -100, 5, 1));
                if (posHombroSagital < 0) posHombroSagital = 0; // Limit to minimum position
                Bicep.write(posHombroSagital);
                Serial.println("HombroSagital moved to " + String(posHombroSagital) + " degrees");
            } else if (ctl->axisY() >= 100) {
                posHombroSagital = posHombroSagital + (map(ctl->axisY(), 100, 512, 1, 5));
                if (posHombroSagital > 180) posHombroSagital = 180; // Limit to maximum position
                Bicep.write(posHombroSagital);
                Serial.println("HombroSagital moved to " + String(posHombroSagital) + " degrees");
            }

        // en axisX y axisY el hombro derecho (cuando ya este impreso)
        }
        if ((ctl->buttons() & BUTTON_SHOULDER_L) && !(ctl->buttons() & BUTTON_SHOULDER_R) && !(ctl->buttons() & BUTTON_TRIGGER_R) && !(ctl->buttons() & BUTTON_TRIGGER_L)){
            // solo hombro izquierdo
            if (ctl->axisX() <= -100) {
                posHombroFrontal = posHombroFrontal - (map(ctl->axisX(), -512, -100, 5, 1));
                if (posHombroFrontal < 0) posHombroFrontal = 0; // Limit to minimum position
                HombroFrontal.write(posHombroFrontal);
                Serial.println("HombroFrontal moved to " + String(posHombroFrontal) + " degrees");
            } else if (ctl->axisX() >= 100) {
                posHombroFrontal = posHombroFrontal + (map(ctl->axisX(), 100, 512, 1, 5));
                if (posHombroFrontal > 180) posHombroFrontal = 180; // Limit to maximum position
                HombroFrontal.write(posHombroFrontal);
                Serial.println("HombroFrontal moved to " + String(posHombroFrontal) + " degrees");
            }
            if (ctl->axisY() <= -100) {
                posHombroSagital = posHombroSagital - (map(ctl->axisY(), -512, -100, 5, 1));
                if (posHombroSagital < 0) posHombroSagital = 0; // Limit to minimum position
                Bicep.write(posHombroSagital);
                Serial.println("HombroSagital moved to " + String(posHombroSagital) + " degrees");
            } else if (ctl->axisY() >= 100) {
                posHombroSagital = posHombroSagital + (map(ctl->axisY(), 100, 512, 1, 5));
                if (posHombroSagital > 180) posHombroSagital = 180; // Limit to maximum position
                Bicep.write(posHombroSagital);
                Serial.println("HombroSagital moved to " + String(posHombroSagital) + " degrees");
            }
        }
        if ((ctl->buttons() & BUTTON_SHOULDER_L) && (ctl->buttons() & BUTTON_TRIGGER_L) && !(ctl->buttons() & BUTTON_SHOULDER_R) && !(ctl->buttons() & BUTTON_TRIGGER_R)) {
            // Solo hombro izquierdo (completo con HombroFrontal, HombroSagital, HombroTransversal) y bicep, muñeca y mano el joystick secundario (axisR)
                if (ctl->axisX() <= -100) {
                posHombroFrontal = posHombroFrontal - (map(ctl->axisX(), -512, -100, 5, 1));
                if (posHombroFrontal < 0) posHombroFrontal = 0; // Limit to minimum position
                HombroFrontal.write(posHombroFrontal);
                Serial.println("HombroFrontal moved to " + String(posHombroFrontal) + " degrees");
            } else if (ctl->axisX() >= 100) {
                posHombroFrontal = posHombroFrontal + (map(ctl->axisX(), 100, 512, 1, 5));
                if (posHombroFrontal > 180) posHombroFrontal = 180; // Limit to maximum position
                HombroFrontal.write(posHombroFrontal);
                Serial.println("HombroFrontal moved to " + String(posHombroFrontal) + " degrees");
            }
            if (ctl->axisY() <= -100) {
                posHombroSagital = posHombroSagital - (map(ctl->axisY(), -512, -100, 5, 1));
                if (posHombroSagital < 0) posHombroSagital = 0; // Limit to minimum position
                HombroSagital.write(posHombroSagital);
                Serial.println("HombroSagital moved to " + String(posHombroSagital) + " degrees");
            } else if (ctl->axisY() >= 100) {
                posHombroSagital = posHombroSagital + (map(ctl->axisY(), 100, 512, 1, 5));
                if (posHombroSagital > 180) posHombroSagital = 180; // Limit to maximum position
                HombroSagital.write(posHombroSagital);
                Serial.println("HombroSagital moved to " + String(posHombroSagital) + " degrees");
            }
            if (ctl->axisRX() <= -100) {
                posHombroTransversal = posHombroTransversal - (map(ctl->axisRX(), -512, -100, 5, 1));
                if (posHombroTransversal < 0) posHombroTransversal = 0; // Limit to minimum position
                HombroTransversal.write(posHombroTransversal);
                Serial.println("HombroTransversal moved to " + String(posHombroTransversal) + " degrees");
            } else if (ctl->axisRX() >= 100) {
                posHombroTransversal = posHombroTransversal + (map(ctl->axisRX(), 100, 512, 1, 5));
                if (posHombroTransversal > 180) posHombroTransversal = 180; // Limit to maximum position
                HombroTransversal.write(posHombroTransversal);
                Serial.println("HombroTransversal moved to " + String(posHombroTransversal) + " degrees");
            }
            if (ctl->axisRY() <= -100) {
                posBicep = posBicep - (map(ctl->axisRY(), -512, -100, 5, 1));
                if (posBicep < 0) posBicep = 0; // Limit to minimum position
                Bicep.write(posBicep);
                Serial.println("Bicep moved to " + String(posBicep) + " degrees");
            } else if (ctl->axisRY() >= 100) {
                posBicep = posBicep + (map(ctl->axisRY(), 100, 512, 1, 5));
                if (posBicep > 170) posBicep = 170; // Limit to maximum position
                Bicep.write(posBicep);
                Serial.println("Bicep moved to " + String(posBicep) + " degrees");
            }
            
            if ((ctl->buttons() & BUTTON_A) && !(ctl->buttons() & BUTTON_B)) { // Cerrar mano
                Serial.print("Cerrar mano");
                posMano = posMano + 1;
                if (posMano > 180) posMano = 180;
                Mano.write(posMano);
            }
            if ((ctl->buttons() & BUTTON_B) && !(ctl->buttons() & BUTTON_A)) { // Abrir mano
                Serial.print("Abrir mano");
                posMano = posMano - 1;
                if (posMano < 0) posMano = 0;
                Mano.write(posMano);
            }
            if ((ctl->buttons() & BUTTON_X) && !(ctl->buttons() & BUTTON_Y)) { // rotar muñeca reloj
                posMuneca = posMuneca + 1;
                if (posMuneca > 180) posMuneca = 180;
                Muneca.write(posMuneca);
            }
            if ((ctl->buttons() & BUTTON_Y) && !(ctl->buttons() & BUTTON_X)) { // rotar muñeca contrarreloj
                posMuneca = posMuneca - 1;
                if (posMuneca < 0) posMuneca = 0;
                Muneca.write(posMuneca);
            }

            // Comandos inválidos
            if ((ctl->buttons() & BUTTON_A) && (ctl->buttons() & BUTTON_B)) { // Vibrar de comando invalido
                Serial.print("Comando invalido A + B");
                ctl->playDualRumble(0, 250, 0x80, 0x40);
            } else if ((ctl->buttons() & BUTTON_X) && (ctl->buttons() & BUTTON_Y)) { // Vibrar de comando invalido
                Serial.print("Comando invalido X + Y");
                ctl->playDualRumble(0, 250, 0x80, 0x40);
            } else {
                    // No vibrar
            }
        }
        if ((ctl->buttons() & BUTTON_TRIGGER_L) && !(ctl->buttons() & BUTTON_TRIGGER_R) && !(ctl->buttons() & BUTTON_SHOULDER_L) && !(ctl->buttons() & BUTTON_SHOULDER_R)) {
            // la con l2 se controla solo biceps, muñeca, mano(A y B) con joystick primario (axis)

            if (ctl->axisX() <= -100){
                posHombroTransversal = posHombroTransversal - (map(ctl->axisX(), -512, -100, 5, 1));
                if (posHombroTransversal < 0) posHombroTransversal = 0; // Limit to minimum position
                HombroTransversal.write(posHombroTransversal);
                Serial.println("HombroTransversal moved to " + String(posHombroTransversal) + " degrees");
            } else if (ctl->axisX() >= 100) {
                posHombroTransversal = posHombroTransversal + (map(ctl->axisX(), 100, 512, 1, 5));
                if (posHombroTransversal > 180) posHombroTransversal = 180; // Limit to maximum position
                HombroTransversal.write(posHombroTransversal);
                Serial.println("HombroTransversal moved to " + String(posHombroTransversal) + " degrees");
            }
            if (ctl->axisY() <= -100) {
                posBicep = posBicep - (map(ctl->axisY(), -512, -100, 5, 1));
                if (posBicep < 0) posBicep = 0; // Limit to minimum position
                Bicep.write(posBicep);
                Serial.println("Bicep moved to " + String(posBicep) + " degrees");
            } else if (ctl->axisY() >= 100) {
                posBicep = posBicep + (map(ctl->axisY(), 100, 512, 1, 5));
                if (posBicep > 170) posBicep = 170; // Limit to maximum position
                Bicep.write(posBicep);
                Serial.println("Bicep moved to " + String(posBicep) + " degrees");
            }
            if ((ctl->buttons() & BUTTON_A) && !(ctl->buttons() & BUTTON_B)) { // Cerrar mano
                Serial.print("Cerrar mano");
                posMano = posMano + 1;
                if (posMano > 180) posMano = 180;
                Mano.write(posMano);
            }
            if ((ctl->buttons() & BUTTON_B) && !(ctl->buttons() & BUTTON_A)) { // Abrir mano
                Serial.print("Abrir mano");
                posMano = posMano - 1;
                if (posMano < 0) posMano = 0;
                Mano.write(posMano);
            }
            if ((ctl->buttons() & BUTTON_X) && !(ctl->buttons() & BUTTON_Y)) { // rotar muñeca reloj
                posMuneca = posMuneca + 1;
                if (posMuneca > 180) posMuneca = 180;
                Muneca.write(posMuneca);
            }
            if ((ctl->buttons() & BUTTON_Y) && !(ctl->buttons() & BUTTON_X)) { // rotar muñeca contrarreloj
                posMuneca = posMuneca - 1;
                if (posMuneca < 0) posMuneca = 0;
                Muneca.write(posMuneca);
            }

            // Comandos inválidos
            if ((ctl->buttons() & BUTTON_A) && (ctl->buttons() & BUTTON_B)) { // Vibrar de comando invalido
                Serial.print("Comando invalido A + B");
                ctl->playDualRumble(0, 250, 0x80, 0x40);
            } else if ((ctl->buttons() & BUTTON_X) && (ctl->buttons() & BUTTON_Y)) { // Vibrar de comando invalido
                Serial.print("Comando invalido X + Y");
                ctl->playDualRumble(0, 250, 0x80, 0x40);
            } else {
                    // No vibrar
            }
        }
        if ((ctl->buttons() & BUTTON_TRIGGER_L) && (ctl->buttons() & BUTTON_TRIGGER_R) && !(ctl->buttons() & BUTTON_SHOULDER_L) && !(ctl->buttons() & BUTTON_SHOULDER_R))
        {
            if (ctl->axisX() <= -100){
                posHombroTransversal = posHombroTransversal - (map(ctl->axisX(), -512, -100, 5, 1));
                if (posHombroTransversal < 0) posHombroTransversal = 0; // Limit to minimum position
                HombroTransversal.write(posHombroTransversal);
                Serial.println("HombroTransversal moved to " + String(posHombroTransversal) + " degrees");
            } else if (ctl->axisX() >= 100) {
                posHombroTransversal = posHombroTransversal + (map(ctl->axisX(), 100, 512, 1, 5));
                if (posHombroTransversal > 180) posHombroTransversal = 180; // Limit to maximum position
                HombroTransversal.write(posHombroTransversal);
                Serial.println("HombroTransversal moved to " + String(posHombroTransversal) + " degrees");
            }
            if (ctl->axisY() <= -100) {
                posBicep = posBicep - (map(ctl->axisY(), -512, -100, 5, 1));
                if (posBicep < 0) posBicep = 0; // Limit to minimum position
                Bicep.write(posBicep);
                Serial.println("Bicep moved to " + String(posBicep) + " degrees");
            } else if (ctl->axisY() >= 100) {
                posBicep = posBicep + (map(ctl->axisY(), 100, 512, 1, 5));
                if (posBicep > 170) posBicep = 170; // Limit to maximum position
                Bicep.write(posBicep);
                Serial.println("Bicep moved to " + String(posBicep) + " degrees");
            }
            if ((ctl->buttons() & BUTTON_A) && !(ctl->buttons() & BUTTON_B)) { // Cerrar mano
                Serial.print("Cerrar mano");
                posMano = posMano + 1;
                if (posMano > 180) posMano = 180;
                Mano.write(posMano);
            }
            if ((ctl->buttons() & BUTTON_B) && !(ctl->buttons() & BUTTON_A)) { // Abrir mano
                Serial.print("Abrir mano");
                posMano = posMano - 1;
                if (posMano < 0) posMano = 0;
                Mano.write(posMano);
            }
            if ((ctl->buttons() & BUTTON_X) && !(ctl->buttons() & BUTTON_Y)) { // rotar muñeca reloj
                posMuneca = posMuneca + 1;
                if (posMuneca > 180) posMuneca = 180;
                Muneca.write(posMuneca);
            }
            if ((ctl->buttons() & BUTTON_Y) && !(ctl->buttons() & BUTTON_X)) { // rotar muñeca contrarreloj
                posMuneca = posMuneca - 1;
                if (posMuneca < 0) posMuneca = 0;
                Muneca.write(posMuneca);
            }

            // Comandos inválidos
            if ((ctl->buttons() & BUTTON_A) && (ctl->buttons() & BUTTON_B)) { // Vibrar de comando invalido
                Serial.print("Comando invalido A + B");
                ctl->playDualRumble(0, 250, 0x80, 0x40);
            } else if ((ctl->buttons() & BUTTON_X) && (ctl->buttons() & BUTTON_Y)) { // Vibrar de comando invalido
                Serial.print("Comando invalido X + Y");
                ctl->playDualRumble(0, 250, 0x80, 0x40);
            } else {
                    // No vibrar
            }

            // Falta el brazo derecho
        }
        if ((ctl->buttons() & BUTTON_TRIGGER_L) && (ctl->buttons() & BUTTON_SHOULDER_R) && !(ctl->buttons() & BUTTON_TRIGGER_R) && !(ctl->buttons() & BUTTON_SHOULDER_L) )
        {
            if (ctl->axisX() <= -100){
                posHombroTransversal = posHombroTransversal - (map(ctl->axisX(), -512, -100, 5, 1));
                if (posHombroTransversal < 0) posHombroTransversal = 0; // Limit to minimum position
                HombroTransversal.write(posHombroTransversal);
                Serial.println("HombroTransversal moved to " + String(posHombroTransversal) + " degrees");
            } else if (ctl->axisX() >= 100) {
                posHombroTransversal = posHombroTransversal + (map(ctl->axisX(), 100, 512, 1, 5));
                if (posHombroTransversal > 180) posHombroTransversal = 180; // Limit to maximum position
                HombroTransversal.write(posHombroTransversal);
                Serial.println("HombroTransversal moved to " + String(posHombroTransversal) + " degrees");
            }
            if (ctl->axisY() <= -100) {
                posBicep = posBicep - (map(ctl->axisY(), -512, -100, 5, 1));
                if (posBicep < 0) posBicep = 0; // Limit to minimum position
                Bicep.write(posBicep);
                Serial.println("Bicep moved to " + String(posBicep) + " degrees");
            } else if (ctl->axisY() >= 100) {
                posBicep = posBicep + (map(ctl->axisY(), 100, 512, 1, 5));
                if (posBicep > 170) posBicep = 170; // Limit to maximum position
                Bicep.write(posBicep);
                Serial.println("Bicep moved to " + String(posBicep) + " degrees");
            }
            if ((ctl->buttons() & BUTTON_A) && !(ctl->buttons() & BUTTON_B)) { // Cerrar mano
                Serial.print("Cerrar mano");
                posMano = posMano + 1;
                if (posMano > 180) posMano = 180;
                Mano.write(posMano);
            }
            if ((ctl->buttons() & BUTTON_B) && !(ctl->buttons() & BUTTON_A)) { // Abrir mano
                Serial.print("Abrir mano");
                posMano = posMano - 1;
                if (posMano < 0) posMano = 0;
                Mano.write(posMano);
            }
            if ((ctl->buttons() & BUTTON_X) && !(ctl->buttons() & BUTTON_Y)) { // rotar muñeca reloj
                posMuneca = posMuneca + 1;
                if (posMuneca > 180) posMuneca = 180;
                Muneca.write(posMuneca);
            }
            if ((ctl->buttons() & BUTTON_Y) && !(ctl->buttons() & BUTTON_X)) { // rotar muñeca contrarreloj
                posMuneca = posMuneca - 1;
                if (posMuneca < 0) posMuneca = 0;
                Muneca.write(posMuneca);
            }

            // Comandos inválidos
            if ((ctl->buttons() & BUTTON_A) && (ctl->buttons() & BUTTON_B)) { // Vibrar de comando invalido
                Serial.print("Comando invalido A + B");
                ctl->playDualRumble(0, 250, 0x80, 0x40);
            } else if ((ctl->buttons() & BUTTON_X) && (ctl->buttons() & BUTTON_Y)) { // Vibrar de comando invalido
                Serial.print("Comando invalido X + Y");
                ctl->playDualRumble(0, 250, 0x80, 0x40);
            } else {
                    // No vibrar
            }

            // Falta el brazo derecho
        }
        if ((ctl->buttons() & BUTTON_TRIGGER_R) && !(ctl->buttons() & BUTTON_TRIGGER_L) && !(ctl->buttons() & BUTTON_SHOULDER_L) && !(ctl->buttons() & BUTTON_SHOULDER_R)) {
            // Falta el brazo derecho
        }
        if ((ctl->buttons() & BUTTON_TRIGGER_R) && (ctl->buttons() & BUTTON_SHOULDER_R) && !(ctl->buttons() & BUTTON_TRIGGER_L) && !(ctl->buttons() & BUTTON_SHOULDER_L))
        {
            // Falta el brazo derecho
        }
        if ((ctl->buttons() & BUTTON_SHOULDER_R) && !(ctl->buttons() & BUTTON_SHOULDER_L) && !(ctl->buttons() & BUTTON_TRIGGER_R) && !(ctl->buttons() & BUTTON_TRIGGER_L))
        {
            // Falta el brazo derecho
        }
    }
    if (modoControl == 2)
    {
        if (ctl->axisX() <= -100) {
            posHombroFrontal = posHombroFrontal + (map(ctl->axisX(), -512, -100, 5, 1));
            if (posHombroFrontal > 180) posHombroFrontal = 180; // Limit to maximum position
            HombroFrontal.write(posHombroFrontal);
            Serial.println("HombroFrontal moved to " + String(posHombroFrontal) + " degrees");
        } else if (ctl->axisX() >= 100) {
            posHombroFrontal = posHombroFrontal - (map(ctl->axisX(), 100, 512, 1, 5));
            if (posHombroFrontal < 0) posHombroFrontal = 0; // Limit to minimum position
            HombroFrontal.write(posHombroFrontal);
            Serial.println("HombroFrontal moved to " + String(posHombroFrontal) + " degrees");
        }
        if (ctl->axisY() <= -100) {
            posHombroSagital = posHombroSagital - (map(ctl->axisY(), -512, -100, 5, 1));
            if (posHombroSagital < 0) posHombroSagital = 0; // Limit to minimum position
            HombroSagital.write(posHombroSagital);
            Serial.println("HombroSagital moved to " + String(posHombroSagital) + " degrees");
        } else if (ctl->axisY() >= 100) {
            posHombroSagital = posHombroSagital + (map(ctl->axisY(), 100, 512, 1, 5));
            if (posHombroSagital > 180) posHombroSagital = 180; // Limit to maximum position
            HombroSagital.write(posHombroSagital);
            Serial.println("HombroSagital moved to " + String(posHombroSagital) + " degrees");
        }
        if (ctl->axisRX() <= -100) {
            posHombroTransversal = posHombroTransversal - (map(ctl->axisRX(), -512, -100, 5, 1));
            if (posHombroTransversal < 0) posHombroTransversal = 0; // Limit to minimum position
            HombroTransversal.write(posHombroTransversal);
            Serial.println("HombroTransversal moved to " + String(posHombroTransversal) + " degrees");
        } else if (ctl->axisRX() >= 100) {
            posHombroTransversal = posHombroTransversal + (map(ctl->axisRX(), 100, 512, 1, 5));
            if (posHombroTransversal > 180) posHombroTransversal = 180; // Limit to maximum position
            HombroTransversal.write(posHombroTransversal);
            Serial.println("HombroTransversal moved to " + String(posHombroTransversal) + " degrees");
        }
        if (ctl->axisRY() <= -100) {
            posBicep = posBicep - (map(ctl->axisRY(), -512, -100, 5, 1));
            if (posBicep < 0) posBicep = 0; // Limit to minimum position
            Bicep.write(posBicep);
            Serial.println("Bicep moved to " + String(posBicep) + " degrees");
        } else if (ctl->axisRY() >= 100) {
            posBicep = posBicep + (map(ctl->axisRY(), 100, 512, 1, 5));
            if (posBicep > 170) posBicep = 170; // Limit to maximum position
            Bicep.write(posBicep);
            Serial.println("Bicep moved to " + String(posBicep) + " degrees");
        }
        if ((ctl->buttons() & BUTTON_A) && !(ctl->buttons() & BUTTON_B)) { // Cerrar mano
        Serial.print("Cerrar mano");
        posMano = posMano + 1;
        if (posMano > 180) posMano = 180;
        Mano.write(posMano);
        }
        if ((ctl->buttons() & BUTTON_B) && !(ctl->buttons() & BUTTON_A)) { // Abrir mano
            Serial.print("Abrir mano");
            posMano = posMano - 1;
            if (posMano < 0) posMano = 0;
            Mano.write(posMano);
        }
        if ((ctl->buttons() & BUTTON_X) && !(ctl->buttons() & BUTTON_Y)) { // rotar muñeca reloj
            posMuneca = posMuneca + 1;
            if (posMuneca > 180) posMuneca = 180;
            Muneca.write(posMuneca);
        }
        if ((ctl->buttons() & BUTTON_Y) && !(ctl->buttons() & BUTTON_X)) { // rotar muñeca contrarreloj
            posMuneca = posMuneca - 1;
            if (posMuneca < 0) posMuneca = 0;
            Muneca.write(posMuneca);
        }

        // Comandos inválidos
        if ((ctl->buttons() & BUTTON_A) && (ctl->buttons() & BUTTON_B)) { // Vibrar de comando invalido
            Serial.print("Comando invalido A + B");
            ctl->playDualRumble(0, 250, 0x80, 0x40);
        } else if ((ctl->buttons() & BUTTON_X) && (ctl->buttons() & BUTTON_Y)) { // Vibrar de comando invalido
            Serial.print("Comando invalido X + Y");
            ctl->playDualRumble(0, 250, 0x80, 0x40);
        } else {
                // No vibrar
        }

        if (ctl->miscButtons() & MISC_BUTTON_SYSTEM && (ctl->miscButtons() & MISC_BUTTON_START)) {
            if (!powerWasPressed) {
                powerPressedStart = millis();
                powerWasPressed = true;
            } else if (millis() - powerPressedStart >= 5000) {
                Serial.println("POWER presionado por 5 segundos, desconectando...");
                ctl->disconnect();
                powerWasPressed = false;
            }
        } else {
            powerWasPressed = false;
        }
        
        dumpGamepad(ctl); // Dump the gamepad data to the serial console
        // Another way to query controller data is by getting the buttons() function.
        // See how the different "dump*" functions dump the Controller info.
    }

        // Cambio de modo con DPAD y POWER
    if ((ctl->miscButtons() & MISC_BUTTON_SYSTEM) && (ctl->dpad() == DPAD_UP)) {
        if (!modeChangeActive) {
            modeChangeStart = millis();
            modeChangeActive = true;
        } else if (millis() - modeChangeStart >= 5000) {
            modoControl = 1;
            Serial.println("Modo control 1 activado");
            ctl->playDualRumble(0, 500, 0xFF, 0xFF); // vibración fuerte
            modeChangeActive = false;
        }
    } else if ((ctl->miscButtons() & MISC_BUTTON_SYSTEM) && (ctl->dpad() == DPAD_LEFT)) {
        if (!modeChangeActive) {
            modeChangeStart = millis();
            modeChangeActive = true;
        } else if (millis() - modeChangeStart >= 5000) {
            modoControl = 2;
            Serial.println("Modo control 2 activado");
            ctl->playDualRumble(0, 500, 0xFF, 0xFF); // vibración fuerte
            modeChangeActive = false;
        }
    } else {
        modeChangeActive = false;
    }
    // if (ctl->dpad() == DPAD_UP) {
    //     /* code */
    // } else if (ctl->dpad() == DPAD_DOWN) {
    //     /* code */
    // } else if (ctl->dpad() == DPAD_LEFT) {
    //     /* code */
    // } else if (ctl->dpad() == DPAD_RIGHT) {
    //     /* code */
    // }
    
}

void processControllers() {
    for (auto myController : myControllers) {
        if (myController && myController->isConnected() && myController->hasData()) {
            if (myController->isGamepad()) {
                processGamepad(myController);
            } else {
                Serial.println("Unsupported controller");
            }
        }
    }
}

// Arduino setup function. Runs in CPU 1
void setup() {
    
    // Initialize the servos
    // debido a un bug en la librería ESP32Servo, es necesario llamar a attach dos veces
    HombroFrontal.attach(servoPinHombroFrontal);
    HombroFrontal.attach(servoPinHombroFrontal);
    HombroSagital.attach(servoPinHombroSagital);
    HombroSagital.attach(servoPinHombroSagital);
    HombroTransversal.attach(servoPinHombroTransversal);
    HombroTransversal.attach(servoPinHombroTransversal);
    Bicep.attach(servoPinBicep);
    Bicep.attach(servoPinBicep);
    Muneca.attach(servoPinMuneca);
    Muneca.attach(servoPinMuneca);
    Mano.attach(servoPinMano);
    Mano.attach(servoPinMano);

    // test the servos by moving them to a default position
    HombroFrontal.write(posHombroFrontal); // Move to middle position
    HombroSagital.write(posHombroSagital); // Move to middle position
    HombroTransversal.write(posHombroTransversal); // Move to middle position
    Bicep.write(posBicep); // Move to middle position
    Muneca.write(posMuneca); // Move to middle position
    Mano.write(posMano); // Move to middle position

    Serial.begin(115200);
    Serial.printf("Firmware: %s\n", BP32.firmwareVersion());
    const uint8_t* addr = BP32.localBdAddress();
    Serial.printf("BD Addr: %2X:%2X:%2X:%2X:%2X:%2X\n", addr[0], addr[1], addr[2], addr[3], addr[4], addr[5]);

    // Setup the Bluepad32 callbacks
    BP32.setup(&onConnectedController, &onDisconnectedController);

    // "forgetBluetoothKeys()" should be called when the user performs
    // a "device factory reset", or similar.
    // Calling "forgetBluetoothKeys" in setup() just as an example.
    // Forgetting Bluetooth keys prevents "paired" gamepads to reconnect.
    // But it might also fix some connection / re-connection issues.
    BP32.forgetBluetoothKeys();

    // Enables mouse / touchpad support for gamepads that support them.
    // When enabled, controllers like DualSense and DualShock4 generate two connected devices:
    // - First one: the gamepad
    // - Second one, which is a "virtual device", is a mouse.
    // By default, it is disabled.
    BP32.enableVirtualDevice(false);

}

// Arduino loop function. Runs in CPU 1.
void loop() {
    // This call fetches all the controllers' data.
    // Call this function in your main loop.
    bool dataUpdated = BP32.update();
    if (dataUpdated)
        processControllers();
    // Process the servo motors based on gamepad input
    // filepath: c:\Users\crstn\OneDrive\Documentos\Arduino\BLEpad32\BLEpad32.ino
    // ...existing code...
    // ...existing code...
    // The main loop must have some kind of "yield to lower priority task" event.
    // Otherwise, the watchdog will get triggered.
    // If your main loop doesn't have one, just add a simple `vTaskDelay(1)`.
    // Detailed info here:
    // https://stackoverflow.com/questions/66278271/task-watchdog-got-triggered-the-tasks-did-not-reset-the-watchdog-in-time

    //     vTaskDelay(1);
    delay(150);
}
