from groq import Groq

class manejoDeConversacion:

    def __init__(self, system_prompt: str, token: str =None, model: str ="llama-3.1-8b-instant"):
        if not system_prompt:
            raise ValueError("El prompt del sistema no puede estar vacío.")
        self.historial = [{
            "role": "system",
            "content": system_prompt
        }]
        self.model = model 
        self.client = None
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

    def enviarMSG(self, contexto: str, token: str = None):

        if token:
            self.set_token(token)
        if self.client is None:
            raise RuntimeError("Groq client no inicializado. Pase TOKEN en __init__ o en enviar().")
        self.agregar("user", contexto)
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

# Ejemplo de uso:
# manejo = manejoDeConversacion("Eres un robot llamado Zoé...")  Recuerda cambiar el prompt inicial actual, se esta creando el objeto con el prompt del sistema
# manejo.agregar("user", "Hola, ¿cómo estás?")                   Tiene que darle el rol y el mensaje (en este caso del usuario)
# manejo.agregar("assistant", "Hola, estoy bien, gracias.")      Tiene que darle el rol y el mensaje (en este caso del asistente)
# historial_actual = manejo.obtener()                            Así se obtiene el historial completo para enviarlo a la API
# manejo.limpiar()                                               Así se reinicia el historial (aun no creo que se use pero por si acaso ahí está)