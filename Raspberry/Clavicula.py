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