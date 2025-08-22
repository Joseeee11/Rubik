from tkinter import *
from tkinter import ttk
import serial.tools.list_ports
# --- ESP32 Serial ---
# Importar la biblioteca de comunicación serial
import serial
# Configuración del puerto serial (ajusta según la configuración)
puerto_serial = 'COM10'  # Cambia esto al puerto correcto
baud_rate = 115200  # Asegurar que coincida con la configuración del ESP32
ser = None  # Variable global para la conexión serial

def iniciar_conexion_serial(ser):
    global puerto_serial, baud_rate
    try:
        # Inicializar la conexión serial
        ser = serial.Serial(puerto_serial, baud_rate, timeout=1)
        print(f"Conexión serial establecida en {puerto_serial} a {baud_rate} baudios.")
        return ser
    except serial.SerialException as e:
        print(f"Error al iniciar la conexión serial: {e}")
        ser = None
        return ser
    
def enviar_esp32(comando, ser, ):
    if ser is not None and ser.is_open:
        try:
            # Enviar el comando al ESP32
            ser.write(comando.to_bytes(2, byteorder='big'))  # Usa 2 bytes, big endian
            print(f"Comando enviado: {comando}")
        except serial.SerialException as e:
            print(f"Error al enviar comando: {e}")
    else:
        print("La conexión serial no está abierta o no se ha establecido.")

def cerrar_serial(ser):
    if ser is not None and ser.is_open:
        try:
            ser.close()
            print("Conexión serial cerrada.")
        except serial.SerialException as e:
            print(f"Error al cerrar la conexión serial: {e}")
    else:
        print("La conexión serial no está abierta o no se ha establecido.")

def listar_seriales(encabezado, color,cerrar_conexion_serial, ser, actualizar_ser_callback):
    # Listar los puertos seriales disponibles
    puertos = serial.tools.list_ports.comports()
    lista_puertos = [puerto.device for puerto in puertos]
    label_puertos = Label(encabezado, text="Puertos Seriales:", bg=color["Oscuro6"], fg=color["Beige6"], font=("Tine new roman", 12))
    label_puertos.grid(column=7, row=0, sticky="e")
    if not lista_puertos:
        lista_puertos = ["No se encontraron puertos seriales"]
    else:
        # Crear un ComboBox para seleccionar el puerto serial
        combo_puertos = ttk.Combobox(encabezado, values=lista_puertos, state="readonly", font=("Tine new roman", 12))
        combo_puertos.grid(column=8, row=0, sticky="e")
        combo_puertos.bind("<<ComboboxSelected>>", lambda event: actualizar_ser_callback(seleccionar_puerto(combo_puertos, cerrar_conexion_serial, ser)))

def seleccionar_puerto(combo_puertos, cerrar_conexion_serial, ser):
    global puerto_serial
    cerrar_conexion_serial()  # Cerrar la conexión actual si está abierta
    seleccion = combo_puertos.get()
    if seleccion:
        puerto_serial = seleccion
        ser = iniciar_conexion_serial(ser)  # Iniciar la conexión con el puerto seleccionado
        return ser
    else:
        print("No se ha seleccionado ningún puerto serial.")
        return ser
