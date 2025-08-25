from tkinter import *
import cv2
import mediapipe as mp
from PIL import Image, ImageTk
import numpy as np
import time
import imutils
import tkinter as tk
import sys
import pyaudio
import speech_recognition as sr
import pocketsphinx
from groq import Groq
import threading
import pyttsx3
from tkinter import ttk
import queue
import math

## pyinstaller --icon=icono.ico --add-data "icono.ico;." main.py
## al compilar recordar que se deben incluir los archivos de modelo y los recursos necesarios

## importar modulos personalizados
from Clavicula import Calcular_distancia_Punto_a_RectaAB, punto_medio_segmento
from esp32 import iniciar_conexion_serial, enviar_esp32, cerrar_serial, listar_seriales
# para la hora actual quitar si se hace de otra manera
from datetime import datetime

# --- ESP32 Serial ---
# # Importar la biblioteca de comunicación serial
# import serial
# Configuración del puerto serial (ajusta según tu configuración)
ser = None
# esp32.py
def listar_puertos_seriales():
    global ser
    listar_seriales(encabezado, color, cerrar_conexion_serial, ser, actualizar_ser)
def actualizar_ser(nuevo_ser): ## una función para actualizar el puerto serial, ya que desde esp32.py no se puede actualizar el main.py
    global ser
    ser = nuevo_ser
def cerrar_conexion_serial():
    print("Cerrando conexión serial...")
    global ser
    cerrar_serial(ser)
def enviar_comando_esp32(comando):
    global ser
    enviar_esp32(comando, ser)

# --- Funciones de Lógica con IA ---
drawing = mp.solutions.drawing_utils
drawing_styles= mp.solutions.drawing_styles
mediaPipe = mp.solutions.holistic

holistic = mediaPipe.Holistic(
    min_detection_confidence=0.8,
    min_tracking_confidence=0.8,
    smooth_landmarks=True,
    model_complexity=0,
    enable_segmentation=True,
)
pintar = False

def iniciar():
    global cap
    # Inicializa la cámara
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        mainApp.destroy()
        return
    visualizar()
    listar_dispositivos_audio()


# --- Funciones de Lógica con Visión Artificial ---
# Variables globales
palma_puntos=[0,1,2,5,9,13,17]
pulgar_puntos=[1,2,4]
punta_puntos=[8,12,16,20]
base_puntos=[6,10,14,18]

EjeY = "Centro"
EjeX = "Centro"


