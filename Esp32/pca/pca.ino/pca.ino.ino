#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pca1 = Adafruit_PWMServoDriver(0x40);


#define SERVOMIN 102  // Minimum pulse length (0 degrees)
#define SERVOMAX 553  // Maximum pulse length (180 degrees)


int Servo_Pos = 0;
int Servo_Pin = 0;

void setup() {
  pca1.begin();
  pca1.setPWMFreq(60);
}

void loop() {
  setServo(0, 90);
  delay(2000);
  setServo(0, 0);
  delay(2000);
  setServo(0, 180);
  delay(2000);
  
}

void setServo(uint8_t n_numero, int grados){
  int hallar_pulso;
  hallar_pulso = map(grados, 0, 180, SERVOMIN, SERVOMAX);
  pca1.setPWM(n_numero, 0, hallar_pulso);
}
