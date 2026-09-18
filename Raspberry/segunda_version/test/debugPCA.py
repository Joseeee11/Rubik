import serial
import time

# ==========================================
# CONFIGURACIÓN
# ==========================================
NUM_MOTORES = 16
HEADER = b'\xAA\x55'
BAUDRATE = 921600

# Cambia esto por tu puerto (ej. "COM3" en Windows, o "/dev/ttyUSB0" en Linux/Mac)
PUERTO = "COM6" 

def enviar_angulos(puerto_serial, angulos):
    """Construye y envía el paquete binario al ESP32."""
    # Convertimos la lista de enteros a bytes y le sumamos el header
    payload = HEADER + bytes(angulos)
    puerto_serial.write(payload)

def main():
    print(f"Intentando conectar al puerto {PUERTO} a {BAUDRATE} baudios...")
    
    try:
        # Abrimos conexión serial
        ser = serial.Serial(PUERTO, BAUDRATE, timeout=1)
        time.sleep(2) # Esperamos 2 segundos a que el ESP32 se reinicie tras conectar
        
        # Limpiamos cualquier mensaje viejo que haya quedado en el buffer
        ser.reset_input_buffer()
        print("\n¡Conexión exitosa!")
        
        # Inicializamos todos los motores en 90 grados (centro)
        estado_motores = [90] * NUM_MOTORES
        enviar_angulos(ser, estado_motores)
        print("Todos los motores han sido centrados a 90°.")
        
        print("\n--- MODO DEBUG DE MOTORES ---")
        print("Instrucciones:")
        print("- Escribe 'motor,grados' para mover. Ejemplo: 1,45 (Mueve el motor 1 a 45°)")
        print("- Escribe 'q' para salir.")
        
        while True:
            comando = input("\nComando (motor,grados): ")
            
            if comando.lower() == 'q':
                print("Saliendo del debug...")
                break
            
            try:
                # Separar el input por la coma
                partes = comando.split(',')
                if len(partes) != 2:
                    print("❌ Formato incorrecto. Debe ser: numero_motor,grados (Ejemplo: 1,90)")
                    continue
                
                motor_idx = int(partes[0].strip())
                angulo = int(partes[1].strip())
                
                # Validaciones de seguridad
                if not (0 <= motor_idx < NUM_MOTORES):
                    print(f"❌ El motor debe estar entre 0 y {NUM_MOTORES - 1}.")
                    continue
                    
                if not (0 <= angulo <= 180):
                    print("❌ El ángulo debe estar entre 0 y 180.")
                    continue
                
                # Actualizar el array y enviar
                estado_motores[motor_idx] = angulo
                enviar_angulos(ser, estado_motores)
                print(f"✅ Enviado: Motor {motor_idx} -> {angulo}°")
                
                # ── NUEVO: LEER LA RESPUESTA DEL ESP32 ───────────────────────
                # Damos 50 milisegundos para que el ESP32 reciba, procese y responda
                time.sleep(0.05) 
                
                # Si hay datos esperando ser leídos en el buffer de entrada...
                if ser.in_waiting > 0:
                    # Leemos todo, lo decodificamos a texto y evitamos errores de caracteres raros
                    respuesta = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    
                    # Imprimimos la respuesta si no está vacía
                    if respuesta.strip():
                        print(f"🤖 [ESP32 RESPONDE]: {respuesta.strip()}")
                # ─────────────────────────────────────────────────────────────
                
            except ValueError:
                print("❌ Error: Solo se aceptan números separados por coma.")
                
    except serial.SerialException as e:
        print(f"\n❌ Error de conexión: {e}")
        print("Verifica que el puerto sea correcto y que el monitor serie de Arduino esté cerrado.")
        
    finally:
        # Cerramos el puerto al terminar de forma segura
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()