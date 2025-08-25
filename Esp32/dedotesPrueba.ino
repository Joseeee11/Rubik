#include "BluetoothSerial.h"
#include "ESP32Servo.h"

String device_name = "ESP32-BT-Slave, Chinis";

//// Servo
// pin
int ServoMedioPin = 25;
int ServoAnularPin = 26;
int ServoMeniquePin = 27;
int ServoIndicePin = 32;
int ServoPulgarPin = 33;
// variables
Servo ServoMedio;
Servo ServoAnular;
Servo ServoMenique;
Servo ServoIndice;
Servo ServoPulgar;
// Check if Bluetooth is available
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

// Check Serial Port Profile
#if !defined(CONFIG_BT_SPP_ENABLED)
#error Serial Port Profile for Bluetooth is not available or not enabled. It is only available for the ESP32 chip.
#endif

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
  SerialBT.begin(device_name);  //Bluetooth device name
  Serial.printf("The device with name \"%s\" is started.\nNow you can pair it with Bluetooth!\n", device_name.c_str());
  ServoMedio.attach(ServoMedioPin);
  ServoAnular.attach(ServoAnularPin);
  ServoMenique.attach(ServoMeniquePin);
  ServoIndice.attach(ServoIndicePin);
  ServoPulgar.attach(ServoPulgarPin);
}

void loop() {
  if (Serial.available()) {
    // int dato = SerialBT.read();
    // String pose = SerialBT.readString();
    int dato = Serial.read();
    Serial.println(dato);
    //letras pares abierto (B, D, F, G, I)
    //letras impares cerrado (A, C, E, H, J)

    //POR DEDO
    if (dato == 'A') {
      ServoMedio.write(80);
    } else if (dato == 'B') {
      ServoMedio.write(180);
    } else if (dato == 'C') {
      ServoAnular.write(80);
    } else if (dato == 'D') {
      ServoAnular.write(180);
    } else if (dato == 'E') {
      ServoMenique.write(90);
    } else if (dato == 'F') {
      ServoMenique.write(180);
    } else if (dato == 'G') {
      ServoIndice.write(0);
    } else if (dato == 'H') {
      ServoIndice.write(110);
    } else if (dato == 'I') {
      ServoPulgar.write(0);
    } else if (dato == 'J') {
      ServoPulgar.write(110);
    }

    //POSES BÁSICAS (me gustaría hacerlo con mediapipe, imitar gestos básicos de la mano)
    // if (pose == 'PAZ') {
    //   ServoPulgar.write(80);
    //   ServoIndice.write(180);
    //   ServoMedio.write(180);
    //   ServoAnular.write(80);
    //   ServoMenique.write(80);
    // } else if (pose == 'LIKE') {
    //   ServoPulgar.write(180);
    //   ServoIndice.write(80);
    //   ServoMedio.write(80);
    //   ServoAnular.write(80);
    //   ServoMenique.write(80);
    // } else if (pose == 'CERRADO') {
    //   ServoPulgar.write(80);
    //   ServoIndice.write(80);
    //   ServoMedio.write(80);
    //   ServoAnular.write(80);
    //   ServoMenique.write(80);
    // } else if (pose == 'ABIERTO') {
    //   ServoPulgar.write(180);
    //   ServoIndice.write(180);
    //   ServoMedio.write(180);
    //   ServoAnular.write(180);
    //   ServoMenique.write(180);
    // } else if (pose == 'SEÑALAR') {
    //   ServoPulgar.write(80);
    //   ServoIndice.write(180);
    //   ServoMedio.write(80);
    //   ServoAnular.write(80);
    //   ServoMenique.write(80);
    // } else if (pose == 'PROMISE') {
    //   ServoPulgar.write(80);
    //   ServoIndice.write(80);
    //   ServoMedio.write(80);
    //   ServoAnular.write(80);
    //   ServoMenique.write(180);
    // } else if (pose == 'SHAKA') {
    //   ServoPulgar.write(180);
    //   ServoIndice.write(80);
    //   ServoMedio.write(80);
    //   ServoAnular.write(80);
    //   ServoMenique.write(180);
    // } else if (pose == 'HEAVY') {
    //   ServoPulgar.write(180);
    //   ServoIndice.write(180);
    //   ServoMedio.write(80);
    //   ServoAnular.write(80);
    //   ServoMenique.write(180);
    // }
  }
  // if (Serial.available()) {
  //   // Lee el mensaje recibido por serie
  //   String incomingMessage = Serial.readStringUntil('\n');
  //   Serial.print("Recibido por serie: ");
  //   Serial.println(incomingMessage);
    
  //   // Envía el mensaje recibido por Bluetooth
  //   SerialBT.write((const uint8_t *) incomingMessage.c_str(), incomingMessage.length());
  //   SerialBT.write((uint8_t) '\n');
  // }

  delay(50);
}
/////////////////////////////////////////////////////////////
  // if (Serial.available()) {
  //   digitalWrite(LED_BUILTIN, LOW);
  //   SerialBT.write(Serial.read());
  // }
  // if (SerialBT.available()) {
  //   digitalWrite(LED_BUILTIN, HIGH);
  //   Serial.write(SerialBT.read());
  // }{