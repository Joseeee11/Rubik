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
def enviar_ESP(codigo):
    # if serialESP32.is_open:
    #     # Envía el número como dos bytes (big endian)
    #     serialESP32.write(codigo.to_bytes(2, byteorder='big'))
    #     print(f"Mensaje enviado: {codigo}")
    # else:
    #     print("Error: No se pudo abrir el puerto serie.")
    print("")

angulos_promedio_mld = []
angulos_promedio_mfd = []
angulos_promedio_mfcd = []
ultimo_movimiento_mld = "ninguno"  # para evitar enviar mensajes repetidos
ultimo_movimiento_mfd = "ninguno"
ultimo_movimiento_mfcd = "ninguno"

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo leer el frame.")
        break

    frame = imutils.resize(frame, width=1200)
    height, width, _ = frame.shape
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = holistic.process(frame_rgb)

    if result.pose_landmarks is not None:
        drawing.draw_landmarks(
            frame,
            result.pose_landmarks,
            mediaPipe.POSE_CONNECTIONS,
            landmark_drawing_spec=drawing_styles.get_default_pose_landmarks_style()
        )
        coord_pose = result.pose_world_landmarks.landmark

        #coordenadas de cada punto
        coord_hombro_derecho = np.array([coord_pose[12].x, coord_pose[12].y, coord_pose[12].z])
        coord_hombro_izquierdo = np.array([coord_pose[11].x, coord_pose[11].y, coord_pose[11].z])
        coord_codo_derecho = np.array([coord_pose[14].x, coord_pose[14].y, coord_pose[14].z])
        coord_codo_izquierdo = np.array([coord_pose[13].x, coord_pose[13].y, coord_pose[13].z])
        coord_cadera_derecha = np.array([coord_pose[24].x, coord_pose[24].y, coord_pose[24].z])
        coord_cadera_izquierda = np.array([coord_pose[23].x, coord_pose[23].y, coord_pose[23].z])
        coord_muneca_derecha = np.array([coord_pose[16].x, coord_pose[16].y, coord_pose[16].z])
        coord_muneca_izquierda = np.array([coord_pose[15].x, coord_pose[15].y, coord_pose[15].z])

        
        # Funciones para determinados calculos
        def normalizar_vector(vector):
            norma = np.linalg.norm(vector)
            if norma < 1e-6:   # 1e-6 es 0.000001, para evitar división por cero
                return vector
            return vector / norma
        
        def calcular_angulo(componente1, componente2):
            if componente1 == 0 and componente2 == 0:
                return 0
            # aplicaré la funcion "atan2" arcotangente de dos argumentos para obtener el ángulo
            angulo_radianes = np.arctan2(componente1, componente2)
            angulo_grados = int(np.degrees(angulo_radianes))
            return angulo_grados
        

        # MOVIMIENTO DE HOMBRO DERECHO
        # np.linalg.norm normalizo vector - np.cross producto cruzado - np.dot producto punto o escalar

        # Vectores predeterminados
        vector_y = np.array([0.0, 1.0, 0.0])  # Vector predeterminado vertical
        vector_x = np.array([1.0, 0.0, 0.0])  # Vector predeterminado horizontal
        vector_z = np.array([0.0, 0.0, 1.0])  # Vector predeterminado de profundidad

        # Vectores definidos y con sus normalizados
        vector_1_derecha = coord_codo_derecho - coord_hombro_derecho #vector de hombro derecho a codo derecho
        vector_1_derecha_norm = normalizar_vector(vector_1_derecha) #normalizo el vector 1
        vector_2_derecha = coord_cadera_derecha - coord_hombro_derecho #vector de cadera derecha a hombro derecho
        vector_2_derecha_norm = normalizar_vector(vector_2_derecha) #normalizo el vector 2
        vector_3_derecha = coord_hombro_izquierdo - coord_hombro_derecho #vector de hombro izquierdo a hombro derecho
        vector_3_derecha_norm = normalizar_vector(vector_3_derecha) #normalizo el vector 3
        vector_6_derecha = coord_muneca_derecha - coord_codo_derecho #vector de codo derecho a muñeca derecha
        vector_6_derecha_norm = normalizar_vector(vector_6_derecha) #normalizo el vector 6
        

        # Vectores Perpendiculares y con sus normalizados
        vector_4_derecha = np.cross(vector_2_derecha, vector_3_derecha) #vector perpendicular (por medio de producto cruz) de cadera derecha a hombro derecho y hombro izquierdo a hombro derecho
        vector_4_derecha_norm = normalizar_vector(vector_4_derecha) #normalizo el vector 4
        vector_5_derecha = np.cross(vector_2_derecha, vector_4_derecha_norm) #vector perpendicular (por medio de producto cruz) de vector 4 y hombro a cadera derecha
        vector_5_derecha_norm = normalizar_vector(vector_5_derecha) #normalizo el vector 5


        # Primer movimiento: Movimiento Elevación Lateral del Hombro Derecho = mld
        # en este primer movimiento solo quiero saber si el brazo esta arriba o abajo y a la derecha o a la izquierda, es decir lo veré "como en un plano 2D" donde tome en cuenta solo X y Y

        #componentes para calcular el angulo de elevacion lateral
        componente_vertical_mld = vector_1_derecha_norm[1] # el eje Y del vector 1
        componente_horizontal_mld = np.dot(vector_1_derecha_norm, vector_3_derecha_norm)
              #con el componente vertical se sabe si el brazo esta arriba o abajo, y con el componente horizontal se sabe si el brazo esta a la derecha o izquierda

        # calcular el ángulo del movimiento lateral del hombro derecho
        angulo_mld_grados = calcular_angulo(componente_vertical_mld, componente_horizontal_mld)
        angulos_promedio_mld.append(angulo_mld_grados)

        # print("angulo lateral", angulo_mld_grados)

        # promedio de los ángulos para evitar mandar muchos mensajes al ESP32
        # if len(angulos_promedio_mld) > 10:
        #     promedio_total_mld = int(np.mean(angulos_promedio_mld))
        #     print("Promedio total MLD:", promedio_total_mld)
        #     # rango para servo, comando 4100 al 4199 para movimiento lateral del hombro derecho
        #     if promedio_total_mld > -130 and promedio_total_mld <= -100:
        #         print("brazo lateralmente hacia arriba")
        #         if ultimo_movimiento_mld != "arriba":
        #             enviar_ESP(4110)
        #             ultimo_movimiento_mld = "arriba"
        #     elif promedio_total_mld > -100 and promedio_total_mld <= -50:
        #         print("brazo lateralmente hacia arriba medio izquierda")
        #         if ultimo_movimiento_mld != "arriba_medio_izquierda":
        #             ultimo_movimiento_mld = "arriba_medio_izquierda"
        #             enviar_ESP(4115)
        #     elif promedio_total_mld > -50 and promedio_total_mld <= 30:  # IMPOSIBLE
        #         print("brazo lateralmente hacia izquierda")
        #         if ultimo_movimiento_mld != "izquierda":
        #             ultimo_movimiento_mld = "izquierda"
        #             enviar_ESP(4120)
        #     elif promedio_total_mld > 30  and promedio_total_mld <= 70: # IMPOSIBLE
        #         print("brazo lateralmente hacia izquierda medio abajo")
        #         if ultimo_movimiento_mld != "izquierda_medio_abajo":
        #             ultimo_movimiento_mld = "izquierda_medio_abajo"
        #             enviar_ESP(4125)
        #     elif promedio_total_mld > 70  and promedio_total_mld <= 95: # IMPOSIBLE
        #         print("brazo lateralmente hacia abajo medio izquierda")
        #         if ultimo_movimiento_mld != "abajo_medio_izquierda":
        #             ultimo_movimiento_mld = "abajo_medio_izquierda"
        #             enviar_ESP(4130)
        #     elif promedio_total_mld > 95  and promedio_total_mld <= 115:
        #         print("brazo lateralmente hacia abajo")
        #         if ultimo_movimiento_mld != "abajo":
        #             ultimo_movimiento_mld = "abajo"
        #             enviar_ESP(4135)           
        #     elif promedio_total_mld > 115  and promedio_total_mld <= 130:
        #         print("brazo lateralmente hacia abajo medio derecha")
        #         if ultimo_movimiento_mld != "abajo_medio_derecha":
        #             ultimo_movimiento_mld = "abajo_medio_derecha"
        #             enviar_ESP(4140)  
        #     elif promedio_total_mld > 130  and promedio_total_mld <= 160:
        #         print("brazo lateralmente hacia derecha medio abajo")
        #         if ultimo_movimiento_mld != "derecha_medio_abajo":
        #             ultimo_movimiento_mld = "derecha_medio_abajo"
        #             enviar_ESP(4145)   
        #     elif promedio_total_mld > 160  or promedio_total_mld <= -160:
        #         print("brazo lateralmente hacia derecha")
        #         if ultimo_movimiento_mld != "derecha":
        #             ultimo_movimiento_mld = "derecha"
        #             enviar_ESP(4150)  
        #     elif promedio_total_mld > -160  and promedio_total_mld <= -150:
        #         print("brazo lateralmente hacia derecha medio arriba")
        #         if ultimo_movimiento_mld != "derecha_medio_arriba":
        #             ultimo_movimiento_mld = "derecha_medio_arriba"
        #             enviar_ESP(4155)  
        #     elif promedio_total_mld > -150 and promedio_total_mld <= -130:
        #         print("brazo lateralmente hacia arriba medio derecha")
        #         if ultimo_movimiento_mld != "arriba_medio_derecha":
        #             ultimo_movimiento_mld = "arriba_medio_derecha"
        #             enviar_ESP(4160)

        #     angulos_promedio_mld = []  # Reiniciar la lista después de enviar el mensaje


        # Segundo movimiento: Movimiento Frontal del Hombro Derecho = mfd

        # componentes para calcular el ángulo frontal
        componente_horizontal_mfd = np.dot(vector_1_derecha_norm, vector_3_derecha_norm) # el frontal
        componente_profundidad_mfd = vector_1_derecha_norm[2] # el lateral

        # calcular el ángulo del movimiento frontal del hombro derecho
        angulo_mfd_grados = calcular_angulo(componente_profundidad_mfd, componente_horizontal_mfd)
        angulos_promedio_mfd.append(angulo_mld_grados)

        print("comoponente profundidad", componente_profundidad_mfd)
        # print("angulo frontal", angulo_mfd_grados)

        # if len(angulos_promedio_mfd) > 10:
        #     promedio_total_mfd = np.mean(angulos_promedio_mfd)
        #     # rango para servo, comando 4200 al 4299 para movimiento lateral del hombro derecho

        #     if ultimo_movimiento_mld != "ninguno" and ultimo_movimiento_mld != "arriba" and ultimo_movimiento_mld != "abajo":
        #         if ultimo_movimiento_mld == "abajo_medio_derecha" or ultimo_movimiento_mld == "derecha_medio_abajo" or ultimo_movimiento_mld == "izquierda_medio_abajo" or ultimo_movimiento_mld == "abajo_medio_izquierda":
        #             if promedio_total_mfd > 20 and promedio_total_mfd <= 50:
        #                 print("brazo hacia frente")
        #                 if ultimo_movimiento_mfd != "frente":
        #                     enviar_ESP(4210)
        #                     ultimo_movimiento_mfd = "frente"
        #             elif promedio_total_mfd > 50 and promedio_total_mfd <= 80:
        #                 print("brazo hacia frente derecha")
        #                 if ultimo_movimiento_mfd != "frente_derecha":
        #                     ultimo_movimiento_mfd = "frente_derecha"
        #                     enviar_ESP(4215)
        #         elif ultimo_movimiento_mld == "arriba_medio_derecha" or ultimo_movimiento_mld == "derecha_medio_arriba" or ultimo_movimiento_mld == "izquierda_medio_arriba" or ultimo_movimiento_mld == "arriba_medio_izquierda":
        #             if promedio_total_mfd > 20 and promedio_total_mfd <= 40:
        #                 print("brazo hacia frente")
        #                 if ultimo_movimiento_mfd != "frente":
        #                     enviar_ESP(4210)
        #                     ultimo_movimiento_mfd = "frente"
        #             elif promedio_total_mfd > 40 and promedio_total_mfd <= 80:
        #                 print("brazo hacia frente derecha")
        #                 if ultimo_movimiento_mfd != "frente_derecha":
        #                     ultimo_movimiento_mfd = "frente_derecha"
        #                     enviar_ESP(4215)
        #         elif ultimo_movimiento_mld == "derecha" or ultimo_movimiento_mld == "izquierda":
        #             if promedio_total_mfd > 40 and promedio_total_mfd <= 50:
        #                 print("brazo hacia frente")
        #                 if ultimo_movimiento_mfd != "frente":
        #                     enviar_ESP(4210)
        #                     ultimo_movimiento_mfd = "frente"
        #             elif promedio_total_mfd > 50 and promedio_total_mfd <= 80:
        #                 print("brazo hacia frente derecha")
        #                 if ultimo_movimiento_mfd != "frente_derecha":
        #                     ultimo_movimiento_mfd = "frente_derecha"
        #                     enviar_ESP(4215) 

        #         if promedio_total_mfd > 80 and promedio_total_mfd <= 100:
        #             print("brazo hacia derecha, no hay extensión horizontal")
        #             if ultimo_movimiento_mfd != "derecha":
        #                 ultimo_movimiento_mfd = "derecha"
        #                 enviar_ESP(4220)
        #         # no probados, pero por lógica
        #         elif promedio_total_mfd > 100 and promedio_total_mfd <= 180:
        #             print("brazo hacia atras derecha")
        #             if ultimo_movimiento_mfd != "atras_derecha":
        #                 ultimo_movimiento_mfd = "atras_derecha"
        #                 enviar_ESP(4225)
        #         elif promedio_total_mfd > -180 and promedio_total_mfd <= -100:
        #             print("brazo hacia atras")
        #             if ultimo_movimiento_mfd != "atras":
        #                 ultimo_movimiento_mfd = "atras"
        #                 enviar_ESP(4230)
        #         elif promedio_total_mfd > -100 and promedio_total_mfd <= -80:
        #             print("brazo hacia izquierda, no hay extensión horizontal")
        #             if ultimo_movimiento_mfd != "izquierda":
        #                 ultimo_movimiento_mfd = "izquierda"
        #                 enviar_ESP(4235)
        #         elif promedio_total_mfd > -80 and promedio_total_mfd >= 20:
        #             print("brazo hacia frente izquierda")
        #             if ultimo_movimiento_mfd != "frente_izquierda":
        #                 ultimo_movimiento_mfd = "frente_izquierda"
        #                 enviar_ESP(4240)
        #     else:
        #         print("No hay extensión horizontal, esta a la derecha")
        #         if ultimo_movimiento_mfd != "derecha":
        #             ultimo_movimiento_mfd = "derecha"
        #             enviar_ESP(4220) 
            
        #     angulos_promedio_mfd = []  # Reiniciar la lista después de enviar el mensaje


        # Tercer Movimiento: Flexion de Codo Derecho = mfcd
        # en este aplicaré el calculo de angulos entre dos vectores, el vector 1 y el vector 6, para saber si el codo esta flexionado o estirado

        # hallar varaibles de la formula = coseno es igual al producto punto de dos vectores entre la magnitud uno por la del otro
        producto_vectores_mfcd = np.dot(vector_1_derecha, vector_6_derecha)
        magnitud_vector_1_mfcd = np.linalg.norm(vector_1_derecha)
        magnitud_vector_6_mfcd = np.linalg.norm(vector_6_derecha)

        #calcular angulo con el coseno
        if magnitud_vector_1_mfcd < 1e-6 or magnitud_vector_6_mfcd < 1e-6:
            angulo_mfcd_grados = 0
            # print("angulo flexion codo", angulo_mfcd_grados)  #0 extendido, 180 flexionado
        else:
            coseno_mfcd = producto_vectores_mfcd / (magnitud_vector_1_mfcd * magnitud_vector_6_mfcd)
            coseno_mfcd = np.clip(coseno_mfcd, -1.0, 1.0)  # Asegurar que el coseno esté en el rango válido
            angulo_mfcd_radianes = np.arccos(coseno_mfcd)
            angulo_mfcd_grados = np.degrees(angulo_mfcd_radianes)

        angulos_promedio_mfcd.append(angulo_mfcd_grados)
        print("angulo flexion codo", angulo_mfcd_grados)  #0 extendido, 180 flexionado


        # if len(angulos_promedio_mfcd) > 10:
        #     promedio_total_mfcd = np.mean(angulos_promedio_mfcd)
        #     # rango para servo, comando 4300 al 4399 para movimiento lateral del hombro derecho
        #     if promedio_total_mfcd < 30:
        #         print("codo extendido")
        #         if ultimo_movimiento_mfcd != "extendido":
        #             ultimo_movimiento_mfcd = "extendido"
        #             enviar_ESP(4310)
        #     elif promedio_total_mfcd >= 30 and promedio_total_mfcd < 80:
        #         print("codo medio flexionado")
        #         if ultimo_movimiento_mfcd != "medio_flexionado":
        #             ultimo_movimiento_mfcd = "medio_flexionado"
        #             enviar_ESP(4320)
        #     elif promedio_total_mfcd >= 80 and promedio_total_mfcd < 180:
        #         print("codo flexionado")
        #         if ultimo_movimiento_mfcd != "flexionado":
        #             ultimo_movimiento_mfcd = "flexionado"
        #             enviar_ESP(4330)
            
        #     angulos_promedio_mfcd = []  # Reiniciar la lista después de enviar el mensaje



    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # Presiona ESC para salir
        break

cap.release()
cv2.destroyAllWindows()

