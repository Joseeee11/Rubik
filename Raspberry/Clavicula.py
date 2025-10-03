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
    print(x_medio)
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

def mapear_valor(valor, min_original, max_original, min_deseado, max_deseado):
    # Cálculo
    proporcion = (valor - min_original) / (max_original - min_original)
    valor_mapeado = proporcion * (max_deseado - min_deseado) + min_deseado
    return round(valor_mapeado)

def definir_flexion(angulo, brazo):
    # brazo_derecho[0] es posición flexión y brazo_derecho[1] es el ángulo al esp32
    # rango para flexion de codo derecha 4000 a 4199
    # rango para flexion de codo izquierdo 4200 a 4399

    # min_original = 30
    # max_original = 80
    # min_deseado = 0
    # max_deseado = 180
    # angulo_original = round(angulo)
    # angulo_absoluto = mapear_valor(angulo_original, min_original, max_original, min_deseado, max_deseado)

    angulo_absoluto = round(angulo)

    # de 30 a 80 en mediapipe
    if angulo_absoluto < 30:
        angulo_absoluto = 30
    elif angulo_absoluto > 80:
        angulo_absoluto = 80
    ## mapear angulo de 30 a 80 a 0 a 180
    angulo_absoluto = mapear_valor(angulo_absoluto, 30, 80, 0, 180)
    if brazo == "derecho":
        angulo_esp = angulo_absoluto + 4000 # valor que se enviará al esp32
    if brazo == "izquierdo":
        angulo_esp = angulo_absoluto + 4200 # valor que se enviará al esp32
    if 0 <= angulo < 30:
        # if (brazo == "derecho"):
        #     angulo_esp = angulo_absoluto + 4000
        # if (brazo == "izquierdo"):
        #     angulo_esp = angulo_absoluto + 4200
        return "extendido", round(float(angulo_esp))
    elif 30 <= angulo < 45:
        # if (brazo == "derecho"):
        #     angulo_esp = angulo_absoluto + 4000
        # if (brazo == "izquierdo"):
        #     angulo_esp = angulo_absoluto + 4200
        return "ligeramente-flexionado", round(float(angulo_esp))
    elif 45 <= angulo <= 60:
        # if (brazo == "derecho"):
        #     angulo_esp = angulo_absoluto + 4000
        # if (brazo == "izquierdo"):
        #     angulo_esp = angulo_absoluto + 4200
        return "flexionado", round(float(angulo_esp))
    elif 60 < angulo <= 70:
        # if (brazo == "derecho"):
        #     angulo_esp = angulo_absoluto + 4000
        # if (brazo == "izquierdo"):
        #     angulo_esp = angulo_absoluto + 4200
        return "muy-flexionado", round(float(angulo_esp))
    elif angulo > 70:
        # if (brazo == "derecho"):
        #     angulo_esp = angulo_absoluto + 4000
        # if (brazo == "izquierdo"):
        #     angulo_esp = angulo_absoluto + 4200
        return "completamente-flexionado", round(float(angulo_esp))
    else:
        return "Posición de flexión desconocida", 4000

def definir_posicion_frontal(angulo, brazo):
    # brazo_derecho[2] es posición frontal y brazo_derecho[3] es su código para ESP32
    # rango para brazo derecho eje frontal 4400 a 4599
    # rango para brazo izquierdo eje frontal 4600 a 4799
    min_original = 0
    max_original = 180
    min_deseado = 13
    max_deseado = 55
    angulo_original = round(angulo)

    if angulo_original > 0:
        angulo_original = 0
    if angulo_original < -85:
        angulo_original = -85

    angulo_absoluto = mapear_valor(angulo_original, min_original, max_original, min_deseado, max_deseado)


    # angulo_absoluto = angulo
    # if angulo_absoluto > 20:
    #     angulo_absoluto = 20
    # if angulo_absoluto < -85:
    #     angulo_absoluto = -85
    # angulo_absoluto = abs(angulo_absoluto - 20) # deberia ir de 0 a 105

    if (brazo == "derecho"):
        angulo_esp = angulo_absoluto + 4400

        if 20 < angulo:
            return "arriba", round(float(angulo_esp))
        elif -20 < angulo <= 20: 
            # print("Frontal: derecha")
            return "derecha", round(float(angulo_esp))
        elif -45 < angulo <= -20:
            # print("Frontal: derecha-abajo")
            return "derecha-abajo", round(float(angulo_esp))
        elif -65 < angulo <= -45:
            # print("Frontal: abajo-derecha")
            return "abajo-derecha", round(float(angulo_esp))
        elif angulo <= -65:
            # print("Frontal: abajo")
            return "abajo", round(float(angulo_esp))
        else:
            # print("Posición frontal desconocida")
            return None, None

    if (brazo == "izquierdo"):
        angulo_esp = angulo_absoluto + 4600

        if 20 < angulo:
            return "arriba", round(float(angulo_esp))
        elif -20 < angulo <= 20: 
            # print("Frontal: izquierda")
            return "izquierda", round(float(angulo_esp))
        elif -45 < angulo <= -20:
            # print("Frontal: izquierda-abajo")
            return "izquierda-abajo", round(float(angulo_esp))
        elif -65 < angulo <= -45:
            # print("Frontal: abajo-izquierda")
            return "abajo-izquierda", round(float(angulo_esp))
        elif angulo <= -65:
            # print("Frontal: abajo")
            return "abajo", round(float(angulo_esp))
        else:
            # print("Posición frontal desconocida")
            return None, None        

