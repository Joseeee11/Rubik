#include "ESP32Servo.h"
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// PCA
Adafruit_PWMServoDriver pca1 = Adafruit_PWMServoDriver(0x40);
Adafruit_PWMServoDriver pca2 = Adafruit_PWMServoDriver(0x41);
#define SERVOMIN 102  // Minimum pulse length (0 degrees)
#define SERVOMAX 553  // Maximum pulse length (180 degrees)

// CABEZA
// int ServoMandibulaPin = 21;
// int ServoOjoEjeXPin = 23;
// int ServoOjoEjeYPin = 22;
// int ServoCuelloEjeXPin = 19;

int ServoMandibulaPin = 8; // --- pca2
int ServoOjoEjeXPin = 10; // --- pca2
int ServoOjoEjeYPin = 7; // --- pca2
int ServoCuelloEjeXPin = 6; // --- pca2

// TORSO
int ServoCuelloEjeYPin = 9; // --- pca2
int ServoClaviculaIzqPin = 2;
int ServoClaviculaDerPin = 15;

// BRAZO DERECHO
int ServoPulgarDerechoPin = 7; // --- pca1   Blanco-Naranja
int ServoIndiceDerechoPin = 8; // --- pca1   Naranja
int ServoMedioDerechoPin = 9; // --- pca1    Blanco-Azul
int ServoAnularDerechoPin = 10; // --- pca1  Azul
int ServoMeniqueDerechoPin = 11; // --- pca1 Blanco-Verde
int ServoMunecaDerechoPin = 12; // --- pca1  Verde

int ServoBicepsDerechoPin = 13; //pca1       Blanco-Marron
int ServoHombroFrontalDerechoPin = 3; //pca2
int ServoHombroSagitalDerechoPin = 4; //pca2
int ServoHombroRotacionDerechoPin = 5; //pca2

// BRAZO IZQUIERDO
int ServoPulgarIzquierdoPin = 0; // pca1
int ServoIndiceIzquierdoPin = 1; // pca1
int ServoMedioIzquierdoPin = 2; // pca1
int ServoAnularIzquierdoPin = 3; // pca1
int ServoMeniqueIzquierdoPin = 4; // pca1
int ServoMunecaIzquierdaPin = 5; // pca1

int ServoBicepsIzquierdoPin = 6; //pca1
int ServoHombroFrontalIzquierdoPin = 0; //pca2
int ServoHombroSagitalIzquierdoPin = 1; //pca2
int ServoHombroRotacionIzquierdoPin = 2; //pca2

// CABEZA
// Servo ServoMandibula;
// Servo ServoOjoEjeX;
// Servo ServoOjoEjeY;
// Servo ServoCuelloEjeX;

// TORSO
// Servo ServoCuelloEjeY;
Servo ServoClaviculaIzq;
Servo ServoClaviculaDer;

// VARIABLES CABEZA
int OjoEjeX_Pos = 90;
int CuelloEjeX_Pos = 90;
int CuelloEjeY_Pos = 90;
int OjoEjeY_Pos = 140;

int codigo=0;
int min_Y_ojo = 100;
int max_Y_ojo = 180;
int min_X_ojo = 100;
int max_X_ojo = 170;
int min_X_cuello = 10;
int max_X_cuello = 170;
int min_Y_cuello = 60;
int max_Y_cuello = 120;

int Mover_cuello_lento = 0;
unsigned long cuello_last_update = 0;
int Mover_cuello_lento_vertical = 0;
unsigned long cuello_last_update_vertical = 0;

// VARIABLES MANO DERECHA
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

// VARIABLES MANO IZQUIERDA
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

// VARIABLES MANDÍBULA
bool mandibula_activa = false; //para saber cuando esta activa la mandibula
bool mandibula_cerrar = true; //para saber si está abierta o cerrada
    //Control asíncrono de la mandíbula
unsigned long mandibula_last_update = 0;
int mandibula_estado = 0; // 0: inactiva, 1: abriendo, 2: cerrando