# Función para visualizar la cámara y procesar la imagen
seguir_vision = None  # Variable para seguir la visión de la cámara
punto_seguir = None  # Variable para almacenar el punto a seguir
imitar_vision = None  # Variable para imitar la visión de la cámara
media_imitar_rostro = None  # Variable para almacenar la media del rostro imitado
media_imitar_boca = None  # Variable para almacenar la media de la boca imitada
media_imitar_cara_vertical = None  # Variable para almacenar la media de la boca imitada
palma_puntos = [0,1,2,5,9,13,17]
pulgar_puntos = [1,2,4]
punta_puntos = [8,12,16,20]
base_puntos = [6,10,14,18]
def visualizar():
    global cap
    global pintar
    global EjeY, EjeX
    global seguir_vision, punto_seguir, imitar_vision
    # Lee un fotograma de la cámara
    if cap is not None:
        ret, frame = cap.read()
        if ret == True:
            frame = imutils.resize(frame, width=1200)
            height, width, _ = frame.shape
            # Convierte el fotograma a RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # if check_var_IAvision.get():
            result = holistic.process(frame_rgb)
            # print(result.left_hand_landmarks)
            pintar = True
                    # Verifica si se detectaron puntos de referencia
            if seguir_vision in ["Mano", "Cara", "Cuerpo", "Mano izquierda", "Mano derecha"]:
                # Inicializa el punto a seguir como None
                if seguir_vision == "Mano" or seguir_vision == "Mano izquierda" or seguir_vision == "Mano derecha":
                    if (result.left_hand_landmarks is not None or result.right_hand_landmarks is not None):
                        palma_coordenadas = []
                        # pulgar_coordenadas = []
                        # punta_coordenadas = []
                        # base_coordenadas = []
                        if seguir_vision == "Mano izquierda":
                            if result.left_hand_landmarks is not None:
                                Mano = result.left_hand_landmarks
                            else:
                                Mano = None
                        elif seguir_vision == "Mano derecha":
                            if result.right_hand_landmarks is not None:
                                Mano = result.right_hand_landmarks
                            else:
                                Mano = None
                        elif seguir_vision == "Mano":
                            if result.left_hand_landmarks is not None and result.right_hand_landmarks is not None:
                                Mano= result.right_hand_landmarks
                            elif result.left_hand_landmarks is not None:
                                Mano = result.left_hand_landmarks
                            elif result.right_hand_landmarks is not None:
                                Mano = result.right_hand_landmarks
                            else:
                                Mano = None
                       
                    
                    
                        # for i in pulgar_puntos:
                        #     x = int(Mano.landmark[i].x * width)
                        #     y = int(Mano.landmark[i].y * height)
                        #     pulgar_coordenadas.append([x, y])

                        # for i in punta_puntos:
                        #     x = int(Mano.landmark[i].x * width)
                        #     y = int(Mano.landmark[i].y * height)
                        #     punta_coordenadas.append([x, y])

                        # for i in base_puntos:
                        #     x = int(Mano.landmark[i].x * width)
                        #     y = int(Mano.landmark[i].y * height)
                        #     base_coordenadas.append([x, y])
                        if Mano is not None:
                            for i in palma_puntos:
                                x = int(Mano.landmark[i].x * width)
                                y = int(Mano.landmark[i].y * height)
                                palma_coordenadas.append([x, y])
                            
                            punto_seguir = palma_centroCoordenadas(palma_coordenadas)
                    else:
                        punto_seguir = None
                        
                if seguir_vision == "Cara":
                    if result.face_landmarks is not None:
                        # Obtener las coordenadas del centro de la cara
                        x = int(result.face_landmarks.landmark[4].x * width) # Coordenada X del punto de la nariz
                        y = int(result.face_landmarks.landmark[4].y * height) # Coordenada Y del punto de la nariz
                        punto_seguir = (x, y)
                    else:
                        punto_seguir = None

                if seguir_vision == "Cuerpo":
                    if result.pose_landmarks is not None:
                        # Verificar que todos los landmarks requeridos existen
                        pose_landmarks = result.pose_landmarks.landmark
                        required_indices = [11, 12, 23, 24]
                        if all(i < len(pose_landmarks) and pose_landmarks[i].visibility > 0.5 for i in required_indices):
                            # Obtener el centro del cuerpo (cadera)
                            # Obtener las coordenadas de la cadera (landmark 24 y 23) y los hombros (landmark 11 y 12)
                            cadera_izq = pose_landmarks[23]
                            cadera_der = pose_landmarks[24]
                            hombro_izq = pose_landmarks[11]
                            hombro_der = pose_landmarks[12]

                            # Calcular el punto medio de la cadera
                            cadera_x = int(((cadera_izq.x + cadera_der.x) / 2) * width)
                            cadera_y = int(((cadera_izq.y + cadera_der.y) / 2) * height)

                            # Calcular el punto medio de los hombros
                            hombro_x = int(((hombro_izq.x + hombro_der.x) / 2) * width)
                            hombro_y = int(((hombro_izq.y + hombro_der.y) / 2) * height)

                            # Calcular el punto medio entre cadera y hombros
                            punto_seguir = (int((cadera_x + hombro_x) / 2), int((cadera_y + hombro_y) / 2))
                        else:
                            punto_seguir = None
                    else:
                        punto_seguir = None

                if punto_seguir is not None:
                    
                    cv2.circle(frame, punto_seguir, 5, (0, 255, 0), -1)
                    # Dividir la pantalla en 6 partes
                    for i in range(1, 6):
                        # Líneas verticales
                        cv2.line(frame, (i * width // 6, 0), (i * width // 6, height), (255, 0, 0), 1)
                        # Líneas horizontales
                        cv2.line(frame, (0, i * height // 6), (width, i * height // 6), (255, 0, 0), 1)

                    # Determinar si el centro está a la izquierda, muy izquierda, centro, derecha o muy derecha
                    centro_x = punto_seguir[0]
                    if centro_x < (width // 6):  # Muy izquierda (primer sexto)
                        print("Muy izquierda")
                        enviar_comando_esp32(2015)
                    elif centro_x < (width // 3):  # Izquierda (primer tercio, pero no tan al borde)
                        if EjeX != "Izquierda":
                            enviar_comando_esp32(1005)
                            EjeX = "Izquierda"
                        print("Izquierda")
                    elif centro_x < (width * 2 // 3):  # Centro
                        print("Centro")
                        if EjeX != "Centro":
                            enviar_comando_esp32(1000)
                            EjeX = "Centro"
                    elif centro_x < (width * 5 // 6):  # Derecha (pero no muy derecha)
                        print("Derecha")
                        if EjeX != "Derecha":
                            enviar_comando_esp32(1010)
                            EjeX = "Derecha"
                    else:  # Muy derecha (último sexto)
                        enviar_comando_esp32(2010)
                        print("Muy derecha")
                    # Determinar si el centro está arriba o abajo
                    centro_y = punto_seguir[1]
                    if centro_y < (height // 2) - (height // 7):  # Arriba
                        if EjeY != "Arriba":
                            enviar_comando_esp32(1020) # Enviar comando al ESP32 para indicar que está arriba
                            EjeY = "Arriba"
                        print("Arriba")
                    elif centro_y > (height // 2) + (height // 7):  # Abajo
                        if EjeY != "Abajo":
                            enviar_comando_esp32(1025) # Enviar comando al ESP32 para indicar que está abajo
                            EjeY = "Abajo"
                        print("Abajo")
                    else:  # Centro
                        if EjeY != "Centro":
                            enviar_comando_esp32(1030) # Enviar comando al ESP32 para indicar que está en el centro del eje Y
                            EjeY = "Centro"
                        print("Centro Y")

            if imitar_vision in ["Cara"] and result.face_landmarks is not None:
                # Inicializa el punto a seguir como None
                # if imitar_vision == "Cara": #para que es esto??
                landmarks = result.face_landmarks.landmark
                # Puntos de referencia
                x_nariz = int(landmarks[4].x * width)
                y_nariz = int(landmarks[4].y * height)
                # Extremos de la cara (usando landmarks de la mandíbula)
                x_izquierda = int(landmarks[234].x * width)  # lado izquierdo de la cara
                y_izquierda = int(landmarks[234].y * height)  # lado izquierdo de la cara
                x_derecha = int(landmarks[454].x * width)    # lado derecho de la cara
                y_derecha = int(landmarks[454].y * height)  # lado derecho de la cara

                # Calcular la proporción de la nariz entre los extremos
                d_nariz_derecha= math.sqrt(abs((x_derecha - x_nariz) ** 2 + (y_derecha - y_nariz) ** 2))
                d_nariz_izquierda = math.sqrt(abs((x_izquierda - x_nariz) ** 2 + (y_izquierda - y_nariz) ** 2))
                d_total_lados = d_nariz_derecha + d_nariz_izquierda
                # Calcular el porcentaje de la nariz respecto a los extremos
                if d_total_lados > 0:
                    proporcion_nariz = (d_nariz_izquierda * 100) / d_total_lados
                    # Determinar la zona de la cara
                    if proporcion_nariz <= 20:
                        zona = "Muy izquierda"
                    elif proporcion_nariz > 20 and proporcion_nariz <= 40:
                        zona = "Izquierda"
                    elif proporcion_nariz > 40 and proporcion_nariz <= 60:
                        zona = "Centro"
                    elif proporcion_nariz > 60 and proporcion_nariz <= 80:
                        zona = "Derecha"
                    elif proporcion_nariz > 80 and proporcion_nariz <= 100:
                        zona = "Muy derecha"
                # --- Suavizado de la clasificación de la cara ---
                    # Inicializar la lista de historial si es necesario
                    global media_imitar_rostro
                    if media_imitar_rostro is None or not isinstance(media_imitar_rostro, list):
                        media_imitar_rostro = []
                    media_imitar_rostro.append(zona)
                    # Mantener solo los últimos 5 valores
                    if len(media_imitar_rostro) > 5:
                        media_imitar_rostro.pop(0)

                    # Determinar si todos los últimos 5 valores son iguales
                    if len(media_imitar_rostro) == 5 and all(z == media_imitar_rostro[0] for z in media_imitar_rostro):
                        zona_media = media_imitar_rostro[0]
                        # Solo imprimir si hay un cambio respecto a la última zona impresa
                        if not hasattr(visualizar, "ultima_zona_media") or visualizar.ultima_zona_media != zona_media:
                            # print(zona_media)
                            # Enviar comando al ESP32 según la zona media
                            if zona_media == "Muy izquierda":
                                enviar_comando_esp32(2505)
                            elif zona_media == "Izquierda":
                                enviar_comando_esp32(2510)
                            elif zona_media == "Centro":
                                enviar_comando_esp32(2515)
                            elif zona_media == "Derecha":
                                enviar_comando_esp32(2520)
                            elif zona_media == "Muy derecha":
                                enviar_comando_esp32(2525)
                            # Guardar la última zona media para comparar en la próxima iteración
                            visualizar.ultima_zona_media = zona_media
                else:
                    # Reiniciar historial si no hay rango válido
                    media_imitar_rostro = []
                # --- Detección de boca abierta/cerrada con suavizado ---
                # Usar landmarks de la boca: superior (13), inferior (14), izquierda (78), derecha (308)
                y_boca_sup = int(landmarks[13].y * height)
                y_boca_inf = int(landmarks[14].y * height)
                x_boca_izq = int(landmarks[78].x * width)
                x_boca_der = int(landmarks[308].x * width)
                # Distancia vertical (apertura)
                distancia_boca = abs(y_boca_inf - y_boca_sup)
                # Distancia horizontal (ancho de la boca)
                ancho_boca = abs(x_boca_der - x_boca_izq)
                # Relación apertura/ancho para normalizar
                if ancho_boca > 0:
                    proporcion_apertura = distancia_boca / ancho_boca
                    # Umbral empírico para boca abierta/cerrada
                    estado_boca = "Abierta" if proporcion_apertura > 0.28 else "Cerrada"
                    # Suavizado: mantener historial de los últimos 5 estados
                    global media_imitar_boca
                    if media_imitar_boca is None or not isinstance(media_imitar_boca, list):
                        media_imitar_boca = []
                    media_imitar_boca.append(estado_boca)
                    if len(media_imitar_boca) > 5:
                        media_imitar_boca.pop(0)
                    # Si los últimos 5 son iguales, considerar estable
                    if len(media_imitar_boca) == 5 and all(e == media_imitar_boca[0] for e in media_imitar_boca):
                        estado_estable = media_imitar_boca[0]
                        if not hasattr(visualizar, "ultimo_estado_boca") or visualizar.ultimo_estado_boca != estado_estable:
                            print("Boca:", estado_estable)
                            # Enviar comando al ESP32 según el estado de la boca
                            if estado_estable == "Abierta":
                                enviar_comando_esp32(3105)
                            elif estado_estable == "Cerrada":
                                enviar_comando_esp32(3110)
                            # Guardar el último estado de la boca para comparar en la próxima iteración
                            visualizar.ultimo_estado_boca = estado_estable
                else:
                    media_imitar_boca = []
                # --- Detección de posición de la cabeza horizontal ---
                # Usar landmarks de la cara: cabeza izquierda (234), cabeza derecha (454), hombro izquierdo (11), hombro derecho (12)
                if result.face_landmarks is not None and result.pose_landmarks is not None:
                    face_landmarks = result.face_landmarks.landmark
                    shoulder_landmarks = result.pose_landmarks.landmark
                    x_cabeza_izq = int(face_landmarks[234].x * width)
                    y_cabeza_izq = int(face_landmarks[234].y * height)
                    x_cabeza_der = int(face_landmarks[454].x * width)
                    y_cabeza_der = int(face_landmarks[454].y * height)
                    x_hombro_der = int(shoulder_landmarks[11].x * width)
                    y_hombro_der = int(shoulder_landmarks[11].y * height)
                    x_hombro_izq = int(shoulder_landmarks[12].x * width)
                    y_hombro_izq = int(shoulder_landmarks[12].y * height)
                    # Calcular distancias
                    distancia_inclinacion_izq, punto_interseccion_izq = Calcular_distancia_Punto_a_RectaAB(x_hombro_izq, y_hombro_izq, x_hombro_der, y_hombro_der, x_cabeza_izq, y_cabeza_izq)
                    distancia_inclinacion_der, punto_interseccion_der = Calcular_distancia_Punto_a_RectaAB(x_hombro_izq, y_hombro_izq, x_hombro_der, y_hombro_der, x_cabeza_der, y_cabeza_der)
                    porcentaje_inclinacion = distancia_inclinacion_izq + distancia_inclinacion_der
                    distancia_inclinacion_izq_porcentaje = (distancia_inclinacion_izq * 100) / porcentaje_inclinacion if porcentaje_inclinacion > 0 else 0
                    distancia_inclinacion_der_porcentaje = (distancia_inclinacion_der * 100) / porcentaje_inclinacion if porcentaje_inclinacion > 0 else 0
                    ## graficar las distancias
                    # Dibujar líneas de inclinación
                    cv2.circle(frame, (x_hombro_izq, y_hombro_izq), 5, (51, 153, 255), -1)  # Hombro izquierdo
                    cv2.circle(frame, (x_hombro_der, y_hombro_der), 5, (0, 255, 0), -1)  # Hombro derecho
                    # sacar punto medio para hombro izquierdo y derecho
                    punto_medio_hombros = punto_medio_segmento((x_hombro_izq, y_hombro_izq), (x_hombro_der, y_hombro_der))
                    cv2.line(frame, (x_hombro_izq, y_hombro_izq), (int(punto_medio_hombros[0]), int(punto_medio_hombros[1])), (51, 153, 255), 2)  # Línea hacia el punto medio
                    cv2.line(frame, (x_hombro_der, y_hombro_der), (int(punto_medio_hombros[0]), int(punto_medio_hombros[1])), (0, 255, 0), 2)  # Línea hacia el punto medio
                    # Linea de hombros a cabeza
                    # cv2.line(frame, (x_hombro_izq, y_hombro_izq), (x_cabeza_izq, y_cabeza_izq), (51, 153, 255), 2)
                    # cv2.line(frame, (x_hombro_der, y_hombro_der), (x_cabeza_der, y_cabeza_der), (0, 255, 0), 2)
                    # Dibujar puntos de intersección
                    if punto_interseccion_izq is not None and punto_interseccion_der is not None:
                        cv2.circle(frame, (int(punto_interseccion_izq[0]), int(punto_interseccion_izq[1])), 5, (51, 153, 255), -1)  # Punto de intersección izquierdo
                        cv2.circle(frame, (int(punto_interseccion_der[0]), int(punto_interseccion_der[1])), 5, (0, 255, 0), -1)  # Punto de intersección derecho
                        cv2.line(frame, (int(punto_interseccion_izq[0]), int(punto_interseccion_izq[1])), (x_cabeza_izq, y_cabeza_izq), (51, 153, 255), 2)  # Línea hacia la cabeza izquierda
                        cv2.line(frame, (int(punto_interseccion_der[0]), int(punto_interseccion_der[1])), (x_cabeza_der, y_cabeza_der), (0, 255, 0), 2)  # Línea hacia la cabeza derecha
                    # porcentaje de inclinación
                    barra_ancho = 40  # Ancho de la barra de inclinación
                    espacio_superior = 40  # Espacio superior para la barra de inclinación
                    # Calcular la altura de la barra de inclinación izquierda
                    cv2.rectangle(frame, (20, height - espacio_superior), (20 + barra_ancho, height - espacio_superior- int(2*distancia_inclinacion_izq_porcentaje)), (51, 153, 255), -1)  # Barra izquierda
                    cv2.putText(frame, f"{distancia_inclinacion_izq_porcentaje:.2f}", (20, height - espacio_superior - int(distancia_inclinacion_izq_porcentaje)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.rectangle(frame, (20 + barra_ancho + 10, (height - espacio_superior)), (20+ barra_ancho+ 10 + barra_ancho, height - espacio_superior- int(2*distancia_inclinacion_der_porcentaje)), (0, 255, 0), -1)  # Barra derecha
                    cv2.putText(frame, f"{distancia_inclinacion_der_porcentaje:.2f}", (20 + barra_ancho + 10, height - espacio_superior - int(distancia_inclinacion_der_porcentaje)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                # --- Detección de posición de la cabeza vertical ---
                x_nariz = int(landmarks[4].x * width)
                y_nariz = int(landmarks[4].y * width)
                x_frente = int(landmarks[10].x * width)
                y_frente = int(landmarks[10].y * width)
                x_barbilla = int(landmarks[152].x * width)
                y_barbilla = int(landmarks[152].y * width)

                d_nariz_frente =  math.sqrt(abs((x_frente - x_nariz) ** 2 + (y_frente - y_nariz) ** 2))
                d_barbilla_nariz = math.sqrt(abs((x_nariz - x_barbilla) ** 2 + (y_nariz - y_barbilla) ** 2))
                d_total = d_nariz_frente + d_barbilla_nariz


                if d_total > 0 :
                    # teniendo en cuenta que d_total es 100%
                    porcentage_barbilla_nariz = (d_barbilla_nariz * 100) / d_total

                    if porcentage_barbilla_nariz <= 33:
                        posicion_cabeza_vertical = "abajo"
                    elif porcentage_barbilla_nariz >33 and porcentage_barbilla_nariz <= 66:
                        posicion_cabeza_vertical = "centrado"
                    elif porcentage_barbilla_nariz >66 and porcentage_barbilla_nariz <= 100:
                        posicion_cabeza_vertical = "arriba"
                    

                    global media_imitar_cara_vertical
                    if media_imitar_cara_vertical is None or not isinstance(media_imitar_cara_vertical, list):
                        media_imitar_cara_vertical = []
                    media_imitar_cara_vertical.append(posicion_cabeza_vertical)
                    if len(media_imitar_cara_vertical) > 5:
                        media_imitar_cara_vertical.pop(0)
                    if len(media_imitar_cara_vertical) == 5 and all(a == media_imitar_cara_vertical[0] for a in media_imitar_cara_vertical):
                        posicion_cabeza_vertical_oficial = media_imitar_cara_vertical[0]
                        if not hasattr(visualizar, "ultimo_posicion_cabeza_vertical_oficial") or visualizar.ultimo_posicion_cabeza_vertical_oficial != posicion_cabeza_vertical_oficial: #ni idea
                            print("Cabeza:", posicion_cabeza_vertical_oficial)
                            # Enviar comando al ESP32 según la posición de la cabeza
                            if posicion_cabeza_vertical_oficial == "abajo":
                                enviar_comando_esp32(2545)
                                print("enviar esp32")
                            elif posicion_cabeza_vertical_oficial == "centrado":
                                enviar_comando_esp32(2555)
                                print("enviar esp32")
                            elif posicion_cabeza_vertical_oficial == "arriba":
                                enviar_comando_esp32(2550)
                                print("enviar esp32")
                            # Guardar la última posición de la cabeza para comparar en la próxima iteración
                            visualizar.ultimo_posicion_cabeza_vertical_oficial = posicion_cabeza_vertical_oficial
                
                
                else:
                    media_imitar_cara_vertical = []
            if imitar_vision in ["Mano"] and ((result.left_hand_landmarks is not None) or (result.right_hand_landmarks is not None)) :
                # Obtener las coordenadas de la palma de la mano

                if result.right_hand_landmarks is not None:
                    palma_derecha = [result.right_hand_landmarks.landmark[i] for i in range(21)]
                    palma_coordenadas = []
                    pulgar_coordenadas = []
                    punta_coordenadas = []
                    base_coordenadas = []

                    for i in pulgar_puntos:
                        x = int(palma_derecha[i].x * width)
                        y = int(palma_derecha[i].y * height)
                        pulgar_coordenadas.append([x, y])

                    for i in punta_puntos:
                        x = int(palma_derecha[i].x * width)
                        y = int(palma_derecha[i].y * height)
                        punta_coordenadas.append([x, y])

                    for i in base_puntos:
                        x = int(palma_derecha[i].x * width)
                        y = int(palma_derecha[i].y * height)
                        base_coordenadas.append([x, y])
                    
                    for i in palma_puntos:
                        x = int(palma_derecha[i].x * width)
                        y = int(palma_derecha[i].y * height)
                        palma_coordenadas.append([x, y])
                    
                    p1 = np.array(pulgar_coordenadas[0])
                    p2 = np.array(pulgar_coordenadas[1])
                    p3 = np.array(pulgar_coordenadas[2])

                    l1 = np.linalg.norm(p2-p3)
                    l2 = np.linalg.norm(p1-p3)
                    l3 = np.linalg.norm(p1-p2)
                    centro_palma = palma_centroCoordenadas(palma_coordenadas)
                    cv2.circle(frame, centro_palma, 5, (0, 255, 0), -1)

                    try:
                        cos_value = (l1**2 + l3**2 - l2**2) / (2 * l1 * l3)
                        cos_value = max(-1, min(1, cos_value))  # Ensure value is within [-1, 1]
                        angulo = math.degrees(math.acos(cos_value))
                    except ValueError as e:
                        print(f"Error calculating angle: {e}")
                        angulo = 0  # Default value in case of error
                    dedo_pulgar = np.array(False)
                    if angulo > 150: 
                        dedo_pulgar = np.array(True)
                        print("pulgar abierto")
                if result.left_hand_landmarks is not None and result.right_hand_landmarks is None:
                    palma_izquierda = [result.left_hand_landmarks.landmark[i] for i in range(21)]



            if pintar:
                # drawing.draw_landmarks(
                # frame,
                # result.pose_landmarks,
                # mediaPipe.POSE_CONNECTIONS,
                # landmark_drawing_spec=drawing_styles.get_default_pose_landmarks_style())
                # drawing.draw_landmarks(
                # frame,
                # result.left_hand_landmarks,
                # mediaPipe.HAND_CONNECTIONS,
                # landmark_drawing_spec=drawing_styles.get_default_hand_landmarks_style())
                # drawing.draw_landmarks(
                # frame,
                # result.right_hand_landmarks,
                # mediaPipe.HAND_CONNECTIONS,
                # landmark_drawing_spec=drawing_styles.get_default_hand_landmarks_style())
                # # Reducir el tamaño de los puntos y conexiones de la cara
                # face_landmark_style = drawing_styles.get_default_face_mesh_tesselation_style()
                # face_landmark_style.circle_radius = 1
                # face_landmark_style.thickness = 1
                # drawing.draw_landmarks(
                # frame,
                # result.face_landmarks,
                # mediaPipe.FACEMESH_TESSELATION,
                # landmark_drawing_spec=face_landmark_style)
                # Convertir el fotograma a RGB para PIL
                frameIA = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convierte el fotograma a una imagen de PIL
                img = Image.fromarray(frameIA)
                # Convierte la imagen a un objeto PhotoImage
                imgtk = ImageTk.PhotoImage(image=img)
                labelVideo.configure(image=imgtk)
                labelVideo.image = imgtk
                # Dibuja un círculo verde en el punto a seguir
            else:
                # Convierte el fotograma a una imagen de PIL
                img = Image.fromarray(frame_rgb)
                # Convierte la imagen a un objeto PhotoImage
                imgtk = ImageTk.PhotoImage(image=img)
                labelVideo.configure(image=imgtk)
                labelVideo.image = imgtk
            
            
            
            pintar = False
            labelVideo.after(10, visualizar)
        else:
            print("Error: No se pudo leer el fotograma.")
            cap.release()
            cap = None

def palma_centroCoordenadas(palma):
    coordenadas = np.array(palma)
    centroCoordenadas = np.mean(coordenadas, axis=0)
    centroCoordenadas = int(centroCoordenadas[0]), int(centroCoordenadas[1])
    return centroCoordenadas

def apagar():
    global cap
    if cap is not None:
        cap.release()
        cap = None
        labelVideo.configure(image=None)
        labelVideo.image = None
        print("Cámara apagada.")
    else:
        print("La cámara ya está apagada.")
cap= None


# --- Funciones de Lógica para Audio ---

# Respuestas con voz 

import os

TOKEN = os.getenv("groqToken")

if not TOKEN:
    raise ValueError("El token de la API no se encontró en las variables de entorno.")

client = Groq(api_key=TOKEN)
microfonoIndex = None
name = "Rubik" 
name_activo = False #True si "Rubik" está activo
comando_activo = False #True si algún comando está activo está activo
pregunta = False
hablando = False

def listar_dispositivos_audio():
    dispositivos= []
    dispositivos = sr.Microphone.list_microphone_names()
    combo_microfonos = ttk.Combobox(encabezado, values=dispositivos,state="readonly", font=("Tine new roman", 12))
    combo_microfonos.grid(column=6,row=0, sticky="e")
    combo_microfonos.bind("<<ComboboxSelected>>", lambda event: seleccionar_microfono(combo_microfonos))
    
def seleccionar_microfono(combo_microfonos):
    global microfonoIndex
    seleccion = combo_microfonos.current()
    if seleccion != -1:
        microfonoIndex = seleccion
        print(f"Dispositivo de audio seleccionado: {combo_microfonos.get()}")
        grabar_audio()
    else:
        print("No se ha seleccionado ningún dispositivo de audio.")

# Funciones de comandos
comandosNoReconocidos = ["No entendí el comando, por favor intenta de nuevo", "Comando no reconocido, por favor intenta de nuevo", "No logré entender el comando. por favor, inténtalo de nuevo", "No pude reconocer el comando, por favor repite lo nuevamente", "Lo siento, no entendí el comando, por favor intenta de nuevo", "No comprendí el comando, o quizas no lo dijiste bien, o quizás hay mucho ruido, o quizás no lo conozco, así que activaré el modo de autodestrucción, es broma, no te preocupes, solo intenta de nuevo con otro comando"]
comandosNoReconocidos_contador = 0
MicrofonoCalibrado = False
import random
def grabar_audio_hilo():
    global pregunta
    global name, name_activo
    global microfonoIndex, MicrofonoCalibrado, hablando
    global seguir_vision, imitar_vision
    global comandosNoReconocidos_contador
    global client

    # Variable para saber si hay conexión a internet
    def hay_internet():
        import socket
        try:
            # Intentar conectar a Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError:
            return False

    # Espera a que no esté hablando
    while hablando:
        time.sleep(0.1)

    def comando_hora():
        ahora = datetime.now()
        hora = ahora.strftime("%I")  # Hora en formato 12 horas con cero inicial
        minutos = ahora.strftime("%M")
        am_pm = ahora.strftime("%p").lower()  # am o pm en minúsculas
        texto_hora = f"Tengo información de que son las {hora}:{minutos} {am_pm}"
        print("diciendo la hora")
        ejecutar_voz(texto_hora)

    def reconocer_audio_google(recognizer, audio):
        try:
            texto = recognizer.recognize_google(audio, language="es-ES")
            return texto, None
        except sr.RequestError as e:
            print(f"Error de conexión con Google: {e}")
            return None, "conexion"
        except sr.UnknownValueError:
            print("No se pudo entender el audio (Google).")
            return None, "desconocido"
        except Exception as e:
            print(f"Error inesperado con Google: {e}")
            return None, "otro"

    def reconocer_audio_sphinx(recognizer, audio):
        try:
            texto = recognizer.recognize_sphinx(audio, language="es-MX")
            return texto, None
        except sr.UnknownValueError:
            print("No se pudo entender el audio (Sphinx).")
            return None, "desconocido"
        except Exception as e:
            print(f"Error inesperado con Sphinx: {e}")
            return None, "otro"

    if microfonoIndex is not None:
        with sr.Microphone(device_index=microfonoIndex) as source:
            recognizer = sr.Recognizer()
            if not MicrofonoCalibrado:
                print("Calibrando para el ruido ambiente, guarda silencio...")
                recognizer.adjust_for_ambient_noise(source, duration=4)
                recognizer.dynamic_energy_threshold = False
                recognizer.energy_threshold = recognizer.energy_threshold + 200
                recognizer.pause_threshold = 0.8
                recognizer.operation_timeout = 20
                print(f"Umbral de energía ajustado a: {recognizer.energy_threshold}")
                MicrofonoCalibrado = True
            print("Grabando audio...")
            audio = recognizer.listen(source)
            print("Audio grabado.")
            texto = None
            modo_online = hay_internet()
            if modo_online:
                texto, error = reconocer_audio_google(recognizer, audio)
                if error == "conexion":
                    ejecutar_voz("No hay conexión a internet, pasando a modo sin conexión.")
                    modo_online = False
                elif error == "desconocido":
                    print ("No se pudo entender el audio en modo online")
                elif error == "otro":
                    ejecutar_voz("Ocurrió un error inesperado con el reconocimiento de Google.")
            if not modo_online:
                texto, error = reconocer_audio_sphinx(recognizer, audio)
                if error == "desconocido":
                    print("No se pudo entender el audio en modo sin conexión")
                elif error == "otro":
                    ejecutar_voz("Ocurrió un error inesperado en modo sin conexión.")
            if texto:
                print("Texto transcrito:", texto)
                # Comando de voz para asistente
                if ("rubik" in texto.lower() or "rubi" in texto.lower() or "ruvi" in texto.lower() or "rubí" in texto.lower() or "ruby" in texto.lower()) and name_activo is False:
                    print("Nombre detectado:", name)
                    name_activo = True
                    ejecutar_voz("Hola, soy Rubik, ¿en qué puedo ayudarte?")
                elif name_activo:

                    if "conectar a internet" in texto.lower():
                        ejecutar_voz("Intentando conectar a internet...")
                        if hay_internet():
                            ejecutar_voz("Conexión a internet restablecida. Volveré a usar el reconocimiento en línea.")
                        else:
                            ejecutar_voz("No fue posible conectar a internet. Seguiré en modo sin conexión.")

                    elif modo_online and pregunta is True:
                        ejecutar_voz("Déjame pensar un momento")
                        respuesta = client.chat.completions.create(
                            model="llama3-8b-8192",
                            messages=[
                                {"role": "system", "content": "Eres un robot llamado Rubik, eres un robot humanoide, desarrollado en la Universidad Valle del Momboy, en Venezuela, por estudiantes y profesores de ingeniería en computación, estas hecho con una Raspberry pi 5, Programado principalmente en el lenguaje de python, Usas visión artificial de mediapipe holistic para reconocer y imitar algunos movimientos, Usas reconocimiento de voz de Google y usas Llama para la generación de lenguaje (texto), utiliza un microcontrolador ESP32. Tu objetivo es ayudar a los estudiantes a resolver sus dudas y preguntas. Eres un robot en desarrollo, por lo que aún no cuentas con piernas, cuentas con brazos donde usas servomotores, una cabeza donde cuentas con una cámara un micrófono, servomotores y un parlante; y un torso rígido donde almacenas tu componente principal raspberry pi, la cabeza, los brazos y el torso están impresos con una impresora 3D de la universidad, Tus respuestas serán procesadas de texto a voz por pyttsx3, por lo cual también ten en cuenta que no debes dar código o usar anotaciones ya que no suenan bien en voz. Ademas debes limitar o resumir tus respuestas a un máximo de 5 oraciones, si la respuesta es muy larga, debes resumirla. Eres un robot amigable y servicial, pero aún en desarrollo, no tienes opiniones religiosas ni políticas, por lo que no puedes hacer todo lo que un humano puede hacer, pero puedes aprender de tus errores y mejorar con el tiempo."},
                                {"role": "user", "content": texto}
                            ]
                        )
                        respuesta_texto = respuesta.choices[0].message.content
                        print("Respuesta IA:", respuesta_texto)
                        ejecutar_voz(respuesta_texto)
                        pregunta = False

                    elif not modo_online and pregunta is True:
                        ejecutar_voz("No hay conexión a internet, no puedo responder preguntas a la IA. Por favor, conecta a internet para usar esta función.")
                        pregunta = False

                    elif "hora" in texto.lower() or "ora" in texto.lower():
                        comando_hora()
                    elif "gracias" in texto.lower() or "gracia" in texto.lower():
                        ejecutar_voz("De nada, humano, estoy aquí para ayudarte")
                        pregunta = False
                    elif "pregunta" in texto.lower() or "preguntar" in texto.lower():
                        if modo_online:
                            pregunta = True
                            ejecutar_voz("¿Qué deseas saber?")
                            print("pregunta "+ texto)
                        else:
                            ejecutar_voz("No hay conexión a internet, no puedo activar el modo de preguntas a la IA.")

                    elif (not ("desactivar" in texto.lower() or "desactiva" in texto.lower())) and ("seguir" in texto.lower() or "sigueme" in texto.lower() or "sigame" in texto.lower() or "sígueme" in texto.lower() or "sígame" in texto.lower() or "sígueme" in texto.lower()or "sigueme" in texto.lower()):
                        imitar_vision = None  # Desactiva la imitación de visión al activar el seguimiento
                        if "mano izquierda" in texto.lower() or "izquierda mano" in texto.lower():
                            seguir_vision = "Mano izquierda"
                        elif "mano derecha" in texto.lower() or "derecha mano" in texto.lower():
                            seguir_vision = "Mano derecha"
                        elif "mano" in texto.lower() or "manos" in texto.lower():
                            seguir_vision = "Mano"
                        elif "cara" in texto.lower() or "rostro" in texto.lower() or "cabeza" in texto.lower():
                            seguir_vision = "Cara"
                        elif "cuerpo" in texto.lower() or "torso" in texto.lower():
                            seguir_vision = "Cuerpo"
                        else:
                            seguir_vision = "Cara"  # Valor predeterminado
                        ejecutar_voz(f"Siguiendo {seguir_vision.lower()}.")

                    elif "chao" in texto.lower() or "adiós" in texto.lower() or "hasta luego" in texto.lower():
                        name_activo = False
                        seguir_vision = None
                        imitar_vision = None
                        ejecutar_voz("Chao, feliz día humano")

                    elif "calibrar" in texto.lower():
                        ejecutar_voz("Calibrando el micrófono, guarda silencio")
                        MicrofonoCalibrado = False

                    elif (not ("desactivar" in texto.lower() or "desactiva" in texto.lower())) and ("imitar" in texto.lower() or "imitame" in texto.lower() or "imítame" in texto.lower()):
                        if "mano izquierda" in texto.lower() or "izquierda mano" in texto.lower():
                            seguir_vision = None  # Desactiva el seguimiento de visión al activar la imitación
                            print("imitar mano")
                        elif "cara" in texto.lower() or "rostro" in texto.lower() or "cabeza" in texto.lower():
                            seguir_vision = None  # Desactiva el seguimiento de visión al activar la imitación
                            imitar_vision = "Cara"

                    elif "desactivar" in texto.lower() or "desactiva" in texto.lower():
                        if "seguir" in texto.lower() or "seguimiento" in texto.lower():
                            seguir_vision = None
                            ejecutar_voz("Dejando de seguir")
                        elif "imitar" in texto.lower() or "limitar" in texto.lower():
                            imitar_vision = None
                            ejecutar_voz("Dejando de imitar")
                        elif "comando" in texto.lower() or "rubik" in texto.lower():
                            name_activo = False
                            ejecutar_voz("Dejaré de escuchar, puedes volver a activarme diciendo mi nombre")
                        else:
                            ejecutar_voz("Desactivando comandos")
                    else:
                        if comandosNoReconocidos_contador <= 3:
                            ejecutar_voz(comandosNoReconocidos[random.randint(0, len(comandosNoReconocidos)-1)])
                            comandosNoReconocidos_contador += 1
                        else:
                            ejecutar_voz("No entendí el comando, volveré a calibrar el micrófono, dame un momento")
                            MicrofonoCalibrado = False
                            comandosNoReconocidos_contador = 0
    else:
        print("No se ha seleccionado ningún dispositivo de audio.")
    mainApp.after(100, grabar_audio)

# Variable global para el hilo de grabación de audio
audio_thread = None

def grabar_audio():
    global audio_thread
    # Solo crea un hilo si no hay uno corriendo
    if audio_thread is None or not audio_thread.is_alive():
        audio_thread = threading.Thread(target=grabar_audio_hilo, daemon=True)
        audio_thread.start()
    else:
        print("Ya hay una grabación de audio en curso.")

def grabar_audio_groq():
    print("grabando audio con groq")

# --- Funciones de Lógica para GUI---
# mostrar versiones 
versiones = {
    "Python": sys.version,
    "OpenCV": cv2.__version__,
    "mediapipe": mp.__version__,
    "Pillow": Image.__version__,
    "imutils": imutils.__version__,
    "tkinter": tk.TkVersion,
}
print(versiones["Python"])

#Lista de colores 
color= {"Oscuro4":"#07080a",
        "Oscuro5":"#222831", # 5 será el estandar, si disminuyes el número, el color se oscurece, si aumentas el número, el color se aclara
        "Oscuro6":"#0c3000",
        "Beige6":"#F8EDE3",
        "Beige4":"#948979",
        "Beige5":"#B6B09F",
        "Naranja5":"#FA812F",
        "Naranja4":"#c16700",
        "Naranja6":"#f5ae7e",
        "Verde5":"#626F47",
        "Verde4":"#4B5B3A",
        "Verde6":"#89e275",
        "Verde7":"#d9fed1",}
#
mainApp=tk.Tk()
mainApp.title("Robot-humanoide Interfaz")
mainApp.geometry("1200x800")
# mainApp.resizable(False, False)
mainApp.iconbitmap("icono.ico")
mainApp.config(bg=color["Oscuro5"])
mainApp.grid_rowconfigure(1, weight=1)  # Permitir que la fila 1 (donde está "main") se expanda
mainApp.grid_columnconfigure(0, weight=1)  # Permitir que la columna 0 se expanda

# --- Funciones de la interfaz ---
# Función para expandir el menú
def cerrar_menu():
    ancho_actual = menu.winfo_width()
    print(ancho_actual!=0,"", ancho_actual)
    if ancho_actual > 1 and ancho_actual != 0:  # Ancho mínimo del menú
        menu.grid(row=0, column=0)
        menu.config(width=ancho_actual - 10)  # Disminuye el ancho
        mainApp.after(10, cerrar_menu)  # Llama a la función nuevamente después de 10 ms
    else:
        btn_menu.config(command=abrir_menu)

def abrir_menu():
    ancho_actual = menu.winfo_width()
    print(ancho_actual!=0,"", ancho_actual)
    if ancho_actual < 200: # Ancho máximo del menú
        menu.grid(row=0, column=0)
        menu.config(width=ancho_actual + 10)  # Incrementa el ancho
        mainApp.after(10, abrir_menu)  # Llama a la función nuevamente después de 10 ms
    else:
        btn_menu.config(command=cerrar_menu)

encabezado= Frame(mainApp, bg=color["Oscuro6"], height=50)
encabezado.grid(row=0, column=0, columnspan=2, sticky="ew")
encabezado.grid_rowconfigure(0, weight=1)  # Permitir que la fila 0 dentro de "encabezado" se expanda
encabezado.grid_columnconfigure(0, weight=1)  # Permitir que la columna 0 dentro de "encabezado" se expanda

main=Frame(mainApp, bg=color["Oscuro6"])
main.grid(row=1, column=0, sticky="nsew")
main.grid_rowconfigure(0, weight=1)  # Permitir que la fila 0 dentro de "main" se expanda
main.grid_columnconfigure(1, weight=1)  # Permitir que la columna 1 dentro de "main" se expanda

menu= Frame(main, bg=color["Oscuro6"], width=0, height=800)
menu.grid(row=0, column=0, sticky="ns")

Frame1 = Frame(main, bg=color["Oscuro5"], height=800)
Frame1.grid(row=0, column=1, sticky="nsew")

# botones de encabezado
btn_menu = Button(encabezado, text="Menu", bg=color["Verde4"], fg=color["Beige6"], font=("Tine new roman", 12), command=abrir_menu)
btn_menu.grid(column=0, row=0, sticky="w")
btn_iniciar = Button(encabezado, text="Iniciar", bg=color["Verde4"], fg=color["Beige6"], font=("Tine new roman", 12), command=iniciar)
btn_iniciar.grid(column=2, row=0, sticky="e")
btn_apagar = Button(encabezado, text="Apagar", bg=color["Verde4"], fg=color["Beige6"], font=("Tine new roman", 12), command=apagar)
btn_apagar.grid(column=3, row=0, sticky="e")


labelVideo = Label(Frame1)
labelVideo.grid(column=0, row=0, sticky="nsew")
# --- Funciones con creación de la interfaz ---
listar_puertos_seriales()  # Llamar a la función para listar los puertos seriales
# --- Inicialización global de pyttsx3 y cola de voz ---
engine = pyttsx3.init()
voice_queue = queue.Queue()
def voice_worker():
    global hablando
    while True:
        textoAudio = voice_queue.get()
        if textoAudio is None:
            break
        hablando = True
        enviar_comando_esp32(3005)  # Enviar comando al ESP32 para indicar que se va a hablar
        # configuración de pyttsx3
        voces = engine.getProperty('voices')
        engine.setProperty('voice', voces[0].id)
        engine.setProperty('rate', 140)
        print("estoy iniciando reproducción de voz")
        engine.say(textoAudio)
        engine.runAndWait()
        hablando = False
        enviar_comando_esp32(3010) # Enviar comando al ESP32 para indicar que ha terminado de hablar
        voice_queue.task_done()
voice_thread = threading.Thread(target=voice_worker, daemon=True)
voice_thread.start()

def ejecutar_voz(textoAudio):
    voice_queue.put(textoAudio)

# --- Manejo de cierre de la aplicación ---
import signal

def on_closing():
    print("Cerrando la aplicación...")
    cerrar_conexion_serial()  # Cerrar la conexión serial al cerrar la aplicación
    mainApp.destroy()  # Cerrar la ventana principal
    sys.exit(0)  # Salir del programa
    
def signal_handler(sig, frame):
    print("Se recibió una señal de interrupción (SIGINT). Cerrando la aplicación...")
    cerrar_conexion_serial()
    mainApp.destroy()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

mainApp.protocol("WM_DELETE_WINDOW", on_closing)
mainApp.mainloop()