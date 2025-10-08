import mediapipe as mp
import numpy as np
import math
import imutils
import cv2
import serial


drawing = mp.solutions.drawing_utils
drawing_styles = mp.solutions.drawing_styles
mediaPipe = mp.solutions.holistic

holistic = mediaPipe.Holistic(
    min_detection_confidence=0.8,
    min_tracking_confidence=0.8,
    smooth_landmarks=True,
    model_complexity=0,
    enable_segmentation=True,
)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: No se pudo abrir la cámara.")
    exit()

# serialESP32 = serial.Serial(port='COM7', baudrate=115200, timeout=1)
# def enviar_ESP(codigo):
#     if serialESP32.is_open:
#         # Envía el número como dos bytes (big endian)
#         serialESP32.write(codigo.to_bytes(2, byteorder='big'))
#         print(f"Mensaje enviado: {codigo}")
#     else:
#         print("Error: No se pudo abrir el puerto serie.")

angulos_hombro_derecho_promedio_frontal = []
angulos_hombro_derecho_promedio_lateral = []
ultimo_movimiento_frontal_hombro_der = "ninguno"  # para evitar enviar mensajes repetidos
ultimo_movimiento_lateral_hombro_der = "ninguno"  # para evitar enviar mensajes repetidos


# brazo_derecho y brazo_izquierdo es ["frontal", "codigo", "sagital", "codigo", "flexion", "codigo", "rotacion", "codigo"])
brazo_derecho = ["None", "None", "None", "None", "None", "None", "None", "None"]
brazo_izquierdo = ["None", "None", "None", "None", "None", "None", "None", "None"]

# Funciones necesarias
def normalizar_vector(vector):
    norma = np.linalg.norm(vector)
    if norma == 0:
        return vector
    return vector / norma

def calcular_angulo(componente1, componente2):
    if componente1 == 0 and componente2 == 0:
        return 0
    # aplicaré la funcion "atan2" arcotangente de dos argumentos
    angulo_radianes = np.arctan2(componente1, componente2)
    angulo_grados = np.degrees(angulo_radianes)
    return angulo_grados

def calcular_angulo_flexion(vector1, vector2):
    producto_escalar = np.dot(vector1, vector2)
    magnitud_vector1 = np.linalg.norm(vector1)
    magnitud_vector2 = np.linalg.norm(vector2)
    if magnitud_vector1 < 1e-6 or magnitud_vector2 < 1e-6:
        return 0
        # print("angulo flexion codo", angulo_mfcd_grados)  #0 extendido, 180 flexionado
    else:
        coseno = producto_escalar / (magnitud_vector1 * magnitud_vector2)
        coseno = np.clip(coseno, -1.0, 1.0)  # Asegurar que el coseno esté en el rango válido
        angulo_radianes = np.arccos(coseno)
        angulo_grados = np.degrees(angulo_radianes)
        return angulo_grados

def calcular_vector_perpendicular(vectorFijo, vectorReferencia):
    # x, y, z de nuestro vector perpendicular
    x = vectorReferencia[0]
    z = vectorReferencia[2]
    y = -(vectorFijo[0]*x + vectorFijo[2]*z) / vectorFijo[1]
    vector_perpendicular = np.array([x, y, z])
    return vector_perpendicular

