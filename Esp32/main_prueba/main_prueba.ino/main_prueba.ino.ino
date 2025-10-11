#include "ESP32Servo.h"
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pca1 = Adafruit_PWMServoDriver(0x40);
Adafruit_PWMServoDriver pca2 = Adafruit_PWMServoDriver(0x41);

#define SERVOMIN 102  // Minimum pulse length (0 degrees)
#define SERVOMAX 553  // Maximum pulse length (180 degrees)

// BRAZO DERECHO
int ServoPulgarDerechoPin = 7; // Blanco naranja --- pca1
int ServoIndiceDerechoPin = 8; // naranja --- pca1
int ServoMedioDerechoPin = 9; // --- pca1
int ServoAnularDerechoPin = 10; // --- pca1
int ServoMeniqueDerechoPin = 11; // --- pca1
int ServoMunecaDerechoPin = 12; // --- pca1

int ServoBicepsDerechoPin = 13; //pca1
int ServoHombroFrontalDerechoPin = 0; //pca2
int ServoHombroSagitalDerechoPin = 1; //pca2
int ServoHombroRotacionDerechoPin = 2; //pca2

// BRAZO IZQUIERDO
int ServoPulgarIzquierdoPin = 0; // pca1
int ServoIndiceIzquierdoPin = 1; // pca1
int ServoMedioIzquierdoPin = 2; // pca1
int ServoAnularIzquierdoPin = 3; // pca1
int ServoMeniqueIzquierdoPin = 4; // pca1
int ServoMunecaIzquierdaPin = 5; // pca1

int ServoBicepsIzquierdoPin = 6; //pca1
int ServoHombroFrontalIzquierdoPin = 3; //pca2
int ServoHombroSagitalIzquierdoPin = 4; //pca2
int ServoHombroRotacionIzquierdoPin = 5; //pca2


int Pulgar_Der_Pos_deseada = 0;
bool Pulgar_Der_return = false;
int Pulgar_Der_Pos = 0;
unsigned long Pulgar_Der_last_update = 0;
int Indice_Der_Pos_deseada = 0;
bool Indice_Der_return = false;
int Indice_Der_Pos = 0;
unsigned long Indice_Der_last_update = 0;
int Medio_Der_Pos_deseada = 0;
bool Medio_Der_return = false;
int Medio_Der_Pos = 0;
unsigned long Medio_Der_last_update = 0;
int Anular_Der_Pos_deseada = 180;
bool Anular_Der_return = false;
int Anular_Der_Pos = 180;
unsigned long Anular_Der_last_update = 0;  
int Menique_Der_Pos_deseada = 180;
bool Menique_Der_return = false;
int Menique_Der_Pos = 180;
unsigned long Menique_Der_last_update = 0;
int Muneca_Der_Pos_deseada = 0;
bool Muneca_Der_return = false;
int Muneca_Der_Pos = 0;
unsigned long Muneca_Der_last_update = 0;



int Pulgar_Izq_Pos_deseada = 0;
bool Pulgar_Izq_return = false;
int Pulgar_Izq_Pos = 180;
unsigned long Pulgar_Izq_last_update = 0;
int Indice_Izq_Pos_deseada = 0;
bool Indice_Izq_return = false;
int Indice_Izq_Pos = 180;
unsigned long Indice_Izq_last_update = 0;
int Medio_Izq_Pos_deseada = 0;
bool Medio_Izq_return = false;
int Medio_Izq_Pos = 0;
unsigned long Medio_Izq_last_update = 0;
int Anular_Izq_Pos_deseada = 180;
bool Anular_Izq_return = false;
int Anular_Izq_Pos = 0;
unsigned long Anular_Izq_last_update = 0;  
int Menique_Izq_Pos_deseada = 180;
bool Menique_Izq_return = false;
int Menique_Izq_Pos = 0;
unsigned long Menique_Izq_last_update = 0;
int Muneca_Izq_Pos_deseada = 0;
bool Muneca_Izq_return = false;
int Muneca_Izq_Pos = 180;
unsigned long Muneca_Izq_last_update = 0;

