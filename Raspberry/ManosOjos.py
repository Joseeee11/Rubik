import cv2
import mediapipe as mp
import numpy as np
import serial
import time
from math import acos, degrees

drawing = mp.solutions.drawing_utils
drawing_styles= mp.solutions.drawing_styles
hands = mp.solutions.hands

def palma_centroCoordenadas(palma):
    coordenadas = np.array(palma)
    centroCoordenadas = np.mean(coordenadas, axis=0)
    centroCoordenadas = int(centroCoordenadas[0]), int(centroCoordenadas[1])
    return centroCoordenadas

serialESP32 = serial.Serial(port='COM10', baudrate=115200, timeout=1)
time.sleep(2)
last_send_time0 = 0
last_send_time1 = 0
last_send_time2 = 0
last_send_time3 = 0
last_send_time4 = 0
memoria0 = 0
memoria1 = 0
memoria2 = 0
memoria3 = 0
memoria4 = 0

def send_message(message):
    if serialESP32.is_open:
        serialESP32.write((message+'\n').encode())
        print(f"Mensaje enviado: {message}")
    else:
        print("Error: No se pudo abrir el puerto serie.")

# Inicializar la captura de video
enVivo = cv2.VideoCapture(0)

palma_puntos=[0,1,2,5,9,13,17]
pulgar_puntos=[1,2,4]
punta_puntos=[8,12,16,20]
base_puntos=[6,10,14,18]
with hands.Hands(

    static_image_mode=False,
    max_num_hands=1, # hay que cambiarlo
    min_detection_confidence=0.5,
    min_tracking_confidence = 0.5) as manos:

    while True:

        ret, frame = enVivo.read()
        if ret == False:
            break

        height, width, _ = frame.shape
        frame= cv2.flip(frame,1)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = manos.process(frame_rgb)

        if results.multi_hand_landmarks is not None:
            palma_coordenadas = []
            pulgar_coordenadas = []
            punta_coordenadas = []
            base_coordenadas = []
            for hand_landmarks in results.multi_hand_landmarks:
                for i in pulgar_puntos:
                    x = int(hand_landmarks.landmark[i].x * width)
                    y = int(hand_landmarks.landmark[i].y * height)
                    pulgar_coordenadas.append([x, y])

                for i in punta_puntos:
                    x = int(hand_landmarks.landmark[i].x * width)
                    y = int(hand_landmarks.landmark[i].y * height)
                    punta_coordenadas.append([x, y])

                for i in base_puntos:
                    x = int(hand_landmarks.landmark[i].x * width)
                    y = int(hand_landmarks.landmark[i].y * height)
                    base_coordenadas.append([x, y])
                
                for i in palma_puntos:
                    x = int(hand_landmarks.landmark[i].x * width)
                    y = int(hand_landmarks.landmark[i].y * height)
                    palma_coordenadas.append([x, y])
                
                p1 = np.array(pulgar_coordenadas[0])
                p2 = np.array(pulgar_coordenadas[1])
                p3 = np.array(pulgar_coordenadas[2])

                l1 = np.linalg.norm(p2-p3)
                l2 = np.linalg.norm(p1-p3)
                l3 = np.linalg.norm(p1-p2)
                centro_palma = palma_centroCoordenadas(palma_coordenadas)
                cv2.circle(frame, centro_palma, 5, (0, 255, 0), -1)
                # Dividir la pantalla en 7 partes
                for i in range(1, 7):
                    # Líneas verticales
                    cv2.line(frame, (i * width // 7, 0), (i * width // 7, height), (255, 0, 0), 1)
                    # Líneas horizontales
                    cv2.line(frame, (0, i * height // 7), (width, i * height // 7), (255, 0, 0), 1)

                # Determinar si el centro de la mano está a la izquierda o derecha
                centro_x = centro_palma[0]
                if centro_x < (width // 2) - (width // 7):  # Izquierda
                    send_message("L")
                elif centro_x > (width // 2) + (width // 7):  # Derecha
                    send_message("R")
                # Determinar si el centro de la mano está arriba o abajo
                centro_y = centro_palma[1]
                if centro_y < (height // 2) - (height // 7):  # Arriba
                    send_message("W")
                elif centro_y > (height // 2) + (height // 7):  # Abajo
                    send_message("S")
                try:
                    cos_value = (l1**2 + l3**2 - l2**2) / (2 * l1 * l3)
                    cos_value = max(-1, min(1, cos_value))  # Ensure value is within [-1, 1]
                    angulo = degrees(acos(cos_value))
                except ValueError as e:
                    print(f"Error calculating angle: {e}")
                    angulo = 0  # Default value in case of error
                dedo_pulgar = np.array(False)
                if angulo > 150: 
                    dedo_pulgar = np.array(True)
                    serialESP32.write(b'1')

                # Palma
                xn, yn = palma_centroCoordenadas(palma_coordenadas)
                centro_coordenadas = np.array([xn, yn])
                # dedos
                punta_coordenadas = np.array(punta_coordenadas)
                base_coordenadas = np.array(base_coordenadas)

                # Distancia entre la punta y la base de los dedos
                dis_centro_punta = np.linalg.norm(centro_coordenadas - punta_coordenadas, axis=1)
                dis_centro_base = np.linalg.norm(centro_coordenadas - base_coordenadas, axis=1)
                diferencia = dis_centro_base - dis_centro_punta 
                dedosAbiertos = diferencia < 0
                dedosAbiertos = np.append(dedo_pulgar ,dedosAbiertos)
                print("Dedos abiertos: ", dedosAbiertos)
                # Enviar datos al ESP32
                current_time0 = time.time()
                if current_time0 - last_send_time0 >= 0.5:
                    if dedosAbiertos[0] and memoria0 == False:
                        send_message("I")
                        memoria0 = True
                    elif dedosAbiertos[0] == False and memoria0 == True:
                        send_message("J")
                        memoria0 = False
                    last_send_time0 = current_time0
                current_time1 = time.time()
                if current_time1 - last_send_time1 >= 0.5:
                    if dedosAbiertos[1] and memoria1 == False:
                        send_message("G")
                        memoria1 = True
                    elif dedosAbiertos[1] == False and memoria1 == True:
                        send_message("H")
                        memoria1 = False
                    last_send_time1 = current_time1
                current_time2 = time.time()
                if current_time2 - last_send_time2 >= 0.5:
                    if dedosAbiertos[2] and memoria2 == False:
                        send_message("B")
                        memoria2 = True
                    elif dedosAbiertos[2] == False and memoria2 == True:
                        send_message("A")
                        memoria2 = False
                    last_send_time2 = current_time2
                current_time3 = time.time()
                if current_time3 - last_send_time3 >= 0.5:
                    if dedosAbiertos[3] and memoria3 == False:
                        send_message("D")
                        memoria3 = True
                    elif dedosAbiertos[3] == False and memoria3 == True:
                        send_message("C")
                        memoria3 = False
                    last_send_time3 = current_time3
                current_time4 = time.time()
                if current_time4 - last_send_time4 >= 0.5:
                    if dedosAbiertos[4] and memoria4 == False:
                        send_message("F")
                        memoria4 = True
                    elif dedosAbiertos[4] == False and memoria4 == True:
                        send_message("E")
                        memoria4 = False
                    last_send_time4 = current_time4
                drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    hands.HAND_CONNECTIONS,
                    drawing_styles.get_default_hand_landmarks_style(),
                    drawing_styles.get_default_hand_connections_style())
                print("memorias: ", memoria0, memoria1, memoria2, memoria3, memoria4)
        cv2.imshow('LiveStream', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

enVivo.release()
cv2.destroyAllWindows()
serialESP32.close()
# import ctypes

# Obtener la resolución de la pantalla
# user32 = ctypes.windll.user32
# screen_width = user32.GetSystemMetrics(0)
# screen_height = user32.GetSystemMetrics(1)

    # # Calcular la relación de aspecto de la imagen
    # aspect_ratio = width / height

    # # Calcular nuevas dimensiones manteniendo la relación de aspecto
    # if width > screen_width or height > screen_height:
    #     if screen_width / aspect_ratio <= screen_height:
    #         new_width = screen_width
    #         new_height = int(screen_width / aspect_ratio)
    #     else:
    #         new_height = screen_height
    #         new_width = int(screen_height * aspect_ratio)
    # else:
    #     new_width = width
    #     new_height = height

    # # Redimensionar la imagen
    # envivo_resized = cv2.resize(envivo, (new_width, new_height))
    # envivo_resized = cv2.flip(envivo_resized, 1)

    # envivo_RGB = cv2.cvtColor(envivo, cv2.COLOR_BGR2RGB)



    # envivo_resized = cv2.flip(envivo_resized, 1)

# # Mostrar la imagen redimensionada
# cv2.imshow("Image", imagen_resized)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

