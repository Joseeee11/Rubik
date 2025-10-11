#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pca1 = Adafruit_PWMServoDriver(0x41);
Adafruit_PWMServoDriver pca0 = Adafruit_PWMServoDriver(0x40);

#define SERVOMIN 102  // Minimum pulse length (0 degrees)
#define SERVOMAX 553  // Maximum pulse length (180 degrees)

int pinServo = 0;
int posServo = 30;

void setup() {
  Serial.begin(115200);

  pca0.begin();
  pca0.setPWMFreq(60);

  pca1.begin();
  pca1.setPWMFreq(60);

  setServoPCA0(13, 40); //bicep derecho
  setServoPCA0(6, 40);  //bicep izquierdo
  // setServoPCA(1, 40);  // hombro sagi derecho
  // setServoPCA(4, 40);  // hombro sagi izquierdo
  // setServoPCA(0, 40);  // hombro fron derecho
  // setServoPCA(3, 40);  // hombro fron izquierdo
  // setServoPCA(2, 40);  // hombro rotac derecho

  setServoPCA(pinServo, posServo);
  delay(100);
}

void loop() {

  if (Serial.available()) {
    String serialEntrada = Serial.readStringUntil('\n');
    int entrada = serialEntrada.toInt();
    if (entrada < 0) {
      Serial.println("El numero ingresado debe ser mayor a 0");
      posServo = 0;
    }
    else if (entrada > 180) {
      Serial.println("El numero ingresado debe ser meno a 180");
      posServo = 180;
    } else {
      posServo = entrada;
    }
  }
  setServoPCA(pinServo, posServo);
  delay(100);
  
//  if(posServo >= 180){
//    orientacion = -1;
//  }else if(posServo <= 0){
//    orientacion = 1;
//  }
//  posServo += orientacion;
//  servo21.write(posServo);
//  delay(500); 
}

void setServoPCA(uint8_t n_numero, int grados){
  int hallar_pulso;
  hallar_pulso = map(grados, 0, 180, SERVOMIN, SERVOMAX);
  pca1.setPWM(n_numero, 0, hallar_pulso);
}
void setServoPCA0(uint8_t n_numero, int grados){
  int hallar_pulso;
  hallar_pulso = map(grados, 0, 180, SERVOMIN, SERVOMAX);
  pca0.setPWM(n_numero, 0, hallar_pulso);
}
