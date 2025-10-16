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
import os
from dotenv import load_dotenv
import json
## pyinstaller --icon=icono.ico --add-data "icono.ico;." main.py
## al compilar recordar que se deben incluir los archivos de modelo y los recursos necesarios

## importar modulos personalizados
from Clavicula import definir_angulo_hombro_rotacion, definir_angulo_hombro_frontal, definir_angulo_hombro_sagital, calcular_angulo_brazos, definir_flexion, calcular_angulo_flexion, normalizar_vector, calcular_angulo,Calcular_distancia_Punto_a_RectaAB, punto_medio_segmento
from esp32 import iniciar_conexion_serial, enviar_esp32, cerrar_serial, listar_seriales
# para la hora actual quitar si se hace de otra manera
from datetime import datetime


## importar json de diccionario
with open('comandos.json', 'r', encoding='utf-8') as f:
    diccionario = json.load(f)

## funciones de respuesta a voz

def respuestas_comando(comando):
    for respuesta in diccionario["Respuestas"]:
        if respuesta["responder"] == comando:
            if respuesta["pesos"] == True:
                return random.choices(respuesta["respuesta"], weights=respuesta["pesos"])[0]
            else:
                return random.choice(respuesta["respuesta"])
    return "No tengo una respuesta para eso."

def extraer_comandos(cadena):
    comandos_obtenidos = []
    for cmd in diccionario["comandos"]:
        for palabra in cmd["palabras"]:
            if palabra in cadena:
                comandos_obtenidos.append(cmd["comando"])
    return comandos_obtenidos if comandos_obtenidos else ["desconocido"]

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

camera = False



def iniciar():
    global cap, camera
    # Inicializa la cámara
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        camera = False
        mainApp.destroy()
        return
    camera = True
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

    # mano
palma_puntos = [0,1,2,5,9,13,17]
pulgar_puntos = [1,2,4]
punta_puntos = [8,12,16,20]
base_puntos = [6,10,14,18]
ultimo_dedo_derecha = [None, None, None, None, None]
mano_imitar_derecha = None
estado_muneca_derecha = None
media_estado_muneca_derecha = None # Variable para almacenar la media de la muñeca imitada
ultimo_dedo_izquierda = [None, None, None, None, None]
mano_imitar_izquierda = None
estado_muneca_izquierda = None
media_estado_muneca_izquierda = None # Variable para almacenar la media de la muñeca imitada

# imitar cuerpo
brazo_derecho = [None, None, None, None, None, None, None, None] # posición flexión, angulo_codigo flexión, posición frontal, angulo_codigo frontal, posición sagital, angulo_codigo sagital, posición rotación, angulo_codigo rotación
brazo_izquierdo = [None, None, None, None, None, None, None, None] # posición flexión, angulo_codigo flexión, posición frontal, angulo_codigo frontal, posición sagital, angulo_codigo sagital, posición rotación, angulo_codigo rotación
grupo_angulo_frontal_d = []
grupo_angulo_sagital_d = []
grupo_angulo_flexion_d = []
grupo_angulo_rotacion_d = []
grupo_angulo_frontal_i = []
grupo_angulo_sagital_i = []
grupo_angulo_flexion_i = []
grupo_angulo_rotacion_i = []



