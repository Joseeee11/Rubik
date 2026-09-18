from groq import Groq
import base64
from io import BytesIO
from PIL import Image
import cv2

class manejoDeConversacion:

    def __init__(self, system_prompt: str, token: str =None, model: str ="llama-3.1-8b-instant", modelImage: str ="meta-llama/llama-4-scout-17b-16e-instruct"):
        if not system_prompt:
            raise ValueError("El prompt del sistema no puede estar vacío.")
        self.historial = [{
            "role": "system",
            "content": system_prompt
        }]
        self.model = model 
        self.client = None
        self.modelImage = modelImage
        if token:
            self.set_token(token)
    
    def set_token(self, token: str):
        if not token:
            raise ValueError("El token no puede estar vacío.")
        self.client = Groq(api_key=token)

    def agregar(self, role: str, contenido: str):
        if not role or not contenido:
            raise ValueError("El rol y el contenido no pueden estar vacíos.")
        
        if role not in ["user", "assistant", "system"]:
            raise ValueError("El rol debe ser 'user', 'assistant' o 'system'.")
        
        self.historial.append({
            "role": role,
            "content": contenido
        })
    
    def obtener(self):
        return self.historial
    
    def limpiar(self):
        system_message = self.historial[0]
        self.historial.clear()
        self.historial.append(system_message)

    def enviarMSG(self, contexto: str, token: str = None, frameExportado: str = None):
        if token:
            self.set_token(token)
        if self.client is None:
            raise RuntimeError("Groq client no inicializado. Pase TOKEN en __init__ o en enviar().")
        # entorno = self.imagenContexto(token=token, frameExportado=frameExportado)
        # \n Esto es una descripción del entorno del que te encuentras (La siguiente información es subministrada por una IA de reconocimiento de imagen, puede contener algún pequeño detalle que haya omitido) : {entorno} (Esta información es subministrada por IA de reconocimiento)
        self.agregar("user", f"{contexto}. ")

        try:
            respuesta = self.client.chat.completions.create(
                model=self.model,
                messages=self.historial
            )
            mensaje_respuesta = respuesta.choices[0].message.content
            self.agregar("assistant", mensaje_respuesta)
            return mensaje_respuesta
        except Exception as e:
            # Propaga o loggea según prefieras
            raise RuntimeError(f"Error al llamar a la API de Groq: {e}")

    def imagenContexto(self, token: str = None, frameExportado: str = None):

        if self.client is None and token:
            self.set_token(token)
        if self.client is None:
            raise RuntimeError("Groq client no inicializado. Pase TOKEN en __init__ o en enviarMSG().")

        if not frameExportado.shape:
            raise ValueError("frameExportado se encuentra vacío o no es válido.")

        imageBase64 = self.frameToBase64(frameExportado)

        # data_url = f"data:image/png;base64,{imageBase64}"

        # Construir content: texto + objeto image_url (image_url debe ser un objeto)
        # user_content = [
        #     {"type": "text", "text": "Analiza la siguiente imagen y proporciona una descripción detallada y información relevante al entorno como objetos, colores, personas (ropa, expresión. etc)."},
        #     {"type": "image_url", "image_url": {"url": data_url}}
        # ]

        # messages = [
        #     {"role": "user", "content": user_content}
        # ]

        try:
            respuesta = self.client.chat.completions.create(
                model=self.modelImage,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe detalladamente la siguiente imagen, mencionando objetos, colores, personas (ropa, expresión, etc), y cualquier información relevante sobre el entorno."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{imageBase64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100,
            )
            mensaje_respuesta = respuesta.choices[0].message.content
            return mensaje_respuesta
        except Exception as e:
            raise RuntimeError(f"Error al procesar la imagen con la API de Groq: {e}")


    def frameToBase64(self, frame):
        """Recibe un frame (BGR numpy) y devuelve base64 string (sin data:)."""
        if frame is None:
            return None
        try:
            _, buffer = cv2.imencode('.jpg', frame)
            jpeg_bytes = buffer.tobytes()
            base64_encoded_string = base64.b64encode(jpeg_bytes).decode('utf-8')
            return base64_encoded_string
        except Exception as e:
            print("frameToBase64 error:", e)
            return None
# Ejemplo de uso:
# manejo = manejoDeConversacion("Eres un robot llamado Zoé...")  Recuerda cambiar el prompt inicial actual, se esta creando el objeto con el prompt del sistema
# manejo.agregar("user", "Hola, ¿cómo estás?")                   Tiene que darle el rol y el mensaje (en este caso del usuario)
# manejo.agregar("assistant", "Hola, estoy bien, gracias.")      Tiene que darle el rol y el mensaje (en este caso del asistente)
# historial_actual = manejo.obtener()                            Así se obtiene el historial completo para enviarlo a la API
# manejo.limpiar()                                               Así se reinicia el historial (aun no creo que se use pero por si acaso ahí está)