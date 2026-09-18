def grados_a_micropulsos(grados, min_us=500, max_us=2500, rango_total=180):
    """
    Convierte grados a microsegundos (PWM) para un servomotor.
    """
    # Validar que los grados estén dentro del rango permitido
    if grados < 0 or grados > rango_total:
        return f"Error: Ingresa un valor entre 0 y {rango_total}"

    # Aplicar la fórmula de interpolación lineal
    micropulsos = min_us + ((max_us - min_us) / rango_total) * grados
    
    return round(micropulsos)

# Solicitar entrada al usuario
try:
    entrada = float(input("Ingresa los grados (0-180): "))
    resultado = grados_a_micropulsos(entrada)
    
    if isinstance(resultado, int):
        print(f"Para {entrada}°, el pulso debe ser de: {resultado} µs")
    else:
        print(resultado)
except ValueError:
    print("Por favor, ingresa un número válido.")