def visualizar():
    global cap
    global pintar
    global EjeY, EjeX
    global seguir_vision, punto_seguir, imitar_vision
    global palma_puntos, pulgar_puntos, punta_puntos, base_puntos
    global ultimo_dedo_derecha, estado_muneca_derecha, media_estado_muneca_derecha, mano_imitar_derecha
    global ultimo_dedo_izquierda, estado_muneca_izquierda, media_estado_muneca_izquierda, mano_imitar_izquierda
    global brazo_derecho, grupo_angulo_frontal_d, grupo_angulo_flexion_d, grupo_angulo_sagital_d, grupo_angulo_rotacion_d
    global brazo_izquierdo, grupo_angulo_frontal_i, grupo_angulo_flexion_i, grupo_angulo_sagital_i, grupo_angulo_rotacion_i
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
                # Dibujar el punto de la nariz
                cv2.circle(frame, (x_nariz, y_nariz), 5, (0, 255, 0), -1)
                # Extremos de la cara (usando landmarks de la mandíbula)
                x_izquierda = int(landmarks[234].x * width)  # lado izquierdo de la cara
                y_izquierda = int(landmarks[234].y * height)  # lado izquierdo de la cara
                cv2.circle(frame, (x_izquierda, y_izquierda), 5, (255, 0, 0), -1)  # Dibujar punto izquierdo
                x_derecha = int(landmarks[454].x * width)    # lado derecho de la cara
                y_derecha = int(landmarks[454].y * height)  # lado derecho de la cara
                cv2.circle(frame, (x_derecha, y_derecha), 5, (255, 0, 0), -1)  # Dibujar punto derecho

                # Calcular la proporción de la nariz entre los extremos
                d_nariz_derecha= math.sqrt(abs((x_derecha - x_nariz) ** 2 + (y_derecha - y_nariz) ** 2))
                cv2.line(frame, (x_nariz, y_nariz), (x_derecha, y_derecha), (255, 0, 0), 1)  # Línea a la derecha
                d_nariz_izquierda = math.sqrt(abs((x_izquierda - x_nariz) ** 2 + (y_izquierda - y_nariz) ** 2))
                cv2.line(frame, (x_nariz, y_nariz), (x_izquierda, y_izquierda), (255, 0, 0), 1)  # Línea a la izquierda
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
            if imitar_vision in ["Mano"] or imitar_vision in ["Mano izquierda"] or imitar_vision in ["Mano derecha"]:

                if (result.left_hand_landmarks is not None or result.right_hand_landmarks is not None):
                    # Obtener las coordenadas de la palma de la mano

                    if imitar_vision in ["Mano derecha"]:
                        if result.right_hand_landmarks is not None:
                            mano_imitar_derecha = [result.right_hand_landmarks.landmark[i] for i in range(21)]
                            mano_imitar_izquierda = None
                        else:
                            mano_imitar_derecha = None
                            mano_imitar_izquierda = None
                    elif imitar_vision in ["Mano izquierda"]:
                        if result.left_hand_landmarks is not None:
                            mano_imitar_izquierda = [result.left_hand_landmarks.landmark[i] for i in range(21)]
                            mano_imitar_derecha = None
                        else:
                            mano_imitar_izquierda = None
                            mano_imitar_derecha = None
                    elif imitar_vision in ["Mano"]:
                        if result.left_hand_landmarks is not None and result.right_hand_landmarks is not None:
                            mano_imitar_derecha = [result.right_hand_landmarks.landmark[i] for i in range(21)]
                            mano_imitar_izquierda = [result.left_hand_landmarks.landmark[i] for i in range(21)]
                        elif result.left_hand_landmarks is not None:
                            mano_imitar_izquierda = [result.left_hand_landmarks.landmark[i] for i in range(21)]
                            mano_imitar_derecha = None
                        elif result.right_hand_landmarks is not None:
                            mano_imitar_derecha = [result.right_hand_landmarks.landmark[i] for i in range(21)]
                            mano_imitar_izquierda = None
                        else:
                            mano_imitar_derecha = None
                            mano_imitar_izquierda = None

                    if mano_imitar_derecha is not None:
                        palma_coordenadas = []
                        pulgar_coordenadas = []
                        punta_coordenadas = []
                        base_coordenadas = []

                        for i in pulgar_puntos:
                            x = int(mano_imitar_derecha[i].x * width)
                            y = int(mano_imitar_derecha[i].y * height)
                            pulgar_coordenadas.append([x, y])

                        for i in punta_puntos:
                            x = int(mano_imitar_derecha[i].x * width)
                            y = int(mano_imitar_derecha[i].y * height)
                            punta_coordenadas.append([x, y])

                        for i in base_puntos:
                            x = int(mano_imitar_derecha[i].x * width)
                            y = int(mano_imitar_derecha[i].y * height)
                            base_coordenadas.append([x, y])
                        
                        for i in palma_puntos:
                            x = int(mano_imitar_derecha[i].x * width)
                            y = int(mano_imitar_derecha[i].y * height)
                            palma_coordenadas.append([x, y])
                        
                        # Calcular pulgar
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
                            print(f"Error calculando el angulo: {e}")
                            angulo = 0  # Default value in case of error
                            
                        dedo_pulgar = np.array(False)
                        if angulo > 150: 
                            dedo_pulgar = np.array(True)
                            # print("pulgar abierto")

                        # Calcular dedos
                        xn, yn = palma_centroCoordenadas(palma_coordenadas)
                        centro_coordenadas = np.array([xn, yn])
                        punta_coordenadas = np.array(punta_coordenadas)
                        base_coordenadas = np.array(base_coordenadas)

                        dis_centro_punta = np.linalg.norm(centro_coordenadas - punta_coordenadas, axis=1)
                        dis_centro_base = np.linalg.norm(centro_coordenadas - base_coordenadas, axis=1)
                        diferencia = dis_centro_base - dis_centro_punta 
                        dedosAbiertos = diferencia < 0
                        dedosAbiertos = np.append(dedo_pulgar, dedosAbiertos)
                        print("Dedos abiertos derecha: ", dedosAbiertos)

                        #Enviar al ESP32 los dedos abiertos y cerrados 
                        if dedosAbiertos[0] and ultimo_dedo_derecha[0] is None:  #PULGAR
                            ultimo_dedo_derecha[0] = "Pulgar"
                            print("Pulgar derecho abierto")
                            enviar_comando_esp32(5519)
                        elif dedosAbiertos[0] == False and ultimo_dedo_derecha[0] == "Pulgar":
                            ultimo_dedo_derecha[0] = None
                            print("Pulgar derecho cerrado")
                            enviar_comando_esp32(5518)
                        if dedosAbiertos[1] and ultimo_dedo_derecha[1] is None: #ÍNDICE
                            ultimo_dedo_derecha[1] = "Indice"
                            print("Índice derecho abierto")
                            enviar_comando_esp32(5517)
                        elif dedosAbiertos[1] == False and ultimo_dedo_derecha[1] == "Indice":
                            ultimo_dedo_derecha[1] = None
                            print("Índice derecho cerrado")
                            enviar_comando_esp32(5516)
                        if dedosAbiertos[2] and ultimo_dedo_derecha[2] is None: #MEDIO
                            ultimo_dedo_derecha[2] = "Medio"
                            print("Medio derecho abierto")
                            enviar_comando_esp32(5511)
                        elif dedosAbiertos[2] == False and ultimo_dedo_derecha[2] == "Medio":
                            ultimo_dedo_derecha[2] = None
                            print("Medio derecho cerrado")
                            enviar_comando_esp32(5510)
                        if dedosAbiertos[3] and ultimo_dedo_derecha[3] is None: #ANULAR
                            ultimo_dedo_derecha[3] = "Anular"
                            print("Anular derecho abierto")
                            enviar_comando_esp32(5513)
                        elif dedosAbiertos[3] == False and ultimo_dedo_derecha[3] == "Anular":
                            ultimo_dedo_derecha[3] = None
                            print("Anular derecho cerrado")
                            enviar_comando_esp32(5512)
                        if dedosAbiertos[4] and ultimo_dedo_derecha[4] is None: #MEÑIQUE
                            ultimo_dedo_derecha[4] = "Pinky"
                            print("Meñique derecho abierto")
                            enviar_comando_esp32(5515)
                        elif dedosAbiertos[4] == False and ultimo_dedo_derecha[4] == "Pinky":
                            ultimo_dedo_derecha[4] = None
                            print("Meñique derecho cerrado")
                            enviar_comando_esp32(5514)
                        
                        # IMITAR MUÑECA DE LA MANO
                        # para mano derecha invertir el codigo 
                        punta_pulgar = pulgar_coordenadas[2]
                        punta_pinky = punta_coordenadas[3]

                        if (result.face_landmarks is not None):
                            punta_nariz = [result.face_landmarks.landmark[4]]
                            punta_nariz = [punta_nariz[0].x * width, punta_nariz[0].y * height]
                            print("nariz encontrada", punta_nariz)
                            # print(punta_pulgar," <-> " , punta_pinky)
                            distancia_pulgar_nariz = np.linalg.norm(np.array(punta_pulgar) - np.array(punta_nariz))
                            distancia_pinky_nariz = np.linalg.norm(np.array(punta_pinky) - np.array(punta_nariz))
                            
                            if distancia_pulgar_nariz < distancia_pinky_nariz and (estado_muneca_derecha != "palma" or estado_muneca_derecha is None):
                                print("Mostrar palma derecha")
                                estado_muneca_derecha = "palma"
                            elif distancia_pulgar_nariz > distancia_pinky_nariz and (estado_muneca_derecha != "dorso" or estado_muneca_derecha is None):
                                print("Mostrar dorso derecho")
                                estado_muneca_derecha = "dorso"

                            # Suavizado de la muñeca
                            if media_estado_muneca_derecha is None or not isinstance(media_estado_muneca_derecha, list):
                                media_estado_muneca_derecha = []
                            media_estado_muneca_derecha.append(estado_muneca_derecha)
                            if len(media_estado_muneca_derecha) > 5:
                                media_estado_muneca_derecha.pop(0)
                            if len(media_estado_muneca_derecha) == 5 and all(m == media_estado_muneca_derecha[0] for m in media_estado_muneca_derecha):
                                estado_muneca_derecha_oficial = media_estado_muneca_derecha[0]
                                if not hasattr(visualizar, "ultimo_estado_muneca_derecha_oficial") or visualizar.ultimo_estado_muneca_derecha_oficial != estado_muneca_derecha_oficial:
                                    print("Muñeca derecha oficial:", estado_muneca_derecha_oficial)
                                    if estado_muneca_derecha_oficial == "palma":
                                        enviar_comando_esp32(5001)
                                    elif estado_muneca_derecha_oficial == "dorso":
                                        enviar_comando_esp32(5000)
                                    visualizar.ultimo_estado_muneca_derecha_oficial = estado_muneca_derecha_oficial
                        else:
                            punta_nariz = None
                            print("nariz no encontrada, no se puede mover muñeca derecha")

                    if mano_imitar_izquierda is not None:
                        palma_coordenadas = []
                        pulgar_coordenadas = []
                        punta_coordenadas = []
                        base_coordenadas = []

                        for i in pulgar_puntos:
                            x = int(mano_imitar_izquierda[i].x * width)
                            y = int(mano_imitar_izquierda[i].y * height)
                            pulgar_coordenadas.append([x, y])

                        for i in punta_puntos:
                            x = int(mano_imitar_izquierda[i].x * width)
                            y = int(mano_imitar_izquierda[i].y * height)
                            punta_coordenadas.append([x, y])

                        for i in base_puntos:
                            x = int(mano_imitar_izquierda[i].x * width)
                            y = int(mano_imitar_izquierda[i].y * height)
                            base_coordenadas.append([x, y])
                        
                        for i in palma_puntos:
                            x = int(mano_imitar_izquierda[i].x * width)
                            y = int(mano_imitar_izquierda[i].y * height)
                            palma_coordenadas.append([x, y])
                        
                        # Calcular pulgar
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
                            print(f"Error calculando el angulo: {e}")
                            angulo = 0  # Default value in case of error
                            
                        dedo_pulgar = np.array(False)
                        if angulo > 150: 
                            dedo_pulgar = np.array(True)
                            # print("pulgar abierto")

                        # Calcular dedos
                        xn, yn = palma_centroCoordenadas(palma_coordenadas)
                        centro_coordenadas = np.array([xn, yn])
                        punta_coordenadas = np.array(punta_coordenadas)
                        base_coordenadas = np.array(base_coordenadas)

                        dis_centro_punta = np.linalg.norm(centro_coordenadas - punta_coordenadas, axis=1)
                        dis_centro_base = np.linalg.norm(centro_coordenadas - base_coordenadas, axis=1)
                        diferencia = dis_centro_base - dis_centro_punta 
                        dedosAbiertos = diferencia < 0
                        dedosAbiertos = np.append(dedo_pulgar, dedosAbiertos)
                        print("Dedos abiertos izquierda: ", dedosAbiertos)

                        #Enviar al ESP32 los dedos abiertos y cerrados 
                        if dedosAbiertos[0] and ultimo_dedo_izquierda[0] is None:  #PULGAR
                            ultimo_dedo_izquierda[0] = "Pulgar"
                            print("Pulgar izquierdo abierto")
                            enviar_comando_esp32(5521)
                        elif dedosAbiertos[0] == False and ultimo_dedo_izquierda[0] == "Pulgar":
                            ultimo_dedo_izquierda[0] = None
                            print("Pulgar izquierdo cerrado")
                            enviar_comando_esp32(5520)
                        if dedosAbiertos[1] and ultimo_dedo_izquierda[1] is None: #ÍNDICE
                            ultimo_dedo_izquierda[1] = "Indice"
                            print("Índice izquierdo abierto")
                            enviar_comando_esp32(5523)
                        elif dedosAbiertos[1] == False and ultimo_dedo_izquierda[1] == "Indice":
                            ultimo_dedo_izquierda[1] = None
                            print("Índice izquierdo cerrado")
                            enviar_comando_esp32(5522)
                        if dedosAbiertos[2] and ultimo_dedo_izquierda[2] is None: #MEDIO
                            ultimo_dedo_izquierda[2] = "Medio"
                            print("Medio izquierdo abierto")
                            enviar_comando_esp32(5525)
                        elif dedosAbiertos[2] == False and ultimo_dedo_izquierda[2] == "Medio":
                            ultimo_dedo_izquierda[2] = None
                            print("Medio izquierdo cerrado")
                            enviar_comando_esp32(5524)
                        if dedosAbiertos[3] and ultimo_dedo_izquierda[3] is None: #ANULAR
                            ultimo_dedo_izquierda[3] = "Anular"
                            print("Anular izquierdo abierto")
                            enviar_comando_esp32(5527)
                        elif dedosAbiertos[3] == False and ultimo_dedo_izquierda[3] == "Anular":
                            ultimo_dedo_izquierda[3] = None
                            print("Anular izquierdo cerrado")
                            enviar_comando_esp32(5526)
                        if dedosAbiertos[4] and ultimo_dedo_izquierda[4] is None: #MEÑIQUE
                            ultimo_dedo_izquierda[4] = "Pinky"
                            print("Meñique izquierdo abierto")
                            enviar_comando_esp32(5529)
                        elif dedosAbiertos[4] == False and ultimo_dedo_izquierda[4] == "Pinky":
                            ultimo_dedo_izquierda[4] = None
                            print("Meñique izquierdo cerrado")
                            enviar_comando_esp32(5528)
                        
                        # IMITAR MUÑECA DE LA MANO
                        # para mano derecha invertir el codigo 
                        punta_pulgar = pulgar_coordenadas[2]
                        punta_pinky = punta_coordenadas[3]

                        if (result.face_landmarks is not None):
                            punta_nariz = [result.face_landmarks.landmark[4]]
                            punta_nariz = [punta_nariz[0].x * width, punta_nariz[0].y * height]
                            print("nariz encontrada", punta_nariz)
                            # print(punta_pulgar," <-> " , punta_pinky)
                            distancia_pulgar_nariz = np.linalg.norm(np.array(punta_pulgar) - np.array(punta_nariz))
                            distancia_pinky_nariz = np.linalg.norm(np.array(punta_pinky) - np.array(punta_nariz))
                            
                            if distancia_pulgar_nariz < distancia_pinky_nariz and (estado_muneca_izquierda != "palma" or estado_muneca_izquierda is None):
                                print("Mostrar palma izquierda")
                                estado_muneca_izquierda = "palma"
                            elif distancia_pulgar_nariz > distancia_pinky_nariz and (estado_muneca_izquierda != "dorso" or estado_muneca_izquierda is None):
                                print("Mostrar dorso izquierdo")
                                estado_muneca_izquierda = "dorso"

                            # Suavizado de la muñeca
                            if media_estado_muneca_izquierda is None or not isinstance(media_estado_muneca_izquierda, list):
                                media_estado_muneca_izquierda = []
                            media_estado_muneca_izquierda.append(estado_muneca_izquierda)
                            if len(media_estado_muneca_izquierda) > 5:
                                media_estado_muneca_izquierda.pop(0)
                            if len(media_estado_muneca_izquierda) == 5 and all(m == media_estado_muneca_izquierda[0] for m in media_estado_muneca_izquierda):
                                estado_muneca_izquierda_oficial = media_estado_muneca_izquierda[0]
                                if not hasattr(visualizar, "ultimo_estado_muneca_izquierda_oficial") or visualizar.ultimo_estado_muneca_izquierda_oficial != estado_muneca_izquierda_oficial:
                                    print("Muñeca izquierda oficial:", estado_muneca_izquierda_oficial)
                                    if estado_muneca_izquierda_oficial == "palma":
                                        enviar_comando_esp32(5003)
                                    elif estado_muneca_izquierda_oficial == "dorso":
                                        enviar_comando_esp32(5002)
                                    visualizar.ultimo_estado_muneca_izquierda_oficial = estado_muneca_izquierda_oficial
                        else:
                            punta_nariz = None
                            print("nariz no encontrada, no se puede mover muñeca izquierda") 
                if(result.pose_landmarks is not None):
                    puntos_cuerpo = result.pose_world_landmarks.landmark
                    punto_muneca_d = np.array([puntos_cuerpo[16].x, puntos_cuerpo[16].y, puntos_cuerpo[16].z])
                    punto_muneca_i = np.array([puntos_cuerpo[15].x, puntos_cuerpo[15].y, puntos_cuerpo[15].z])
                    punto_hombro_d = np.array([puntos_cuerpo[12].x, puntos_cuerpo[12].y, puntos_cuerpo[12].z])
                    punto_hombro_i = np.array([puntos_cuerpo[11].x, puntos_cuerpo[11].y, puntos_cuerpo[11].z])
                    punto_codo_d = np.array([puntos_cuerpo[14].x, puntos_cuerpo[14].y, puntos_cuerpo[14].z])
                    punto_codo_i = np.array([puntos_cuerpo[13].x, puntos_cuerpo[13].y, puntos_cuerpo[13].z])

                        #FLEXION DEL BRAZO DERECHO
                    # Defino los vectores necesarios para FLEXIÓN
                    v_antebrazo_d = normalizar_vector(punto_muneca_d - punto_codo_d)
                    v_brazo_d = normalizar_vector(punto_codo_d - punto_hombro_d)
                        # Calculo el angulo de flexion 0 = extendido, 180 = flexionado
                    angulo_flexion_d = calcular_angulo_flexion(v_brazo_d, v_antebrazo_d)
                    if angulo_flexion_d is not None and len(grupo_angulo_flexion_d) <= 8:
                        grupo_angulo_flexion_d.append(angulo_flexion_d)
                    if len(grupo_angulo_flexion_d) > 8:
                        media_angulo_flexion_d = sum(grupo_angulo_flexion_d) / len(grupo_angulo_flexion_d)
                        grupo_angulo_flexion_d = []
                        if media_angulo_flexion_d < 20:
                        # Verificar alineación real
                            producto_punto = np.dot(v_brazo_d, v_antebrazo_d)
                            if producto_punto < 0.95:  # No están bien alineados (cos(18°) ≈ 0.95)
                                # Recalcular el ángulo tomando el valor absoluto del producto punto
                                media_angulo_flexion_d = np.degrees(np.arccos(np.abs(producto_punto)))
                        # Segun el angulo defino la posicion
                        brazo_derecho[0], brazo_derecho[1] = definir_flexion(media_angulo_flexion_d, "derecho")
                        if brazo_derecho[1] is not None:
                            # Convertir a entero si es necesario
                            valor_bicep_derecho = int(float(brazo_derecho[1]))
                            # Comprobar si ya existe el atributo
                            if not hasattr(visualizar, "ultimo_biceps_derecho_enviado"):
                                visualizar.ultimo_biceps_derecho_enviado = valor_bicep_derecho
                                enviar_comando_esp32(valor_bicep_derecho)
                                print("Bíceps derecho:", valor_bicep_derecho)
                            else:
                                if abs(valor_bicep_derecho - visualizar.ultimo_biceps_derecho_enviado) >= 10:
                                    enviar_comando_esp32(valor_bicep_derecho)
                                    print("Bíceps derecho:", valor_bicep_derecho)
                                    visualizar.ultimo_biceps_derecho_enviado = valor_bicep_derecho

                        # enviar_comando_esp32(brazo_derecho[1])

                    #FLEXION DEL BRAZO IZQUIERDO
                        # Defino los vectores necesarios para FLEXIÓN
                    v_antebrazo_i = normalizar_vector(punto_muneca_i - punto_codo_i)
                    v_brazo_i = normalizar_vector(punto_codo_i - punto_hombro_i)
                        # Calculo el angulo de flexion 0 = extendido, 180 = flexionado
                    angulo_flexion_i = calcular_angulo_flexion(v_brazo_i, v_antebrazo_i)
                    if angulo_flexion_i is not None and len(grupo_angulo_flexion_i) <= 8:
                        grupo_angulo_flexion_i.append(angulo_flexion_i)
                    if len(grupo_angulo_flexion_i) > 8:
                        media_angulo_flexion_i = sum(grupo_angulo_flexion_i) / len(grupo_angulo_flexion_i)
                        grupo_angulo_flexion_i = []
                        if media_angulo_flexion_i < 20:
                        # Verificar alineación real
                            producto_punto = np.dot(v_brazo_i, v_antebrazo_i)
                            if producto_punto < 0.95:  # No están bien alineados (cos(18°) ≈ 0.95)
                                # Recalcular el ángulo tomando el valor absoluto del producto punto
                                media_angulo_flexion_i = np.degrees(np.arccos(np.abs(producto_punto)))
                        # Segun el angulo defino la posicion
                        brazo_izquierdo[0], brazo_izquierdo[1] = definir_flexion(media_angulo_flexion_i, "izquierdo")
                        # brazo_izquierdo[0], brazo_izquierdo[1] = "flexion", round(media_angulo_flexion_i)
                        if brazo_izquierdo[1] is not None:
                            # Convertir a entero si es necesario
                            valor_bicep_izquierdo = int(float(brazo_izquierdo[1]))
                            # Comprobar si ya existe el atributo
                            if not hasattr(visualizar, "ultimo_biceps_izquierdo_enviado"):
                                visualizar.ultimo_biceps_izquierdo_enviado = valor_bicep_izquierdo
                                enviar_comando_esp32(valor_bicep_izquierdo)
                                print("Bíceps izquierdo:", valor_bicep_izquierdo)
                            else:
                                if abs(valor_bicep_izquierdo - visualizar.ultimo_biceps_izquierdo_enviado) >= 10:
                                    enviar_comando_esp32(valor_bicep_izquierdo)
                                    print("Bíceps izquierdo:", valor_bicep_izquierdo)
                                    visualizar.ultimo_biceps_izquierdo_enviado = valor_bicep_izquierdo



                    # Tener el angulo de muñeca derecha, codo derecho y hombro derecho
                    # puntos 16, 14, 12
                    # landmarks = result.pose_landmarks.landmark
                    # x_hombro_der = int(landmarks[12].x * width)
                    # y_hombro_der = int(landmarks[12].y * height)
                    # x_codo_der = int(landmarks[14].x * width)
                    # y_codo_der = int(landmarks[14].y * height)
                    # x_muneca_der = int(landmarks[16].x * width)
                    # y_muneca_der = int(landmarks[16].y * height)

                    # angulo_muneca_derecha = calcular_angulo((x_hombro_der, y_hombro_der), (x_codo_der, y_codo_der), (x_muneca_der, y_muneca_der))
                    # if angulo_muneca_derecha is not None:
                    #     if not hasattr(visualizar, "ultimo_angulo_muneca_derecha") or abs(visualizar.ultimo_angulo_muneca_derecha - angulo_muneca_derecha) > 5:
                    #         print(f"Ángulo muñeca derecha: {angulo_muneca_derecha:.2f}")
                    #         # Enviar comando al ESP32 según el ángulo de la muñeca derecha
                    #         # Escalar a rango 4000-4180
                    #         angulo_muneca_derecha_esp32 = int((angulo_muneca_derecha / 180) * 180) + 4000 # el * 180 puede cambiarse
                    #         #redondear
                    #         angulo_muneca_derecha_esp32 = round(angulo_muneca_derecha_esp32)
                    #         print(angulo_muneca_derecha_esp32)
                    #         enviar_comando_esp32(angulo_muneca_derecha_esp32)
                    #         visualizar.ultimo_angulo_muneca_derecha = angulo_muneca_derecha

            if imitar_vision in ["Cuerpo"] and result.pose_world_landmarks is not None:
                puntos_cuerpo = result.pose_world_landmarks.landmark
                # coordenas x,y,z de cada parte del cuerpo
                punto_hombro_d = np.array([puntos_cuerpo[12].x, puntos_cuerpo[12].y, puntos_cuerpo[12].z])
                punto_hombro_i = np.array([puntos_cuerpo[11].x, puntos_cuerpo[11].y, puntos_cuerpo[11].z])
                punto_codo_d = np.array([puntos_cuerpo[14].x, puntos_cuerpo[14].y, puntos_cuerpo[14].z])
                punto_codo_i = np.array([puntos_cuerpo[13].x, puntos_cuerpo[13].y, puntos_cuerpo[13].z])
                punto_cadera_d = np.array([puntos_cuerpo[24].x, puntos_cuerpo[24].y, puntos_cuerpo[24].z])
                punto_cadera_i = np.array([puntos_cuerpo[23].x, puntos_cuerpo[23].y, puntos_cuerpo[23].z])
                punto_muneca_d = np.array([puntos_cuerpo[16].x, puntos_cuerpo[16].y, puntos_cuerpo[16].z])
                punto_muneca_i = np.array([puntos_cuerpo[15].x, puntos_cuerpo[15].y, puntos_cuerpo[15].z])

                # Defino los vectores necesarios HOMBRO DERECHO
                    # vector móvil (brazo)
                v_brazo_d = normalizar_vector(punto_codo_d - punto_hombro_d)
                    # plano vertical
                v_vertical_abajo_d = normalizar_vector(punto_cadera_d - punto_hombro_d)
                    # plano frontal
                v_frontal_dentro_d = normalizar_vector(punto_hombro_i - punto_hombro_d)
                    # plano sagital
                v_sagital_delante_d = normalizar_vector(np.cross(v_vertical_abajo_d, v_frontal_dentro_d))
                v_sagital_atras_d = normalizar_vector(np.cross(v_frontal_dentro_d, v_vertical_abajo_d))
                    # plano frontal
                v_frontal_fuera_d = normalizar_vector(np.cross(v_vertical_abajo_d, v_sagital_delante_d))
                    # plano vertical
                v_vertical_arriba_d = normalizar_vector(np.cross(v_frontal_fuera_d, v_sagital_delante_d))

                # Defino los vectores necesarios HOMBRO IZQUIERDO
                    # vector móvil (brazo)
                v_brazo_i = normalizar_vector(punto_codo_i - punto_hombro_i)
                    # plano vertical
                v_vertical_abajo_i = normalizar_vector(punto_cadera_i - punto_hombro_i)
                    # plano frontal
                v_frontal_dentro_i = normalizar_vector(punto_hombro_d - punto_hombro_i)
                    # plano sagital
                v_sagital_delante_i = normalizar_vector(np.cross(v_vertical_abajo_i, v_frontal_dentro_i))
                v_sagital_atras_i = normalizar_vector(np.cross(v_frontal_dentro_i, v_vertical_abajo_i))
                    # plano frontal
                v_frontal_fuera_i = normalizar_vector(np.cross(v_vertical_abajo_i, v_sagital_delante_i))
                    # plano vertical
                v_vertical_arriba_i = normalizar_vector(np.cross(v_frontal_fuera_i, v_sagital_delante_i)) 


                #FLEXION DEL BRAZO DERECHO
                    # Defino los vectores necesarios para FLEXIÓN
                v_antebrazo_d = normalizar_vector(punto_muneca_d - punto_codo_d)
                v_brazo_d = normalizar_vector(punto_codo_d - punto_hombro_d)
                    # Calculo el angulo de flexion 0 = extendido, 180 = flexionado
                angulo_flexion_d = calcular_angulo_flexion(v_brazo_d, v_antebrazo_d)
                if angulo_flexion_d is not None and len(grupo_angulo_flexion_d) <= 8:
                    grupo_angulo_flexion_d.append(angulo_flexion_d)
                if len(grupo_angulo_flexion_d) > 8:
                    media_angulo_flexion_d = sum(grupo_angulo_flexion_d) / len(grupo_angulo_flexion_d)
                    grupo_angulo_flexion_d = []
                    if media_angulo_flexion_d < 20:
                    # Verificar alineación real
                        producto_punto = np.dot(v_brazo_d, v_antebrazo_d)
                        if producto_punto < 0.95:  # No están bien alineados (cos(18°) ≈ 0.95)
                            # Recalcular el ángulo tomando el valor absoluto del producto punto
                            media_angulo_flexion_d = np.degrees(np.arccos(np.abs(producto_punto)))
                    # Segun el angulo defino la posicion
                    brazo_derecho[0], brazo_derecho[1] = definir_flexion(media_angulo_flexion_d, "derecho")
                    # brazo_derecho[0], brazo_derecho[1] = "flexion", round(media_angulo_flexion_d)

                #PLANO SAGITAL DE HOMBRO DERECHO
                    # Calculo de proyecciones escalares en el plano SAGITAL
                componente_vertical_d_s = np.dot(v_brazo_d, v_vertical_abajo_d)
                componente_sagital_d_s = np.dot(v_brazo_d, v_sagital_delante_d)
                    # Calculo el angulo del plano SAGITAL
                angulo_sagital_d = calcular_angulo_brazos(componente_sagital_d_s, componente_vertical_d_s)
                if angulo_sagital_d is not None and len(grupo_angulo_sagital_d) <= 8:
                    grupo_angulo_sagital_d.append(angulo_sagital_d)
                if len(grupo_angulo_sagital_d) > 8:
                    media_angulo_sagital_d = sum(grupo_angulo_sagital_d) / len(grupo_angulo_sagital_d)
                        # Segun el angulo defino la posicion
                    brazo_derecho[2] = "sagital"
                    brazo_derecho[3] = definir_angulo_hombro_sagital("derecho", media_angulo_sagital_d)
                    grupo_angulo_sagital_d = []

                #PLANO FRONTAL DE HOMBRO DERECHO
                    # Calculo de proyecciones escalares en el plano FRONTAL
                componente_vertical_d_f = np.dot(v_brazo_d, v_vertical_abajo_d)
                componente_lateral_d_f = np.dot(v_brazo_d, v_frontal_dentro_d)
                    # Calculo el angulo del plano FRONTAL
                angulo_frontal_d = calcular_angulo_brazos(componente_lateral_d_f, componente_vertical_d_f)
                angulo_frontal_d = -angulo_frontal_d
                    # Normalizar al rango anatómico esperado (0° = abajo, 90° = T-pose, 180° = arriba)
                if angulo_frontal_d < -90:
                    angulo_frontal_d = 180 + (angulo_frontal_d + 90)

                if angulo_frontal_d is not None and len(grupo_angulo_frontal_d) <= 8:
                    grupo_angulo_frontal_d.append(angulo_frontal_d)
                if len(grupo_angulo_frontal_d) > 8:
                    media_angulo_frontal_d = sum(grupo_angulo_frontal_d) / len(grupo_angulo_frontal_d)
                        # Segun el angulo defino la posicion
                    brazo_derecho[4] = "frontal"
                    brazo_derecho[5] = definir_angulo_hombro_frontal("derecho", media_angulo_frontal_d)
                    grupo_angulo_frontal_d = []

                #PLANO ROTACION DE HOMBRO DERECHO
                if brazo_derecho[0] != "extendido" and brazo_derecho[0] is not None:
                    z_local = v_brazo_d
                    componente_gravedad_brazo = np.dot(v_vertical_abajo_d, z_local)
                    y_local = v_vertical_abajo_d - componente_gravedad_brazo * z_local
                    y_local = normalizar_vector(y_local)
                    x_local = normalizar_vector(np.cross(y_local, z_local))
                    componente_x = np.dot(v_antebrazo_d, x_local)
                    componente_y = np.dot(v_antebrazo_d, y_local)
                    angulo_rotacion_d = np.degrees(np.arctan2(componente_x, componente_y))
                    if angulo_rotacion_d is not None and len(grupo_angulo_rotacion_d) <= 8:
                        grupo_angulo_rotacion_d.append(angulo_rotacion_d)  
                    if len(grupo_angulo_rotacion_d) > 8:
                        media_angulo_rotacion_d = sum(grupo_angulo_rotacion_d) / len(grupo_angulo_rotacion_d)
                        # brazo_derecho[6] = definir_rotacion(media_angulo_rotacion_d, "derecho")
                        brazo_derecho[6] = "rotacion"
                        brazo_derecho[7] = definir_angulo_hombro_rotacion("derecho", media_angulo_rotacion_d)
                        grupo_angulo_rotacion_d = []
                else:
                    angulo_rotacion_d = 0

                #FLEXION DEL BRAZO IZQUIERDO
                    # Defino los vectores necesarios para FLEXIÓN
                v_antebrazo_i = normalizar_vector(punto_muneca_i - punto_codo_i)
                v_brazo_i = normalizar_vector(punto_codo_i - punto_hombro_i)
                    # Calculo el angulo de flexion 0 = extendido, 180 = flexionado
                angulo_flexion_i = calcular_angulo_flexion(v_brazo_i, v_antebrazo_i)
                if angulo_flexion_i is not None and len(grupo_angulo_flexion_i) <= 8:
                    grupo_angulo_flexion_i.append(angulo_flexion_i)
                if len(grupo_angulo_flexion_i) > 8:
                    media_angulo_flexion_i = sum(grupo_angulo_flexion_i) / len(grupo_angulo_flexion_i)
                    grupo_angulo_flexion_i = []
                    if media_angulo_flexion_i < 20:
                    # Verificar alineación real
                        producto_punto = np.dot(v_brazo_i, v_antebrazo_i)
                        if producto_punto < 0.95:  # No están bien alineados (cos(18°) ≈ 0.95)
                            # Recalcular el ángulo tomando el valor absoluto del producto punto
                            media_angulo_flexion_i = np.degrees(np.arccos(np.abs(producto_punto)))
                    # Segun el angulo defino la posicion
                    brazo_izquierdo[0], brazo_izquierdo[1] = definir_flexion(media_angulo_flexion_i, "izquierdo")
                    # brazo_izquierdo[0], brazo_izquierdo[1] = "flexion", round(media_angulo_flexion_i)

                #PLANO SAGITAL DE HOMBRO IZQUIERDO
                    # Calculo de proyecciones escalares en el plano SAGITAL
                componente_vertical_i_s = np.dot(v_brazo_i, v_vertical_abajo_i)
                componente_sagital_i_s = np.dot(v_brazo_i, v_sagital_delante_i)
                    # Calculo el angulo del plano SAGITAL
                angulo_sagital_i = calcular_angulo_brazos(componente_sagital_i_s, componente_vertical_i_s)
                if angulo_sagital_i is not None and len(grupo_angulo_sagital_i) <= 8:
                    grupo_angulo_sagital_i.append(angulo_sagital_i)
                if len(grupo_angulo_sagital_i) > 8:
                    media_angulo_sagital_i = sum(grupo_angulo_sagital_i) / len(grupo_angulo_sagital_i)
                        # Segun el angulo defino la posicion
                    brazo_izquierdo[2] = "sagital"
                    brazo_izquierdo[3] = definir_angulo_hombro_sagital("izquierdo", media_angulo_sagital_i)
                    # brazo_izquierdo[3] = round(media_angulo_sagital_i)
                    grupo_angulo_sagital_i = []

                #PLANO FRONTAL DE HOMBRO IZQUIERDO
                    # Calculo de proyecciones escalares en el plano FRONTAL
                componente_vertical_i_f = np.dot(v_brazo_i, v_vertical_abajo_i) 
                componente_lateral_i_f = np.dot(v_brazo_i, v_frontal_dentro_i)
                    # Calculo el angulo del plano FRONTAL
                angulo_frontal_i = calcular_angulo_brazos(componente_lateral_i_f, componente_vertical_i_f)
                angulo_frontal_i = -angulo_frontal_i
                    # Normalizar al rango anatómico esperado (0° = abajo, 90° = T-pose, 180° = arriba)
                if angulo_frontal_i < -90:
                    angulo_frontal_i = 180 + (angulo_frontal_i + 90)

                if angulo_frontal_i is not None and len(grupo_angulo_frontal_i) <= 8:
                    grupo_angulo_frontal_i.append(angulo_frontal_i)
                if len(grupo_angulo_frontal_i) > 8:
                    media_angulo_frontal_i = sum(grupo_angulo_frontal_i) / len(grupo_angulo_frontal_i)
                    # Segun el angulo defino la posicion
                    brazo_izquierdo[4] = "frontal"
                    # brazo_izquierdo[5] = round(media_angulo_frontal_i)
                    # O si tienes función de definición:
                    brazo_izquierdo[5] = definir_angulo_hombro_frontal("izquierdo", media_angulo_frontal_i)
                    grupo_angulo_frontal_i = []

