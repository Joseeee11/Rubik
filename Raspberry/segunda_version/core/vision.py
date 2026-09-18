import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision as mp_vision
import time

class MotorDeVision:
    def __init__(self, 
                 ruta_modelo_cara, 
                 ruta_modelo_pose, 
                 ruta_modelo_manos,
                 callback_cara, 
                 callback_pose, 
                 callback_manos):
        
        """
        Inicializa los 3 modelos de MediaPipe cargándolos en RAM de una sola vez.
        Requiere las rutas de los archivos .task y las funciones (callbacks) 
        que recibirán los resultados.
        """
        
        # ==========================================
        # 1. CONFIGURACIÓN DEL MODELO DE CARA
        # ==========================================
        base_options_face = mp_tasks.BaseOptions(model_asset_path=ruta_modelo_cara)
        options_face = mp_vision.FaceLandmarkerOptions(
            base_options=base_options_face,
            running_mode=mp_vision.RunningMode.LIVE_STREAM,
            output_face_blendshapes=True, # Necesario para detectar la boca abierta/cerrada
            result_callback=callback_cara
        )
        self.face_landmarker = mp_vision.FaceLandmarker.create_from_options(options_face)

        # ==========================================
        # 2. CONFIGURACIÓN DEL MODELO DE CUERPO (POSE)
        # ==========================================
        base_options_pose = mp_tasks.BaseOptions(model_asset_path=ruta_modelo_pose)
        options_pose = mp_vision.PoseLandmarkerOptions(
            base_options=base_options_pose,
            running_mode=mp_vision.RunningMode.LIVE_STREAM,
            result_callback=callback_pose
        )
        self.pose_landmarker = mp_vision.PoseLandmarker.create_from_options(options_pose)

        # ==========================================
        # 3. CONFIGURACIÓN DEL MODELO DE MANOS
        # ==========================================
        base_options_hand = mp_tasks.BaseOptions(model_asset_path=ruta_modelo_manos)
        options_hand = mp_vision.HandLandmarkerOptions(
            base_options=base_options_hand,
            running_mode=mp_vision.RunningMode.LIVE_STREAM,
            num_hands=2, # Queremos detectar ambas manos
            result_callback=callback_manos
        )
        self.hand_landmarker = mp_vision.HandLandmarker.create_from_options(options_hand)

    def procesar_frame(self, frame_rgb, modo_vision):
        """
        Recibe un frame de la cámara y lo envía solo a los modelos necesarios,
        ahorrando CPU (Soft Switching).
        
        :param frame_rgb: Imagen en formato RGB (array de numpy)
        :param modo_vision: String ("Cara", "Cuerpo", "Mano", "Todo", None)
        """
        if modo_vision is None:
            return # Si no hay nada que seguir o imitar, no gastamos CPU

        # MediaPipe requiere su propio formato de imagen
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Se requiere un timestamp único para cada frame en modo LIVE_STREAM
        timestamp_ms = int(time.time() * 1000)

        # Enviamos la imagen solo a los modelos que lo requieran según el estado
        if modo_vision in ["Cara", "Todo"]:
            self.face_landmarker.detect_async(mp_image, timestamp_ms)
            
        if modo_vision in ["Cuerpo", "Todo"]:
            self.pose_landmarker.detect_async(mp_image, timestamp_ms)
            
        if modo_vision in ["Mano", "Mano izquierda", "Mano derecha", "Todo"]:
            self.hand_landmarker.detect_async(mp_image, timestamp_ms)

    def cerrar_modelos(self):
        """
        Libera la memoria RAM. Útil cuando se cierra el programa principal.
        """
        self.face_landmarker.close()
        self.pose_landmarker.close()
        self.hand_landmarker.close()