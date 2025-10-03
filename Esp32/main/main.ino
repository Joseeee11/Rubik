#include "ESP32Servo.h"
// #include <Adafruit_PWMServoDriver.h>

// PCA
// Adafruit_PWMServoDriver pca1 = Adafruit_PWMServoDriver(0x40)

// CABEZA
int ServoMandibulaPin = 21;
int ServoOjoEjeXPin = 23;
int ServoOjoEjeYPin = 22;
int ServoCuelloEjeXPin = 19;

// TORSO
int ServoCuelloEjeYPin = 18;
int ServoClaviculaIzqPin = 2;
int ServoClaviculaDerPin = 15;

// BRAZO DERECHO
int ServoPulgarDerechoPin = 32;
int ServoIndiceDerechoPin = 33;
int ServoMedioDerechoPin = 25;
int ServoAnularDerechoPin = 26;
int ServoMeniqueDerechoPin = 27;
int ServoMunecaDerechoPin = 14;
int ServoBicepsDerechoPin = 12;

// BRAZO IZQUIERDO
int ServoPulgarIzquierdoPin = 23;
int ServoIndiceIzquierdoPin = 22;
int ServoMedioIzquierdoPin = 21;
int ServoAnularIzquierdoPin = 19;
int ServoMeniqueIzquierdoPin = 18;
int ServoMunecaIzquierdaPin = 17;
int ServoBicepsIzquierdoPin = 16;

Servo ServoMandibula;
Servo ServoOjoEjeX;
Servo ServoOjoEjeY;
Servo ServoCuelloEjeX;

Servo ServoCuelloEjeY;
Servo ServoClaviculaIzq;
Servo ServoClaviculaDer;

Servo ServoMunecaDerecho;
Servo ServoPulgarDerecho;
Servo ServoIndiceDerecho;
Servo ServoMedioDerecho;
Servo ServoAnularDerecho;
Servo ServoMeniqueDerecho;
Servo ServoBicepsDerecho;

Servo ServoMunecaIzquierda;
Servo ServoPulgarIzquierdo;
Servo ServoIndiceIzquierdo;
Servo ServoMedioIzquierdo;
Servo ServoAnularIzquierdo;
Servo ServoMeniqueIzquierdo;
Servo ServoBicepsIzquierdo;

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

// DERECHO
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

// IZQUIERDO
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

bool mandibula_activa = false; //para saber cuando esta activa la mandibula
bool mandibula_cerrar = true; //para saber si está abierta o cerrada

// Variables para control asíncrono de la mandíbula
unsigned long mandibula_last_update = 0;
int mandibula_estado = 0; // 0: inactiva, 1: abriendo, 2: cerrando

// Variables PCA
int Muneca_Derecha_Pos = 0;

