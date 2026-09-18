import serial
import time

# ==========================================
# CONFIGURACIÓN
# ==========================================
NUM_MOTORES = 16
HEADER = b'\xAA\x55'
BAUDRATE = 921600
PUERTO = "COM6"  # <-- Ajusta tu puerto aquí

# Índices de los motores (Ojos y Párpados)
M_OJO_IZQ_V = 0
M_OJO_IZQ_H = 1
M_PARP_IZQ_SUP = 2
M_PARP_IZQ_INF = 3
M_OJO_DER_V = 4
M_OJO_DER_H = 5
M_PARP_DER_SUP = 6
M_PARP_DER_INF = 7

# Índices de los motores (Expresiones Faciales)
M_CEJA_IZQ = 8
M_FRENTE_NARIZ_IZQ = 9
M_MEJILLA_IZQ = 10
M_LABIO_SUP = 11
M_CEJA_DER = 12
M_FRENTE_NARIZ_DER = 13
M_MEJILLA_DER = 14
M_MANDIBULA = 15

def enviar_angulos(puerto_serial, estado_motores):
    """Envía el array de 16 ángulos al ESP32."""
    payload = HEADER + bytes(estado_motores)
    puerto_serial.write(payload)

def aplicar_mirada(estado, hori=90, vert=90, parp_sup=90, parp_inf=90):
    """Ajusta la dirección de los ojos y la apertura de los párpados."""
    estado[M_OJO_IZQ_H] = hori
    estado[M_OJO_DER_H] = hori
    estado[M_OJO_IZQ_V] = vert
    estado[M_OJO_DER_V] = vert
    
    estado[M_PARP_IZQ_SUP] = parp_sup
    estado[M_PARP_DER_SUP] = parp_sup
    estado[M_PARP_IZQ_INF] = parp_inf
    estado[M_PARP_DER_INF] = parp_inf

def aplicar_expresion(estado, ceja_i=90, ceja_d=90, nariz_i=90, nariz_d=90, mej_i=90, mej_d=90, labio=90, mandibula=0):
    """Ajusta los motores de la cara para crear gestos."""
    estado[M_CEJA_IZQ] = ceja_i
    estado[M_CEJA_DER] = ceja_d
    estado[M_FRENTE_NARIZ_IZQ] = nariz_i
    estado[M_FRENTE_NARIZ_DER] = nariz_d
    estado[M_MEJILLA_IZQ] = mej_i
    estado[M_MEJILLA_DER] = mej_d
    estado[M_LABIO_SUP] = labio
    estado[M_MANDIBULA] = mandibula

def centrar_todo(estado):
    """Devuelve todos los motores de la cara a su posición de descanso (90°)."""
    for i in range(NUM_MOTORES):
        estado[i] = 90
    estado[M_MANDIBULA] = 0