def definir_posicion_frontal(angulo, brazo):
    # brazo_dereccho[0] es posición frontal y brazo_derecho[1] es su código para ESP32
    if (brazo == "derecho"):
        if 75 < angulo <= 105:
            # print("Frontal: arriba")
            brazo_derecho[0] = "arriba"
            # brazo_derecho[1] = "1560"
        elif 45 < angulo <= 75:
            # print("Frontal: arriba-derecha")
            brazo_derecho[0] = "arriba-derecha"
        elif 20 < angulo <= 45:
            # print("Frontal: derecha-arriba")
            brazo_derecho[0] = "derecha-arriba"
        elif -20 < angulo <= 20:
            # print("Frontal: derecha")
            brazo_derecho[0] = "derecha"
        elif -45 < angulo <= -20:
            # print("Frontal: derecha-abajo")
            brazo_derecho[0] = "derecha-abajo"
        elif -65 < angulo <= -45:
            # print("Frontal: abajo-derecha")
            brazo_derecho[0] = "abajo-derecha"
        elif -105 < angulo <= -65:
            # print("Frontal: abajo")
            brazo_derecho[0] = "abajo"
        elif 105 < angulo:
            # print("Frontal: arriba-izquierda")
            brazo_derecho[0] = "arriba-izquierda"
        elif angulo <= -105:
            # print("Frontal: abajo-izquierda")
            brazo_derecho[0] = "abajo-izquierda"
        else:
            # print("Posición frontal desconocida")
            brazo_derecho[0] = "None"

def definir_posicion_sagital(angulo, brazo):
    # brazo_derecho[2] es posición frontal y brazo_derecho[3] es su código para ESP32
    if (brazo == "derecho"):
        if brazo_derecho[0] != "None" and (brazo_derecho[0] != "arriba-izquierda" and brazo_derecho[0] != "arriba-derecha" and brazo_derecho[0] != "derecha-arriba" and brazo_derecho[0] != "arriba"):
            if -50 >= angulo:
                # print("Sagital: izquierda")
                brazo_derecho[2] = "izquierda"
            elif -5 >= angulo > -50:
                # print("Sagital: frente-izquierda")
                brazo_derecho[2] = "frente-izquierda"
            elif -5 < angulo <= 45:
                # print("Sagital: frente")
                brazo_derecho[2] = "frente"
            elif 45 < angulo <= 75:
                # print("Sagital: frente-derecha")
                brazo_derecho[2] = "frente-derecha"
            elif 75 < angulo <= 95:
                # print("Sagital: derecha")
                brazo_derecho[2] = "derecha"
            elif 95 < angulo:
                # print("Sagital: atras-derecha")
                brazo_derecho[2] = "atras-derecha"
            else:
                # print("Posición sagital desconocida")
                brazo_derecho[2] = "None"
        elif (brazo_derecho[0] != "None"):
            if -60 >= angulo:
                # print("Sagital: izquierda")
                brazo_derecho[2] = "izquierda"
            elif -5 >= angulo > -60:
                # print("Sagital: frente-izquierda")
                brazo_derecho[2] = "frente-izquierda"
            elif -5 < angulo <= 45:
                # print("Sagital: frente")
                brazo_derecho[2] = "frente"
            elif 45 < angulo <= 68:
                # print("Sagital: frente-derecha")
                brazo_derecho[2] = "frente-derecha"
            elif 68 < angulo <= 80:
                print("Sagital: derecha")
                brazo_derecho[2] = "derecha"
            elif 80 < angulo:
                # print("Sagital: atras-derecha")
                brazo_derecho[2] = "atras-derecha"
            else:
                # print("Posición sagital desconocida")
                brazo_derecho[2] = "None"
        # elif (brazo_derecho[0] == "arriba" and brazo_derecho[0] == "abajo"):
        #     print("Si el brazo está arriba o abajo la posición sagital es neutra")
        #     brazo_derecho[2] = "None"
        else:
            # print("Posición sagital desconocida")
            brazo_derecho[2] = "None"

