#include "ESP32Servo.h"

//// Servo
// pin
int ServoEjeYPin = 14;
int ServoEjeXPin = 12;

int ServoMedioPin = 25;
int ServoAnularPin = 26;
int ServoMeniquePin = 27;
int ServoIndicePin = 32;
int ServoPulgarPin = 33;
//
int ServoEjeYPos = 90; 
int ServoEjeXPos = 90;
//
int Min_Y = 60;
int Max_Y = 120;
int Min_X = 40;
int Max_X = 140;
//
Servo ServoEjeY;
Servo ServoEjeX;
Servo ServoMedio;
Servo ServoAnular;
Servo ServoMenique;
Servo ServoIndice;
Servo ServoPulgar;

void setup() {
  Serial.begin(115200);
  ServoEjeX.attach(ServoEjeXPin);
  ServoEjeY.attach(ServoEjeYPin);
  ServoMedio.attach(ServoMedioPin);
  ServoAnular.attach(ServoAnularPin);
  ServoMenique.attach(ServoMeniquePin);
  ServoIndice.attach(ServoIndicePin);
  ServoPulgar.attach(ServoPulgarPin);
  delay(500);
}

void loop() {
  if (Serial.available()) {
    char dato = Serial.read();
    Serial.println(dato);

    if (dato == 'L'){
      ServoEjeXPos -= 1;
    }else if (dato == 'R'){
      ServoEjeXPos += 1;
    }else if (dato == 'W') {
      ServoEjeYPos += 1;
    }else if (dato == 'S'){
      ServoEjeYPos -= 1;
    } else if (dato == 'A') {
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
    // Rectificador X
    if (ServoEjeXPos >= Max_X){
      ServoEjeXPos = Max_X - 1;
    }
    if (ServoEjeXPos <= Min_X){
      ServoEjeXPos = Min_X + 1;
    }
    // Rectificador Y
    if (ServoEjeYPos >= Max_Y){
      ServoEjeYPos = Max_Y - 1;
    }
    if (ServoEjeYPos <= Min_Y){
      ServoEjeYPos = Min_Y + 1;
    }
  }
  ServoEjeY.write(ServoEjeYPos);
  ServoEjeX.write(ServoEjeXPos);
}