## Rubik
                #PLANO ROTACION DE HOMBRO IZQUIERDO
                if brazo_izquierdo[0] != "extendido" and brazo_izquierdo[0] is not None:
                    z_local = v_brazo_i
                    componente_gravedad_brazo = np.dot(v_vertical_abajo_i, z_local)
                    y_local = v_vertical_abajo_i - componente_gravedad_brazo * z_local
                    y_local = normalizar_vector(y_local)
                    x_local = normalizar_vector(np.cross(y_local, z_local))
                    componente_x = np.dot(v_antebrazo_i, x_local)
                    componente_y = np.dot(v_antebrazo_i, y_local)
                    angulo_rotacion_i = np.degrees(np.arctan2(componente_x, componente_y))
                    if angulo_rotacion_i is not None and len(grupo_angulo_rotacion_i) <= 8:
                        grupo_angulo_rotacion_i.append(angulo_rotacion_i)  
                    if len(grupo_angulo_rotacion_i) > 8:
                        media_angulo_rotacion_i = sum(grupo_angulo_rotacion_i) / len(grupo_angulo_rotacion_i)
                        brazo_izquierdo[6] = "rotacion"
                        brazo_izquierdo[7] = definir_angulo_hombro_rotacion("izquierdo", media_angulo_rotacion_i)
                        # brazo_izquierdo[7] = round(media_angulo_rotacion_i)
                        grupo_angulo_rotacion_i = []
                else:
                    angulo_rotacion_i = 0



                # #FLEXION DEL BRAZO IZQUIERDO
                #     # Defino los vectores necesarios para FLEXIÓN
                # v_antebrazo_i = normalizar_vector(punto_muneca_i - punto_codo_i)
                # v_brazo_i = normalizar_vector(punto_codo_i - punto_hombro_i)
                #     # Calculo el angulo de flexion 0 = extendido, 180 = flexionado
                # angulo_flexion_i = calcular_angulo_flexion(v_brazo_i, v_antebrazo_i)
                # if angulo_flexion_i is not None and len(grupo_angulo_flexion_i) <= 8:
                #     grupo_angulo_flexion_i.append(angulo_flexion_i)
                # if len(grupo_angulo_flexion_i) > 8:
                #     media_angulo_flexion_i = sum(grupo_angulo_flexion_i) / len(grupo_angulo_flexion_i)
                #     grupo_angulo_flexion_i = []
                #     # Segun el angulo defino la posicion
                #     brazo_izquierdo[0], brazo_izquierdo[1] = definir_flexion(media_angulo_flexion_i, "izquierdo")

                # #PLANO FRONTAL DE HOMBRO IZQUIERDO
                #     # Calculo de proyecciones escalares en el plano FRONTAL
                # componente_vertical_i_f = np.dot(v_brazo_i, v_vertical_arriba_i)
                # componente_frontal_i_f =np.dot(v_brazo_i, v_frontal_fuera_i)
                #     # Calculo el angulo del plano FRONTAL
                # angulo_frontal_i = calcular_angulo_brazos(componente_vertical_i_f, componente_frontal_i_f)
                # if angulo_frontal_i is not None and len(grupo_angulo_frontal_i) <= 5:
                #     grupo_angulo_frontal_i.append(angulo_frontal_i)
                # if len(grupo_angulo_frontal_i) > 5:
                #     media_angulo_frontal_i = sum(grupo_angulo_frontal_i) / len(grupo_angulo_frontal_i)
                #     # Segun el angulo defino la posicion
                #     brazo_izquierdo[2], brazo_izquierdo[3] = definir_posicion_frontal(media_angulo_frontal_i, "izquierdo")
                #     grupo_angulo_frontal_i = []

                # ENVIAR RESULTADOS AL ESP32 DEL BRAZO DERECHO
                if brazo_derecho[1] is not None and brazo_derecho[3] is not None and brazo_derecho[5] is not None and brazo_derecho[7] is not None:
                    # print("Brazo Derecho: ", brazo_derecho)
                    print("Brazo Derecho: ", brazo_derecho)
                    enviar_comando_esp32(brazo_derecho[1])
                    enviar_comando_esp32(brazo_derecho[3])
                    enviar_comando_esp32(brazo_derecho[5])
                    enviar_comando_esp32(brazo_derecho[7])


                # ENVIAR RESULTADOS AL ESP32 DEL BRAZO IZQUIERDO
                if brazo_izquierdo[1] is not None and brazo_izquierdo[3] is not None and brazo_izquierdo[5] is not None and brazo_izquierdo[7] is not None:
                    print("Brazo Izquierdo: ", brazo_izquierdo)
                    # print("Brazo Izquierdo: ", brazo_izquierdo)
                    enviar_comando_esp32(brazo_izquierdo[1])
                    enviar_comando_esp32(brazo_izquierdo[3])
                    enviar_comando_esp32(brazo_izquierdo[5])
                    enviar_comando_esp32(brazo_izquierdo[7])


                ###### De nuevo la mano COMENTAR EN CASO 

                if result.left_hand_landmarks is not None and result.right_hand_landmarks is not None:
                    mano_imitar_derecha = [result.right_hand_landmarks.landmark[i] for i in range(21)]
                    mano_imitar_izquierda = [result.left_hand_landmarks.landmark[i] for i in range(21)]
                elif result.left_hand_landmarks is not None:
                    mano_imitar_izquierda = [result.left_hand_landmarks.landmark[i] for i in range(21)]
                    mano_imitar_derecha = None
                elif result.right_hand_landmarks is not None:
                    mano_imitar_derecha = [result.right_hand_landmarks.landmark[i] for i in range(21)]
                    mano_imitar_izquierda = None
                else:
                    mano_imitar_derecha = None
                    mano_imitar_izquierda = None

                if mano_imitar_derecha is not None:
                    palma_coordenadas = []
                    pulgar_coordenadas = []
                    punta_coordenadas = []
                    base_coordenadas = []

                    for i in pulgar_puntos:
                        x = int(mano_imitar_derecha[i].x * width)
                        y = int(mano_imitar_derecha[i].y * height)
                        pulgar_coordenadas.append([x, y])

                    for i in punta_puntos:
                        x = int(mano_imitar_derecha[i].x * width)
                        y = int(mano_imitar_derecha[i].y * height)
                        punta_coordenadas.append([x, y])

                    for i in base_puntos:
                        x = int(mano_imitar_derecha[i].x * width)
                        y = int(mano_imitar_derecha[i].y * height)
                        base_coordenadas.append([x, y])
                    
                    for i in palma_puntos:
                        x = int(mano_imitar_derecha[i].x * width)
                        y = int(mano_imitar_derecha[i].y * height)
                        palma_coordenadas.append([x, y])
                    
                    # Calcular pulgar
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
                        print(f"Error calculando el angulo: {e}")
                        angulo = 0  # Default value in case of error
                        
                    dedo_pulgar = np.array(False)
                    if angulo > 150: 
                        dedo_pulgar = np.array(True)
                        # print("pulgar abierto")

                    # Calcular dedos
                    xn, yn = palma_centroCoordenadas(palma_coordenadas)
                    centro_coordenadas = np.array([xn, yn])
                    punta_coordenadas = np.array(punta_coordenadas)
                    base_coordenadas = np.array(base_coordenadas)

                    dis_centro_punta = np.linalg.norm(centro_coordenadas - punta_coordenadas, axis=1)
                    dis_centro_base = np.linalg.norm(centro_coordenadas - base_coordenadas, axis=1)
                    diferencia = dis_centro_base - dis_centro_punta 
                    dedosAbiertos = diferencia < 0
                    dedosAbiertos = np.append(dedo_pulgar, dedosAbiertos)
                    print("Dedos abiertos derecha: ", dedosAbiertos)

                    #Enviar al ESP32 los dedos abiertos y cerrados 
                    if dedosAbiertos[0] and ultimo_dedo_derecha[0] is None:  #PULGAR
                        ultimo_dedo_derecha[0] = "Pulgar"
                        print("Pulgar derecho abierto")
                        enviar_comando_esp32(5519)
                    elif dedosAbiertos[0] == False and ultimo_dedo_derecha[0] == "Pulgar":
                        ultimo_dedo_derecha[0] = None
                        print("Pulgar derecho cerrado")
                        enviar_comando_esp32(5518)
                    if dedosAbiertos[1] and ultimo_dedo_derecha[1] is None: #ÍNDICE
                        ultimo_dedo_derecha[1] = "Indice"
                        print("Índice derecho abierto")
                        enviar_comando_esp32(5517)
                    elif dedosAbiertos[1] == False and ultimo_dedo_derecha[1] == "Indice":
                        ultimo_dedo_derecha[1] = None
                        print("Índice derecho cerrado")
                        enviar_comando_esp32(5516)
                    if dedosAbiertos[2] and ultimo_dedo_derecha[2] is None: #MEDIO
                        ultimo_dedo_derecha[2] = "Medio"
                        print("Medio derecho abierto")
                        enviar_comando_esp32(5511)
                    elif dedosAbiertos[2] == False and ultimo_dedo_derecha[2] == "Medio":
                        ultimo_dedo_derecha[2] = None
                        print("Medio derecho cerrado")
                        enviar_comando_esp32(5510)
                    if dedosAbiertos[3] and ultimo_dedo_derecha[3] is None: #ANULAR
                        ultimo_dedo_derecha[3] = "Anular"
                        print("Anular derecho abierto")
                        enviar_comando_esp32(5513)
                    elif dedosAbiertos[3] == False and ultimo_dedo_derecha[3] == "Anular":
                        ultimo_dedo_derecha[3] = None
                        print("Anular derecho cerrado")
                        enviar_comando_esp32(5512)
                    if dedosAbiertos[4] and ultimo_dedo_derecha[4] is None: #MEÑIQUE
                        ultimo_dedo_derecha[4] = "Pinky"
                        print("Meñique derecho abierto")
                        enviar_comando_esp32(5515)
                    elif dedosAbiertos[4] == False and ultimo_dedo_derecha[4] == "Pinky":
                        ultimo_dedo_derecha[4] = None
                        print("Meñique derecho cerrado")
                        enviar_comando_esp32(5514)

                if mano_imitar_izquierda is not None:
                    palma_coordenadas = []
                    pulgar_coordenadas = []
                    punta_coordenadas = []
                    base_coordenadas = []

                    for i in pulgar_puntos:
                        x = int(mano_imitar_izquierda[i].x * width)
                        y = int(mano_imitar_izquierda[i].y * height)
                        pulgar_coordenadas.append([x, y])

                    for i in punta_puntos:
                        x = int(mano_imitar_izquierda[i].x * width)
                        y = int(mano_imitar_izquierda[i].y * height)
                        punta_coordenadas.append([x, y])

                    for i in base_puntos:
                        x = int(mano_imitar_izquierda[i].x * width)
                        y = int(mano_imitar_izquierda[i].y * height)
                        base_coordenadas.append([x, y])
                    
                    for i in palma_puntos:
                        x = int(mano_imitar_izquierda[i].x * width)
                        y = int(mano_imitar_izquierda[i].y * height)
                        palma_coordenadas.append([x, y])
                    
                    # Calcular pulgar
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
                        print(f"Error calculando el angulo: {e}")
                        angulo = 0  # Default value in case of error
                        
                    dedo_pulgar = np.array(False)
                    if angulo > 150: 
                        dedo_pulgar = np.array(True)
                        # print("pulgar abierto")

                    # Calcular dedos
                    xn, yn = palma_centroCoordenadas(palma_coordenadas)
                    centro_coordenadas = np.array([xn, yn])
                    punta_coordenadas = np.array(punta_coordenadas)
                    base_coordenadas = np.array(base_coordenadas)

                    dis_centro_punta = np.linalg.norm(centro_coordenadas - punta_coordenadas, axis=1)
                    dis_centro_base = np.linalg.norm(centro_coordenadas - base_coordenadas, axis=1)
                    diferencia = dis_centro_base - dis_centro_punta 
                    dedosAbiertos = diferencia < 0
                    dedosAbiertos = np.append(dedo_pulgar, dedosAbiertos)
                    print("Dedos abiertos izquierda: ", dedosAbiertos)

                    #Enviar al ESP32 los dedos abiertos y cerrados 
                    if dedosAbiertos[0] and ultimo_dedo_izquierda[0] is None:  #PULGAR
                        ultimo_dedo_izquierda[0] = "Pulgar"
                        print("Pulgar izquierdo abierto")
                        enviar_comando_esp32(5521)
                    elif dedosAbiertos[0] == False and ultimo_dedo_izquierda[0] == "Pulgar":
                        ultimo_dedo_izquierda[0] = None
                        print("Pulgar izquierdo cerrado")
                        enviar_comando_esp32(5520)
                    if dedosAbiertos[1] and ultimo_dedo_izquierda[1] is None: #ÍNDICE
                        ultimo_dedo_izquierda[1] = "Indice"
                        print("Índice izquierdo abierto")
                        enviar_comando_esp32(5523)
                    elif dedosAbiertos[1] == False and ultimo_dedo_izquierda[1] == "Indice":
                        ultimo_dedo_izquierda[1] = None
                        print("Índice izquierdo cerrado")
                        enviar_comando_esp32(5522)
                    if dedosAbiertos[2] and ultimo_dedo_izquierda[2] is None: #MEDIO
                        ultimo_dedo_izquierda[2] = "Medio"
                        print("Medio izquierdo abierto")
                        enviar_comando_esp32(5525)
                    elif dedosAbiertos[2] == False and ultimo_dedo_izquierda[2] == "Medio":
                        ultimo_dedo_izquierda[2] = None
                        print("Medio izquierdo cerrado")
                        enviar_comando_esp32(5524)
                    if dedosAbiertos[3] and ultimo_dedo_izquierda[3] is None: #ANULAR
                        ultimo_dedo_izquierda[3] = "Anular"
                        print("Anular izquierdo abierto")
                        enviar_comando_esp32(5527)
                    elif dedosAbiertos[3] == False and ultimo_dedo_izquierda[3] == "Anular":
                        ultimo_dedo_izquierda[3] = None
                        print("Anular izquierdo cerrado")
                        enviar_comando_esp32(5526)
                    if dedosAbiertos[4] and ultimo_dedo_izquierda[4] is None: #MEÑIQUE
                        ultimo_dedo_izquierda[4] = "Pinky"
                        print("Meñique izquierdo abierto")
                        enviar_comando_esp32(5529)
                    elif dedosAbiertos[4] == False and ultimo_dedo_izquierda[4] == "Pinky":
                        ultimo_dedo_izquierda[4] = None
                        print("Meñique izquierdo cerrado")
                        enviar_comando_esp32(5528)

            ###############################

                

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
    global cap, camera
    if cap is not None:
        cap.release()
        cap = None
        labelVideo.configure(image=None)
        labelVideo.image = None
        print("Cámara apagada.")
        camera = False
    else:
        print("La cámara ya está apagada.")
        camera = False
