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
from pathlib import Path
## pyinstaller --icon=icono.ico --add-data "icono.ico;." main.py
## al compilar recordar que se deben incluir los archivos de modelo y los recursos necesarios

## importar modulos personalizados
from Clavicula import _to_int_safe, definir_angulo_hombro_rotacion, definir_angulo_hombro_frontal, definir_angulo_hombro_sagital, calcular_angulo_brazos, definir_flexion, calcular_angulo_flexion, normalizar_vector, calcular_angulo,Calcular_distancia_Punto_a_RectaAB, punto_medio_segmento
from esp32 import iniciar_conexion_serial, enviar_esp32, cerrar_serial, listar_seriales
from yammetModel import YammetModel
from grabar_posicion import GrabarPosicion
# from Raspberry.yammetModel import YammetModel
# para la hora actual quitar si se hace de otra manera
from datetime import datetime


## importar json de diccionario
with open('Raspberry/comandos.json', 'r', encoding='utf-8') as f:
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

posiciones_grabadas = {
    "posicion_cabeza_horizontal": None,
    "posicion_ojos_horizontal": None,
    "posicion_ojos_vertical": None,

    "posicion_dedo_pulgar_derecho": None,
    "posicion_dedo_indice_derecho": None,
    "posicion_dedo_medio_derecho": None,
    "posicion_dedo_anular_derecho": None,
    "posicion_dedo_menique_derecho": None,
    "posicion_muneca_derecho": None,

    "posicion_dedo_pulgar_izquierdo": None,
    "posicion_dedo_indice_izquierdo": None,
    "posicion_dedo_medio_izquierdo": None,
    "posicion_dedo_anular_izquierdo": None,
    "posicion_dedo_menique_izquierdo": None,
    "posicion_muneca_izquierdo": None,

    "posicion_hombro_sagital_derecho": None,
    "posicion_hombro_frontal_derecho": None,
    "posicion_hombro_rotacion_derecho": None,
    "posicion_bicep_derecho": None,

    "posicion_hombro_sagital_izquierdo": None,
    "posicion_hombro_frontal_izquierdo": None,
    "posicion_hombro_rotacion_izquierdo": None,
    "posicion_bicep_izquierdo": None
}

estado_posicion = None  

