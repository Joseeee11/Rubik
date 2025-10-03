#include <ESP32Servo.h>
int pin21 = 16;
int pos21 = 10;
int orientacion = 1;
Servo servo21;

void setup() {
  Serial.begin(115200);
  ESP32PWM::allocateTimer(0);
  servo21.setPeriodHertz(50);
  servo21.attach(pin21, 500, 2400);
  delay(100);
}

void loop() {

  if (Serial.available()) {
    String serialEntrada = Serial.readStringUntil('\n');
    int entrada = serialEntrada.toInt();
    if (entrada < 0) {
      Serial.println("El numero ingresado debe ser mayor a 0");
      pos21 = 0;
    }
    else if (entrada > 180) {
      Serial.println("El numero ingresado debe ser meno a 180");
      pos21 = 180;
    } else {
      pos21 = entrada;
    }
  }
  servo21.write(pos21);
  delay(100);
  
//  if(pos21 >= 180){
//    orientacion = -1;
//  }else if(pos21 <= 0){
//    orientacion = 1;
//  }
//  pos21 += orientacion;
//  servo21.write(pos21);
//  delay(500); 
}