def definir_flexion(angulo, brazo):
    # brazo_derecho[4] es posición flexión y brazo_derecho[5] es su código para ESP32
    if (brazo == "derecho"):
        if 0 <= angulo < 30:
            # print("Flexión: extendido")
            brazo_derecho[4] = "extendido"
            brazo_derecho[5] = str(angulo)
        elif 30 <= angulo < 45:
            # print("Flexión: ligeramente flexionado")
            brazo_derecho[4] = "ligeramente-flexionado"
            brazo_derecho[5] = str(angulo)
        elif 45 <= angulo <= 65:
            # print("Flexión: flexionado")
            brazo_derecho[4] = "flexionado"
            brazo_derecho[5] = str(angulo)
        elif 65 < angulo <= 80:
            # print("Flexión: muy flexionado")
            brazo_derecho[4] = "muy-flexionado"
            brazo_derecho[5] = str(angulo)
        elif angulo > 80:
            # print("Flexión: completamente flexionado")
            brazo_derecho[4] = "completamente-flexionado"
            brazo_derecho[5] = str(angulo)
        else:
            print("Posición de flexión desconocida")
            brazo_derecho[4] = "None"

def definir_rotacion(angulo, brazo):
    # brazo_derecho[6] es posición rotación y brazo_derecho[7] es su código para ESP32
    if (brazo == "derecho"):
        if (brazo_derecho[2] != "None"):
            if (brazo_derecho[2] == "frente" or brazo_derecho[2] == "frente-izquierda"):
                if -10 >= angulo > -50:
                    # print("Rotación: cero")
                    brazo_derecho[6] = "cero"
                elif -50 >= angulo > -80:
                    # print("Rotación: neutro")
                    brazo_derecho[6] = "neutro"
                elif -80 >= angulo >= -110:
                    # print("Rotación: full")
                    brazo_derecho[6] = "full"
                else:
                    print("Posición de rotación desconocida")
                    brazo_derecho[6] = "neutro"
            elif (brazo_derecho[2] == "frente-derecha" or brazo_derecho[2] == "derecha" or brazo_derecho[2] == "izquierda"):
                if -10 <= angulo < 50:
                    # print("Rotación: cero")
                    brazo_derecho[6] = "cero"
                elif -50 < angulo < -10:
                    # print("Rotación: neutro")
                    brazo_derecho[6] = "neutro"
                elif -100 <= angulo <= -50:
                    # print("Rotación: full")
                    brazo_derecho[6] = "full"
                else:
                    print("Posición de rotación desconocida")
                    brazo_derecho[6] = "neutro"
            elif (brazo_derecho[2] == "atras-derecha"):
                print("rota atras")
            else:
                print("el brazo tiene eje z pronunciado")
                

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer el frame.")
        break

    frame = imutils.resize(frame, width=1200)
    height, width, _ = frame.shape
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = holistic.process(frame_rgb)

    if results.pose_world_landmarks:
        # Defino los puntos del cuerpo con sus coordenadas
        punto_pose = results.pose_world_landmarks.landmark
        c_hombro_d = np.array([punto_pose[12].x, punto_pose[12].y, punto_pose[12].z])
        c_hombro_i = np.array([punto_pose[11].x, punto_pose[11].y, punto_pose[11].z])
        c_codo_d = np.array([punto_pose[14].x, punto_pose[14].y, punto_pose[14].z])
        c_codo_i = np.array([punto_pose[13].x, punto_pose[13].y, punto_pose[13].z])
        c_cadera_d = np.array([punto_pose[24].x, punto_pose[24].y, punto_pose[24].z])
        c_cadera_i = np.array([punto_pose[23].x, punto_pose[23].y, punto_pose[23].z])
        c_muneca_d = np.array([punto_pose[16].x, punto_pose[16].y, punto_pose[16].z])
        c_muneca_i = np.array([punto_pose[15].x, punto_pose[15].y, punto_pose[15].z])

        # print("Coordenadas del hombro derecho:", c_hombro_d, "Coordenadas del hombro izquierdo:", c_hombro_i, "Coordenadas del codo derecho:", c_codo_d, "Coordenadas de la cadera derecha:", c_cadera_d, "Coordenadas de la muñeca derecha:", c_muneca_d)

        # Defino los vectores necesarios HOMBRO DERECHO
            # vector móvil (brazo)
        v_antebrazo_d = normalizar_vector(c_muneca_d - c_codo_d)
        v_brazo_d = normalizar_vector(c_codo_d - c_hombro_d)
            # plano vertical
        v_vertical_abajo_d = normalizar_vector(c_cadera_d - c_hombro_d)
            # plano frontal
        v_frontal_dentro_d = normalizar_vector(c_hombro_i - c_hombro_d)
            # plano sagital
        v_sagital_delante_d = normalizar_vector(np.cross(v_vertical_abajo_d, v_frontal_dentro_d))
        v_sagital_atras_d = normalizar_vector(np.cross(v_frontal_dentro_d, v_vertical_abajo_d))
            # plano frontal
        v_frontal_fuera_d = normalizar_vector(np.cross(v_vertical_abajo_d, v_sagital_delante_d))
            # plano vertical
        v_vertical_arriba_d = normalizar_vector(np.cross(v_frontal_fuera_d, v_sagital_delante_d))

            #FLEXIÓN ENTRE BRAZO Y ANTEBRAZO DERECHO
            # Calculo el angulo de flexion 0 = extendido (apuntan a la misma dirección), 180 = flexionado (apunta a direcciones distintas)
        angulo_flexion_d = calcular_angulo_flexion(v_brazo_d, v_antebrazo_d)
        definir_flexion(angulo_flexion_d, "derecho")

            #PLANO SAGITAL
            # Calculo de proyecciones escalares en el plano SAGITAL
        componente_vertical_s = np.dot(v_brazo_d, v_vertical_abajo_d)
        componente_sagital_s = np.dot(v_brazo_d, v_sagital_delante_d)

        # IMPORTANTE: El orden correcto es (sagital, vertical)
        angulo_sagital_d = calcular_angulo(componente_sagital_s, componente_vertical_s)


            #PLANO FRONTAL 
            # Calculo de proyecciones escalares en el plano FRONTAL
        # Componentes en el plano frontal

        componente_vertical_f = np.dot(v_brazo_d, v_vertical_abajo_d)
        componente_lateral_f = np.dot(v_brazo_d, v_frontal_dentro_d)

        # IMPORTANTE: El orden correcto es (lateral, vertical) para que 90° sea la T-pose
        angulo_frontal_d = calcular_angulo(componente_lateral_f, componente_vertical_f)

        # Ajustar para que sea más intuitivo:
        # Negativo hacia el cuerpo, Positivo alejándose
        angulo_frontal_d = -angulo_frontal_d

        # Normalizar al rango anatómico esperado (0° = abajo, 90° = T-pose, 180° = arriba)
        if angulo_frontal_d < -90:
            angulo_frontal_d = 180 + (angulo_frontal_d + 90)
            

            #PLANO TRANSVERSAL/SAGITAL
            # Va a actuar dependiendo de si hay una mínima flexión del codo
            ##############################################################################
        if brazo_derecho[4] != "extendido" and brazo_derecho[4] != "None":
            z_local = v_brazo_d
            componente_gravedad_brazo = np.dot(v_vertical_abajo_d, z_local)
            y_local = v_vertical_abajo_d - componente_gravedad_brazo * z_local
            y_local = normalizar_vector(y_local)
            x_local = normalizar_vector(np.cross(y_local, z_local))
            componente_x = np.dot(v_antebrazo_d, x_local)
            componente_y = np.dot(v_antebrazo_d, y_local)
            angulo_rotacion_d = np.degrees(np.arctan2(componente_x, componente_y))
        else:
            angulo_rotacion_d = 0

        if angulo_flexion_d < 20:
            # Verificar alineación real
            producto_punto = np.dot(v_brazo_d, v_antebrazo_d)
            if producto_punto < 0.95:  # No están bien alineados (cos(18°) ≈ 0.95)
                # Recalcular el ángulo tomando el valor absoluto del producto punto
                angulo_flexion_d = np.degrees(np.arccos(np.abs(producto_punto)))

        print(f"sagital {angulo_sagital_d:.2f}, frontal {angulo_frontal_d:.2f}, biceps {angulo_flexion_d:.2f}, rotacion {angulo_rotacion_d:.2f}")

            ##############################################################################
        # if brazo_derecho[4] != "extendido" and brazo_derecho[4] != "None":
        #     # Vector perpendicular móvil (normal al plano brazo-antebrazo)
        #     v_perp_movil_d = normalizar_vector(np.cross(v_brazo_d, v_antebrazo_d))
            
        #     # Proyectar sobre el plano transversal (remover componente vertical)
        #     componente_vertical_perp = np.dot(v_perp_movil_d, v_vertical_abajo_d)
        #     v_perp_proyectado = v_perp_movil_d - componente_vertical_perp * v_vertical_abajo_d
        #     v_perp_proyectado = normalizar_vector(v_perp_proyectado)
            
        #     # Calcular ángulo en el plano transversal usando referencias fijas
        #     componente_sagital_rot = np.dot(v_perp_proyectado, v_sagital_delante_d)
        #     componente_frontal_rot = np.dot(v_perp_proyectado, v_frontal_fuera_d)
            
        #     angulo_rotacion_d = calcular_angulo(componente_frontal_rot, componente_sagital_rot)
        #     # definir_rotacion(angulo_rotacion_d, "derecho")
        # # if brazo_derecho[4] != "extendido" and brazo_derecho[4] != "None":
        # #     v_vertical_abajo_d = normalizar_vector(c_cadera_d - c_hombro_d)
        # #         # vector perpendicular móvil
        # #     v_perp_movil_d = normalizar_vector(np.cross(v_brazo_d, v_antebrazo_d))
        # #         # vector de referencia
        # #     v_ref_vertical_d = normalizar_vector(np.cross(v_brazo_d, v_vertical_abajo_d))
        # #     v_ref_horizontal_d = normalizar_vector(np.cross(v_brazo_d, v_ref_vertical_d))
        # #         # Calculo de proyecciones escalares
        # #     componente_vertical_d_r = np.dot(v_perp_movil_d, v_ref_vertical_d)
        # #     componente_horizontal_d_r = np.dot(v_perp_movil_d, v_ref_horizontal_d)
        # #         # Calculo el angulo de rotación
        # #     angulo_rotacion_d = calcular_angulo(componente_vertical_d_r, componente_horizontal_d_r)
        # #     # print(f"Ángulo de rotación derecho: {angulo_rotacion_d:.2f} grados")
        # #     # definir_rotacion(angulo_rotacion_d, "derecho")
        # else:
        #     #configurar un vector entre la muñeca y el pulgar, y entre la muñeca y el meñique
        #     #con esos vectores voy a usar las mismas refrerencias anteriores, si sale como quiero el pulgar al apuntas al vector vertical (70 a 110 grados) está mostrando la palma y si esta al contrario (-70 a -110) está mostrando el dorso. 
        #     angulo_rotacion_d = 0
        #     # print(f"Brazo extendido rotacion: {angulo_rotacion_d:.2f} grados")

        # print("sagital", angulo_sagital_d, ", frontal", angulo_frontal_d, ", biceps", angulo_flexion_d, ", rotacion", angulo_rotacion_d)














        #     #PLANO FRONTAL 
        #     # Calculo de proyecciones escalares en el plano FRONTAL
        # componente_vertical_d_f = np.dot(v_brazo_d, v_vertical_arriba_d)
        # componente_frontal_d_f =np.dot(v_brazo_d, v_frontal_fuera_d)
        #     # Calculo el angulo del plano FRONTAL
        # angulo_frontal_d = calcular_angulo(componente_vertical_d_f, componente_frontal_d_f)
        # # print(f"Ángulo frontal derecho: {angulo_frontal_d:.2f} grados")
        #     # Segun el angulo defino la posicion
        # definir_posicion_frontal(angulo_frontal_d, "derecho")

        #     #PLANO SAGITAL
        #     # Calculo de proyecciones escalares en el plano SAGITAL
        # componente_frontal_d_s = np.dot(v_brazo_d, v_frontal_fuera_d)
        # componente_sagital_d_s = np.dot(v_brazo_d, v_sagital_delante_d)
        #     # Calculo el angulo del plano SAGITAL
        # angulo_sagital_d = calcular_angulo(componente_frontal_d_s, componente_sagital_d_s)
        # # print(f"Ángulo sagital derecho: {angulo_sagital_d:.2f} grados")
        #     # Segun el angulo defino la posicion
        # definir_posicion_sagital(angulo_sagital_d, "derecho")

        # #FLEXIÓN ENTRE BRAZO Y ANTEBRAZO DERECHO 
        #     # Defino los vectores necesarios para FLEXIÓN
        # v_antebrazo_d = normalizar_vector(c_muneca_d - c_codo_d)
        # v_brazo_d = normalizar_vector(c_codo_d - c_hombro_d)
        #     # Calculo el angulo de flexion 0 = extendido (apuntan a la misma dirección), 180 = flexionado (apunta a direcciones distintas)
        # angulo_flexion_d = calcular_angulo_flexion(v_brazo_d, v_antebrazo_d)
        # # print(f"Ángulo de flexión del codo derecho: {angulo_flexion_d:.2f} grados")
        #     # Segun el angulo defino la posicion
        # definir_flexion(angulo_flexion_d, "derecho")

        #     #PLANO TRANSVERSAL/SAGITAL
        #     # Va a actuar dependiendo de si hay una mínima flexión del codo
        # if brazo_derecho[4] != "extendido" and brazo_derecho[4] != "None":
        #     # Defino los vectores necesarios para la rotación por flexion
        #         # vector antebrazo (perpendicular a brazo para evitar problemas al estar más flexionado o menos flexionado)
        #     # v_antebrazo_perp_d = calcular_vector_perpendicular(v_brazo_d, v_antebrazo_d)
        #         # vector plano vertical
        #     v_vertical_abajo_d = normalizar_vector(c_cadera_d - c_hombro_d)
        #         # vector perpendicular móvil
        #     v_perp_movil_d = normalizar_vector(np.cross(v_brazo_d, v_antebrazo_d))
        #     # v_perp_movil_d = normalizar_vector(np.cross(v_brazo_d, v_antebrazo_perp_d))
        #         # vector de referencia
        #     v_ref_vertical_d = normalizar_vector(np.cross(v_brazo_d, v_vertical_abajo_d))
        #     v_ref_horizontal_d = normalizar_vector(np.cross(v_brazo_d, v_ref_vertical_d))
        #         # Calculo de proyecciones escalares
        #     componente_vertical_d_r = np.dot(v_perp_movil_d, v_ref_vertical_d)
        #     componente_horizontal_d_r = np.dot(v_perp_movil_d, v_ref_horizontal_d)
        #         # Calculo el angulo de rotación
        #     angulo_rotacion_d = calcular_angulo(componente_vertical_d_r, componente_horizontal_d_r)
        #     # print(f"Ángulo de rotación del hombro derecho: {angulo_rotacion_d:.2f} grados")
        #     definir_rotacion(angulo_rotacion_d, "derecho")
        # else:
        #     #configurar un vector entre la muñeca y el pulgar, y entre la muñeca y el meñique
        #     #con esos vectores voy a usar las mismas refrerencias anteriores, si sale como quiero el pulgar al apuntas al vector vertical (70 a 110 grados) está mostrando la palma y si esta al contrario (-70 a -110) está mostrando el dorso. 
        #     angulo_rotacion_d = 0
        # print("brazo derecho", brazo_derecho)

    cv2.imshow("Frame", frame)
    # Salir si se presiona ESC o si la ventana fue cerrada
    if cv2.waitKey(1) & 0xFF == 27 or cv2.getWindowProperty("Frame", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()

