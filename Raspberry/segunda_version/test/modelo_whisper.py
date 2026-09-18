import whisper

print("Iniciando carga/descarga del modelo Whisper 'base'...")
# Esta es la línea que detona la descarga la primera vez
modelo = whisper.load_model("base") 

print("✅ ¡El modelo está en tu computadora y listo para usarse!")