void setup() {
  Serial.begin(115200);
  ServoMandibula.attach(ServoMandibulaPin);
  ServoOjoEjeY.attach(ServoOjoEjeYPin);
  ServoOjoEjeX.attach(ServoOjoEjeXPin);
  ServoCuelloEjeY.attach(ServoCuelloEjeYPin);
  ServoCuelloEjeX.attach(ServoCuelloEjeXPin);

  ServoClaviculaIzq.attach(ServoClaviculaIzqPin);
  ServoClaviculaDer.attach(ServoClaviculaDerPin);
  ServoMunecaDerecho.attach(ServoMunecaDerechoPin);

  ServoPulgarDerecho.attach(ServoPulgarDerechoPin);
  ServoIndiceDerecho.attach(ServoIndiceDerechoPin);
  ServoMedioDerecho.attach(ServoMedioDerechoPin);
  ServoAnularDerecho.attach(ServoAnularDerechoPin);
  ServoMeniqueDerecho.attach(ServoMeniqueDerechoPin);
  ServoMunecaDerecho.attach(ServoMunecaDerechoPin);
  ServoBicepsDerecho.attach(ServoBicepsDerechoPin);

  ServoPulgarIzquierdo.attach(ServoPulgarIzquierdoPin);
  ServoIndiceIzquierdo.attach(ServoIndiceIzquierdoPin);
  ServoMedioIzquierdo.attach(ServoMedioIzquierdoPin);
  ServoAnularIzquierdo.attach(ServoAnularIzquierdoPin);
  ServoMeniqueIzquierdo.attach(ServoMeniqueIzquierdoPin);
  ServoMunecaIzquierda.attach(ServoMunecaIzquierdaPin);
  ServoBicepsIzquierdo.attach(ServoBicepsIzquierdoPin);

  delay(100);

  ServoPulgarDerecho.write(0);
  ServoIndiceDerecho.write(0);
  ServoMedioDerecho.write(0);
  ServoAnularDerecho.write(180);
  ServoMeniqueDerecho.write(180);
  ServoMunecaDerecho.write(0);
  ServoBicepsDerecho.write(20);

  ServoPulgarIzquierdo.write(180);
  ServoIndiceIzquierdo.write(180);
  ServoMedioIzquierdo.write(0);
  ServoAnularIzquierdo.write(0);
  ServoMeniqueIzquierdo.write(0);
  ServoMunecaIzquierda.write(180);
  ServoBicepsIzquierdo.write(20);

  ServoCuelloEjeX.write(90);
  ServoOjoEjeY.write(140);
  ServoOjoEjeX.write(90);
  ServoPulgarDerecho.write(0);
  ServoIndiceDerecho.write(0);
  ServoMedioDerecho.write(0);
  ServoAnularDerecho.write(180);
  ServoMeniqueDerecho.write(180);
  ServoMunecaDerecho.write(0);

  delay(100);

  // pca1.begin();
  // pca1.setPWMFreq(50);
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

      //MUÑECA DERECHA
    if (codigo == 5001) {
      // Muneca_Der_Pos_deseada = 180;  //mostrar palma
      ServoMunecaDerecho.write(180);
    }
    if (codigo == 5000) {
      // Muneca_Der_Pos_deseada = 0;  //mostrar dorso
      ServoMunecaDerecho.write(0);
    }

      // MUÑECA IZQUIERDA
    if (codigo == 5002) {
      // Muneca_Der_Pos_deseada = 180;  //mostrar dorso
      ServoMunecaIzquierda.write(180);
    }
    if (codigo == 5003) {
      // Muneca_Der_Pos_deseada = 0;  //mostrar palma
      ServoMunecaIzquierda.write(0);
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
    if (codigo > 4000 && codigo < 4180) { //  codigo de biceps 
      // Biceps_Der_Pos_deseada = 20;
      int grados_biceps_derecho = codigo % 1000; // o usa codigo - 4000
      grados_biceps_derecho = map(grados_biceps_derecho, 180, 0, 20, 80);
      ServoBicepsDerecho.write(grados_biceps_derecho);
    }
    if (codigo > 4200 && codigo < 4280) { //  codigo de biceps 
      // Biceps_Der_Pos_deseada = 20;
      int grados_biceps_izquierdo = codigo - 4200
      grados_biceps_izquierdo = map(grados_biceps_izquierdo, 180, 0, 20, 80);
      ServoBicepsIzquierdo.write(grados_biceps_izquierdo);
    }
    delay(10);
  }

  if (Pulgar_Der_Pos_deseada == 0){
    Pulgar_Der_return = false;
    Pulgar_Der_Pos = 0;
    ServoPulgarDerecho.write(Pulgar_Der_Pos);
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
    ServoPulgarDerecho.write(Pulgar_Der_Pos);
  }

  // Indice

  if (Indice_Der_Pos_deseada == 0){
    Indice_Der_return = false;
    Indice_Der_Pos = 0;
    ServoIndiceDerecho.write(Indice_Der_Pos);
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
    ServoIndiceDerecho.write(Indice_Der_Pos);
  }

    // Medio

  if (Medio_Der_Pos_deseada == 0){
    Medio_Der_return = false;
    Medio_Der_Pos = 0;
    ServoMedioDerecho.write(Medio_Der_Pos);
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
    ServoMedioDerecho.write(Medio_Der_Pos);
  }

    // Anular
 
  if (Anular_Der_Pos_deseada == 180){
    Anular_Der_return = false;
    Anular_Der_Pos = 180;
    ServoAnularDerecho.write(Anular_Der_Pos);
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
    ServoAnularDerecho.write(Anular_Der_Pos);
  }

      // Menique

  if (Menique_Der_Pos_deseada == 180){
    Menique_Der_return = false;
    Menique_Der_Pos = 180;
    ServoMeniqueDerecho.write(Menique_Der_Pos);
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
    ServoMeniqueDerecho.write(Menique_Der_Pos);
  }
  



    // Regresar 15° (cuando están recogido) los dedos para apagar servomotor y evitar calentamiento
  if (Pulgar_Izq_Pos_deseada == 180){
    Pulgar_Izq_return = false;
    Pulgar_Izq_Pos = 180;
    ServoPulgarIzquierdo.write(Pulgar_Izq_Pos);
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
    ServoPulgarIzquierdo.write(Pulgar_Izq_Pos);
  }

  // Indice

  if (Indice_Izq_Pos_deseada == 180){
    Indice_Izq_return = false;
    Indice_Izq_Pos = 180;
    ServoIndiceIzquierdo.write(Indice_Izq_Pos);
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
    ServoIndiceIzquierdo.write(Indice_Izq_Pos);
  }

    // Medio

  if (Medio_Izq_Pos_deseada == 0){
    Medio_Izq_return = false;
    Medio_Izq_Pos = 0;
    ServoMedioIzquierdo.write(Medio_Izq_Pos);
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
    ServoMedioIzquierdo.write(Medio_Izq_Pos);
  }

    // Anular

  if (Anular_Izq_Pos_deseada == 0){ //abrir
    Anular_Izq_return = false;
    Anular_Izq_Pos = 0;
    ServoAnularIzquierdo.write(Anular_Izq_Pos);
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
    ServoAnularIzquierdo.write(Anular_Izq_Pos);
  }

      // Menique

  if (Menique_Izq_Pos_deseada == 0){
    Menique_Izq_return = false;
    Menique_Izq_Pos = 0;
    ServoMeniqueIzquierdo.write(Menique_Izq_Pos);
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
    ServoMeniqueIzquierdo.write(Menique_Izq_Pos);
  }
  

  mover_mandibula();

  // if (Pulgar_Pos_deseada < Pulgar_ultima_Pos) {
  //   Pulgar_Direccion = -1;
  // } else if (Pulgar_Pos_deseada > Pulgar_ultima_Pos) {
  //   Pulgar_Direccion = 1;
  // }

  // if(Pulgar_Pos != Pulgar_Pos_deseada){
  //   static unsigned long tiempo_espera_pulgar = 100; // tiempo entre movimientos
  //   unsigned long ahora_pulgar = millis();
  //   if (Pulgar_Direccion > 0 && (ahora_pulgar - pulgar_last_update >= tiempo_espera_pulgar)) {
  //     Pulgar_Pos += 5;
  //     pulgar_last_update = ahora_pulgar;
  //   } else if (Pulgar_Direccion < 0 && (ahora_pulgar - pulgar_last_update >= tiempo_espera_pulgar)) {
  //     Pulgar_Pos -= 5;
  //     pulgar_last_update = ahora_pulgar;
  //   }

  //   if (Pulgar_Pos >= Dedos_max){
  //     Pulgar_Pos = Dedos_max;
  //   }
  //   if (Pulgar_Pos <= Dedos_min){
  //     Pulgar_Pos = Dedos_min;
  //   }
  //   ServoPulgarDerecho.write(Pulgar_Pos);

  // } else {
  //   Pulgar_ultima_Pos = Pulgar_Pos_deseada;
  //   Pulgar_Pos = Pulgar_ultima_Pos;
  // }
  

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

}

void mover_mandibula() {
  static unsigned long tiempo_espera = 250; // tiempo entre movimientos
  if (mandibula_activa) {
    unsigned long ahora = millis();
    if (!mandibula_cerrar) {
      if (mandibula_estado == 0) {
        ServoMandibula.write(119); // abrir
        mandibula_last_update = ahora;
        mandibula_estado = 1;
      } else if (mandibula_estado == 1 && (ahora - mandibula_last_update >= tiempo_espera)) {
        ServoMandibula.write(100); // semi-cerrar
        mandibula_last_update = ahora;
        mandibula_estado = 2;
      } else if (mandibula_estado == 2 && (ahora - mandibula_last_update >= tiempo_espera)) {
        ServoMandibula.write(85); // cerrar-hablando
        mandibula_last_update = ahora;
        mandibula_estado = 3;

      } else if (mandibula_estado == 3 && (ahora - mandibula_last_update >= tiempo_espera)) {
        mandibula_estado = 0; // listo para el siguiente ciclo
      }
    }
    if (mandibula_cerrar) {
      ServoMandibula.write(75); // cerrar completamente
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