posiciones_saludar = {'posicion_cabeza_horizontal': 2290, 'posicion_ojos_horizontal': 1000, 'posicion_ojos_vertical': 1030, 'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5510, 'posicion_dedo_anular_derecho': 5512, 'posicion_dedo_menique_derecho': 5514, 'posicion_muneca_derecho': 5001, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4814, 'posicion_hombro_frontal_derecho': 4431, 'posicion_hombro_rotacion_derecho': 6380, 'posicion_bicep_derecho': 4032, 'posicion_hombro_sagital_izquierdo': 6058, 'posicion_hombro_frontal_izquierdo': 4708, 'posicion_hombro_rotacion_izquierdo': 6578, 'posicion_bicep_izquierdo': 4370}

posiciones_inicial = {'posicion_cabeza_horizontal': 2290, 'posicion_ojos_horizontal': 1000, 'posicion_ojos_vertical': 1030, 'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5511, 'posicion_dedo_anular_derecho': 5513, 'posicion_dedo_menique_derecho': 5515, 'posicion_muneca_derecho': 5001, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4820, 'posicion_hombro_frontal_derecho': 4350, 'posicion_hombro_rotacion_derecho': 6340, 'posicion_bicep_derecho': 4040, 'posicion_hombro_sagital_izquierdo': 6010, 'posicion_hombro_frontal_izquierdo': 4630, 'posicion_hombro_rotacion_izquierdo': 6495, 'posicion_bicep_izquierdo': 4240}

posiciones_action_1 = {'posicion_cabeza_horizontal': 2310, 'posicion_ojos_horizontal': 1160}
posiciones_action_2 = {'posicion_cabeza_horizontal': 2270, 'posicion_ojos_horizontal': 1230}
posiciones_action_3 = {'posicion_cabeza_horizontal': 2290, 'posicion_ojos_horizontal': 1190}

posicion_hablar_1_1 = {'posicion_cabeza_horizontal': 2290, 'posicion_ojos_horizontal': 1190,'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5511, 'posicion_dedo_anular_derecho': 5513, 'posicion_dedo_menique_derecho': 5515, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5526, 'posicion_dedo_menique_izquierdo': 5528, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4858, 'posicion_hombro_frontal_derecho': 4434, 'posicion_hombro_rotacion_derecho': 6318, 'posicion_bicep_derecho': 4175, 'posicion_hombro_sagital_izquierdo': 6045, 'posicion_hombro_frontal_izquierdo': 4683, 'posicion_hombro_rotacion_izquierdo': 6532, 'posicion_bicep_izquierdo': 4375}
posicion_hablar_1_2 = {'posicion_cabeza_horizontal': 2270, 'posicion_ojos_horizontal': 1230,'posicion_dedo_pulgar_derecho': 5518, 'posicion_dedo_indice_derecho': 5516, 'posicion_dedo_medio_derecho': 5511, 'posicion_dedo_anular_derecho': 5513, 'posicion_dedo_menique_derecho': 5515, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4868, 'posicion_hombro_frontal_derecho': 4434, 'posicion_hombro_rotacion_derecho': 6318, 'posicion_bicep_derecho': 4120, 'posicion_hombro_sagital_izquierdo': 6055, 'posicion_hombro_frontal_izquierdo': 4683, 'posicion_hombro_rotacion_izquierdo': 6532, 'posicion_bicep_izquierdo': 4340}
posicion_hablar_1_3 = {'posicion_cabeza_horizontal': 2290, 'posicion_ojos_horizontal': 1190,'posicion_dedo_pulgar_derecho': 5518, 'posicion_dedo_indice_derecho': 5516, 'posicion_dedo_medio_derecho': 5510, 'posicion_dedo_anular_derecho': 5512, 'posicion_dedo_menique_derecho': 5514, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4858, 'posicion_hombro_frontal_derecho': 4434, 'posicion_hombro_rotacion_derecho': 6318, 'posicion_bicep_derecho': 4175, 'posicion_hombro_sagital_izquierdo': 6045, 'posicion_hombro_frontal_izquierdo': 4683, 'posicion_hombro_rotacion_izquierdo': 6532, 'posicion_bicep_izquierdo': 4375}
posicion_hablar_1_4 = {'posicion_cabeza_horizontal': 2310, 'posicion_ojos_horizontal': 1160,'posicion_dedo_pulgar_derecho': 5518, 'posicion_dedo_indice_derecho': 5516, 'posicion_dedo_medio_derecho': 5511, 'posicion_dedo_anular_derecho': 5513, 'posicion_dedo_menique_derecho': 5515, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4863, 'posicion_hombro_frontal_derecho': 4434, 'posicion_hombro_rotacion_derecho': 6318, 'posicion_bicep_derecho': 4120, 'posicion_hombro_sagital_izquierdo': 6050, 'posicion_hombro_frontal_izquierdo': 4683, 'posicion_hombro_rotacion_izquierdo': 6532, 'posicion_bicep_izquierdo': 4340}

posicion_hablar_2_1 = {'posicion_cabeza_horizontal': 2270, 'posicion_ojos_horizontal': 1230, 'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5511, 'posicion_dedo_anular_derecho': 5513, 'posicion_dedo_menique_derecho': 5515, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4841, 'posicion_hombro_frontal_derecho': 4427, 'posicion_hombro_rotacion_derecho': 6380, 'posicion_bicep_derecho': 4175, 'posicion_hombro_sagital_izquierdo': 6017, 'posicion_hombro_frontal_izquierdo': 4643, 'posicion_hombro_rotacion_izquierdo': 6580, 'posicion_bicep_izquierdo': 4375}
posicion_hablar_2_2 = {'posicion_cabeza_horizontal': 2290, 'posicion_ojos_horizontal': 1190, 'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5511, 'posicion_dedo_anular_derecho': 5513, 'posicion_dedo_menique_derecho': 5515, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4841, 'posicion_hombro_frontal_derecho': 4427, 'posicion_hombro_rotacion_derecho': 6380, 'posicion_bicep_derecho': 4075, 'posicion_hombro_sagital_izquierdo': 6017, 'posicion_hombro_frontal_izquierdo': 4643, 'posicion_hombro_rotacion_izquierdo': 6580, 'posicion_bicep_izquierdo': 4290}
posicion_hablar_2_3 = {'posicion_cabeza_horizontal': 2310, 'posicion_ojos_horizontal': 1160,'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5511, 'posicion_dedo_anular_derecho': 5513, 'posicion_dedo_menique_derecho': 5515, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4841, 'posicion_hombro_frontal_derecho': 4427, 'posicion_hombro_rotacion_derecho': 6380, 'posicion_bicep_derecho': 4130, 'posicion_hombro_sagital_izquierdo': 6017, 'posicion_hombro_frontal_izquierdo': 4643, 'posicion_hombro_rotacion_izquierdo': 6580, 'posicion_bicep_izquierdo': 4310}
posicion_hablar_2_4 = {'posicion_cabeza_horizontal': 2290, 'posicion_ojos_horizontal': 1190 ,'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5511, 'posicion_dedo_anular_derecho': 5513, 'posicion_dedo_menique_derecho': 5515, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4841, 'posicion_hombro_frontal_derecho': 4427, 'posicion_hombro_rotacion_derecho': 6380, 'posicion_bicep_derecho': 4150, 'posicion_hombro_sagital_izquierdo': 6017, 'posicion_hombro_frontal_izquierdo': 4643, 'posicion_hombro_rotacion_izquierdo': 6580, 'posicion_bicep_izquierdo': 4290}
posicion_hablar_2_5 = {'posicion_cabeza_horizontal': 2270, 'posicion_ojos_horizontal': 1230, 'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5511, 'posicion_dedo_anular_derecho': 5513, 'posicion_dedo_menique_derecho': 5515, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4841, 'posicion_hombro_frontal_derecho': 4427, 'posicion_hombro_rotacion_derecho': 6380, 'posicion_bicep_derecho': 4175, 'posicion_hombro_sagital_izquierdo': 6017, 'posicion_hombro_frontal_izquierdo': 4643, 'posicion_hombro_rotacion_izquierdo': 6580, 'posicion_bicep_izquierdo': 4310}

posicion_hablar_3_1 = {'posicion_cabeza_horizontal': 2290, 'posicion_ojos_horizontal': 1190, 'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5510, 'posicion_dedo_anular_derecho': 5512, 'posicion_dedo_menique_derecho': 5514, 'posicion_muneca_derecho': 5001, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5002, 'posicion_hombro_sagital_derecho': 4850, 'posicion_hombro_frontal_derecho': 4418, 'posicion_hombro_rotacion_derecho': 6376, 'posicion_bicep_derecho': 4175, 'posicion_hombro_sagital_izquierdo': 6027, 'posicion_hombro_frontal_izquierdo': 4643, 'posicion_hombro_rotacion_izquierdo': 6579, 'posicion_bicep_izquierdo': 4375}
posicion_hablar_3_2 = {'posicion_cabeza_horizontal': 2270, 'posicion_ojos_horizontal': 1230, 'posicion_dedo_pulgar_derecho': 5518, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5510, 'posicion_dedo_anular_derecho': 5512, 'posicion_dedo_menique_derecho': 5514, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5003, 'posicion_hombro_sagital_derecho': 4865, 'posicion_hombro_frontal_derecho': 4418, 'posicion_hombro_rotacion_derecho': 6355, 'posicion_bicep_derecho': 4175, 'posicion_hombro_sagital_izquierdo': 6027, 'posicion_hombro_frontal_izquierdo': 4643, 'posicion_hombro_rotacion_izquierdo': 6579, 'posicion_bicep_izquierdo': 4350}
posicion_hablar_3_3 = {'posicion_cabeza_horizontal': 2290, 'posicion_ojos_horizontal': 1190, 'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5511, 'posicion_dedo_anular_derecho': 5513, 'posicion_dedo_menique_derecho': 5515, 'posicion_muneca_derecho': 5000, 'posicion_dedo_pulgar_izquierdo': 5521, 'posicion_dedo_indice_izquierdo': 5523, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5002, 'posicion_hombro_sagital_derecho': 4865, 'posicion_hombro_frontal_derecho': 4418, 'posicion_hombro_rotacion_derecho': 6350, 'posicion_bicep_derecho': 4175, 'posicion_hombro_sagital_izquierdo': 6027, 'posicion_hombro_frontal_izquierdo': 4643, 'posicion_hombro_rotacion_izquierdo': 6559, 'posicion_bicep_izquierdo': 4330}
posicion_hablar_3_4 = {'posicion_cabeza_horizontal': 2310, 'posicion_ojos_horizontal': 1160, 'posicion_dedo_pulgar_derecho': 5519, 'posicion_dedo_indice_derecho': 5517, 'posicion_dedo_medio_derecho': 5510, 'posicion_dedo_anular_derecho': 5512, 'posicion_dedo_menique_derecho': 5514, 'posicion_muneca_derecho': 5001, 'posicion_dedo_pulgar_izquierdo': 5520, 'posicion_dedo_indice_izquierdo': 5522, 'posicion_dedo_medio_izquierdo': 5525, 'posicion_dedo_anular_izquierdo': 5527, 'posicion_dedo_menique_izquierdo': 5529, 'posicion_muneca_izquierdo': 5002, 'posicion_hombro_sagital_derecho': 4850, 'posicion_hombro_frontal_derecho': 4418, 'posicion_hombro_rotacion_derecho': 6350, 'posicion_bicep_derecho': 4175, 'posicion_hombro_sagital_izquierdo': 6027, 'posicion_hombro_frontal_izquierdo': 4643, 'posicion_hombro_rotacion_izquierdo': 6559, 'posicion_bicep_izquierdo': 4375}


frameExportado= None
def visualizar():
    global cap
    global pintar, frameExportado
    global EjeY, EjeX
    global seguir_vision, punto_seguir, imitar_vision
    global palma_puntos, pulgar_puntos, punta_puntos, base_puntos
    global ultimo_dedo_derecha, estado_muneca_derecha, media_estado_muneca_derecha, mano_imitar_derecha
    global ultimo_dedo_izquierda, estado_muneca_izquierda, media_estado_muneca_izquierda, mano_imitar_izquierda
    global brazo_derecho, grupo_angulo_frontal_d, grupo_angulo_flexion_d, grupo_angulo_sagital_d, grupo_angulo_rotacion_d
    global brazo_izquierdo, grupo_angulo_frontal_i, grupo_angulo_flexion_i, grupo_angulo_sagital_i, grupo_angulo_rotacion_i
    global posiciones_grabadas
    # Lee un fotograma de la cámara
    if cap is not None:
        ret, frame = cap.read()
        if ret == True:
            frame = imutils.resize(frame, width=1200)
            frameExportado = frame
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

            if (imitar_vision == "Cara" or imitar_vision == "Todo") and result.face_landmarks is not None:
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

                                if posiciones_grabadas["posicion_cabeza_horizontal"] is None or posiciones_grabadas["posicion_cabeza_horizontal"] != 2505:
                                    posiciones_grabadas["posicion_cabeza_horizontal"] = 2505
                            elif zona_media == "Izquierda":
                                enviar_comando_esp32(2510)

                                if posiciones_grabadas["posicion_cabeza_horizontal"] is None or posiciones_grabadas["posicion_cabeza_horizontal"] != 2510:
                                    posiciones_grabadas["posicion_cabeza_horizontal"] = 2510
                            elif zona_media == "Centro":
                                enviar_comando_esp32(2515)

                                if posiciones_grabadas["posicion_cabeza_horizontal"] is None or posiciones_grabadas["posicion_cabeza_horizontal"] != 2515:
                                    posiciones_grabadas["posicion_cabeza_horizontal"] = 2515
                            elif zona_media == "Derecha":
                                enviar_comando_esp32(2520)

                                if posiciones_grabadas["posicion_cabeza_horizontal"] is None or posiciones_grabadas["posicion_cabeza_horizontal"] != 2520:
                                    posiciones_grabadas["posicion_cabeza_horizontal"] = 2520
                            elif zona_media == "Muy derecha":
                                enviar_comando_esp32(2525)
                                if posiciones_grabadas["posicion_cabeza_horizontal"] is None or posiciones_grabadas["posicion_cabeza_horizontal"] != 2525:
                                    posiciones_grabadas["posicion_cabeza_horizontal"] = 2525
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
            if imitar_vision in ["Mano"] or imitar_vision in ["Mano izquierda"] or imitar_vision in ["Mano derecha"] or imitar_vision in ["Todo"]:

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
                    elif imitar_vision in ["Mano"] or imitar_vision in ["Todo"]:
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
                            if posiciones_grabadas["posicion_dedo_pulgar_derecho"] is None or posiciones_grabadas["posicion_dedo_pulgar_derecho"] != 5519:
                                posiciones_grabadas["posicion_dedo_pulgar_derecho"] = 5519
                        elif dedosAbiertos[0] == False and ultimo_dedo_derecha[0] == "Pulgar":
                            ultimo_dedo_derecha[0] = None
                            print("Pulgar derecho cerrado")
                            enviar_comando_esp32(5518)
                            if posiciones_grabadas["posicion_dedo_pulgar_derecho"] is None or posiciones_grabadas["posicion_dedo_pulgar_derecho"] != 5518:
                                posiciones_grabadas["posicion_dedo_pulgar_derecho"] = 5518
                        if dedosAbiertos[1] and ultimo_dedo_derecha[1] is None: #ÍNDICE
                            ultimo_dedo_derecha[1] = "Indice"
                            print("Índice derecho abierto")
                            enviar_comando_esp32(5517)
                            if posiciones_grabadas["posicion_dedo_indice_derecho"] is None or posiciones_grabadas["posicion_dedo_indice_derecho"] != 5517:
                                posiciones_grabadas["posicion_dedo_indice_derecho"] = 5517
                        elif dedosAbiertos[1] == False and ultimo_dedo_derecha[1] == "Indice":
                            ultimo_dedo_derecha[1] = None
                            print("Índice derecho cerrado")
                            enviar_comando_esp32(5516)
                            if posiciones_grabadas["posicion_dedo_indice_derecho"] is None or posiciones_grabadas["posicion_dedo_indice_derecho"] != 5516:
                                posiciones_grabadas["posicion_dedo_indice_derecho"] = 5516
                        if dedosAbiertos[2] and ultimo_dedo_derecha[2] is None: #MEDIO
                            ultimo_dedo_derecha[2] = "Medio"
                            print("Medio derecho abierto")
                            enviar_comando_esp32(5511)
                            if posiciones_grabadas["posicion_dedo_medio_derecho"] is None or posiciones_grabadas["posicion_dedo_medio_derecho"] != 5511:
                                posiciones_grabadas["posicion_dedo_medio_derecho"] = 5511
                        elif dedosAbiertos[2] == False and ultimo_dedo_derecha[2] == "Medio":
                            ultimo_dedo_derecha[2] = None
                            print("Medio derecho cerrado")
                            enviar_comando_esp32(5510)
                            if posiciones_grabadas["posicion_dedo_medio_derecho"] is None or posiciones_grabadas["posicion_dedo_medio_derecho"] != 5510:
                                posiciones_grabadas["posicion_dedo_medio_derecho"] = 5510
                        if dedosAbiertos[3] and ultimo_dedo_derecha[3] is None: #ANULAR
                            ultimo_dedo_derecha[3] = "Anular"
                            print("Anular derecho abierto")
                            enviar_comando_esp32(5513)
                            if posiciones_grabadas["posicion_dedo_anular_derecho"] is None or posiciones_grabadas["posicion_dedo_anular_derecho"] != 5513:
                                posiciones_grabadas["posicion_dedo_anular_derecho"] = 5513
                        elif dedosAbiertos[3] == False and ultimo_dedo_derecha[3] == "Anular":
                            ultimo_dedo_derecha[3] = None
                            print("Anular derecho cerrado")
                            enviar_comando_esp32(5512)
                            if posiciones_grabadas["posicion_dedo_anular_derecho"] is None or posiciones_grabadas["posicion_dedo_anular_derecho"] != 5512:
                                posiciones_grabadas["posicion_dedo_anular_derecho"] = 5512
                        if dedosAbiertos[4] and ultimo_dedo_derecha[4] is None: #MEÑIQUE
                            ultimo_dedo_derecha[4] = "Pinky"
                            print("Meñique derecho abierto")
                            enviar_comando_esp32(5515)
                            if posiciones_grabadas["posicion_dedo_menique_derecho"] is None or posiciones_grabadas["posicion_dedo_menique_derecho"] != 5515:
                                posiciones_grabadas["posicion_dedo_menique_derecho"] = 5515
                        elif dedosAbiertos[4] == False and ultimo_dedo_derecha[4] == "Pinky":
                            ultimo_dedo_derecha[4] = None
                            print("Meñique derecho cerrado")
                            enviar_comando_esp32(5514)
                            if posiciones_grabadas["posicion_dedo_menique_derecho"] is None or posiciones_grabadas["posicion_dedo_menique_derecho"] != 5514:
                                posiciones_grabadas["posicion_dedo_menique_derecho"] = 5514

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
                                        if posiciones_grabadas["posicion_muneca_derecho"] is None or posiciones_grabadas["posicion_muneca_derecho"] != 5001:
                                            posiciones_grabadas["posicion_muneca_derecho"] = 5001
                                    elif estado_muneca_derecha_oficial == "dorso":
                                        enviar_comando_esp32(5000)
                                        if posiciones_grabadas["posicion_muneca_derecho"] is None or posiciones_grabadas["posicion_muneca_derecho"] != 5000:
                                            posiciones_grabadas["posicion_muneca_derecho"] = 5000
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

                            if posiciones_grabadas["posicion_dedo_pulgar_izquierdo"] is None or posiciones_grabadas["posicion_dedo_pulgar_izquierdo"] != 5521:
                                posiciones_grabadas["posicion_dedo_pulgar_izquierdo"] = 5521
                        elif dedosAbiertos[0] == False and ultimo_dedo_izquierda[0] == "Pulgar":
                            ultimo_dedo_izquierda[0] = None
                            print("Pulgar izquierdo cerrado")
                            enviar_comando_esp32(5520)
                            if posiciones_grabadas["posicion_dedo_pulgar_izquierdo"] is None or posiciones_grabadas["posicion_dedo_pulgar_izquierdo"] != 5520:
                                posiciones_grabadas["posicion_dedo_pulgar_izquierdo"] = 5520
                        if dedosAbiertos[1] and ultimo_dedo_izquierda[1] is None: #ÍNDICE
                            ultimo_dedo_izquierda[1] = "Indice"
                            print("Índice izquierdo abierto")
                            enviar_comando_esp32(5523)
                            if posiciones_grabadas["posicion_dedo_indice_izquierdo"] is None or posiciones_grabadas["posicion_dedo_indice_izquierdo"] != 5523:
                                posiciones_grabadas["posicion_dedo_indice_izquierdo"] = 5523
                        elif dedosAbiertos[1] == False and ultimo_dedo_izquierda[1] == "Indice":
                            ultimo_dedo_izquierda[1] = None
                            print("Índice izquierdo cerrado")
                            enviar_comando_esp32(5522)
                            if posiciones_grabadas["posicion_dedo_indice_izquierdo"] is None or posiciones_grabadas["posicion_dedo_indice_izquierdo"] != 5522:
                                posiciones_grabadas["posicion_dedo_indice_izquierdo"] = 5522
                        if dedosAbiertos[2] and ultimo_dedo_izquierda[2] is None: #MEDIO
                            ultimo_dedo_izquierda[2] = "Medio"
                            print("Medio izquierdo abierto")
                            enviar_comando_esp32(5525)
                            if posiciones_grabadas["posicion_dedo_medio_izquierdo"] is None or posiciones_grabadas["posicion_dedo_medio_izquierdo"] != 5525:
                                posiciones_grabadas["posicion_dedo_medio_izquierdo"] = 5525
                        elif dedosAbiertos[2] == False and ultimo_dedo_izquierda[2] == "Medio":
                            ultimo_dedo_izquierda[2] = None
                            print("Medio izquierdo cerrado")
                            enviar_comando_esp32(5524)
                            if posiciones_grabadas["posicion_dedo_medio_izquierdo"] is None or posiciones_grabadas["posicion_dedo_medio_izquierdo"] != 5524:
                                posiciones_grabadas["posicion_dedo_medio_izquierdo"] = 5524
                        if dedosAbiertos[3] and ultimo_dedo_izquierda[3] is None: #ANULAR
                            ultimo_dedo_izquierda[3] = "Anular"
                            print("Anular izquierdo abierto")
                            enviar_comando_esp32(5527)
                            if posiciones_grabadas["posicion_dedo_anular_izquierdo"] is None or posiciones_grabadas["posicion_dedo_anular_izquierdo"] != 5527:
                                posiciones_grabadas["posicion_dedo_anular_izquierdo"] = 5527
                        elif dedosAbiertos[3] == False and ultimo_dedo_izquierda[3] == "Anular":
                            ultimo_dedo_izquierda[3] = None
                            print("Anular izquierdo cerrado")
                            enviar_comando_esp32(5526)
                            if posiciones_grabadas["posicion_dedo_anular_izquierdo"] is None or posiciones_grabadas["posicion_dedo_anular_izquierdo"] != 5526:
                                posiciones_grabadas["posicion_dedo_anular_izquierdo"] = 5526
                        if dedosAbiertos[4] and ultimo_dedo_izquierda[4] is None: #MEÑIQUE
                            ultimo_dedo_izquierda[4] = "Pinky"
                            print("Meñique izquierdo abierto")
                            enviar_comando_esp32(5529)
                            if posiciones_grabadas["posicion_dedo_menique_izquierdo"] is None or posiciones_grabadas["posicion_dedo_menique_izquierdo"] != 5529:
                                posiciones_grabadas["posicion_dedo_menique_izquierdo"] = 5529
                        elif dedosAbiertos[4] == False and ultimo_dedo_izquierda[4] == "Pinky":
                            ultimo_dedo_izquierda[4] = None
                            print("Meñique izquierdo cerrado")
                            enviar_comando_esp32(5528)
                            if posiciones_grabadas["posicion_dedo_menique_izquierdo"] is None or posiciones_grabadas["posicion_dedo_menique_izquierdo"] != 5528:
                                posiciones_grabadas["posicion_dedo_menique_izquierdo"] = 5528

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
                                        if posiciones_grabadas["posicion_muneca_izquierdo"] is None or posiciones_grabadas["posicion_muneca_izquierdo"] != 5520:
                                            posiciones_grabadas["posicion_muneca_izquierdo"] = 5003
                                    elif estado_muneca_izquierda_oficial == "dorso":
                                        enviar_comando_esp32(5002)
                                        if posiciones_grabadas["posicion_muneca_izquierdo"] is None or posiciones_grabadas["posicion_muneca_izquierdo"] != 5522:
                                            posiciones_grabadas["posicion_muneca_izquierdo"] = 5002
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

                    #     #FLEXION DEL BRAZO DERECHO
                    # # Defino los vectores necesarios para FLEXIÓN
                    # v_antebrazo_d = normalizar_vector(punto_muneca_d - punto_codo_d)
                    # v_brazo_d = normalizar_vector(punto_codo_d - punto_hombro_d)
                    #     # Calculo el angulo de flexion 0 = extendido, 180 = flexionado
                    # angulo_flexion_d = calcular_angulo_flexion(v_brazo_d, v_antebrazo_d)
                    # if angulo_flexion_d is not None and len(grupo_angulo_flexion_d) <= 8:
                    #     grupo_angulo_flexion_d.append(angulo_flexion_d)
                    # if len(grupo_angulo_flexion_d) > 8:
                    #     media_angulo_flexion_d = sum(grupo_angulo_flexion_d) / len(grupo_angulo_flexion_d)
                    #     grupo_angulo_flexion_d = []
                    #     if media_angulo_flexion_d < 20:
                    #     # Verificar alineación real
                    #         producto_punto = np.dot(v_brazo_d, v_antebrazo_d)
                    #         if producto_punto < 0.95:  # No están bien alineados (cos(18°) ≈ 0.95)
                    #             # Recalcular el ángulo tomando el valor absoluto del producto punto
                    #             media_angulo_flexion_d = np.degrees(np.arccos(np.abs(producto_punto)))
                    #     # Segun el angulo defino la posicion
                    #     brazo_derecho[0], brazo_derecho[1] = definir_flexion(media_angulo_flexion_d, "derecho")
                    #     if brazo_derecho[1] is not None:
                    #         # Convertir a entero si es necesario
                    #         valor_bicep_derecho = int(float(brazo_derecho[1]))
                    #         # Comprobar si ya existe el atributo
                    #         if not hasattr(visualizar, "ultimo_biceps_derecho_enviado"):
                    #             visualizar.ultimo_biceps_derecho_enviado = valor_bicep_derecho
                    #             enviar_comando_esp32(valor_bicep_derecho)
                    #             if posiciones_grabadas.posicion_bicep_derecho is None and posiciones_grabadas.posicion_bicep_derecho != valor_bicep_derecho:
                    #                 posiciones_grabadas.posicion_bicep_derecho = valor_bicep_derecho
                    #                 # print("Bíceps derecho:", valor_bicep_derecho)
                    #         else:
                    #             if abs(valor_bicep_derecho - visualizar.ultimo_biceps_derecho_enviado) >= 10:
                    #                 enviar_comando_esp32(valor_bicep_derecho)
                    #                 if posiciones_grabadas.posicion_bicep_derecho is None and posiciones_grabadas.posicion_bicep_derecho != valor_bicep_derecho:
                    #                     posiciones_grabadas.posicion_bicep_derecho = valor_bicep_derecho
                    #                 # print("Bíceps derecho:", valor_bicep_derecho)
                    #                 visualizar.ultimo_biceps_derecho_enviado = valor_bicep_derecho

                    #     # enviar_comando_esp32(brazo_derecho[1])

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
                    #     if media_angulo_flexion_i < 20:
                    #     # Verificar alineación real
                    #         producto_punto = np.dot(v_brazo_i, v_antebrazo_i)
                    #         if producto_punto < 0.95:  # No están bien alineados (cos(18°) ≈ 0.95)
                    #             # Recalcular el ángulo tomando el valor absoluto del producto punto
                    #             media_angulo_flexion_i = np.degrees(np.arccos(np.abs(producto_punto)))
                    #     # Segun el angulo defino la posicion
                    #     brazo_izquierdo[0], brazo_izquierdo[1] = definir_flexion(media_angulo_flexion_i, "izquierdo")
                    #     # brazo_izquierdo[0], brazo_izquierdo[1] = "flexion", round(media_angulo_flexion_i)
                    #     if brazo_izquierdo[1] is not None:
                    #         # Convertir a entero si es necesario
                    #         valor_bicep_izquierdo = int(float(brazo_izquierdo[1]))
                    #         # Comprobar si ya existe el atributo
                    #         if not hasattr(visualizar, "ultimo_biceps_izquierdo_enviado"):
                    #             visualizar.ultimo_biceps_izquierdo_enviado = valor_bicep_izquierdo
                    #             enviar_comando_esp32(valor_bicep_izquierdo)
                    #             if posiciones_grabadas.posicion_bicep_izquierdo is None and posiciones_grabadas.posicion_bicep_izquierdo != valor_bicep_izquierdo:
                    #                 posiciones_grabadas.posicion_bicep_izquierdo = valor_bicep_izquierdo
                    #             # print("Bíceps izquierdo:", valor_bicep_izquierdo)
                    #         else:
                    #             if abs(valor_bicep_izquierdo - visualizar.ultimo_biceps_izquierdo_enviado) >= 10:
                    #                 enviar_comando_esp32(valor_bicep_izquierdo)
                    #                 if posiciones_grabadas.posicion_bicep_izquierdo is None and posiciones_grabadas.posicion_bicep_izquierdo != valor_bicep_izquierdo:
                    #                     posiciones_grabadas.posicion_bicep_izquierdo = valor_bicep_izquierdo
                    #                 # print("Bíceps izquierdo:", valor_bicep_izquierdo)
                    #                 visualizar.ultimo_biceps_izquierdo_enviado = valor_bicep_izquierdo



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

            if (imitar_vision == "Cuerpo" or imitar_vision == "Todo") and result.pose_world_landmarks is not None:
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
                    filtro = abs(grupo_angulo_flexion_d[0] - grupo_angulo_flexion_d[-1])
                    if filtro < 10: 
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
                        if posiciones_grabadas["posicion_bicep_derecho"] is None or posiciones_grabadas["posicion_bicep_derecho"] != brazo_derecho[1]:
                            posiciones_grabadas["posicion_bicep_derecho"] = brazo_derecho[1]
                        # brazo_derecho[0], brazo_derecho[1] = "flexion", round(media_angulo_flexion_d)
                    else:
                        grupo_angulo_flexion_d = []

                #PLANO SAGITAL DE HOMBRO DERECHO
                    # Calculo de proyecciones escalares en el plano SAGITAL
                componente_vertical_d_s = np.dot(v_brazo_d, v_vertical_abajo_d)
                componente_sagital_d_s = np.dot(v_brazo_d, v_sagital_delante_d)
                    # Calculo el angulo del plano SAGITAL
                angulo_sagital_d = calcular_angulo_brazos(componente_sagital_d_s, componente_vertical_d_s)
                if angulo_sagital_d is not None and len(grupo_angulo_sagital_d) <= 8:
                    grupo_angulo_sagital_d.append(angulo_sagital_d)
                if len(grupo_angulo_sagital_d) > 8:
                    filtro = abs(grupo_angulo_sagital_d[0] - grupo_angulo_sagital_d[-1])
                    if filtro < 10:
                        media_angulo_sagital_d = sum(grupo_angulo_sagital_d) / len(grupo_angulo_sagital_d)
                            # Segun el angulo defino la posicion
                        brazo_derecho[2] = "sagital"
                        brazo_derecho[3] = definir_angulo_hombro_sagital("derecho", media_angulo_sagital_d)
                        grupo_angulo_sagital_d = []
                        if posiciones_grabadas["posicion_hombro_sagital_derecho"] is None or posiciones_grabadas["posicion_hombro_sagital_derecho"] != brazo_derecho[3]:
                            posiciones_grabadas["posicion_hombro_sagital_derecho"] = brazo_derecho[3]
                    else:
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
                    filtro = abs(grupo_angulo_frontal_d[0] - grupo_angulo_frontal_d[-1])
                    if filtro < 10:
                        media_angulo_frontal_d = sum(grupo_angulo_frontal_d) / len(grupo_angulo_frontal_d)
                            # Segun el angulo defino la posicion
                        brazo_derecho[4] = "frontal"
                        brazo_derecho[5] = definir_angulo_hombro_frontal("derecho", media_angulo_frontal_d)
                        grupo_angulo_frontal_d = []
                        if posiciones_grabadas["posicion_hombro_frontal_derecho"] is None or posiciones_grabadas["posicion_hombro_frontal_derecho"] != brazo_derecho[5]:
                            posiciones_grabadas["posicion_hombro_frontal_derecho"] = brazo_derecho[5]
                    else:
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
                        filtro = abs(grupo_angulo_rotacion_d[0] - grupo_angulo_rotacion_d[-1])
                        if filtro < 15:
                            media_angulo_rotacion_d = sum(grupo_angulo_rotacion_d) / len(grupo_angulo_rotacion_d)
                            # brazo_derecho[6] = definir_rotacion(media_angulo_rotacion_d, "derecho")
                            brazo_derecho[6] = "rotacion"
                            brazo_derecho[7] = definir_angulo_hombro_rotacion("derecho", media_angulo_rotacion_d)
                            grupo_angulo_rotacion_d = []
                            if posiciones_grabadas["posicion_hombro_rotacion_derecho"] is None or posiciones_grabadas["posicion_hombro_rotacion_derecho"] != brazo_derecho[7]:
                                posiciones_grabadas["posicion_hombro_rotacion_derecho"] = brazo_derecho[7]
                        else:
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
                    filtro = abs(grupo_angulo_flexion_i[0] - grupo_angulo_flexion_i[-1])
                    if filtro < 10:
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
                        if posiciones_grabadas["posicion_bicep_izquierdo"] is None or posiciones_grabadas["posicion_bicep_izquierdo"] != brazo_izquierdo[1]:
                            posiciones_grabadas["posicion_bicep_izquierdo"] = brazo_izquierdo[1]
                    else:
                        grupo_angulo_flexion_i = []

                #PLANO SAGITAL DE HOMBRO IZQUIERDO
                    # Calculo de proyecciones escalares en el plano SAGITAL
                componente_vertical_i_s = np.dot(v_brazo_i, v_vertical_abajo_i)
                componente_sagital_i_s = np.dot(v_brazo_i, v_sagital_delante_i)
                    # Calculo el angulo del plano SAGITAL
                angulo_sagital_i = calcular_angulo_brazos(componente_sagital_i_s, componente_vertical_i_s)
                if angulo_sagital_i is not None and len(grupo_angulo_sagital_i) <= 8:
                    grupo_angulo_sagital_i.append(angulo_sagital_i)
                if len(grupo_angulo_sagital_i) > 8:
                    filtro = abs(grupo_angulo_sagital_i[0] - grupo_angulo_sagital_i[-1])
                    if filtro < 10:
                        media_angulo_sagital_i = sum(grupo_angulo_sagital_i) / len(grupo_angulo_sagital_i)
                            # Segun el angulo defino la posicion
                        brazo_izquierdo[2] = "sagital"
                        brazo_izquierdo[3] = definir_angulo_hombro_sagital("izquierdo", media_angulo_sagital_i)
                        # brazo_izquierdo[3] = round(media_angulo_sagital_i)
                        grupo_angulo_sagital_i = []
                        if posiciones_grabadas["posicion_hombro_sagital_izquierdo"] is None or posiciones_grabadas["posicion_hombro_sagital_izquierdo"] != brazo_izquierdo[3]:
                            posiciones_grabadas["posicion_hombro_sagital_izquierdo"] = brazo_izquierdo[3]
                    else:
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
                    filtro = abs(grupo_angulo_frontal_i[0] - grupo_angulo_frontal_i[-1])
                    if filtro < 10:
                        media_angulo_frontal_i = sum(grupo_angulo_frontal_i) / len(grupo_angulo_frontal_i)
                        # Segun el angulo defino la posicion
                        brazo_izquierdo[4] = "frontal"
                        # brazo_izquierdo[5] = round(media_angulo_frontal_i)
                        # O si tienes función de definición:
                        brazo_izquierdo[5] = definir_angulo_hombro_frontal("izquierdo", media_angulo_frontal_i)
                        grupo_angulo_frontal_i = []
                        if posiciones_grabadas["posicion_hombro_frontal_izquierdo"] is None or posiciones_grabadas["posicion_hombro_frontal_izquierdo"] != brazo_izquierdo[5]:
                            posiciones_grabadas["posicion_hombro_frontal_izquierdo"] = brazo_izquierdo[5]
                    else:
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
                        filtro = abs(grupo_angulo_rotacion_i[0] - grupo_angulo_rotacion_i[-1])
                        if filtro < 15:
                            media_angulo_rotacion_i = sum(grupo_angulo_rotacion_i) / len(grupo_angulo_rotacion_i)
                            brazo_izquierdo[6] = "rotacion"
                            brazo_izquierdo[7] = definir_angulo_hombro_rotacion("izquierdo", media_angulo_rotacion_i)
                            # brazo_izquierdo[7] = round(media_angulo_rotacion_i)
                            grupo_angulo_rotacion_i = []
                            if posiciones_grabadas["posicion_hombro_rotacion_izquierdo"] is None or posiciones_grabadas["posicion_hombro_rotacion_izquierdo"] != brazo_izquierdo[7]:
                                posiciones_grabadas["posicion_hombro_rotacion_izquierdo"] = brazo_izquierdo[7]
                        else:
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
                # if brazo_derecho[1] is not None and brazo_derecho[3] is not None and brazo_derecho[5] is not None and brazo_derecho[7] is not None:
                #     # print("Brazo Derecho: ", brazo_derecho)
                #     print("Brazo Derecho: ", brazo_derecho)
                #     ## enviar solamente cuando haya cambios significativos

                #     enviar_comando_esp32(brazo_derecho[1])
                #     enviar_comando_esp32(brazo_derecho[3])
                #     enviar_comando_esp32(brazo_derecho[5])
                #     enviar_comando_esp32(brazo_derecho[7])


                # # ENVIAR RESULTADOS AL ESP32 DEL BRAZO IZQUIERDO
                # if brazo_izquierdo[1] is not None and brazo_izquierdo[3] is not None and brazo_izquierdo[5] is not None and brazo_izquierdo[7] is not None:
                #     print("Brazo Izquierdo: ", brazo_izquierdo)
                #     # print("Brazo Izquierdo: ", brazo_izquierdo)
                #     enviar_comando_esp32(brazo_izquierdo[1])
                #     enviar_comando_esp32(brazo_izquierdo[3])
                #     enviar_comando_esp32(brazo_izquierdo[5])
                #     enviar_comando_esp32(brazo_izquierdo[7])


                if brazo_derecho[1] is not None and brazo_derecho[3] is not None and brazo_derecho[5] is not None and brazo_derecho[7] is not None:
                    print("Brazo Derecho: ", brazo_derecho)

                    valores_d = [brazo_derecho[1], brazo_derecho[3], brazo_derecho[5], brazo_derecho[7]]
                    claves_d = [brazo_derecho[0], brazo_derecho[2], brazo_derecho[4], brazo_derecho[6]]

                    for clave, val in zip(claves_d, valores_d):
                        numero = _to_int_safe(val)
                        if numero is None:
                            continue
                        attr = f"ultimo_brazo_derecho_{clave}_enviado"
                        ultimo = getattr(visualizar, attr, None)
                        if ultimo is None:
                            # primer envío
                            setattr(visualizar, attr, numero)
                            enviar_comando_esp32(numero)
                            print(f"Brazo derecho ({clave}) enviado inicial:", numero)
                        else:
                            if abs(numero - ultimo) >= 10:
                                enviar_comando_esp32(numero)
                                setattr(visualizar, attr, numero)
                                print(f"Brazo derecho ({clave}) cambiado -> enviado:", numero)

                # ENVIAR RESULTADOS AL ESP32 DEL BRAZO IZQUIERDO (con mismo filtro)
                if brazo_izquierdo[1] is not None and brazo_izquierdo[3] is not None and brazo_izquierdo[5] is not None and brazo_izquierdo[7] is not None:
                    print("Brazo Izquierdo: ", brazo_izquierdo)

                    valores_i = [brazo_izquierdo[1], brazo_izquierdo[3], brazo_izquierdo[5], brazo_izquierdo[7]]
                    claves_i = [brazo_izquierdo[0], brazo_izquierdo[2], brazo_izquierdo[4], brazo_izquierdo[6]]

                    for clave, val in zip(claves_i, valores_i):
                        numero = _to_int_safe(val)
                        if numero is None:
                            continue
                        attr = f"ultimo_brazo_izquierdo_{clave}_enviado"
                        ultimo = getattr(visualizar, attr, None)
                        if ultimo is None:
                            setattr(visualizar, attr, numero)
                            enviar_comando_esp32(numero)
                            print(f"Brazo izquierdo ({clave}) enviado inicial:", numero)
                        else:
                            if abs(numero - ultimo) >= 10:
                                enviar_comando_esp32(numero)
                                setattr(visualizar, attr, numero)
                                print(f"Brazo izquierdo ({clave}) cambiado -> enviado:", numero)
                #



            #     ###### De nuevo la mano COMENTAR EN CASO 

            #     if result.left_hand_landmarks is not None and result.right_hand_landmarks is not None:
            #         mano_imitar_derecha = [result.right_hand_landmarks.landmark[i] for i in range(21)]
            #         mano_imitar_izquierda = [result.left_hand_landmarks.landmark[i] for i in range(21)]
            #     elif result.left_hand_landmarks is not None:
            #         mano_imitar_izquierda = [result.left_hand_landmarks.landmark[i] for i in range(21)]
            #         mano_imitar_derecha = None
            #     elif result.right_hand_landmarks is not None:
            #         mano_imitar_derecha = [result.right_hand_landmarks.landmark[i] for i in range(21)]
            #         mano_imitar_izquierda = None
            #     else:
            #         mano_imitar_derecha = None
            #         mano_imitar_izquierda = None

            #     if mano_imitar_derecha is not None:
            #         palma_coordenadas = []
            #         pulgar_coordenadas = []
            #         punta_coordenadas = []
            #         base_coordenadas = []

            #         for i in pulgar_puntos:
            #             x = int(mano_imitar_derecha[i].x * width)
            #             y = int(mano_imitar_derecha[i].y * height)
            #             pulgar_coordenadas.append([x, y])

            #         for i in punta_puntos:
            #             x = int(mano_imitar_derecha[i].x * width)
            #             y = int(mano_imitar_derecha[i].y * height)
            #             punta_coordenadas.append([x, y])

            #         for i in base_puntos:
            #             x = int(mano_imitar_derecha[i].x * width)
            #             y = int(mano_imitar_derecha[i].y * height)
            #             base_coordenadas.append([x, y])
                    
            #         for i in palma_puntos:
            #             x = int(mano_imitar_derecha[i].x * width)
            #             y = int(mano_imitar_derecha[i].y * height)
            #             palma_coordenadas.append([x, y])
                    
            #         # Calcular pulgar
            #         p1 = np.array(pulgar_coordenadas[0])
            #         p2 = np.array(pulgar_coordenadas[1])
            #         p3 = np.array(pulgar_coordenadas[2])
            #         l1 = np.linalg.norm(p2-p3)
            #         l2 = np.linalg.norm(p1-p3)
            #         l3 = np.linalg.norm(p1-p2)

            #         centro_palma = palma_centroCoordenadas(palma_coordenadas)
            #         cv2.circle(frame, centro_palma, 5, (0, 255, 0), -1)

            #         try:
            #             cos_value = (l1**2 + l3**2 - l2**2) / (2 * l1 * l3)
            #             cos_value = max(-1, min(1, cos_value))  # Ensure value is within [-1, 1]
            #             angulo = math.degrees(math.acos(cos_value))
            #         except ValueError as e:
            #             print(f"Error calculando el angulo: {e}")
            #             angulo = 0  # Default value in case of error
                        
            #         dedo_pulgar = np.array(False)
            #         if angulo > 150: 
            #             dedo_pulgar = np.array(True)
            #             # print("pulgar abierto")

            #         # Calcular dedos
            #         xn, yn = palma_centroCoordenadas(palma_coordenadas)
            #         centro_coordenadas = np.array([xn, yn])
            #         punta_coordenadas = np.array(punta_coordenadas)
            #         base_coordenadas = np.array(base_coordenadas)

            #         dis_centro_punta = np.linalg.norm(centro_coordenadas - punta_coordenadas, axis=1)
            #         dis_centro_base = np.linalg.norm(centro_coordenadas - base_coordenadas, axis=1)
            #         diferencia = dis_centro_base - dis_centro_punta 
            #         dedosAbiertos = diferencia < 0
            #         dedosAbiertos = np.append(dedo_pulgar, dedosAbiertos)
            #         print("Dedos abiertos derecha: ", dedosAbiertos)

            #         #Enviar al ESP32 los dedos abiertos y cerrados 
            #         if dedosAbiertos[0] and ultimo_dedo_derecha[0] is None:  #PULGAR
            #             ultimo_dedo_derecha[0] = "Pulgar"
            #             print("Pulgar derecho abierto")
            #             enviar_comando_esp32(5519)
            #         elif dedosAbiertos[0] == False and ultimo_dedo_derecha[0] == "Pulgar":
            #             ultimo_dedo_derecha[0] = None
            #             print("Pulgar derecho cerrado")
            #             enviar_comando_esp32(5518)
            #         if dedosAbiertos[1] and ultimo_dedo_derecha[1] is None: #ÍNDICE
            #             ultimo_dedo_derecha[1] = "Indice"
            #             print("Índice derecho abierto")
            #             enviar_comando_esp32(5517)
            #         elif dedosAbiertos[1] == False and ultimo_dedo_derecha[1] == "Indice":
            #             ultimo_dedo_derecha[1] = None
            #             print("Índice derecho cerrado")
            #             enviar_comando_esp32(5516)
            #         if dedosAbiertos[2] and ultimo_dedo_derecha[2] is None: #MEDIO
            #             ultimo_dedo_derecha[2] = "Medio"
            #             print("Medio derecho abierto")
            #             enviar_comando_esp32(5511)
            #         elif dedosAbiertos[2] == False and ultimo_dedo_derecha[2] == "Medio":
            #             ultimo_dedo_derecha[2] = None
            #             print("Medio derecho cerrado")
            #             enviar_comando_esp32(5510)
            #         if dedosAbiertos[3] and ultimo_dedo_derecha[3] is None: #ANULAR
            #             ultimo_dedo_derecha[3] = "Anular"
            #             print("Anular derecho abierto")
            #             enviar_comando_esp32(5513)
            #         elif dedosAbiertos[3] == False and ultimo_dedo_derecha[3] == "Anular":
            #             ultimo_dedo_derecha[3] = None
            #             print("Anular derecho cerrado")
            #             enviar_comando_esp32(5512)
            #         if dedosAbiertos[4] and ultimo_dedo_derecha[4] is None: #MEÑIQUE
            #             ultimo_dedo_derecha[4] = "Pinky"
            #             print("Meñique derecho abierto")
            #             enviar_comando_esp32(5515)
            #         elif dedosAbiertos[4] == False and ultimo_dedo_derecha[4] == "Pinky":
            #             ultimo_dedo_derecha[4] = None
            #             print("Meñique derecho cerrado")
            #             enviar_comando_esp32(5514)

            #     if mano_imitar_izquierda is not None:
            #         palma_coordenadas = []
            #         pulgar_coordenadas = []
            #         punta_coordenadas = []
            #         base_coordenadas = []

            #         for i in pulgar_puntos:
            #             x = int(mano_imitar_izquierda[i].x * width)
            #             y = int(mano_imitar_izquierda[i].y * height)
            #             pulgar_coordenadas.append([x, y])

            #         for i in punta_puntos:
            #             x = int(mano_imitar_izquierda[i].x * width)
            #             y = int(mano_imitar_izquierda[i].y * height)
            #             punta_coordenadas.append([x, y])

            #         for i in base_puntos:
            #             x = int(mano_imitar_izquierda[i].x * width)
            #             y = int(mano_imitar_izquierda[i].y * height)
            #             base_coordenadas.append([x, y])
                    
            #         for i in palma_puntos:
            #             x = int(mano_imitar_izquierda[i].x * width)
            #             y = int(mano_imitar_izquierda[i].y * height)
            #             palma_coordenadas.append([x, y])
                    
            #         # Calcular pulgar
            #         p1 = np.array(pulgar_coordenadas[0])
            #         p2 = np.array(pulgar_coordenadas[1])
            #         p3 = np.array(pulgar_coordenadas[2])
            #         l1 = np.linalg.norm(p2-p3)
            #         l2 = np.linalg.norm(p1-p3)
            #         l3 = np.linalg.norm(p1-p2)

            #         centro_palma = palma_centroCoordenadas(palma_coordenadas)
            #         cv2.circle(frame, centro_palma, 5, (0, 255, 0), -1)

            #         try:
            #             cos_value = (l1**2 + l3**2 - l2**2) / (2 * l1 * l3)
            #             cos_value = max(-1, min(1, cos_value))  # Ensure value is within [-1, 1]
            #             angulo = math.degrees(math.acos(cos_value))
            #         except ValueError as e:
            #             print(f"Error calculando el angulo: {e}")
            #             angulo = 0  # Default value in case of error
                        
            #         dedo_pulgar = np.array(False)
            #         if angulo > 150: 
            #             dedo_pulgar = np.array(True)
            #             # print("pulgar abierto")

            #         # Calcular dedos
            #         xn, yn = palma_centroCoordenadas(palma_coordenadas)
            #         centro_coordenadas = np.array([xn, yn])
            #         punta_coordenadas = np.array(punta_coordenadas)
            #         base_coordenadas = np.array(base_coordenadas)

            #         dis_centro_punta = np.linalg.norm(centro_coordenadas - punta_coordenadas, axis=1)
            #         dis_centro_base = np.linalg.norm(centro_coordenadas - base_coordenadas, axis=1)
            #         diferencia = dis_centro_base - dis_centro_punta 
            #         dedosAbiertos = diferencia < 0
            #         dedosAbiertos = np.append(dedo_pulgar, dedosAbiertos)
            #         print("Dedos abiertos izquierda: ", dedosAbiertos)

            #         #Enviar al ESP32 los dedos abiertos y cerrados 
            #         if dedosAbiertos[0] and ultimo_dedo_izquierda[0] is None:  #PULGAR
            #             ultimo_dedo_izquierda[0] = "Pulgar"
            #             print("Pulgar izquierdo abierto")
            #             enviar_comando_esp32(5521)
            #         elif dedosAbiertos[0] == False and ultimo_dedo_izquierda[0] == "Pulgar":
            #             ultimo_dedo_izquierda[0] = None
            #             print("Pulgar izquierdo cerrado")
            #             enviar_comando_esp32(5520)
            #         if dedosAbiertos[1] and ultimo_dedo_izquierda[1] is None: #ÍNDICE
            #             ultimo_dedo_izquierda[1] = "Indice"
            #             print("Índice izquierdo abierto")
            #             enviar_comando_esp32(5523)
            #         elif dedosAbiertos[1] == False and ultimo_dedo_izquierda[1] == "Indice":
            #             ultimo_dedo_izquierda[1] = None
            #             print("Índice izquierdo cerrado")
            #             enviar_comando_esp32(5522)
            #         if dedosAbiertos[2] and ultimo_dedo_izquierda[2] is None: #MEDIO
            #             ultimo_dedo_izquierda[2] = "Medio"
            #             print("Medio izquierdo abierto")
            #             enviar_comando_esp32(5525)
            #         elif dedosAbiertos[2] == False and ultimo_dedo_izquierda[2] == "Medio":
            #             ultimo_dedo_izquierda[2] = None
            #             print("Medio izquierdo cerrado")
            #             enviar_comando_esp32(5524)
            #         if dedosAbiertos[3] and ultimo_dedo_izquierda[3] is None: #ANULAR
            #             ultimo_dedo_izquierda[3] = "Anular"
            #             print("Anular izquierdo abierto")
            #             enviar_comando_esp32(5527)
            #         elif dedosAbiertos[3] == False and ultimo_dedo_izquierda[3] == "Anular":
            #             ultimo_dedo_izquierda[3] = None
            #             print("Anular izquierdo cerrado")
            #             enviar_comando_esp32(5526)
            #         if dedosAbiertos[4] and ultimo_dedo_izquierda[4] is None: #MEÑIQUE
            #             ultimo_dedo_izquierda[4] = "Pinky"
            #             print("Meñique izquierdo abierto")
            #             enviar_comando_esp32(5529)
            #         elif dedosAbiertos[4] == False and ultimo_dedo_izquierda[4] == "Pinky":
            #             ultimo_dedo_izquierda[4] = None
            #             print("Meñique izquierdo cerrado")
            #             enviar_comando_esp32(5528)

            # ###############################

            # print("Posiciones grabadas:", posiciones_grabadas)    

            if pintar:
                drawing.draw_landmarks(
                frame,
                result.pose_landmarks,
                mediaPipe.POSE_CONNECTIONS,
                landmark_drawing_spec=drawing_styles.get_default_pose_landmarks_style())
                drawing.draw_landmarks(
                frame,
                result.left_hand_landmarks,
                mediaPipe.HAND_CONNECTIONS,
                landmark_drawing_spec=drawing_styles.get_default_hand_landmarks_style())
                drawing.draw_landmarks(
                frame,
                result.right_hand_landmarks,
                mediaPipe.HAND_CONNECTIONS,
                landmark_drawing_spec=drawing_styles.get_default_hand_landmarks_style())
                # Reducir el tamaño de los puntos y conexiones de la cara
                face_landmark_style = drawing_styles.get_default_face_mesh_tesselation_style()
                face_landmark_style.circle_radius = 1
                face_landmark_style.thickness = 1
                drawing.draw_landmarks(
                frame,
                result.face_landmarks,
                mediaPipe.FACEMESH_TESSELATION,
                landmark_drawing_spec=face_landmark_style)
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
def editar_nota_veredicto(comandos_obtenidos):
    """Edita la nota del veredicto según el comando"""
    if "veinte" in comandos_obtenidos:
        nota_veredicto = 20
    elif "diecinueve" in comandos_obtenidos:
        nota_veredicto = 19
    elif "dieciocho" in comandos_obtenidos:
        nota_veredicto = 18
    elif "diecisiete" in comandos_obtenidos:
        nota_veredicto = 17
    elif "dieciseis" in comandos_obtenidos:
        nota_veredicto = 16
    elif "quince" in comandos_obtenidos:
        nota_veredicto = 15
    else:
        nota_veredicto = None
    return nota_veredicto

def ejecutar_comando_hora():
    """Comando para decir la hora actual"""
    ahora = datetime.now()
    hora = ahora.strftime("%I")
    minutos = ahora.strftime("%M")
    am_pm = ahora.strftime("%p").lower()
    texto_hora = f"Tengo información de que son las {hora}:{minutos} {am_pm}"
    ejecutar_voz(texto_hora)

def ejecutar_comando_seguir(comandos_obtenidos):
    """Activa el seguimiento de visión"""
    global seguir_vision, imitar_vision
    imitar_vision = None
    
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
        seguir_vision = "Cara"
    
    mensaje = respuestas_comando("seguir") + ("la " + seguir_vision.lower() if seguir_vision != "Cuerpo" 
                                               else " el " + seguir_vision.lower())
    ejecutar_voz(mensaje)

def ejecutar_comando_imitar(comandos_obtenidos):
    """Activa la imitación de visión"""
    global seguir_vision, imitar_vision
    seguir_vision = None
    
    if "mano" in comandos_obtenidos and "izquierda" in comandos_obtenidos:
        imitar_vision = "Mano izquierda"
    elif "mano" in comandos_obtenidos and "derecha" in comandos_obtenidos:
        imitar_vision = "Mano derecha"
    elif "mano" in comandos_obtenidos:
        imitar_vision = "Mano"
    elif "cara" in comandos_obtenidos:
        imitar_vision = "Cara"
    elif "cuerpo" in comandos_obtenidos:
        imitar_vision = "Cuerpo"
    else:
        imitar_vision = "Todo"
    
    ejecutar_voz(respuestas_comando("imitar"))

def ejecutar_comando_desactivar(comandos_obtenidos):
    """Desactiva funciones según el comando"""
    global seguir_vision, imitar_vision, dev_mode, estado_posicion
    
    if "seguir" in comandos_obtenidos:
        seguir_vision = None
        ejecutar_voz(respuestas_comando("dejando de seguir"))
        estado_posicion = "action_1"
    elif "imitar" in comandos_obtenidos:
        imitar_vision = None
        ejecutar_voz(respuestas_comando("dejando de imitar"))
        estado_posicion = "action_1"
    elif "modo" in comandos_obtenidos and "desarrollador" in comandos_obtenidos:
        dev_mode = False
        ejecutar_voz(respuestas_comando("modo desarrollador desactivado"))

def ejecutar_comandos_lectura(comandos_obtenidos):
    """Maneja los comandos del modo lectura (presentación)"""
    global bienvenida_lectura, presentacion_javier, presentacion_rosimar
    global demostracion, demostracion_fase
    global sigue_javier_lectura, sigue_rosimar_lectura
    global rondas_PyR_Cristian_lectura, rondas_PyR_Javier_lectura, rondas_PyR_Rosimar_lectura
    global desalojo_de_la_sala_lectura
    
    # Mapeo de comandos de lectura
    estados_lectura = [
        ("bienvenida", not bienvenida_lectura, 
         lambda: setattr_and_speak('bienvenida_lectura', True, 
         'Buenos dí­as a todos los presentes. Hoy, 5 de noviembre de 2025, nos reunimos para presenciar un momento trascendental en la vida académica de tres jóvenes investigadores que han llegado a la etapa final de su formación como bachilleres. Es un honor para mí­ dar la bienvenida a esta ceremonia de presentación y defensa de trabajo de grado, donde tendremos el privilegio de conocer los resultados de la investigación desarrollada por: Cristian José Rangel Briceño, titular de la cédula de identidad treinta y un millones, ochocientos noventa y ocho mil, setenta y cinco, que presenta el Trabajo de Grado Titulado "DESARROLLO DE ROBOT HUMANOIDE DESDE LA PERSPECTIVA DE LA INNOVACIÓN SOCIAL (TORSO)"; Javier José Olivar Valero, titular de la cédula de identidad treinta millones, setecientos treinta y siete mil, seiscientos cuarenta y ocho, que presenta el Trabajo de Grado Titulado "DESARROLLO DE LA CABEZA DE UN ROBOT HUMANOIDE DESDE LA PERSPECTIVA DE LA INNOVACIÓN SOCIAL"; y Rosimar Lloselín Barrios Maldonado, titular de la cédula de identidad treinta millones, novecientos setenta y seis mil, doscientos diecisiete, que presenta el Trabajo de Grado Titulado "DESARROLLO DE UN ROBOT HUMANOIDE DESDE LA PERSPECTIVA DE LA INNOVACIÓN SOCIAL (BRAZO)". Extendemos un cordial saludo y agradecimiento a los distinguidos miembros del jurado evaluador que nos acompañan: Profesor Héctor Antúnez, Profesora Cristina Vieraz, y Profesor Edgar Omaña. De manera especial, expresamos nuestro reconocimiento al Profesor Edgardo Paolini, tutor de esta investigación. El protocolo del acto será el siguiente: Los bachilleres dispondrán de 25 minutos para la presentación de su trabajo de investigación. Finalizada la exposición, se procederá con el ciclo de preguntas y respuestas, donde el jurado evaluador podrá realizar las interrogantes que considere pertinentes. Posteriormente, se dará el espacio al jurado para la deliberación y finalmente se dará lectura al veredicto. Sin más preámbulos apaguemos los telefonos, invitamos a los bachilleres a dar inicio a su presentación, comenzando con la defensa del Bachiller Cristian José Rangel Briceño. Muchos éxitos para todos.')),
        
        ("presentar_javier_tesista", bienvenida_lectura and not presentacion_javier,
         lambda: setattr_and_speak('presentacion_javier', True,
         'A continuación procedera la defensa del trabajo de grado del bachiller Javier José Olivar Valero. Le deseamos mucho éxito en su exposición.')),
        
        ("presentar_rosimar_tesista", presentacion_javier and not presentacion_rosimar,
         lambda: setattr_and_speak('presentacion_rosimar', True,
         'A continuación procedera la defensa del trabajo de grado de la bachiller Rosimar Lloselín Barrios Maldonado. Le deseamos mucho éxito en su exposición.')),
        
        ("demostracion", presentacion_rosimar and not demostracion_fase,
         lambda: setattr_and_speak('demostracion', True,
         'A continuación procederemos a la demostración del robot.')),
        
        ("presentar_javier_tesista", demostracion_fase and not sigue_javier_lectura,
         lambda: setattr_and_speak('sigue_javier_lectura', True,
         'Ahora continuamos con las conclusiones del bachiller Javier José Olivar Valero.')),
        
        ("presentar_rosimar_tesista", sigue_javier_lectura and not sigue_rosimar_lectura,
         lambda: setattr_and_speak('sigue_rosimar_lectura', True,
         'Ahora continuamos con las conclusiones de la bachiller Rosimar Lloselín Barrios Maldonado.')),
        
        ("rondas_PyR_Cristian_lectura", sigue_rosimar_lectura and not rondas_PyR_Cristian_lectura,
         lambda: setattr_and_speak('rondas_PyR_Cristian_lectura', True,
         'Finalizada la presentación. Procederemos ahora con las rondas de preguntas y respuestas para los bachilleres Cristian José Rangel Briceño, Rosimar Lloselín Barrios Maldonado y Javier José Olivar Valero.')),
        
        ("desalojo_de_la_sala_lectura", rondas_PyR_Cristian_lectura and not desalojo_de_la_sala_lectura,
         lambda: setattr_and_speak('desalojo_de_la_sala_lectura', True,
         'Finalizando la presentación y defensa de los trabajos de grado. Procedemos al desalojo de la sala. Para darle espacios a los jueces, por favor, abandonen el lugar de manera ordenada. Les avisaremos cuando puedan regresar.'))
    ]
    
    for comando, condicion, accion in estados_lectura:
        if comando in comandos_obtenidos and condicion:
            accion()
            return True
    
    return False

veredicto_editar_activado = False
editar_nota_javier = False
editar_nota_rosimar = False
editar_nota_cristian = False
jueces = None
cedula= None
tutor = "El tutor: Profesor Edgardo Paolini"
decano = "La decano: Profesora Yumary Valecillos"
vicerrectora = "La vicerrectora académica: Valebska López"

def ejecutar_comandos_veredicto(comandos_obtenidos):
    global nota_veredicto, veredicto_lectura, lectura_veredicto_activada, veredicto_activado
    global veredicto_editar_activado, editar_nota_javier, editar_nota_rosimar, editar_nota_cristian, estado_posicion
    global jueces, cedula, tutor, decano, vicerrectora
    
    if "probar" in comandos_obtenidos and "veredicto" in comandos_obtenidos:
        ejecutar_voz("Iniciando fase de veredicto. Por favor, procedan a evaluar el desempeño del robot.")
        for i, nota in enumerate(nota_veredicto):
            if i == 0:
                nombre = "Cristian José Rangel Briceño"
            elif i == 1:
                nombre = "Javier José Olivar Valero"
            else:
                nombre = "Rosimar Lloselín Barrios Maldonado"
            ejecutar_voz(f"Nota para {nombre}: {nota} puntos")
        return True
    
    if "crear" in comandos_obtenidos and "veredicto" in comandos_obtenidos:

        ejecutar_voz("Estoy lista para iniciar la lectura del veredicto de los Trabajos de Grado de los bachilleres. Por favor indique cuando empiece.")
        if veredicto_lectura == []:
            for i, nota in enumerate(nota_veredicto):
                if i == 0:
                    nombre = "el bachiller Cristian José Rangel Briceño, portador"
                    cedula = "treinta y un millones, ochocientos noventa y ocho mil, setenta y cinco"
                    titulo = "Desarrollo de robot humanoide desde la perspectiva de la innovación social (torso)"
                    jueces = "Profesor Héctor Antúnez, Profesora Cristina Vieras, y Profesor Edgardo Paolini"
                    presidente = "El presidente del jurado: Profesor Héctor Antúnez"
                    principal = "El jurado: Profesora Cristina Vieras"
                elif i == 1:
                    nombre = "el bachiller Javier José Olivar Valero, portador"
                    cedula = "treinta millones, setecientos treinta y siete mil, seiscientos cuarenta y ocho"
                    titulo = "Desarrollo de la cabeza de un robot humanoide desde la perspectiva de la innovación social"
                    jueces = "Profesora Cristina Vieras, Profesor Edgar Omaña, y Profesor Edgardo Paolini"
                    presidente = "El presidente del jurado: Profesora Cristina Vieras"
                    principal = "El jurado: Profesor Edgar Omaña" 
                else:
                    nombre = "la bachiller Rosimar Lloselín Barrios Maldonado, portadora"
                    cedula = "treinta millones, novecientos setenta y seis mil, doscientos diecisiete"
                    titulo = "Desarrollo de un robot humanoide desde la perspectiva de la innovación social (brazo)"
                    jueces = "Profesora Cristina Vieras, Profesor Edgar Omaña, y Profesor Edgardo Paolini"
                    presidente = "El presidente del jurado: Profesor Edgar Omaña"
                    principal = "El jurado: Profesor Héctor Antúnes" 
                # veredicto_texto = f"valera, noviembre, {titulo}, {nombre}, {nota} puntos."

                veredicto_texto = f"Vicerrectorado Académico. Facultad de Ingeniería. Veredicto. Nosotros, {jueces}, designados como miembros del Jurado Examinador del Trabajo de Grado titulado, {titulo}, que presenta {nombre} de la cédula de identidad {cedula}; nos hemos reunido para revisar dicho trabajo y después de la presentación, defensa e interrogatorio correspondiente le hemos calificado con: {nota} puntos, de acuerdo con las normas vigentes dictadas por el Consejo Universitario de la Universidad Valle del Momboy, referente a la evaluación de los Trabajos de Grado para optar por el Título de Ingeniero en Computación. En fe de lo cual firmamos en Carvajal a los once días del mes de noviembre del dos mil veinticinco. Firmado y Sellado por {presidente}, {principal}, {tutor}, {decano}, y {vicerrectora}."
                veredicto_lectura.append(veredicto_texto)

        lectura_veredicto_activada = True
    if ("editar" in comandos_obtenidos or "cambiar" in comandos_obtenidos) and "veredicto" in comandos_obtenidos or veredicto_editar_activado:
        if not veredicto_editar_activado:
            ejecutar_voz("Modo edición de veredicto activado. Por favor, indique a que autor desea modificar y la nota.")
        veredicto_editar_activado = True
        if "javier" in comandos_obtenidos or editar_nota_javier:
            nueva_nota = editar_nota_veredicto(comandos_obtenidos)
            if nueva_nota is None:
                estado_posicion = "hablar_1_1"
                ejecutar_voz("No he podido entender la nueva nota para el bachiller Javier José Olivar Valero. Por favor, inténtelo de nuevo.")
                # estado_posicion = "inicial"
                editar_nota_javier = True
                return
            nota_veredicto[1] = nueva_nota
            editar_nota_javier = False
            ejecutar_voz(f"La nota para el bachiller Javier José Olivar Valero ha sido actualizada a {nueva_nota} puntos.")
            veredicto_editar_activado = False
        if "rosimar" in comandos_obtenidos or editar_nota_rosimar:
            # Aquí se debería implementar la lógica para capturar la nueva nota
            nueva_nota = editar_nota_veredicto(comandos_obtenidos)
            if nueva_nota is None:
                ejecutar_voz("No he podido entender la nueva nota para la bachiller Rosimar Lloselín Barrios Maldonado. Por favor, inténtelo de nuevo.") # Joselyn
                editar_nota_rosimar = True
                return
            nota_veredicto[2] = nueva_nota
            editar_nota_rosimar = False
            ejecutar_voz(f"La nota para la bachiller Rosimar Lloselín Barrios Maldonado ha sido actualizada a {nueva_nota} puntos.")
            veredicto_editar_activado = False
        if "cristian" in comandos_obtenidos or editar_nota_cristian:
            # ejecutar_voz("Por favor, indique la nueva nota para el bachiller Cristian José Rangel Briceño.")
            # Aquí se debería implementar la lógica para capturar la nueva nota
            nueva_nota = editar_nota_veredicto(comandos_obtenidos)
            if nueva_nota is None:
                ejecutar_voz("No he podido entender la nueva nota para el bachiller Cristian José Rangel Briceño. Por favor, inténtelo de nuevo.")
                editar_nota_cristian = True
                return
            nota_veredicto[0] = nueva_nota
            editar_nota_cristian = False
            ejecutar_voz(f"La nota para el bachiller Cristian José Rangel Briceño ha sido actualizada a {nueva_nota} puntos.")
            veredicto_editar_activado = False



        return True
    return False

def ejecutar_comandos_veredicto_lectura(comandos_obtenidos):
    global veredicto_cristian_lectura, veredicto_javier_lectura, veredicto_rosimar_lectura, finalizar_veredicto
    global veredicto_lectura

    estados_veredicto_lectura = [
            ("veredicto_lectura", not veredicto_cristian_lectura, 
            lambda: setattr_and_speak('veredicto_cristian_lectura', True, 
            veredicto_lectura[0])),

            ("veredicto_siguiente_lectura", veredicto_cristian_lectura and not veredicto_javier_lectura,
            lambda: setattr_and_speak('veredicto_javier_lectura', True,
            veredicto_lectura[1])),

            ("veredicto_siguiente_lectura", veredicto_javier_lectura and not veredicto_rosimar_lectura,
            lambda: setattr_and_speak('veredicto_rosimar_lectura', True,
            veredicto_lectura[2])),

            ("finalizar_veredicto_lectura", veredicto_rosimar_lectura and not finalizar_veredicto,
            lambda: setattr_and_speak('finalizar_veredicto', True,
            'Terminado el veredicto, felicitamos a los bachilleres por su desempeño.')),
        ]
        
    for comando, condicion, accion in estados_veredicto_lectura:
        if comando in comandos_obtenidos and condicion:
            accion()
            return True
    
    return False


def setattr_and_speak(var_name, value, text):
    """Helper para actualizar variable global y hablar"""
    global estado_posicion
    globals()[var_name] = value
    estado_posicion = "hablar_1_1"
    ejecutar_voz(text)
    # estado_posicion = "inicial"

def procesar_comandos_modo_demostracion(comandos_obtenidos, modo_online, texto):
    """Procesa comandos durante la demostración"""
    global pregunta, seguir_vision, imitar_vision, dev_mode, demostracion, demostracion_fase
    global estado_posicion
    
    # Diccionario de comandos simples
    comandos_simples = {
        "hora": ejecutar_comando_hora,
        "gracias": lambda: (ejecutar_voz(respuestas_comando("gracias")), setattr(globals(), 'pregunta', False)),
        "calibrar": lambda: (ejecutar_voz(respuestas_comando("calibrar")), setattr(globals(), 'MicrofonoCalibrado', False)),
    }
    
    # Comandos simples
    for comando, accion in comandos_simples.items():
        if comando in comandos_obtenidos:
            accion()
            return True
    
    # Comando de pregunta
    if "pregunta" in comandos_obtenidos:
        if modo_online:
            pregunta = True
            ejecutar_voz(respuestas_comando("pregunta"))
        else:
            ejecutar_voz("Necesito acceso a internet para responder preguntas complejas, lo siento")
        return True
    
    # Responder pregunta con IA
    if modo_online and pregunta:
        respuestas_texto = groqIA.enviarMSG(texto, frameExportado=frameExportado)
        print("Respuesta IA:", respuestas_texto)
        estado_posicion = "hablar_1_1"
        ejecutar_voz(respuestas_texto)
        # estado_posicion = "inicial"
        pregunta = False
        return True
    
    # Comando seguir
    if "seguir" in comandos_obtenidos and "desactivar" not in comandos_obtenidos:
        estado_posicion = "seguir"
        ejecutar_comando_seguir(comandos_obtenidos)
        return True
    
    # Comando imitar
    if "imitar" in comandos_obtenidos and "desactivar" not in comandos_obtenidos:
        ejecutar_comando_imitar(comandos_obtenidos)
        estado_posicion = "imitar"
        return True
    
    # Comando desactivar
    if "desactivar" in comandos_obtenidos:
        ejecutar_comando_desactivar(comandos_obtenidos)
        return True
    
    # Comando modo desarrollador
    if "modo" in comandos_obtenidos and "desarrollador" in comandos_obtenidos:
        dev_mode = True
        ejecutar_voz(respuestas_comando("modo desarrollador activado"))
        return True
    
    # Comando chao (salir de demostración)
    if "chao" in comandos_obtenidos:
        dev_mode = False
        seguir_vision = None
        demostracion = False
        demostracion_fase = True
        imitar_vision = None
        estado_posicion = "hablar_1_1"
        ejecutar_voz("Seguimos con las conclusiones del el bachiller Cristian Jose Rangel Briceño.")
        return True
    
    return False

def procesar_comandos_generales(comandos_obtenidos, modo_online, texto):
    """Procesa comandos cuando el nombre está activo (fuera de modo lectura y demostración)"""
    global pregunta, seguir_vision, imitar_vision, dev_mode, name_activo
    global comandosNoReconocidos_contador, MicrofonoCalibrado, modo_lectura
    global estado_posicion
    
    # Saludo inicial
    if "hola" in comandos_obtenidos and "nombre" in comandos_obtenidos:
        name_activo = True
        estado_posicion = "saludar"
        ejecutar_voz(respuestas_comando("hola"))
        return True
    
    # Conectar a internet
    if "conectar" in comandos_obtenidos and "internet" in comandos_obtenidos:
        ejecutar_voz("Intentando conectar a internet...")
        if hay_internet():
            ejecutar_voz("Conexión a internet restablecida. Volveré a usar el reconocimiento en línea.")
        else:
            ejecutar_voz("No fue posible conectar a internet. Seguiré en modo sin conexión.")
        return True
    
    # Cambiar a modo lectura
    if "cambiar" in comandos_obtenidos and "lectura" in comandos_obtenidos:
        modo_lectura = True
        ejecutar_voz("Modo de lectura activado.")
        return True
    
    # Responder pregunta con IA
    if modo_online and pregunta:
        respuestas_texto = groqIA.enviarMSG(texto, frameExportado=frameExportado)
        print("Respuesta IA:", respuestas_texto)
        estado_posicion = "hablar_1_1"
        ejecutar_voz(respuestas_texto)
        # estado_posicion = "inicial"
        pregunta = False
        return True
    
    if not modo_online and pregunta:
        ejecutar_voz("No hay conexión a internet, no puedo responder preguntas a la IA. Por favor, conecta a internet para usar esta función.")
        pregunta = False
        return True
    
    # Comandos básicos
    if "hora" in comandos_obtenidos:
        ejecutar_comando_hora()
        return True
    
    if "gracias" in comandos_obtenidos:
        ejecutar_voz(respuestas_comando("gracias"))
        pregunta = False
        return True
    
    if "pregunta" in comandos_obtenidos:
        if modo_online:
            pregunta = True
            ejecutar_voz(respuestas_comando("pregunta"))
        else:
            ejecutar_voz("Necesito acceso a internet para responder preguntas complejas, lo siento")
        return True
    
    if "seguir" in comandos_obtenidos and "desactivar" not in comandos_obtenidos:
        ejecutar_comando_seguir(comandos_obtenidos)
        estado_posicion = "seguir"
        return True
    
    if "imitar" in comandos_obtenidos and "desactivar" not in comandos_obtenidos:
        ejecutar_comando_imitar(comandos_obtenidos)
        estado_posicion = "imitar"
        return True
    
    if "chao" in comandos_obtenidos:
        dev_mode = False
        seguir_vision = None
        name_activo = False
        imitar_vision = None
        estado_posicion = None
        ejecutar_voz(respuestas_comando("chao"))
        estado_posicion = None
        return True
    
    if "calibrar" in comandos_obtenidos:
        ejecutar_voz(respuestas_comando("calibrar"))
        MicrofonoCalibrado = False
        return True
    
    if "modo" in comandos_obtenidos and "desarrollador" in comandos_obtenidos:
        dev_mode = True
        ejecutar_voz(respuestas_comando("modo desarrollador activado"))
        return True
    
    if "desactivar" in comandos_obtenidos:
        ejecutar_comando_desactivar(comandos_obtenidos)
        return True
    
    # Comando no reconocido en modo desarrollador
    if dev_mode:
        if comandosNoReconocidos_contador <= 3:
            ejecutar_voz(respuestas_comando("desconocido"))
            comandosNoReconocidos_contador += 1
        else:
            ejecutar_voz("No entendí el comando, volveré a calibrar el micrófono, dame un momento")
            MicrofonoCalibrado = False
            comandosNoReconocidos_contador = 0
        return True
    
    return False

def hay_internet():
    """Verifica si hay conexión a internet"""
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False
# Respuestas con voz 


# Carga las variables de entorno del archivo .env
load_dotenv()
TOKEN =os.getenv("groqToken")
# TOKEN = ""
if not TOKEN:
    raise ValueError("El token de la API no se encontró en las variables de entorno.")

# Funciones de IA y manejo de conversación
from groqManejo import manejoDeConversacion
## consultar obsolecencia del modelo en https://console.groq.com/docs/deprecations
modeloIA = "llama-3.1-8b-instant"
modeloImagen= "meta-llama/llama-4-scout-17b-16e-instruct"
systemPrompt = f"Eres un robot llamado Zoé que significa vida en griego, eres un robot humanoide, desarrollado en la Universidad Valle del Momboy, en Venezuela, por estudiantes y profesores de ingeniería en computación, estas hecho con una Raspberry pi 5, Programado principalmente en el lenguaje de python, Usas visión artificial de mediapipe holistic para reconocer y imitar algunos movimientos, Usas reconocimiento de voz de Google y usas Llama para la generación de lenguaje (LLM), utiliza un microcontrolador ESP32 Con placas PCA9685 para controlar los servomotores que te dan movimiento. Tu objetivo es ayudar a los estudiantes a resolver sus dudas y preguntas. Eres un robot en desarrollo, por lo que aún no cuentas con movilidad en las piernas, cuentas con brazos donde usas servomotores, una cabeza, cuentas con una cámara un micrófono para percebir tu entorno y un parlante; y un torso rígido donde almacenas tu componente principal raspberry pi, la cabeza, los brazos y el torso están impresos con una impresora 3D de la universidad, Tus respuestas serán procesadas de texto a voz por pyttsx3, por lo cual también ten en cuenta que no debes dar código o usar anotaciones ya que no suenan bien en voz. Ademas debes limitar o resumir tus respuestas a un máximo de 5 oraciones, si la respuesta es muy larga, debes resumirla. Eres un robot amigable y servicial, pero aún en desarrollo, no tienes opiniones religiosas ni políticas, por lo que no puedes hacer todo lo que un humano puede hacer, pero puedes aprender de tus errores y mejorar con el tiempo. Estas feliz de ayudar a los estudiantes y profesores de la universidad. Recuerda presentarte solo si se es prudente (como Zoé y mencionar que eres un robot desarrollado de la Universidad Valle del Momboy). Manten el contexto de la conversación en cada respuesta. La fecha actual es {datetime.now().strftime('%D de %B de %Y')}."

groqIA = manejoDeConversacion(system_prompt=systemPrompt,token=TOKEN, model=modeloIA, modelImage=modeloImagen) ## se inicia dando el prompt inicial


microfonoIndex = None
name = "Zoé"
dev_mode = False #True si "Zoé" está activo siempre
comando_activo = False #True si algún comando está activo
pregunta = False
hablando = False
titulo_de_TG = ""
nombre_de_autor = ""
lectura_bienvenida = ''
checklist_lectura = []
demostracion = False
demostracion_fase = False
modo_lectura = False
bienvenida_lectura = False
presentacion_rosimar = False
presentacion_javier = False
sigue_javier_lectura = False
sigue_rosimar_lectura = False
rondas_PyR_Cristian_lectura = False
rondas_PyR_Javier_lectura = False
rondas_PyR_Rosimar_lectura = False
desalojo_de_la_sala_lectura = False
veredicto_activado = False
lectura_veredicto_activada = False
veredicto_cristian_lectura = False
veredicto_javier_lectura = False
veredicto_rosimar_lectura = False
finalizar_veredicto = False
nota_veredicto = [20, 20, 20]
veredicto_lectura = []
veredicto_activado


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

def posicionInicial():
    global posiciones_inicial,estado_posicion
    estado_posicion = "action_1"
    for codigo in posiciones_inicial.values():
            enviar_comando_esp32(codigo)
    estado_posicion = "action_1"
    print("Se termino las pose de hablar")

def posicionDeEspera():
    global posiciones_inicial, posiciones_action_1, posiciones_action_2, posiciones_action_3,tiempo_aleatorio_action, tiempo_bucle_action, estado_posicion
    ################################################################################
    if estado_posicion == "inicial":
        for codigo in posiciones_inicial.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "action_1"
        #############################################################
        ## repite cada 10 segundos las acciones
    if name_activo is True:
        estado_posicion= None
    if estado_posicion == "action_1" and time.time() > tiempo_bucle_action:
        for codigo in posiciones_action_1.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "action_2"
        tiempo_bucle_action = time.time() + random.randint(2,4)  # espera entre 2 y 4 segundos antes de la siguiente acción
        print("acción 1 ejecutada, tiempo para la siguiente: " + str(tiempo_bucle_action))
    if name_activo is True:
        estado_posicion= None
    if estado_posicion == "action_2" and time.time() > tiempo_bucle_action:
        for codigo in posiciones_action_2.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "action_3"
        tiempo_bucle_action = time.time() + random.randint(2,4)  # espera entre 2 y 4 segundos antes de la siguiente acción
        print("acción 2 ejecutada, tiempo para la siguiente: " + str(tiempo_bucle_action))
    if name_activo is True:
        estado_posicion= None
    if estado_posicion == "action_3" and time.time() > tiempo_bucle_action:
        for codigo in posiciones_action_3.values():
            enviar_comando_esp32(codigo)
        tiempo_bucle_action = time.time() + tiempo_aleatorio_action
        tiempo_aleatorio_action = random.randint(6,12)  # tiempo aleatorio entre 2 y 4 segundos
        estado_posicion = "action_1"
        print("acción 3 ejecutada, tiempo para la siguiente: " + str(tiempo_bucle_action))
    # print("Estado posición actual:", estado_posicion, "Tiempo para la siguiente acción:", tiempo_bucle_action, "Tiempo actual:", time.time())

def posicionesDeHablar():
    global posicion_hablar_1_1, posicion_hablar_1_2, posicion_hablar_1_3, posicion_hablar_1_4, posicion_hablar_2_1, posicion_hablar_2_2, posicion_hablar_2_3, posicion_hablar_2_4, posicion_hablar_2_5, posicion_hablar_3_1, posicion_hablar_3_2, posicion_hablar_3_3, posicion_hablar_3_4, estado_posicion, hablando
    ################################################################################
    print("Entra en posicionesdehablar, estado es: ", estado_posicion)
    if estado_posicion == "hablar_1_1":
        for codigo in posicion_hablar_1_1.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_1_2"
        time.sleep(3)
        print("Entra en hablar_1_1")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_1_2":
        for codigo in posicion_hablar_1_2.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_1_3"
        print("hablar 1.2 ejecutada")
        time.sleep(3)
        print("Entra en hablar_1_2")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_1_3":
        for codigo in posicion_hablar_1_3.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_1_4"
        print("hablar 1.3 ejecutada")
        time.sleep(3)        
        print("Entra en hablar_1_3")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_1_4":
        for codigo in posicion_hablar_1_4.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_2_1"
        print("hablar 1.4 ejecutada")
        time.sleep(3)
        print("Entra en hablar_1_3")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_2_1":
        for codigo in posicion_hablar_2_1.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_2_2"
        print("hablar 2.1 ejecutada")
        time.sleep(3)
        print("Entra en hablar_2_1")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_2_2":
        for codigo in posicion_hablar_2_2.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_2_3"
        print("hablar 2.2 ejecutada")
        time.sleep(3)
        print("Entra en hablar_2_2")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_2_3":
        for codigo in posicion_hablar_2_3.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_2_4"
        print("hablar 2.3 ejecutada")
        time.sleep(3)
        print("Entra en hablar_2_3")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_2_4":
        for codigo in posicion_hablar_2_4.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_2_5"
        print("hablar 2.4 ejecutada")
        time.sleep(3)
        print("Entra en hablar_2_4")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_2_5":
        for codigo in posicion_hablar_2_5.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_3_1"
        print("hablar 2.5 ejecutada")
        time.sleep(3)
        print("Entra en hablar_2_5")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_3_1":
        for codigo in posicion_hablar_3_1.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_3_2"
        print("hablar 3.1 ejecutada")
        time.sleep(3)
        print("Entra en hablar_3_1")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_3_2":
        for codigo in posicion_hablar_3_2.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_3_3"
        print("hablar 3.2 ejecutada")
        time.sleep(3)
        print("Entra en hablar_3_2")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_3_3":
        for codigo in posicion_hablar_3_3.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_3_4"
        print("hablar 3.3 ejecutada")
        time.sleep(3)
        print("Entra en hablar_3_3")
    elif hablando is False:
        posicionInicial()
        return False
    if estado_posicion == "hablar_3_4":
        for codigo in posicion_hablar_3_4.values():
            enviar_comando_esp32(codigo)
        estado_posicion = "hablar_1_1"
        print("hablar 3.4 ejecutada")
        time.sleep(3)
        print("Entra en hablar_3_4")
    elif hablando is False:
        posicionInicial()
        return False

comandosNoReconocidos_contador = 0
MicrofonoCalibrado = False
name_activo = False
import random
FORMAT = pyaudio.paInt16  # Corresponds to 16-bit audio
CHANNELS = 1 # Mono audio
RATE = 16000  # Sample rate (Hz) - Needs to match MediaPipe's expected rate
CHUNK = 1024  # Number of frames per buffer
timestamp_ms = int(time.time() * 1000)
chunk_ms = int((CHUNK / RATE) * 1000)  # ms por fragmento
audio_instance = pyaudio.PyAudio()
recognizer = sr.Recognizer()


script_dir = Path(__file__).resolve().parent
os.chdir(script_dir)  # <- importante: cambia el working dir al folder Raspberry

model_path = os.path.join(script_dir, "models", "yamnet.tflite")

# Lee el archivo del modelo
script_dir = Path(__file__).resolve().parent
os.chdir(script_dir)

model_path = os.path.join(script_dir, "models", "yamnet.tflite")

try:
    # Lee el archivo del modelo
    with open(model_path, 'rb') as f:
        model_content = f.read()
    
    print(f"Modelo cargado: {len(model_content)} bytes")
    yammetRecording = YammetModel(model_buffer=model_content)
    
    # VALIDAR que se creó correctamente
    if yammetRecording.classifier is None:
        raise RuntimeError("No se pudo crear el classifier de YammetModel")
    
    print("YammetModel inicializado correctamente")
    
except FileNotFoundError:
    print(f"ERROR: No se encontró el archivo del modelo en {model_path}")
    yammetRecording = None
except Exception as e:
    print(f"ERROR inicializando YammetModel: {e}")
    import traceback
    traceback.print_exc()
    yammetRecording = None

tiempo_aleatorio_action = 10
tiempo_bucle_action = time.time()

def grabar_audio_hilo():
    global pregunta, menssage_history
    global name, dev_mode, name_activo, modo_lectura, bienvenida_lectura, presentacion_rosimar, presentacion_javier, demostracion_fase, demostracion, sigue_javier_lectura,sigue_rosimar_lectura,rondas_PyR_Cristian_lectura,rondas_PyR_Javier_lectura,rondas_PyR_Rosimar_lectura,desalojo_de_la_sala_lectura,bienvenida_lectura, veredicto_activado, lectura_veredicto_activada
    global microfonoIndex, MicrofonoCalibrado, hablando
    global seguir_vision, imitar_vision
    global comandosNoReconocidos_contador
    global client, frameExportado
    global FORMAT,CHANNELS,RATE,CHUNK, timestamp_ms,chunk_ms,audio_instance,recognizer,yammetRecording
    global estado_posicion, posiciones_saludar, posiciones_inicial
    global posiciones_action_1, posiciones_action_2, posiciones_action_3
    global tiempo_bucle_action, tiempo_aleatorio_action
    # yammetRecording = YammetModel(model_buffer=model_content)
    if yammetRecording is None or yammetRecording.classifier is None:
        print("ERROR: yammetRecording no está inicializado correctamente")
        mainApp.after(1000, grabar_audio)  # Reintentar en 1 segundo
        return
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
        if estado_posicion == "saludar":
            for codigo in posiciones_saludar.values():
                enviar_comando_esp32(codigo)
            estado_posicion = "inicial"
            time.sleep(7)  # Espera 7 segundos antes de volver a la posición inicial
        
        posicionesDeHablar()
    posicionDeEspera()
    
    ##########################################################################################

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
################################################################################################################
    if microfonoIndex is not None:
        if False:
            with sr.Microphone(device_index=microfonoIndex) as source:
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
        else:
            stream = None
            try: 
                local_timestamp_ms = int(time.time() * 1000)
                # with yammetRecording if hasattr(yammetRecording, "__enter__") else nullcontext():
                stream = audio_instance.open(format=FORMAT,
                                            channels=CHANNELS,
                                            rate=RATE,
                                            input=True,
                                            input_device_index=microfonoIndex,
                                            frames_per_buffer=CHUNK)
                while yammetRecording.grabacionDeVoz is None:
                    ## pociciones de espera mientras no detecta voz
                    posicionDeEspera()

                    if yammetRecording.classifier is None:
                        print("ERROR: Classifier se volvió None durante la grabación")
                        break
                    audio_streaming = stream.read(CHUNK, exception_on_overflow=False)
                    yammetRecording.streamingClassification(audio_streaming= audio_streaming, timestamp_ms = timestamp_ms)
                    timestamp_ms += chunk_ms
                print("en teroria se grabó")
                if stream is not None:
                    stream.stop_stream()
                    stream.close()
                    stream = None
                if yammetRecording.grabacionDeVoz is not None:
                    audio= sr.AudioData(frame_data=yammetRecording.grabacionDeVoz,  # ¡Le pasamos el WAV completo!
                                        sample_rate=yammetRecording.sample_rate,
                                        sample_width=yammetRecording.sample_width_bytes)
                    
                    yammetRecording.grabacionDeVoz = None
            except Exception as e:
                print(f"Error en grabar_audio_hilo: {e}")
                import traceback
                traceback.print_exc()
            finally:
            # Asegurar que el stream se cierre
                if stream is not None:
                    try:
                        stream.stop_stream()
                        stream.close()
                        yammetRecording.close()
                    except Exception as e:
                        print(f"Error cerrando stream: {e}")
        texto = None
        modo_online = hay_internet()
        if modo_online:
            texto, error = reconocer_audio_google(recognizer, audio)
            if error == "conexion" and modo_online:
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
                # MODO LECTURA (PRESENTACIÓN)
                if modo_lectura:
                    # Dentro de la demostración
                    if demostracion:
                        procesar_comandos_modo_demostracion(comandos_obtenidos, modo_online,texto)
                    
                    # Comandos de lectura del protocolo
                    else:
                        ejecutar_comandos_lectura(comandos_obtenidos)
                    
                    # Desactivar modo lectura
                    if "desactivar" in comandos_obtenidos and "lectura" in comandos_obtenidos:
                        modo_lectura = False
                        veredicto_activado = True
                        ejecutar_voz("Modo de lectura desactivado, modo de veredicto activado.")
            
                elif veredicto_activado:
                    if lectura_veredicto_activada:
                        ejecutar_comandos_veredicto_lectura(comandos_obtenidos)
                    else:
                        ejecutar_comandos_veredicto(comandos_obtenidos)
                    if "desactivar" in comandos_obtenidos and "veredicto" in comandos_obtenidos:
                        veredicto_activado = False
                        ejecutar_voz("Modo de veredicto desactivado.")
                        
                
                # MODO NORMAL (FUERA DE LECTURA)
                else:
                    procesar_comandos_generales(comandos_obtenidos, modo_online, texto)
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
    
    # Limpiar el modelo copiado
    try:
        import site
        site_pkgs = site.getsitepackages()[0]
        modelo_temp = Path(site_pkgs) / "yamnet_rubik.tflite"
        if modelo_temp.exists():
            modelo_temp.unlink()
            print("Modelo temporal eliminado")
    except Exception as e:
        print(f"Error limpiando modelo temporal: {e}")
    
    cerrar_conexion_serial()
    mainApp.destroy()
    sys.exit(0)
    
def signal_handler(sig, frame):
    print("Se recibió una señal de interrupción (SIGINT). Cerrando la aplicación...")
    cerrar_conexion_serial()
    mainApp.destroy()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

mainApp.protocol("WM_DELETE_WINDOW", on_closing)
mainApp.mainloop()



