import cv2
import mediapipe as mp
import numpy as np

import matplotlib.pyplot as plt

from hombro_math import calcular_angulos_brazo
# Inicializar MediaPipe Holistic
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

# Cargar imagen
image_path = 'ejemplo.jpg'  # Cambia esto por la ruta de tu imagen
image = cv2.imread(image_path)
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Procesar imagen con Holistic
with mp_holistic.Holistic(static_image_mode=True,
    model_complexity=0,) as holistic:
    results = holistic.process(image_rgb)


if results.pose_world_landmarks:

    Angulos = calcular_angulos_brazo(results.pose_world_landmarks.landmark)
    print(f"Ángulo lateral: {Angulos[0]:.2f} grados")
    print(f"Ángulo frontal: {Angulos[1]:.2f} grados")
    print(f"Ángulo lateral derecho: {Angulos[2]:.2f} grados")
    print(f"Ángulo frontal derecho: {Angulos[3]:.2f} grados")


    landmarks = results.pose_world_landmarks
    mp_drawing.plot_landmarks(landmarks, mp_holistic.POSE_CONNECTIONS)

    image

    plt.show()
    