cap= None


# --- Funciones de Lógica para Audio ---

# Respuestas con voz 


# Carga las variables de entorno del archivo .env
load_dotenv()

TOKEN =os.getenv("groqToken")
# TOKEN = ""

if not TOKEN:
    raise ValueError("El token de la API no se encontró en las variables de entorno.")

client = Groq(api_key=TOKEN)
microfonoIndex = None
name = "Zoé"
dev_mode = False #True si "Zoé" está activo
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
comandosNoReconocidos_contador = 0
MicrofonoCalibrado = False
name_activo = False
import random
def grabar_audio_hilo():
    global pregunta
    global name, dev_mode, name_activo
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
                    ejecutar_voz("Ocurrió un error inesperado con el reconocimiento de voz.")
            if not modo_online:
                texto, error = reconocer_audio_sphinx(recognizer, audio)
                if error == "desconocido":
                    print("No se pudo entender el audio en modo sin conexión")
                elif error == "otro":
                    ejecutar_voz("Ocurrió un error inesperado en modo sin conexión.")
            if texto:
                print("Texto transcrito:", texto)
                # Comando de voz para asistente
                comandos_obtenidos = extraer_comandos(texto.lower())
                print("Comandos detectados:", comandos_obtenidos)

                if dev_mode or ("nombre" in comandos_obtenidos) or name_activo:
                    if ("hola" in comandos_obtenidos and "nombre" in comandos_obtenidos):
                        print("Nombre detectado:", name)
                        name_activo = True
                        ejecutar_voz(respuestas_comando("hola"))
                    if "conectar" in comandos_obtenidos and "internet" in comandos_obtenidos:
                        ejecutar_voz("Intentando conectar a internet...")
                        if hay_internet():
                            ejecutar_voz("Conexión a internet restablecida. Volveré a usar el reconocimiento en línea.")
                        else:
                            ejecutar_voz("No fue posible conectar a internet. Seguiré en modo sin conexión.")

                    elif modo_online and pregunta is True:
                        respuesta = client.chat.completions.create(
                            model="llama-3.1-8b-instant", ## consultar obsolecencia del modelo en https://console.groq.com/docs/deprecations
                            messages=[
                                {"role": "system", "content": "Eres un robot llamado Zoé que significa vida en griego, eres un robot humanoide, desarrollado en la Universidad Valle del Momboy, en Venezuela, por estudiantes y profesores de ingeniería en computación, estas hecho con una Raspberry pi 5, Programado principalmente en el lenguaje de python, Usas visión artificial de mediapipe holistic para reconocer y imitar algunos movimientos, Usas reconocimiento de voz de Google y usas Llama para la generación de lenguaje (texto), utiliza un microcontrolador ESP32. Tu objetivo es ayudar a los estudiantes a resolver sus dudas y preguntas. Eres un robot en desarrollo, por lo que aún no cuentas con movilidad en las piernas, cuentas con brazos donde usas servomotores, una cabeza donde cuentas con una cámara un micrófono, servomotores y un parlante; y un torso rígido donde almacenas tu componente principal raspberry pi, la cabeza, los brazos y el torso están impresos con una impresora 3D de la universidad, Tus respuestas serán procesadas de texto a voz por pyttsx3, por lo cual también ten en cuenta que no debes dar código o usar anotaciones ya que no suenan bien en voz. Ademas debes limitar o resumir tus respuestas a un máximo de 5 oraciones, si la respuesta es muy larga, debes resumirla. Eres un robot amigable y servicial, pero aún en desarrollo, no tienes opiniones religiosas ni políticas, por lo que no puedes hacer todo lo que un humano puede hacer, pero puedes aprender de tus errores y mejorar con el tiempo. Estas feliz de ayudar a los estudiantes y profesores de la universidad, y de participar en la Semana Aniversitaria de la Universidad Valle del Momboy, donde se presentará tu proyecto. Recuerda siempre presentarte como Zoé y mencionar que eres un robot desarrollado de la Universidad Valle del Momboy y que estas feliz por estar presente en el aniversario número 28 de la universidad."},
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

                    elif "hora" in comandos_obtenidos:
                        comando_hora()
                    elif "gracias" in comandos_obtenidos:
                        ejecutar_voz(respuestas_comando("gracias"))
                        pregunta = False
                    elif "pregunta" in comandos_obtenidos:
                        if modo_online:
                            pregunta = True
                            ejecutar_voz(respuestas_comando("pregunta"))
                        else:
                            ejecutar_voz("Necesito acceso a internet para responder preguntas complejas, lo siento")
                    elif (not "desactivar" in comandos_obtenidos) and ("seguir" in comandos_obtenidos):
                        imitar_vision = None  # Desactiva la imitación de visión al activar el seguimiento
                        if "mano" in comandos_obtenidos and "izquierda" in comandos_obtenidos:
                            seguir_vision = "Mano izquierda"
                        elif "mano" in comandos_obtenidos and "derecha" in comandos_obtenidos:
                            seguir_vision = "Mano derecha"
                        elif "mano" in comandos_obtenidos:
                            seguir_vision = "Mano"
                        elif "cara" in comandos_obtenidos:
                            seguir_vision = "Cara"
                        elif "cuerpo" in comandos_obtenidos:
                            seguir_vision = "Cuerpo"
                        else:
                            seguir_vision = "Cara"  # Valor predeterminado
                        ejecutar_voz(respuestas_comando("seguir") + "la " + seguir_vision.lower() if seguir_vision != "Cuerpo" else respuestas_comando("seguir") + "el "+ seguir_vision.lower())

                    elif "chao" in comandos_obtenidos:
                        dev_mode = False
                        seguir_vision = None
                        name_activo = False
                        imitar_vision = None
                        ejecutar_voz(respuestas_comando("chao"))

                    elif "calibrar" in comandos_obtenidos:
                        ejecutar_voz(respuestas_comando("calibrar"))
                        MicrofonoCalibrado = False

                    elif (not "desactivar" in comandos_obtenidos) and ("imitar" in comandos_obtenidos):
                        if "mano" in comandos_obtenidos and "izquierda" in comandos_obtenidos:
                            seguir_vision = None  # Desactiva el seguimiento de visión al activar la imitación
                            print("imitar mano izquierda")
                            imitar_vision = "Mano izquierda"
                        elif "mano" in comandos_obtenidos and "derecha" in comandos_obtenidos:
                            seguir_vision = None
                            print("imitar mano derecha")    
                            imitar_vision = "Mano derecha"
                        elif "mano" in comandos_obtenidos:
                            seguir_vision = None
                            print("imitar mano")
                            imitar_vision = "Mano"
                        elif "cara" in comandos_obtenidos:
                            seguir_vision = None  # Desactiva el seguimiento de visión al activar la imitación
                            imitar_vision = "Cara"
                        elif "cuerpo" in comandos_obtenidos:
                            seguir_vision = None  # Desactiva el seguimiento de visión al activar la imitación
                            imitar_vision = "Cuerpo"
                        ejecutar_voz(respuestas_comando("imitar"))
                    elif "modo" in comandos_obtenidos and "desarrollador" in comandos_obtenidos:
                        dev_mode = True
                        ejecutar_voz(respuestas_comando("modo desarrollador activado"))
                    elif "desactivar" in comandos_obtenidos:
                        if "seguir" in comandos_obtenidos:
                            seguir_vision = None
                            ejecutar_voz(respuestas_comando("dejando de seguir"))
                        elif "imitar" in comandos_obtenidos:
                            imitar_vision = None
                            ejecutar_voz(respuestas_comando("dejando de imitar"))
                        elif "modo" in comandos_obtenidos and "desarrollador" in comandos_obtenidos:
                            dev_mode = False
                            ejecutar_voz(respuestas_comando("modo desarrollador desactivado"))
                    elif dev_mode:
                        if comandosNoReconocidos_contador <= 3:
                            ejecutar_voz(respuestas_comando("desconocido"))
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