// VARIABLES DE SEGURIDAD HOMBRO IZQ Y DER
int grados_seguridad_hombro_sagital_derecho = 0;
int grados_seguridad_hombro_frontal_derecho = 0;
int grados_seguridad_hombro_sagital_izquierdo = 0;
int grados_seguridad_hombro_frontal_izquierdo = 0;

void setup() {
  Serial.begin(115200);

  //SETUP PCA
  pca1.begin();
  pca1.setPWMFreq(60);
  pca2.begin();
  pca2.setPWMFreq(60);

  // ADJUNTAR PINES CABEZA  
//   ServoMandibula.attach(ServoMandibulaPin);
//   ServoOjoEjeY.attach(ServoOjoEjeYPin);
//   ServoOjoEjeX.attach(ServoOjoEjeXPin);
//   ServoCuelloEjeX.attach(ServoCuelloEjeXPin);

  // ADJUNTAR PINES TORSO
  ServoClaviculaIzq.attach(ServoClaviculaIzqPin);
  ServoClaviculaDer.attach(ServoClaviculaDerPin);

  delay(100);

  // INICIAR MOTORES CABEZA Y TORSO EN POSICION
//   ServoCuelloEjeX.write(90);
//   ServoOjoEjeY.write(140);
//   ServoOjoEjeX.write(90);
//   ServoMandibula.write(90);

  // INICIAR MOTORES BRAZO EN POSICION
  setServoPCA1(ServoBicepsDerechoPin, 40);
  setServoPCA2(ServoHombroFrontalDerechoPin, 50);  // 50 abajo
  setServoPCA2(ServoHombroSagitalDerechoPin, 20);
  setServoPCA2(ServoHombroRotacionDerechoPin, 150); //150 medio

  setServoPCA1(ServoBicepsIzquierdoPin, 40);
  setServoPCA2(ServoHombroSagitalIzquierdoPin, 30);
  setServoPCA2(ServoHombroFrontalIzquierdoPin, 40);
  setServoPCA2(ServoHombroRotacionIzquierdoPin, 150); //150 medio

  // INICIAR MOTORES CABEZA EN POSICION
  setServoPCA2(ServoMandibulaPin, 90); // cerrar completamente
  setServoPCA2(ServoOjoEjeXPin, 135); // 135 medio
  setServoPCA2(ServoOjoEjeYPin, 140);
  setServoPCA2(ServoCuelloEjeXPin, 90);
  setServoPCA2(ServoCuelloEjeYPin, 90);

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
    //los códigos 4000 a 4999 y 6000 a 6999-> brazo(hombro-codo) movimiento
    //los códigos 5000 a 5999 -> mano muñeca movimiento

    //MANDIBULA
    if (codigo == 3005){
      mandibula_activa = true;
      mandibula_cerrar = false;
    } else if (codigo == 3010){
      mandibula_cerrar = true;
    }

    //SEGUIMIENTO POR OJOS
      //modos de seguimiento: izquierdaExtremo = 2025, izquierdaMedio = 2015, izquierdaInicio = 1005 
                              //derechaExtremo = 2020, derechaMedio = 2010, derechaInicio = 1010 
                              //arriba = 1020 ---- abajo = 1025
                              // Abrir boca hablar= 3005 ---- Cerrar boca hablar= 3010
                              // Abrir boca imitar = 3105 ---- Cerrar boca imitar = 3110
                              //El rango para mover cuello lento 2500 a 2999
                              // Cuello Muy izquierda = 2505 - izquierda = 2510- medio= 2515 -derecha 2520 -  Muy derecha = 2525
                              // Cuello Arriba = 2545 - Abajo = 2550- Centro= 2555
    if (codigo == 3105){
        // ServoMandibula.write(150); // abrir
        setServoPCA2(ServoMandibulaPin, 150); // abrir
    }else if (codigo == 3110){
        // ServoMandibula.write(90); // cerrar completamente
        setServoPCA2(ServoMandibulaPin, 90); // cerrar completamente
    }

    // MOVER CUELLO
    if (codigo == 2505) { //cuello muy izquierda
      Mover_cuello_lento = min_X_cuello + 20;
    } else if (codigo == 2525) { //cuello muy derecha
      Mover_cuello_lento = max_X_cuello - 20;
    } else if (codigo == 2510) { //cuello izquierda
      Mover_cuello_lento = (min_X_cuello + 90)/ 2; // 50;
    } else if (codigo == 2520) { //cuello derecha
      Mover_cuello_lento = (max_X_cuello + 90) / 2; // 130;
    } else if (codigo == 2515) { //cuello medio
      Mover_cuello_lento = 90;
    } else if(!(codigo >= 2500 && codigo <=2999)){
      Mover_cuello_lento = 0;
    }

    // if (codigo == 2545) { //cuello ARRIBA VERTICAL
    //   Mover_cuello_lento_vertical = min_Y_cuello + 20;
    // } else if (codigo == 2550) { //cuello ABAJO
    //   Mover_cuello_lento_vertical = max_Y_cuello - 20;
    // } else if (codigo == 2555) { //cuello CENTRO
    //   Mover_cuello_lento_vertical = 90;
    // } else if(!(codigo >= 2500 && codigo <=2999)){
    //   Mover_cuello_lento_vertical = 0;
    // }
    
    // MOVER OJOS
    if (codigo == 1005) { //izquierda
      OjoEjeX_Pos = min_X_ojo;
    } else if (codigo == 2015) {
      CuelloEjeX_Pos += 3;
    }
    if (codigo == 1010) { //derecha
      OjoEjeX_Pos = max_X_ojo;
    } else if (codigo == 2010) {
      CuelloEjeX_Pos -= 3;
    }

    if (codigo == 1000){
      OjoEjeX_Pos = 135; /////////////////////////////////////////////////////
    }

    if (codigo == 1020) { //arriba
      OjoEjeY_Pos = 100;
    } else if (codigo == 1025) { //abajo
      OjoEjeY_Pos = 180;
    } else if (codigo == 1030){
      OjoEjeY_Pos = 140;
    }
    // Rectificador para cumplir con 0 a 180 CUELLO Y OJOS
    if (CuelloEjeX_Pos >= max_X_cuello){
      CuelloEjeX_Pos = max_X_cuello;
    }
    if (CuelloEjeX_Pos <= min_X_cuello){
      CuelloEjeX_Pos = min_X_cuello;
    }

    setServoPCA2(ServoOjoEjeYPin, OjoEjeY_Pos);
    setServoPCA2(ServoOjoEjeXPin, OjoEjeX_Pos);
    setServoPCA2(ServoCuelloEjeXPin, CuelloEjeX_Pos);



    //MUÑECA DERECHA
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
      grados_biceps_derecho = map(grados_biceps_derecho, 0, 180, 20, 50);
      setServoPCA1(ServoBicepsDerechoPin, grados_biceps_derecho);
    }

    // if (codigo > 4400 && codigo < 4580) { //  codigo de hombro frontal 
    //   int grados_hombro_frontal_derecho = codigo - 4400;
    //   grados_hombro_frontal_derecho = map(grados_hombro_frontal_derecho, 0, 180, 13, 55);
    //   grados_seguridad_hombro_frontal_derecho = grados_hombro_frontal_derecho;

    //   setServoPCA2(ServoHombroFrontalDerechoPin, grados_hombro_frontal_derecho);
    // }

    // if (codigo > 4800 && codigo < 4980) { //  codigo de hombro sagital 
    //   int grados_hombro_sagital_derecho = codigo - 4800;
    //   grados_hombro_sagital_derecho = map(grados_hombro_sagital_derecho, 180, 0, 230, 10);
    //   if (grados_hombro_sagital_derecho > 160){
    //     grados_hombro_sagital_derecho = 160;
    //   }
    //   grados_seguridad_hombro_sagital_derecho = grados_hombro_sagital_derecho;
    //   setServoPCA2(ServoHombroSagitalDerechoPin, grados_hombro_sagital_derecho);
    // }

    // if (codigo >= 6200 && codigo <= 6380) { //  codigo de hombro rotacion
    //   int grados_hombro_rotacion_derecho = codigo - 6200;
    //   grados_hombro_rotacion_derecho = map(grados_hombro_rotacion_derecho, 180, 0, 10, 170);
    //   if (grados_hombro_rotacion_derecho < 130){
    //     if (grados_seguridad_hombro_frontal_derecho < 30 && grados_seguridad_hombro_sagital_derecho < 40){
    //       grados_hombro_rotacion_derecho = 130;
    //     }
    //   }
    //   setServoPCA2(ServoHombroRotacionDerechoPin, grados_hombro_rotacion_derecho);
    // }

    // BRAZO IZQUIERDO
    if (codigo > 4200 && codigo < 4380) { //  codigo de biceps 
      int grados_biceps_izquierdo = codigo - 4200;
      grados_biceps_izquierdo = map(grados_biceps_izquierdo, 0, 180, 20, 80);
      setServoPCA1(ServoBicepsIzquierdoPin, grados_biceps_izquierdo);
    }

    // if (codigo > 6000 && codigo < 6180) { //  codigo de hombro sagital 
    //   int grados_hombro_sagital_izquierdo = codigo - 6000;
    //   grados_hombro_sagital_izquierdo = map(grados_hombro_sagital_izquierdo, 180, 0, 170, 30);
    //   if (grados_hombro_sagital_izquierdo > 160){
    //     grados_hombro_sagital_izquierdo = 160;
    //   }
    //   grados_seguridad_hombro_sagital_izquierdo = grados_hombro_sagital_izquierdo;
    //   setServoPCA2(ServoHombroSagitalIzquierdoPin, grados_hombro_sagital_izquierdo);
    // }

    // if (codigo > 4600 && codigo < 4780) { //  codigo de hombro frontal 
    //   int grados_hombro_frontal_izquierdo = codigo - 4600;
    //   grados_hombro_frontal_izquierdo = map(grados_hombro_frontal_izquierdo, 0, 180, 13, 55);
    //   grados_seguridad_hombro_frontal_izquierdo = grados_hombro_frontal_izquierdo;

    //   setServoPCA2(ServoHombroFrontalIzquierdoPin, grados_hombro_frontal_izquierdo);
    // }

    // if (codigo >= 6400 && codigo <= 6580) { //  codigo de hombro rotacion
    //   int grados_hombro_rotacion_izquierdo = codigo - 6400;
    //   grados_hombro_rotacion_izquierdo = map(grados_hombro_rotacion_izquierdo, 180, 0, 10, 170);
    //   if (grados_hombro_rotacion_izquierdo < 50){
    //     if (grados_seguridad_hombro_frontal_izquierdo < 20 && grados_seguridad_hombro_sagital_izquierdo < 40){
    //       grados_hombro_rotacion_izquierdo = 50;
    //     }
    //   }
    //   setServoPCA2(ServoHombroRotacionIzquierdoPin, grados_hombro_rotacion_izquierdo);
    // }

    delay(10);
  }

  // Apagar muñeca luego de dos segundos
  if (Muneca_Izq_Pos_deseada == 0 || Muneca_Izq_Pos_deseada == 180){
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

        //DEDOS DE LA MANO DERECHA
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
  
    //DEDOS DE LA MANO IZQUIERDA
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
  

  mover_mandibula();

  // Girar cuello con millis
  if (Mover_cuello_lento != CuelloEjeX_Pos && Mover_cuello_lento != 0){
    static unsigned long tiempo_espera_cuello = 200; // tiempo entre movimientos
    unsigned long ahora_cuello = millis();
    if (CuelloEjeX_Pos < Mover_cuello_lento + 10 && CuelloEjeX_Pos > Mover_cuello_lento - 10){
      CuelloEjeX_Pos = Mover_cuello_lento;
    } else if (CuelloEjeX_Pos < Mover_cuello_lento && (ahora_cuello - cuello_last_update >= tiempo_espera_cuello)){
      CuelloEjeX_Pos += 5;
      cuello_last_update = ahora_cuello;
    } else if (CuelloEjeX_Pos > Mover_cuello_lento && (ahora_cuello - cuello_last_update >= tiempo_espera_cuello)){
      CuelloEjeX_Pos -= 5;
      cuello_last_update = ahora_cuello;
    }
        // Rectificador X
    if (CuelloEjeX_Pos >= max_X_cuello){
      CuelloEjeX_Pos = max_X_cuello;
    }
    if (CuelloEjeX_Pos <= min_X_cuello){
      CuelloEjeX_Pos = min_X_cuello;
    }
    // ServoCuelloEjeX.write(CuelloEjeX_Pos);
    setServoPCA2(ServoCuelloEjeXPin, CuelloEjeX_Pos);
  }
 

// vertical
  // if (Mover_cuello_lento_vertical != CuelloEjeY_Pos && Mover_cuello_lento_vertical != 0){
  //   static unsigned long tiempo_espera_cuello_vertical = 200; // tiempo entre movimientos
  //   unsigned long ahora_cuello_vertical = millis();
  //   if (CuelloEjeY_Pos < Mover_cuello_lento_vertical + 10 && CuelloEjeY_Pos > Mover_cuello_lento_vertical - 10){
  //     CuelloEjeY_Pos = Mover_cuello_lento_vertical;
  //   } else if (CuelloEjeY_Pos < Mover_cuello_lento_vertical && (ahora_cuello_vertical - cuello_last_update_vertical >= tiempo_espera_cuello_vertical)){
  //     CuelloEjeY_Pos += 5;
  //     cuello_last_update_vertical = ahora_cuello_vertical;
  //   } else if (CuelloEjeY_Pos > Mover_cuello_lento_vertical && (ahora_cuello_vertical - cuello_last_update_vertical >= tiempo_espera_cuello_vertical)){
  //     CuelloEjeY_Pos -= 5;
  //     cuello_last_update_vertical = ahora_cuello_vertical;
  //   }
  //       // Rectificador X
  //   if (CuelloEjeY_Pos >= max_Y_cuello){
  //     CuelloEjeY_Pos = max_Y_cuello;
  //   }
  //   if (CuelloEjeY_Pos <= min_Y_cuello){
  //     CuelloEjeY_Pos = min_Y_cuello;
  //   }
  //   ServoCuelloEjeY.write(CuelloEjeY_Pos);
  // }

}

