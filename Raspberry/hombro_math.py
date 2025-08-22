import numpy as np
import math
import matplotlib.pyplot as plt

def normalizar(vector):
    """Devuelve el vector unitario (magnitud 1)."""
    norma = np.linalg.norm(vector)
    if norma == 0:
        return vector
    return vector / norma

def calcular_angulos_brazo(world_landmarks):
    """
    Calcula los ángulos lateral y frontal del brazo izquierdo.

    Args:
        world_landmarks: El objeto world_landmarks de MediaPipe Pose.

    Returns:
        Un tuple con (angulo_lateral_grados, angulo_frontal_grados).
    """
    # Obtener puntos clave de MediaPipe (asegúrate de que los índices son correctos)
    # landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    p_hombro_izq = np.array([world_landmarks[11].x, world_landmarks[11].y, world_landmarks[11].z])
    p_hombro_der = np.array([world_landmarks[12].x, world_landmarks[12].y, world_landmarks[12].z])
    p_codo_der = np.array([world_landmarks[14].x, world_landmarks[14].y, world_landmarks[14].z])
    p_cadera_der = np.array([world_landmarks[24].x, world_landmarks[24].y, world_landmarks[24].z])
    p_codo_izq = np.array([world_landmarks[13].x, world_landmarks[13].y, world_landmarks[13].z])
    p_cadera_izq = np.array([world_landmarks[23].x, world_landmarks[23].y, world_landmarks[23].z])

    # 1. Crear el sistema de coordenadas del torso
    v_arriba = normalizar(p_hombro_izq - p_cadera_izq)
    v_lateral_torso = normalizar(p_hombro_der - p_hombro_izq)
    v_adelante = normalizar(np.cross(v_arriba, v_lateral_torso))

    # --- Cálculo para el brazo derecho ---
    # Repetimos el proceso para el brazo derecho
    v_arriba_der = normalizar(p_hombro_der - p_cadera_der)
    v_lateral_torso_der = normalizar(p_hombro_izq - p_hombro_der)
    v_adelante_der = normalizar(np.cross(v_arriba_der, v_lateral_torso_der))
    v_lateral_der = normalizar(np.cross(v_adelante_der, v_arriba_der))
    v_brazo_der = p_codo_der - p_hombro_der

    proy_arriba_lat_der = np.dot(v_brazo_der, v_arriba_der)
    proy_lateral_der = np.dot(v_brazo_der, v_lateral_der)
    angulo_lateral_rad_der = math.atan2(proy_lateral_der, -proy_arriba_lat_der)
    angulo_lateral_grados_der = math.degrees(angulo_lateral_rad_der)

    proy_arriba_fro_der = np.dot(v_brazo_der, v_arriba_der)
    proy_adelante_der = np.dot(v_brazo_der, v_adelante_der)
    angulo_frontal_rad_der = math.atan2(proy_adelante_der, -proy_arriba_fro_der)
    angulo_frontal_grados_der = math.degrees(angulo_frontal_rad_der)
    
    # Recalcular v_lateral_torso para asegurar que sea 100% perpendicular (ortogonal)
    v_lateral = normalizar(np.cross(v_adelante, v_arriba))

    # 2. Vector del brazo
    v_brazo = p_codo_izq - p_hombro_izq

    # 3. Calcular ángulo lateral (Motor 1)
    # Proyección en el plano frontal (arriba, lateral)
    proy_arriba_lat = np.dot(v_brazo, v_arriba)
    proy_lateral = np.dot(v_brazo, v_lateral)
    # Usamos atan2 para el ángulo y medimos desde la vertical hacia abajo (-v_arriba)
    angulo_lateral_rad = math.atan2(proy_lateral, -proy_arriba_lat)
    angulo_lateral_grados = math.degrees(angulo_lateral_rad)

    # 4. Calcular ángulo frontal (Motor 2)
    # Proyección en el plano sagital (arriba, adelante)
    proy_arriba_fro = np.dot(v_brazo, v_arriba)
    proy_adelante = np.dot(v_brazo, v_adelante)
    # Usamos atan2 para el ángulo y medimos desde la vertical hacia abajo (-v_arriba)
    angulo_frontal_rad = math.atan2(proy_adelante, -proy_arriba_fro)
    angulo_frontal_grados = math.degrees(angulo_frontal_rad)

    ## Dibujar los ángulos en mathplotlib
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.title("Ángulo Lateral")
    plt.quiver(0, 0, v_brazo[0], v_brazo[1], angles='xy', scale_units='xy', scale=1, color='blue')
    plt.quiver(0, 0, v_arriba[0], v_arriba[1], angles='xy', scale_units='xy', scale=1, color='red')
    plt.quiver(0, 0, v_lateral[0], v_lateral[1], angles='xy', scale_units='xy', scale=1, color='green')
    plt.grid()
    plt.gca().set_aspect('equal', adjustable='box')


    return (angulo_lateral_grados, angulo_frontal_grados, angulo_lateral_grados_der, angulo_frontal_grados_der)

# --- USO ---
# Dentro de tu bucle de MediaPipe:
# if results.pose_world_landmarks:
#   landmarks = results.pose_world_landmarks.landmark
#   ang_lat, ang_frontal = calcular_angulos_brazo(landmarks)
#   print(f"Ángulo Lateral (Motor 1): {ang_lat:.2f}°")
#   print(f"Ángulo Frontal (Motor 2): {ang_frontal:.2f}°")
#   # Aquí envías los valores a tus servomotores