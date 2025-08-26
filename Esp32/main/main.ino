#include "ESP32Servo.h"

int ServoMandibulaPin = 21;
int ServoOjoEjeXPin = 23;
int ServoOjoEjeYPin = 22;
int ServoCuelloEjeXPin = 19;
int ServoCuelloEjeYPin = 18;
int ServoPulgarPin = 14;
int ServoIndicePin = 13;
int ServoMedioPin = 4;
int ServoAnularPin = 17;
int ServoMeniquePin = 16;

Servo ServoMandibula;
Servo ServoOjoEjeX;
Servo ServoOjoEjeY;
Servo ServoCuelloEjeX;
Servo ServoCuelloEjeY;
Servo ServoPulgar;
Servo ServoIndice;
Servo ServoMedio;
Servo ServoAnular;
Servo ServoMenique;

int OjoEjeX_Pos = 90;
int CuelloEjeX_Pos = 90;
int CuelloEjeY_Pos = 90;
int OjoEjeY_Pos = 140;

int codigo=0;
int min_Y_ojo = 100;
int max_Y_ojo = 180;
int min_X_ojo = 60;
int max_X_ojo = 130;
int min_X_cuello = 10;
int max_X_cuello = 170;
int min_Y_cuello = 60;
int max_Y_cuello = 120;

int Mover_cuello_lento = 0;
unsigned long cuello_last_update = 0;
int Mover_cuello_lento_vertical = 0;
unsigned long cuello_last_update_vertical = 0;

bool mandibula_activa = false; //para saber cuando esta activa la mandibula
bool mandibula_cerrar = true; //para saber si está abierta o cerrada

// Variables para control asíncrono de la mandíbula
unsigned long mandibula_last_update = 0;
int mandibula_estado = 0; // 0: inactiva, 1: abriendo, 2: cerrando

void setup() {
  Serial.begin(115200);
  ServoMandibula.attach(ServoMandibulaPin);
  ServoOjoEjeY.attach(ServoOjoEjeYPin);
  ServoOjoEjeX.attach(ServoOjoEjeXPin);
  ServoCuelloEjeX.attach(ServoCuelloEjeXPin);
  delay(100);

  ServoCuelloEjeX.write(90);
  ServoOjoEjeY.write(140);
  ServoOjoEjeX.write(90);
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
        ServoMandibula.write(150); // abrir
    }else if (codigo == 3110){
        ServoMandibula.write(90); // cerrar completamente
    }
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

    if (codigo == 2545) { //cuello ARRIBA VERTICAL
      Mover_cuello_lento_vertical = min_Y_cuello + 20;
    } else if (codigo == 2550) { //cuello ABAJO
      Mover_cuello_lento_vertical = max_Y_cuello - 20;
    } else if (codigo == 2555) { //cuello CENTRO
      Mover_cuello_lento_vertical = 90;
    } else if(!(codigo >= 2500 && codigo <=2999)){
      Mover_cuello_lento_vertical = 0;
    }

// codigo != 3105 && codigo != 3110 && codigo != 3005 && codigo != 3010
    
    
    
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
      OjoEjeX_Pos = 90;
    }

    if (codigo == 1020) { //arriba
      OjoEjeY_Pos = 100;
    } else if (codigo == 1025) { //abajo
      OjoEjeY_Pos = 180;
    } else if (codigo == 1030){
      OjoEjeY_Pos = 140;
    }
    // Rectificador X
    if (CuelloEjeX_Pos >= max_X_cuello){
      CuelloEjeX_Pos = max_X_cuello;
    }
    if (CuelloEjeX_Pos <= min_X_cuello){
      CuelloEjeX_Pos = min_X_cuello;
    }
    ServoOjoEjeY.write(OjoEjeY_Pos);
    ServoOjoEjeX.write(OjoEjeX_Pos);
    ServoCuelloEjeX.write(CuelloEjeX_Pos);
    delay(10);
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
    ServoCuelloEjeX.write(CuelloEjeX_Pos);
  }



// vertical
  if (Mover_cuello_lento_vertical != CuelloEjeY_Pos && Mover_cuello_lento_vertical != 0){
    static unsigned long tiempo_espera_cuello_vertical = 200; // tiempo entre movimientos
    unsigned long ahora_cuello_vertical = millis();
    if (CuelloEjeY_Pos < Mover_cuello_lento_vertical + 10 && CuelloEjeY_Pos > Mover_cuello_lento_vertical - 10){
      CuelloEjeY_Pos = Mover_cuello_lento_vertical;
    } else if (CuelloEjeY_Pos < Mover_cuello_lento_vertical && (ahora_cuello_vertical - cuello_last_update_vertical >= tiempo_espera_cuello_vertical)){
      CuelloEjeY_Pos += 5;
      cuello_last_update_vertical = ahora_cuello_vertical;
    } else if (CuelloEjeY_Pos > Mover_cuello_lento_vertical && (ahora_cuello_vertical - cuello_last_update_vertical >= tiempo_espera_cuello_vertical)){
      CuelloEjeY_Pos -= 5;
      cuello_last_update_vertical = ahora_cuello_vertical;
    }
        // Rectificador X
    if (CuelloEjeY_Pos >= max_Y_cuello){
      CuelloEjeY_Pos = max_Y_cuello;
    }
    if (CuelloEjeY_Pos <= min_Y_cuello){
      CuelloEjeY_Pos = min_Y_cuello;
    }
    ServoCuelloEjeY.write(CuelloEjeY_Pos);
  }

  //DEDOS DE LA MANO
  if (codigo == 5510) { //  Numeros par cierra 
    ServoMedio.write(0);
  } else if (codigo == 5511) { //  Numeros impar abre
    ServoMedio.write(90);
  } else if (codigo == 5512) {
    ServoAnular.write(0);
  } else if (codigo == 5513) {
    ServoAnular.write(90);
  } else if (codigo == 5514) {
    ServoMenique.write(90);
  } else if (codigo == 5515) {
    ServoMenique.write(180);
  } else if (codigo == 5516) {
    ServoIndice.write(0);
  } else if (codigo == 5517) {
    ServoIndice.write(90);
  } else if (codigo == 5518) {
    ServoPulgar.write(90);
  } else if (codigo == 5519) {
    ServoPulgar.write(180);
  }

}

void mover_mandibula() {
  static unsigned long tiempo_espera = 200; // tiempo entre movimientos
  if (mandibula_activa) {
    unsigned long ahora = millis();
    if (!mandibula_cerrar) {
      if (mandibula_estado == 0) {
        ServoMandibula.write(150); // abrir
        mandibula_last_update = ahora;
        mandibula_estado = 1;
      } else if (mandibula_estado == 1 && (ahora - mandibula_last_update >= tiempo_espera)) {
        ServoMandibula.write(110); // semi-cerrar
        mandibula_last_update = ahora;
        mandibula_estado = 2;
      } else if (mandibula_estado == 2 && (ahora - mandibula_last_update >= tiempo_espera)) {
        mandibula_estado = 0; // listo para el siguiente ciclo
      }
    }
    if (mandibula_cerrar) {
      ServoMandibula.write(90); // cerrar completamente
      mandibula_activa = false;
      mandibula_estado = 0;
    }
  }
}


