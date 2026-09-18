import cv2
import time
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
import serial
import traceback

model_path = 'Raspberry/segunda_version/tasks/vision/face_landmarker.task'

#CONFIGURACIÓN INICIAL
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
FaceLandmarkerResult = mp.tasks.vision.FaceLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

# Utilidades de dibujo (¡siguen siendo las mismas de la API antigua!)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh

# Variable global para guardar los resultados del modelo de forma asíncrona
resultado_actual = None

puertoCom = "COM6"
baudrate = "921600"
try: 
    esp32= serial.Serial(puertoCom, puertoCom, timeout=0.1)
except:
    print("Error al conectar con el esp32")

def enviar_posiciones(lista_pwm):

    if ser is not None and ser.is_open:

        # lista_pwm debe ser una lista de 30 enteros (0 a 4095)
        # H: unsigned short (2 bytes). 30H significa 30 enteros de 2 bytes.
        # '<' significa Little-Endian
        formato = '<30H' 
        
        datos_binarios = struct.pack(formato, *lista_pwm)
        
        # 0xAA y 0x55 son bytes de inicio para que el ESP32 sepa dónde empieza el mensaje
        paquete = b'\xAA\x55' + datos_binarios
        
        # Podrías agregar un checksum aquí para más seguridad
        esp32.write(paquete)

    else:
        print("Conexión serial no esta abierta")


#FUNCIÓN CALLBACK
def guardar_resultado(result: FaceLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global resultado_actual
    resultado_actual = result
    if result.face_blendshapes:
        print('face face_blendshapes result: {}'.format((result.face_blendshapes[0])[1])) ## el forma ingresa las variables entre las llaves {}
        blendshapes = (result.face_blendshapes[0])
        datosOjos(blendshapes)
    # if result.face_blendshapes and result.face_blendshapes[0] > 0:
        # blendShapes = result.face_blendshapes[0]
        # ojoIzquierdo= 
        # print('El ojo izquierdo: {}'.format(ojoIzquierdo))

""" 
9 - eyeBlinkLe
10 - eyeBlinkRight
11 - eyeLookDownLe
12 - eyeLookDownRight
13 - eyeLookInLe
14 - eyeLookInRight
15 - eyeLookOutLe
16 - eyeLookOutRight
17 - eyeLookUpLe
18 - eyeLookUpRight
19 - eyeSquintLe
20 - eyeSquintRight
21 - eyeWideLe
22 - eyeWideRight 
"""
# blendshapes= [Category(index=1, score=0.2931599020957947, display_name='', category_name='browDownLeft'),Category(index=2, score=0.2931599020957947, display_name='', category_name='browDownLeft')]

ojoIzquierdo = {"9": 0, "19":0, "21":0}


def datosOjos(blendshapes):
    global ojoIzquierdo
    try:
        for elemento in blendshapes:

            key = str(elemento.index)

            if key in ojoIzquierdo:
                print("Pocerntaje de parpadeo: ",elemento.score)
                ojoIzquierdo[key]= elemento.score
    
    except Exception as e:

        print("Errror con datosOjos e: ", e)
        print("--- DETALLE EXACTO DEL ERROR ---")
        traceback.print_exc()
        print("--------------------------------")
    finally: 

        print(f"Blink (9): {ojoIzquierdo['9']:.2f}, Squint (19): {ojoIzquierdo['19']:.2f}, Wide (21): {ojoIzquierdo['21']:.2f}")

    
#INICIALIZAR EL MODELO
options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.LIVE_STREAM, # ¡Modo Video en vivo!
    result_callback=guardar_resultado,           # Conectamos nuestra función
    output_face_blendshapes= True               # Para obtener información de expresiones
)