def definir_posicion_sagital(angulo, brazo):
    # brazo_derecho[4] es posición sagital y brazo_derecho[5] es su código para ESP32
    # rango para brazo derecho eje sagital 4800 a 4999
    # rango para brazo izquierdo eje sagital 6000 a 6199


    if (brazo == "derecho"):
        #rangos para mapear
        min_original = -50
        max_original = 95
        min_deseado = 10
        max_deseado = 160
        angulo_original = round(angulo)
        # if angulo_original < -160:
        #     angulo_original = 95
        if angulo_original < -50:
            angulo_original = -50
        if angulo_original > 95:
            angulo_original = 95
        
        # mapeo
        angulo_absoluto = mapear_valor(angulo_original, min_original, max_original, min_deseado, max_deseado)
        print("angulo abs", angulo_absoluto)
        print("angulo original", round(angulo))
        angulo_esp = angulo_absoluto + 4800


        # if angulo_absoluto < -50:
        #         angulo_absoluto = -50
        # if angulo_absoluto > 95:
        #         angulo_absoluto = 95
        # if angulo_absoluto < 0:
        #         angulo_absoluto = abs(angulo_absoluto - 50)  #debería ser un rango de 0 a 50
        # if angulo_absoluto <= 95:
        #         angulo_absoluto = abs(angulo_absoluto + 50) #deberia dar un rango de 50 a 145
        # angulo_esp = angulo_absoluto + 4800 # mandaría la señal al esp32 de 0 grados a 145 grados

        
        if -50 > angulo:
            return "izquierda", round(float(angulo_esp))
        elif -5 >= angulo >= -50:
            return "frente-izquierda", round(float(angulo_esp))
        elif -5 < angulo <= 45:
            return "frente", round(float(angulo_esp))
        elif 45 < angulo <= 75:
            return "frente-derecha", round(float(angulo_esp))
        elif 75 < angulo <= 95:
            return "derecha", round(float(angulo_esp))
        elif 95 < angulo:
            return "atras-derecha", round(float(angulo_esp))
        else:
            print("Posición sagital desconocida")
            return None, None

    if (brazo == "izquierdo"):
        angulo_absoluto = angulo
        if 0 > angulo > -130:
            angulo_absoluto = -130
        elif 0 <= angulo < 85:
            angulo_absoluto = 85
        if  angulo_absoluto <= -130:
            angulo_absoluto = abs(angulo_absoluto) - 180
            if angulo_absoluto < -50:
                    angulo_absoluto = -50
            if angulo_absoluto < 0:
                    angulo_absoluto = abs(angulo_absoluto - 50)  #debería ser un rango de 0 a 50
        elif angulo_absoluto >= 85:
            angulo_absoluto = - angulo_absoluto + 180
            if angulo_absoluto > 95:
                    angulo_absoluto = 95
            if angulo_absoluto <= 95:
                    angulo_absoluto = abs(angulo_absoluto + 50) #deberia dar un rango de 50 a 145
        angulo_esp = angulo_absoluto + 6000 # mandaría la señal al esp32 de 0 grados a 145 grados

        if -130 < angulo > 0:
            return "frente-derecha", round(float(angulo_esp))
        elif -175 < angulo <= -130:
            return "frente-derecha", round(float(angulo_esp))
        elif 135 < angulo <= -175:
            return "frente", round(float(angulo_esp))
        elif 105 < angulo <= 135:
            return "frente-izquierda", round(float(angulo_esp))
        elif 85 <= angulo <= 105:
            return "izquierda", round(float(angulo_esp))
        elif 85 > angulo > 0:
            return "atras-izquierda", round(float(angulo_esp))
        else:
            print("Posición sagital desconocida")
            return None, None