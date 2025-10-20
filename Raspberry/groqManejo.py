from groq import Groq

class manejoDeConversacion:

    def __init__(self, system_prompt: str):
        if not system_prompt:
            raise ValueError("El prompt del sistema no puede estar vacío.")
        self.historial = [{
            "role": "system",
            "content": system_prompt
        }]
    
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

    def enviar(self, contexto: str, TOKEN):
        self.agregar("user", contexto)
        # Aquí puedes agregar la lógica para enviar el contexto a la API de Groq
        client = Groq(api_key=TOKEN)
        respuesta = client.chat.completions.create(
            model="groq-1.5-chat",
            messages=self.historial
        )
        mensaje_respuesta = respuesta.choices[0].message['content']
        self.agregar("assistant", mensaje_respuesta)
        return mensaje_respuesta

# Ejemplo de uso:
# manejo = manejoDeConversacion("Eres un robot llamado Zoé...")  Recuerda cambiar el prompt inicial actual, se esta creando el objeto con el prompt del sistema
# manejo.agregar("user", "Hola, ¿cómo estás?")                   Tiene que darle el rol y el mensaje (en este caso del usuario)
# manejo.agregar("assistant", "Hola, estoy bien, gracias.")      Tiene que darle el rol y el mensaje (en este caso del asistente)
# historial_actual = manejo.obtener()                            Así se obtiene el historial completo para enviarlo a la API
# manejo.limpiar()                                               Así se reinicia el historial (aun no creo que se use pero por si acaso ahí está)