void mover_mandibula() {
  static unsigned long tiempo_espera = 250; // tiempo entre movimientos
  if (mandibula_activa) {
    unsigned long ahora = millis();
    if (!mandibula_cerrar) {
      if (mandibula_estado == 0) {
        // ServoMandibula.write(119); // abrir
        setServoPCA2(ServoMandibulaPin, 119); // abrir
        mandibula_last_update = ahora;
        mandibula_estado = 1;
      } else if (mandibula_estado == 1 && (ahora - mandibula_last_update >= tiempo_espera)) {
        // ServoMandibula.write(100); // semi-cerrar
        setServoPCA2(ServoMandibulaPin, 100); // semi-cerrar
        mandibula_last_update = ahora;
        mandibula_estado = 2;
      } else if (mandibula_estado == 2 && (ahora - mandibula_last_update >= tiempo_espera)) {
        // ServoMandibula.write(85); // cerrar-hablando
        setServoPCA2(ServoMandibulaPin, 85); // cerrar-hablando
        mandibula_last_update = ahora;
        mandibula_estado = 3;

      } else if (mandibula_estado == 3 && (ahora - mandibula_last_update >= tiempo_espera)) {
        mandibula_estado = 0; // listo para el siguiente ciclo
      }
    }
    if (mandibula_cerrar) {
      // ServoMandibula.write(75); // cerrar completamente
      setServoPCA2(ServoMandibulaPin, 75); // cerrar completamente
      // una espera en millis() de medio segundo para devolver un grado y evitar que el motor se sobrecaliente
      
      // mandibula_last_update = ahora;
      // if (ahora - mandibula_last_update >= 500) {
      //   ServoMandibula.write(95);
      // }
      mandibula_activa = false;
      mandibula_estado = 0;
    }
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