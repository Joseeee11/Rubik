import pyaudio

p = pyaudio.PyAudio()
print("🎤 Micrófonos detectados por PyAudio:\n")

for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    # Filtramos para mostrar solo los que tienen entrada (input)
    if dev.get('maxInputChannels') > 0:
        print(f"ID [{i}] - {dev.get('name')}")
        
p.terminate()