int grados_seguridad_hombro_sagital_derecho = 0;
int grados_seguridad_hombro_frontal_derecho = 0;

int grados_seguridad_hombro_sagital_izquierdo = 0;
int grados_seguridad_hombro_frontal_izquierdo = 0;

void setup() {
  Serial.begin(115200);
 
  pca1.begin();
  pca1.setPWMFreq(60);

  pca2.begin();
  pca2.setPWMFreq(60);


  delay(100);

  setServoPCA1(ServoBicepsDerechoPin, 40);
  setServoPCA2(ServoHombroFrontalDerechoPin, 13);
  setServoPCA2(ServoHombroSagitalDerechoPin, 10);
  setServoPCA2(ServoHombroRotacionDerechoPin, 90); //90

  setServoPCA1(ServoBicepsIzquierdoPin, 40);
  setServoPCA2(ServoHombroSagitalIzquierdoPin, 30);

  delay(100);

}

void loop() {
  if (Serial.available()>= 2) {
    
    int highByte = Serial.read();
    int lowByte = Serial.read();
    int codigo = (highByte << 8) | lowByte;
    //los códigos 1000 a 1999 -> ojos movimiento
    //los códigos 2000 a 2999 -> cuello movimiento
    //los códigos 3000 a 3999 -> mandibula movimiento
    //los códigos 4000 a 4999 -> brazo(hombro-codo) movimiento
    //los códigos 5000 a 5999 -> mano muñeca movimiento

  
        //MUÑECA DERECHA
    if (codigo == 5001) {
      Muneca_Der_Pos_deseada = 180;  //mostrar palma
      Muneca_Der_return = false;
      Muneca_Der_last_update = millis();
    }
    if (codigo == 5000) {
      Muneca_Der_Pos_deseada = 0;  //mostrar dorso
      Muneca_Der_return = false;
      Muneca_Der_last_update = millis();
    }

        // MUÑECA IZQUIERDA
    if (codigo == 5002) {
      Muneca_Izq_Pos_deseada = 180;  //mostrar dorso
      Muneca_Izq_return = false;
      Muneca_Izq_last_update = millis();
    }
    if (codigo == 5003) {
      Muneca_Izq_Pos_deseada = 0;  //mostrar palma
      Muneca_Izq_return = false;
      Muneca_Izq_last_update = millis();
    }

        //DEDOS DE LA MANO DERECHA
    if (codigo == 5510) { //  Numeros par cierra 
      Medio_Der_Pos_deseada = 180;
    }
    if (codigo == 5511) { //  Numeros impar abre
      Medio_Der_Pos_deseada = 0;
    } 
    if (codigo == 5512) {
      Anular_Der_Pos_deseada = 0;
    } 
    if (codigo == 5513) {
      Anular_Der_Pos_deseada = 180;
    } 
    if (codigo == 5514) {
      Menique_Der_Pos_deseada = 0;
    } 
    if (codigo == 5515) {
      Menique_Der_Pos_deseada = 180;
    } 
    if (codigo == 5516) {
      Indice_Der_Pos_deseada = 180;
    } 
    if (codigo == 5517) {
      Indice_Der_Pos_deseada = 0;
    } 
    if (codigo == 5518) {
      Pulgar_Der_Pos_deseada = 180;
    } 
    if (codigo == 5519) {
      Pulgar_Der_Pos_deseada = 0;
    }

        //DEDOS DE LA MANO izquierda
    if (codigo == 5524) { //  Numeros par cierra 
      Medio_Izq_Pos_deseada = 140;
    }
    if (codigo == 5525) { //  Numeros impar abre
      Medio_Izq_Pos_deseada = 0;
    } 
    if (codigo == 5526) {
      Anular_Izq_Pos_deseada = 130;
    } 
    if (codigo == 5527) {
      Anular_Izq_Pos_deseada = 0;
    } 
    if (codigo == 5528) {
      Menique_Izq_Pos_deseada = 130;
    } 
    if (codigo == 5529) {
      Menique_Izq_Pos_deseada = 0;
    } 
    if (codigo == 5522) {
      Indice_Izq_Pos_deseada = 30;
    } 
    if (codigo == 5523) {
      Indice_Izq_Pos_deseada = 180;
    } 
    if (codigo == 5520) {
      Pulgar_Izq_Pos_deseada = 90;
    } 
    if (codigo == 5521) {
      Pulgar_Izq_Pos_deseada = 180;
    }

    // BRAZO DERECHO
    if (codigo > 4000 && codigo < 4180) { //  codigo de biceps 
      int grados_biceps_derecho = codigo -  4000; // o usa codigo - 4000
      grados_biceps_derecho = map(grados_biceps_derecho, 0, 180, 20, 80);
      setServoPCA1(ServoBicepsDerechoPin, grados_biceps_derecho);
    }

    if (codigo > 4400 && codigo < 4580) { //  codigo de hombro frontal 
      int grados_hombro_frontal_derecho = codigo - 4400;
      grados_hombro_frontal_derecho = map(grados_hombro_frontal_derecho, 0, 180, 13, 55);
      grados_seguridad_hombro_frontal_derecho = grados_hombro_frontal_derecho;

      setServoPCA2(ServoHombroFrontalDerechoPin, grados_hombro_frontal_derecho);
    }

    if (codigo > 4800 && codigo < 4980) { //  codigo de hombro sagital 
      int grados_hombro_sagital_derecho = codigo - 4800;
      grados_hombro_sagital_derecho = map(grados_hombro_sagital_derecho, 180, 0, 230, 10);
      if (grados_hombro_sagital_derecho > 160){
        grados_hombro_sagital_derecho = 160;
      }
      grados_seguridad_hombro_sagital_derecho = grados_hombro_sagital_derecho;
      setServoPCA2(ServoHombroSagitalDerechoPin, grados_hombro_sagital_derecho);
    }

    if (codigo >= 6200 && codigo <= 6380) { //  codigo de hombro rotacion
      int grados_hombro_rotacion_derecho = codigo - 6200;
      grados_hombro_rotacion_derecho = map(grados_hombro_rotacion_derecho, 180, 0, 10, 170);
      if (grados_hombro_rotacion_derecho < 50){
        if (grados_seguridad_hombro_frontal_derecho < 20 && grados_seguridad_hombro_sagital_derecho < 40){
          grados_hombro_rotacion_derecho = 50;
        }
      }
      setServoPCA2(ServoHombroRotacionDerechoPin, grados_hombro_rotacion_derecho);
    }

    // BRAZO IZQUIERDO
    if (codigo > 4200 && codigo < 4380) { //  codigo de biceps 
      int grados_biceps_izquierdo = codigo - 4200;
      grados_biceps_izquierdo = map(grados_biceps_izquierdo, 180, 0, 20, 80);
      setServoPCA1(ServoBicepsIzquierdoPin, grados_biceps_izquierdo);
    }

    if (codigo > 6000 && codigo < 6180) { //  codigo de hombro sagital 
      int grados_hombro_sagital_izquierdo = codigo - 6000;
      grados_hombro_sagital_izquierdo = map(grados_hombro_sagital_izquierdo, 180, 0, 170, 30);
      if (grados_hombro_sagital_izquierdo > 160){
        grados_hombro_sagital_izquierdo = 160;
      }
      grados_seguridad_hombro_sagital_izquierdo = grados_hombro_sagital_izquierdo;
      setServoPCA2(ServoHombroSagitalIzquierdoPin, grados_hombro_sagital_izquierdo);
    }

    if (codigo > 4600 && codigo < 4780) { //  codigo de hombro frontal 
      int grados_hombro_frontal_izquierdo = codigo - 4600;
      grados_hombro_frontal_izquierdo = map(grados_hombro_frontal_izquierdo, 0, 180, 13, 55);
      grados_seguridad_hombro_frontal_izquierdo = grados_hombro_frontal_izquierdo;

      setServoPCA2(ServoHombroFrontalIzquierdoPin, grados_hombro_frontal_izquierdo);
    }

    if (codigo >= 6400 && codigo <= 6580) { //  codigo de hombro rotacion
      int grados_hombro_rotacion_izquierdo = codigo - 6400;
      grados_hombro_rotacion_izquierdo = map(grados_hombro_rotacion_izquierdo, 180, 0, 10, 170);
      if (grados_hombro_rotacion_izquierdo < 50){
        if (grados_seguridad_hombro_frontal_izquierdo < 20 && grados_seguridad_hombro_sagital_izquierdo < 40){
          grados_hombro_rotacion_izquierdo = 50;
        }
      }
      setServoPCA2(ServoHombroRotacionIzquierdoPin, grados_hombro_rotacion_izquierdo);
    }

    delay(10);
  }

  // Apagar muñeca luego de dos segundos
  if(Muneca_Izq_Pos_deseada == 0 || Muneca_Izq_Pos_deseada == 180){
      static unsigned long tiempo_espera_muneca_izq = 2000;
      unsigned long actual_muneca_izquierda = millis();
      if((actual_muneca_izquierda - Muneca_Izq_last_update >= tiempo_espera_muneca_izq) && !Muneca_Izq_return){
        Muneca_Izq_return = true;
      }
      if(Muneca_Izq_return){
        pca1.setPWM(ServoMunecaIzquierdaPin, 0, 0);
      } else{
        if (Muneca_Izq_Pos_deseada == 0){
          setServoPCA1(ServoMunecaIzquierdaPin, 0);
        }
        if (Muneca_Izq_Pos_deseada == 180){
          setServoPCA1(ServoMunecaIzquierdaPin, 180);
        }
      }
  }

  if (Muneca_Der_Pos_deseada == 0 || Muneca_Der_Pos_deseada == 180){
      static unsigned long tiempo_espera_muneca_der = 2000;
      unsigned long actual_muneca_derecha = millis();
      if((actual_muneca_derecha - Muneca_Der_last_update >= tiempo_espera_muneca_der) && !Muneca_Der_return){
        Muneca_Der_return = true;
      }
      if(Muneca_Der_return){
        pca1.setPWM(ServoMunecaDerechoPin, 0, 0);
      } else{
        if (Muneca_Der_Pos_deseada == 0){
          setServoPCA1(ServoMunecaDerechoPin, 0);
        }
        if (Muneca_Der_Pos_deseada == 180){
          setServoPCA1(ServoMunecaDerechoPin, 180);
        }
      }
  }

  // Regresar 15° (cuando están recogido) los dedos para apagar servomotor y evitar calentamiento
  if (Pulgar_Der_Pos_deseada == 0){
    Pulgar_Der_return = false;
    Pulgar_Der_Pos = 0;
    setServoPCA1(ServoPulgarDerechoPin, Pulgar_Der_Pos);
    Pulgar_Der_last_update = millis();
  }
  if (Pulgar_Der_Pos_deseada == 180){
    static unsigned long tiempo_espera_pulgar = 1500;
    unsigned long ahora_pulgar = millis();
    if((ahora_pulgar - Pulgar_Der_last_update >= tiempo_espera_pulgar)&&!Pulgar_Der_return){
      Pulgar_Der_return = true;
    }
    if(!Pulgar_Der_return){
      Pulgar_Der_Pos = 180;
    }else{
      Pulgar_Der_Pos = 165;
    }
    setServoPCA1(ServoPulgarDerechoPin, Pulgar_Der_Pos);
  }

  // Indice

  if (Indice_Der_Pos_deseada == 0){
    Indice_Der_return = false;
    Indice_Der_Pos = 0;
    setServoPCA1(ServoIndiceDerechoPin, Indice_Der_Pos);
    Indice_Der_last_update = millis();
  }
  if (Indice_Der_Pos_deseada == 180){
    static unsigned long tiempo_espera_indice = 1500;
    unsigned long ahora_indice = millis();
    if((ahora_indice - Indice_Der_last_update >= tiempo_espera_indice)&&!Indice_Der_return){
      Indice_Der_return = true;
    }
    if(!Indice_Der_return){
      Indice_Der_Pos = 180;
    }else{
      Indice_Der_Pos = 165;
    }
    setServoPCA1(ServoIndiceDerechoPin, Indice_Der_Pos);
  }

    // Medio

  if (Medio_Der_Pos_deseada == 0){
    Medio_Der_return = false;
    Medio_Der_Pos = 0;
    setServoPCA1(ServoMedioDerechoPin, Medio_Der_Pos);
    Medio_Der_last_update = millis();
  }
  if (Medio_Der_Pos_deseada == 180){
    static unsigned long tiempo_espera_medio = 1500;
    unsigned long ahora_medio = millis();
    if((ahora_medio - Medio_Der_last_update >= tiempo_espera_medio)&&!Medio_Der_return){
      Medio_Der_return = true;
    }
    if(!Medio_Der_return){
      Medio_Der_Pos = 180;
    }else{
      Medio_Der_Pos = 165;
    }
    setServoPCA1(ServoMedioDerechoPin, Medio_Der_Pos);
  }

    // Anular
 
  if (Anular_Der_Pos_deseada == 180){
    Anular_Der_return = false;
    Anular_Der_Pos = 180;
    setServoPCA1(ServoAnularDerechoPin, Anular_Der_Pos);
    Anular_Der_last_update = millis();
  }
  if (Anular_Der_Pos_deseada == 0){
    static unsigned long tiempo_espera_anular = 1500;
    unsigned long ahora_anular = millis();
    if((ahora_anular - Anular_Der_last_update >= tiempo_espera_anular)&&!Anular_Der_return){
      Anular_Der_return = true;
    }
    if(!Anular_Der_return){
      Anular_Der_Pos = 0;
    }else{
      Anular_Der_Pos = 15;
    }
    setServoPCA1(ServoAnularDerechoPin, Anular_Der_Pos);
  }

      // Menique

  if (Menique_Der_Pos_deseada == 180){
    Menique_Der_return = false;
    Menique_Der_Pos = 180;
    setServoPCA1(ServoMeniqueDerechoPin, Menique_Der_Pos);
    Menique_Der_last_update = millis();
  }
  if (Menique_Der_Pos_deseada == 0){
    static unsigned long tiempo_espera_menique = 1500;
    unsigned long ahora_menique = millis();
    if((ahora_menique - Menique_Der_last_update >= tiempo_espera_menique)&&!Menique_Der_return){
      Menique_Der_return = true;
    }
    if(!Menique_Der_return){
      Menique_Der_Pos = 0;
    }else{
      Menique_Der_Pos = 15;
    }
    setServoPCA1(ServoMeniqueDerechoPin, Menique_Der_Pos);
  }
  



    // Regresar 15° (cuando están recogido) los dedos para apagar servomotor y evitar calentamiento
  if (Pulgar_Izq_Pos_deseada == 180){
    Pulgar_Izq_return = false;
    Pulgar_Izq_Pos = 180;
    setServoPCA1(ServoPulgarIzquierdoPin, Pulgar_Izq_Pos);
    Pulgar_Izq_last_update = millis();
  }
  if (Pulgar_Izq_Pos_deseada == 90){
    static unsigned long tiempo_espera_pulgar = 1500;
    unsigned long ahora_pulgar = millis();
    if((ahora_pulgar - Pulgar_Izq_last_update >= tiempo_espera_pulgar)&&!Pulgar_Izq_return){
      Pulgar_Izq_return = true;
    }
    if(!Pulgar_Izq_return){
      Pulgar_Izq_Pos = 90;
    }else{
      Pulgar_Izq_Pos = 105;
    }
    setServoPCA1(ServoPulgarIzquierdoPin, Pulgar_Izq_Pos);
  }

  // Indice

  if (Indice_Izq_Pos_deseada == 180){
    Indice_Izq_return = false;
    Indice_Izq_Pos = 180;
    setServoPCA1(ServoIndiceIzquierdoPin, Indice_Izq_Pos);
    Indice_Izq_last_update = millis();
  }
  if (Indice_Izq_Pos_deseada == 30){
    static unsigned long tiempo_espera_indice = 1500;
    unsigned long ahora_indice = millis();
    if((ahora_indice - Indice_Izq_last_update >= tiempo_espera_indice)&&!Indice_Izq_return){
      Indice_Izq_return = true;
    }
    if(!Indice_Izq_return){
      Indice_Izq_Pos = 30;
    }else{
      Indice_Izq_Pos = 45;
    }
    setServoPCA1(ServoIndiceIzquierdoPin, Indice_Izq_Pos);
  }

    // Medio

  if (Medio_Izq_Pos_deseada == 0){
    Medio_Izq_return = false;
    Medio_Izq_Pos = 0;
    setServoPCA1(ServoMedioIzquierdoPin, Medio_Izq_Pos);
    Medio_Izq_last_update = millis();
  }
  if (Medio_Izq_Pos_deseada == 140){
    static unsigned long tiempo_espera_medio = 1500;
    unsigned long ahora_medio = millis();
    if((ahora_medio - Medio_Izq_last_update >= tiempo_espera_medio)&&!Medio_Izq_return){
      Medio_Izq_return = true;
    }
    if(!Medio_Izq_return){
      Medio_Izq_Pos = 140;
    }else{
      Medio_Izq_Pos = 125;
    }
    setServoPCA1(ServoMedioIzquierdoPin, Medio_Izq_Pos);
  }

    // Anular

  if (Anular_Izq_Pos_deseada == 0){ //abrir
    Anular_Izq_return = false;
    Anular_Izq_Pos = 0;
    setServoPCA1(ServoAnularIzquierdoPin, Anular_Izq_Pos);
    Anular_Izq_last_update = millis();
  }
  if (Anular_Izq_Pos_deseada == 130){ //cerrar
    static unsigned long tiempo_espera_anular = 1500;
    unsigned long ahora_anular = millis();
    if((ahora_anular - Anular_Izq_last_update >= tiempo_espera_anular)&&!Anular_Izq_return){
      Anular_Izq_return = true;
    }
    if(!Anular_Izq_return){
      Anular_Izq_Pos = 130;
    }else{
      Anular_Izq_Pos = 115;
    }
    setServoPCA1(ServoAnularIzquierdoPin, Anular_Izq_Pos);
  }

      // Menique

  if (Menique_Izq_Pos_deseada == 0){
    Menique_Izq_return = false;
    Menique_Izq_Pos = 0;
    setServoPCA1(ServoMeniqueIzquierdoPin, Menique_Izq_Pos);
    Menique_Izq_last_update = millis();
  }
  if (Menique_Izq_Pos_deseada == 130){
    static unsigned long tiempo_espera_menique = 1500;
    unsigned long ahora_menique = millis();
    if((ahora_menique - Menique_Izq_last_update >= tiempo_espera_menique)&&!Menique_Izq_return){
      Menique_Izq_return = true;
    }
    if(!Menique_Izq_return){
      Menique_Izq_Pos = 130;
    }else{
      Menique_Izq_Pos = 115;
    }
    setServoPCA1(ServoMeniqueIzquierdoPin, Menique_Izq_Pos);
  }
}
  
void setServoPCA1(uint8_t n_numero, int grados){
  int hallar_pulso;
  hallar_pulso = map(grados, 0, 180, SERVOMIN, SERVOMAX);
  pca1.setPWM(n_numero, 0, hallar_pulso);
}
void setServoPCA2(uint8_t n_numero, int grados){
  int hallar_pulso;
  hallar_pulso = map(grados, 0, 180, SERVOMIN, SERVOMAX);
  pca2.setPWM(n_numero, 0, hallar_pulso);
}