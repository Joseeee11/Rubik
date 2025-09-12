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
int ServoClaviculaIzqPin = 2;
int ServoClaviculaDerPin = 15;
int ServoMunecaPin = 27;

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
Servo ServoClaviculaIzq;
Servo ServoClaviculaDer;
Servo ServoMuneca;

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

int Dedos_max = 180;
int Dedos_min = 0;
int Pulgar_Pos_deseada = 0;
bool Pulgar_return = false;
int Pulgar_Pos = 0;
unsigned long Pulgar_last_update = 0;
int Indice_Pos_deseada = 0;
bool Indice_return = false;
int Indice_Pos = 0;
unsigned long Indice_last_update = 0;
int Medio_Pos_deseada = 0;
bool Medio_return = false;
int Medio_Pos = 0;
unsigned long Medio_last_update = 0;
int Anular_Pos_deseada = 180;
bool Anular_return = false;
int Anular_Pos = 180;
unsigned long Anular_last_update = 0;  int Menique_Pos_deseada = 180;
bool Menique_return = false;
int Menique_Pos = 180;
unsigned long Menique_last_update = 0;



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
  ServoCuelloEjeY.attach(ServoCuelloEjeYPin);
  ServoCuelloEjeX.attach(ServoCuelloEjeXPin);
  ServoPulgar.attach(ServoPulgarPin);
  ServoIndice.attach(ServoIndicePin);
  ServoMedio.attach(ServoMedioPin);
  ServoAnular.attach(ServoAnularPin);
  ServoMenique.attach(ServoMeniquePin);
  ServoClaviculaIzq.attach(ServoClaviculaIzqPin);
  ServoClaviculaDer.attach(ServoClaviculaDerPin);
  ServoMuneca.attach(ServoMunecaPin);
  delay(100);

  ServoCuelloEjeX.write(90);
  ServoOjoEjeY.write(140);
  ServoOjoEjeX.write(90);
  ServoPulgar.write(0);
  ServoIndice.write(0);
  ServoMedio.write(0);
  ServoAnular.write(180);
  ServoMenique.write(180);
  ServoMuneca.write(0);

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

        //MUÑECA
    if (codigo == 5001) {
      ServoMuneca.write(180);  //mostrar dorso
    }
    if (codigo == 5000) {
      ServoMuneca.write(0);  //mostrar palma
    }

        //DEDOS DE LA MANO
    if (codigo == 5510) { //  Numeros par cierra 
      Medio_Pos_deseada = 180;
    }
    if (codigo == 5511) { //  Numeros impar abre
      Medio_Pos_deseada = 0;
    } 
    if (codigo == 5512) {
      Anular_Pos_deseada = 0;
    } 
    if (codigo == 5513) {
      Anular_Pos_deseada = 180;
    } 
    if (codigo == 5514) {
      Menique_Pos_deseada = 0;
    } 
    if (codigo == 5515) {
      Menique_Pos_deseada = 180;
    } 
    if (codigo == 5516) {
      Indice_Pos_deseada = 180;
    } 
    if (codigo == 5517) {
      Indice_Pos_deseada = 0;
    } 
    if (codigo == 5518) {
      Pulgar_Pos_deseada = 180;
    } 
    if (codigo == 5519) {
      Pulgar_Pos_deseada = 0;
    }
    delay(10);
  }

  // Regresar 15° (cuando están recogido) los dedos para apagar servomotor y evitar calentamiento
  if (Pulgar_Pos_deseada == 0){
    Pulgar_return = false;
    Pulgar_Pos = 0;
    ServoPulgar.write(Pulgar_Pos);
    Pulgar_last_update = millis();
  }
  if (Pulgar_Pos_deseada == 180){
    static unsigned long tiempo_espera_pulgar = 1500;
    unsigned long ahora_pulgar = millis();
    if((ahora_pulgar - Pulgar_last_update >= tiempo_espera_pulgar)&&!Pulgar_return){
      Pulgar_return = true;
    }
    if(!Pulgar_return){
      Pulgar_Pos = 180;
    }else{
      Pulgar_Pos = 165;
    }
    ServoPulgar.write(Pulgar_Pos);
  }

  // Indice

  if (Indice_Pos_deseada == 0){
    Indice_return = false;
    Indice_Pos = 0;
    ServoIndice.write(Indice_Pos);
    Indice_last_update = millis();
  }
  if (Indice_Pos_deseada == 180){
    static unsigned long tiempo_espera_indice = 1500;
    unsigned long ahora_indice = millis();
    if((ahora_indice - Indice_last_update >= tiempo_espera_indice)&&!Indice_return){
      Indice_return = true;
    }
    if(!Indice_return){
      Indice_Pos = 180;
    }else{
      Indice_Pos = 165;
    }
    ServoIndice.write(Indice_Pos);
  }

    // Medio

  if (Medio_Pos_deseada == 0){
    Medio_return = false;
    Medio_Pos = 0;
    ServoMedio.write(Medio_Pos);
    Medio_last_update = millis();
  }
  if (Medio_Pos_deseada == 180){
    static unsigned long tiempo_espera_medio = 1500;
    unsigned long ahora_medio = millis();
    if((ahora_medio - Medio_last_update >= tiempo_espera_medio)&&!Medio_return){
      Medio_return = true;
    }
    if(!Medio_return){
      Medio_Pos = 180;
    }else{
      Medio_Pos = 165;
    }
    ServoMedio.write(Medio_Pos);
  }

    // Anular
 
  if (Anular_Pos_deseada == 180){
    Anular_return = false;
    Anular_Pos = 180;
    ServoAnular.write(Anular_Pos);
    Anular_last_update = millis();
  }
  if (Anular_Pos_deseada == 0){
    static unsigned long tiempo_espera_anular = 1500;
    unsigned long ahora_anular = millis();
    if((ahora_anular - Anular_last_update >= tiempo_espera_anular)&&!Anular_return){
      Anular_return = true;
    }
    if(!Anular_return){
      Anular_Pos = 0;
    }else{
      Anular_Pos = 15;
    }
    ServoAnular.write(Anular_Pos);
  }

      // Menique

  if (Menique_Pos_deseada == 180){
    Menique_return = false;
    Menique_Pos = 180;
    ServoMenique.write(Menique_Pos);
    Menique_last_update = millis();
  }
  if (Menique_Pos_deseada == 0){
    static unsigned long tiempo_espera_menique = 1500;
    unsigned long ahora_menique = millis();
    if((ahora_menique - Menique_last_update >= tiempo_espera_menique)&&!Menique_return){
      Menique_return = true;
    }
    if(!Menique_return){
      Menique_Pos = 0;
    }else{
      Menique_Pos = 15;
    }
    ServoMenique.write(Menique_Pos);
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
  //   ServoPulgar.write(Pulgar_Pos);

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