def main():
    print(f"🤖 Conectando a Zoé en {PUERTO}...")
    
    try:
        ser = serial.Serial(PUERTO, BAUDRATE, timeout=1)
        time.sleep(2) # Esperar a que el ESP32 reinicie
        ser.reset_input_buffer()
        print("✅ ¡Conexión exitosa! Iniciando rutina de prueba de emociones...\n")
        
        estado_motores = [90] * NUM_MOTORES
        pausa = 3.0

        while True:

            # ── 0. PRUEBA EXCLUSIVA DE MANDÍBULA ──
            print("👄 INICIANDO PRUEBA DE MANDÍBULA (0 a 180)...")
            centrar_todo(estado_motores)
            enviar_angulos(ser, estado_motores)
            time.sleep(1)

            for angulo in [0, 45, 90, 135, 180]:
                print(f"   -> Moviendo mandíbula a: {angulo}°")
                estado_motores[M_MANDIBULA] = angulo
                enviar_angulos(ser, estado_motores)
                time.sleep(1.5)  # Tiempo suficiente para verla moverse
            
            print("   -> Cerrando mandíbula...")
            estado_motores[M_MANDIBULA] = 0
            enviar_angulos(ser, estado_motores)
            time.sleep(2)   

            # ── 1. ESTADO NORMAL / CENTRO ──
            print("😐 Emoción: NORMAL (Centro)")
            centrar_todo(estado_motores)
            enviar_angulos(ser, estado_motores)
            time.sleep(pausa)
            
            # ── 2. FELIZ ──
            print("😄 Emoción: FELIZ")
            # 180 = Feliz, Levantado, Arriba
            # Mejillas felices (180), Cejas ligeramente levantadas (135), Labio subido (180)
            aplicar_expresion(estado_motores, ceja_i=135, ceja_d=135, mej_i=180, mej_d=180, labio=180)
            aplicar_mirada(estado_motores, parp_sup=90, parp_inf=135) # Párpados inf suben por la sonrisa
            enviar_angulos(ser, estado_motores)
            time.sleep(pausa)

            # ── 3. TRISTE ──
            print("😢 Emoción: TRISTE")
            # 0 = Triste, Caído, Abajo
            # Mejillas tristes (0), Labio abajo (0), Cejas caídas (45)
            aplicar_expresion(estado_motores, ceja_i=45, ceja_d=45, mej_i=0, mej_d=0, labio=0)
            aplicar_mirada(estado_motores, parp_sup=45, parp_inf=90, vert=45) # Mirada cabizbaja (45)
            enviar_angulos(ser, estado_motores)
            time.sleep(pausa)

            # ── 4. ENOJADO ──
            print("😠 Emoción: ENOJADO")
            # Cejas fruncidas (0), Nariz encogida/arrugada (0), Labio subido mostrando dientes (180)
            aplicar_expresion(estado_motores, ceja_i=0, ceja_d=0, nariz_i=0, nariz_d=0, mej_i=90, mej_d=90, labio=180, mandibula=120)
            aplicar_mirada(estado_motores, parp_sup=45, parp_inf=135) # Ojos entrecerrados
            enviar_angulos(ser, estado_motores)
            time.sleep(pausa)

            # ── 5. DESAGRADABLE (ASCO) ──
            print("🤢 Emoción: DESAGRADABLE (Asco)")
            # Nariz muy arrugada (0), Labio subido (180), Mejillas un poco subidas de asco (135)
            aplicar_expresion(estado_motores, ceja_i=0, ceja_d=0, nariz_i=0, nariz_d=0, mej_i=135, mej_d=135, labio=180, mandibula=120)
            aplicar_mirada(estado_motores, parp_sup=60, parp_inf=150) # Ojos muy achinados
            enviar_angulos(ser, estado_motores)
            time.sleep(pausa)
            
            # ── 6. MISTERIOSO ──
            print("🕵️ Emoción: MISTERIOSO")
            # Ceja Izq levantada (180), Ceja Der fruncida (0)
            # Mirada de reojo hacia la derecha (0) y ojos entrecerrados
            aplicar_expresion(estado_motores, ceja_i=180, ceja_d=0, nariz_i=90, nariz_d=90, mej_i=90, mej_d=90, labio=90, mandibula=0)
            aplicar_mirada(estado_motores, hori=0, parp_sup=60, parp_inf=120)
            enviar_angulos(ser, estado_motores)
            time.sleep(pausa)

            # ── 7. CURIOSO ──
            print("🤔 Emoción: CURIOSO")
            # Cejas muy levantadas (180), nariz expandida (180)
            # Ojos muy abiertos (180), mirando ligeramente hacia arriba (140)
            aplicar_expresion(estado_motores, ceja_i=180, ceja_d=180, nariz_i=180, nariz_d=180, mej_i=90, mej_d=90, labio=90, mandibula=0)
            aplicar_mirada(estado_motores, vert=140, parp_sup=180, parp_inf=90)
            enviar_angulos(ser, estado_motores)
            time.sleep(pausa)

            # ── 8. PARPADEO RÁPIDO (Transición) ──
            print("😑 Parpadeando...")
            centrar_todo(estado_motores)
            # Cerramos ambos párpados superiores (0 = Cerrado)
            estado_motores[M_PARP_IZQ_SUP] = 0
            estado_motores[M_PARP_DER_SUP] = 0
            enviar_angulos(ser, estado_motores)
            time.sleep(0.3) 
            
            # Los volvemos a abrir a posición normal (90)
            estado_motores[M_PARP_IZQ_SUP] = 90
            estado_motores[M_PARP_DER_SUP] = 90
            enviar_angulos(ser, estado_motores)
            time.sleep(pausa - 0.3)

    except serial.SerialException as e:
        print(f"\n❌ Error de puerto serial: {e}")
    except KeyboardInterrupt:
        print("\n\n⏹️ Prueba detenida por el usuario. Centrando motores...")
        centrar_todo(estado_motores)
        enviar_angulos(ser, estado_motores)
        if 'ser' in locals() and ser.is_open:
            ser.close()
        print("✅ Zoé descansando. ¡Hasta luego!")

if __name__ == "__main__":
    main()