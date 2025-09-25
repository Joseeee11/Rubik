###Formula para calcular el valor de Clavícula
import math
import numpy as np

## Definir la ecuación de la recta los puntos de la recta
def calcular_clavicula(rectaA, rectaB):
    if (rectaA[0] == rectaB[0]) or (rectaA[1] == rectaB[1]):  # Verificar si las rectas son verticales u horizontales
        if rectaA[0] == rectaB[0]:  # Verificar si la recta es vertical
            Horizontal_Vertical = "Vertical"
        elif rectaA[1] == rectaB[1]:  # Verificar si la recta es horizontal
            Horizontal_Vertical = "Horizontal"
        m = 0 # Pendiente de la recta horizontal
        b = None
        clavicula_recta = None
    else:
        m = (rectaB[1] - rectaA[1]) / (rectaB[0] - rectaA[0])  # Pendiente de la recta
        b = rectaA[1] - m * rectaA[0]  # Intersección en y
        clavicula_recta = lambda x: m * x + b  # Ecuación de la recta
        Horizontal_Vertical = "Normal"  # La recta es normal (ni vertical ni horizontal)

    return clavicula_recta , m, b, Horizontal_Vertical

## distancia de un punto a una recta
def distancia_punto_a_recta(punto, m, b):
    # La recta está en la forma Ax + By + C = 0
    A = -m  # Coeficiente de x
    B = 1   # Coeficiente de y
    C = -b  # Intersección en y
    x0, y0 = punto
    # Distancia desde el punto (x0, y0) a la recta Ax + By + C = 0
    distancia = abs(A * x0 + B * y0 + C) / math.sqrt(A**2 + B**2)
    x_inter = (m * (y0 - b) + x0) / (m**2 + 1)
    y_inter = m * x_inter + b
    punto_interseccion = (x_inter, y_inter)  # Punto de intersección en la recta
    return distancia , punto_interseccion

## Encapsular la formula para calcular el valor de clavícula
def Calcular_distancia_Punto_a_RectaAB(coordenada_x_rectaA,coordenada_y_rectaA, coordenada_x_rectaB, coordenada_y_rectaB, coordenada_x_puntoA, coordenada_y_puntoA):
    rectaA = np.array([coordenada_x_rectaA, coordenada_y_rectaA])
    rectaB = np.array([coordenada_x_rectaB, coordenada_y_rectaB])
    punto_A = np.array([coordenada_x_puntoA, coordenada_y_puntoA])

    recta_clavicula, m, b, Horizontal_Vertical = calcular_clavicula(rectaA, rectaB)
    if Horizontal_Vertical == "Vertical":
        # print("La distancia desde el punto a la recta vertical")
        return abs(punto_A[0] - rectaA[0]), None
    elif Horizontal_Vertical == "Horizontal":
        # print("La distancia desde el punto a la recta horizontal")
        return abs(punto_A[1] - rectaA[1]), None
    else:
        # print("La distancia desde el punto a la recta")
        distancia_clavicula, punto_interseccion = distancia_punto_a_recta(punto_A, m, b)
    
    return distancia_clavicula, punto_interseccion

def punto_medio_segmento(puntoA, puntoB):
    ## Calcular el punto medio entre dos puntos
    x_medio = (puntoA[0] + puntoB[0]) / 2
    y_medio = (puntoA[1] + puntoB[1]) / 2
    return (x_medio, y_medio)

def calcular_angulo(puntoA, puntoB, puntoC):
    """
    Calcula el ángulo en puntoB formado por los puntos A-B-C.
    Los puntos deben ser tuplas (x, y).
    Retorna el ángulo en grados.
    """
    # Vectores BA y BC
    BA = np.array([puntoA[0] - puntoB[0], puntoA[1] - puntoB[1]])
    BC = np.array([puntoC[0] - puntoB[0], puntoC[1] - puntoB[1]])
    # Producto punto y norma
    coseno_angulo = np.dot(BA, BC) / (np.linalg.norm(BA) * np.linalg.norm(BC))
    # Limitar el valor para evitar errores numéricos
    coseno_angulo = np.clip(coseno_angulo, -1.0, 1.0)
    angulo_rad = np.arccos(coseno_angulo)
    angulo_deg = np.degrees(angulo_rad)
    return angulo_deg