#BUCLE PRINCIPAL (WEBCAM)
with FaceLandmarker.create_from_options(options) as landmarker:
    # Abrir la webcam (0 es la cámara por defecto)
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        exito, frame = cap.read()
        if not exito:
            print("Ignorando frame vacío de la cámara.")
            continue

        # Voltear el frame horizontalmente para que parezca un espejo
        # ya no xd
        # frame = cv2.flip(frame, 1)

        # OpenCV usa BGR por defecto, MediaPipe necesita RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Enviar el frame al modelo de forma asíncrona (requiere un timestamp en ms)
        timestamp_ms = int(time.time() * 1000)
        landmarker.detect_async(mp_image, timestamp_ms)

        # ==========================================
        # 5. DIBUJAR LOS RESULTADOS
        # ==========================================
        # Si el callback ya recibió datos, los dibujamos sobre el frame
        if resultado_actual is not None and len(resultado_actual.face_landmarks) > 0:
        # 1. Obtenemos los puntos de la PRIMERA cara detectada (índice 0)
            rostro = resultado_actual.face_landmarks[0]
            
            # 2. Obtenemos las dimensiones de tu frame de video
            alto, ancho, _ = frame.shape
            
            # 3. Extraemos el punto 468 (Iris izquierdo) y 473 (Iris derecho)
            iris_izq = rostro[468]
            iris_der = rostro[473]
            
            # 4. Convertimos de coordenadas normalizadas (0.0 - 1.0) a píxeles reales
            px_x_izq = int(iris_izq.x * ancho)
            px_y_izq = int(iris_izq.y * alto)
            
            px_x_der = int(iris_der.x * ancho)
            px_y_der = int(iris_der.y * alto)
            
            # 5. Dibujamos un círculo verde en los iris manualmente con OpenCV
            cv2.circle(frame, (px_x_izq, px_y_izq), 3, (0, 255, 0), -1)
            cv2.circle(frame, (px_x_der, px_y_der), 3, (0, 255, 0), -1)

            for face_landmarks in resultado_actual.face_landmarks:
                
                # Pequeño truco: La nueva API devuelve objetos de Python, pero la herramienta 
                # de dibujo antigua espera un formato "protobuf". Esto hace la conversión rápida:
                face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
                face_landmarks_proto.landmark.extend([
                    landmark_pb2.NormalizedLandmark(x=l.x, y=l.y, z=l.z) for l in face_landmarks
                ])

                # Dibujar la malla facial sobre la imagen original
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks_proto,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
            
            # Depues de dibujar el facemesh se invierte tipo espejo

            frame = cv2.flip(frame, 1)

            ## dibujar rectangulo para porcentaje
            distancia = 0
            for i, elemento in ojoIzquierdo.items():
                distancia+= 50
                cv2.rectangle(frame, pt1= (int(distancia+10),200) , pt2= (int(distancia+20), 200 - int(elemento*200)) , color= (0, 255, 0), thickness= -1)

            esquina_exterior_izq = int(rostro[33].x * ancho)
            esquina_interior_izq = int(rostro[133].x * ancho)
            
            # Calculamos el centro exacto del ojo
            centro_ojo_izq = (esquina_exterior_izq + esquina_interior_izq) / 2
            
            if px_x_izq < centro_ojo_izq - 2: # El "- 2" es un pequeño margen de tolerancia
                cv2.putText(frame, "Mirando a la Izquierda", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            elif px_x_izq > centro_ojo_izq + 2:
                cv2.putText(frame, "Mirando a la Derecha", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            else:
                cv2.putText(frame, "Mirando al Centro", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            ## si no hay cara igual revertir
            frame = cv2.flip(frame, 1)
        
        # Mostrar el resultado final en una ventana
        
        cv2.imshow('Cabeza 2.0 (Utiliza la API TASK)', frame)

        # Presiona la tecla 'ESC' para salir
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Liberar la cámara y cerrar ventanas
    cap.release()
    cv2.destroyAllWindows()

# def draw_landmarks_on_image(rgb_image, detection_result):
#   face_landmarks_list = detection_result.face_landmarks
#   annotated_image = np.copy(rgb_image)

#   # Loop through the detected faces to visualize.
#   for idx in range(len(face_landmarks_list)):
#     face_landmarks = face_landmarks_list[idx]

#     # Draw the face landmarks.


#     drawing_utils.draw_landmarks(
#         image=annotated_image,
#         landmark_list=face_landmarks,
#         connections=vision.FaceLandmarksConnections.FACE_LANDMARKS_TESSELATION,
#         landmark_drawing_spec=None,
#         connection_drawing_spec=drawing_styles.get_default_face_mesh_tesselation_style())
#     drawing_utils.draw_landmarks(
#         image=annotated_image,
#         landmark_list=face_landmarks,
#         connections=vision.FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS,
#         landmark_drawing_spec=None,
#         connection_drawing_spec=drawing_styles.get_default_face_mesh_contours_style())
#     drawing_utils.draw_landmarks(
#         image=annotated_image,
#         landmark_list=face_landmarks,
#         connections=vision.FaceLandmarksConnections.FACE_LANDMARKS_LEFT_IRIS,
#           landmark_drawing_spec=None,
#           connection_drawing_spec=drawing_styles.get_default_face_mesh_iris_connections_style())
#     drawing_utils.draw_landmarks(
#         image=annotated_image,
#         landmark_list=face_landmarks,
#         connections=vision.FaceLandmarksConnections.FACE_LANDMARKS_RIGHT_IRIS,
#           landmark_drawing_spec=None,
#           connection_drawing_spec=drawing_styles.get_default_face_mesh_iris_connections_style())

#   return annotated_image

# def plot_face_blendshapes_bar_graph(face_blendshapes):
#   # Extract the face blendshapes category names and scores.
#   face_blendshapes_names = [face_blendshapes_category.category_name for face_blendshapes_category in face_blendshapes]
#   face_blendshapes_scores = [face_blendshapes_category.score for face_blendshapes_category in face_blendshapes]
#   # The blendshapes are ordered in decreasing score value.
#   face_blendshapes_ranks = range(len(face_blendshapes_names))

#   fig, ax = plt.subplots(figsize=(12, 12))
#   bar = ax.barh(face_blendshapes_ranks, face_blendshapes_scores, label=[str(x) for x in face_blendshapes_ranks])
#   ax.set_yticks(face_blendshapes_ranks, face_blendshapes_names)
#   ax.invert_yaxis()

#   # Label each bar with values
#   for score, patch in zip(face_blendshapes_scores, bar.patches):
#     plt.text(patch.get_x() + patch.get_width(), patch.get_y(), f"{score:.4f}", va="top")

#   ax.set_xlabel('Score')
#   ax.set_title("Face Blendshapes")
#   plt.tight_layout()
#   plt.show()