# Funciones para visualizacion del cuerpo con MediaPipe
def normalizar_vector(vector):
    norma = np.linalg.norm(vector)
    if norma == 0:
        return vector
    return vector / norma

def calcular_angulo_brazos(componente1, componente2):
    if componente1 == 0 and componente2 == 0:
        return 0
    # aplicaré la funcion "atan2" arcotangente de dos argumentos
    angulo_radianes = np.arctan2(componente1, componente2)
    angulo_grados = np.degrees(angulo_radianes)
    return angulo_grados

def calcular_angulo_flexion(vector1, vector2):
    producto_escalar = np.dot(vector1, vector2)
    magnitud_vector1 = np.linalg.norm(vector1)
    magnitud_vector2 = np.linalg.norm(vector2)
    if magnitud_vector1 < 1e-6 or magnitud_vector2 < 1e-6:
        return 0
        # print("angulo flexion codo", angulo_mfcd_grados)  #0 extendido, 180 flexionado
    else:
        coseno = producto_escalar / (magnitud_vector1 * magnitud_vector2)
        coseno = np.clip(coseno, -1.0, 1.0)  # Asegurar que el coseno esté en el rango válido
        angulo_radianes = np.arccos(coseno)
        angulo_grados = np.degrees(angulo_radianes)
        return angulo_grados

def definir_flexion(angulo, brazo):
    # brazo_derecho[0] es posición flexión y brazo_derecho[1] es el ángulo al esp32

    if (brazo == "derecho"):
        angulo_esp = angulo + 4000
    if (brazo == "izquierdo"):
        angulo_esp = angulo + 4200

    if 0 <= angulo < 22:
        if (brazo == "derecho"):
            angulo_esp = angulo + 4000
        if (brazo == "izquierdo"):
            angulo_esp = angulo + 4200
        return "extendido", str(round(float(angulo_esp)))
    elif 22 <= angulo < 60:
        if (brazo == "derecho"):
            angulo_esp = angulo + 4000
        if (brazo == "izquierdo"):
            angulo_esp = angulo + 4200
        return "ligeramente-flexionado", str(round(float(angulo_esp)))
    elif 60 <= angulo <= 90:
        if (brazo == "derecho"):
            angulo_esp = angulo + 4000
        if (brazo == "izquierdo"):
            angulo_esp = angulo + 4200
        return "flexionado", str(round(float(angulo_esp)))
    elif 90 < angulo <= 130:
        if (brazo == "derecho"):
            angulo_esp = angulo + 4000
        if (brazo == "izquierdo"):
            angulo_esp = angulo + 4200
        return "muy-flexionado", str(round(float(angulo_esp)))
    elif angulo > 130:
        if (brazo == "derecho"):
            angulo_esp = angulo + 4000
        if (brazo == "izquierdo"):
            angulo_esp = angulo + 4200
        return "completamente-flexionado", str(round(float(angulo_esp)))
    else:
        print("Posición de flexión desconocida")
        return "None", "None"

def definir_posicion_frontal(angulo, brazo):
    # brazo_dereccho[2] es posición frontal y brazo_derecho[3] es su código para ESP32

    if (brazo == "derecho"):
        angulo_esp = angulo + 4400
    if (brazo == "izquierdo"):
        angulo_esp = angulo + 4600

    if (brazo == "derecho"):
        angulo_absoluto = angulo

        if angulo_absoluto > 20:
            angulo_absoluto = 20
        if angulo_absoluto < -85:
            angulo_absoluto = -85
        angulo_absoluto = abs(angulo_absoluto - 20) # deberia ir de 0 a 105
        angulo_esp = angulo_absoluto + 4400

        if -20 < angulo: 
            # print("Frontal: derecha")
            return "derecha", str(round(float(angulo_esp)))
        elif -45 < angulo <= -20:
            # print("Frontal: derecha-abajo")
            return "derecha-abajo", str(round(float(angulo_esp)))
        elif -65 < angulo <= -45:
            # print("Frontal: abajo-derecha")
            return "abajo-derecha", str(round(float(angulo_esp)))
        elif angulo <= -65:
            # print("Frontal: abajo")
            return "abajo", str(round(float(angulo_esp)))
        else:
            # print("Posición frontal desconocida")
            return "None", "None"
        
