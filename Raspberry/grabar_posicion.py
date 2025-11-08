import numpy as np

class GrabarPosicion:

    def __init__(self, nombre, codigo):
        self.nombre = nombre
        self.codigo = codigo

    # Este método mágico define cómo se imprime el objeto.
    def __repr__(self):
        # Usamos una f-string con saltos de línea para el formato.
        return (f"Nombre: {self.nombre}, Codigo: {self.codigo}\n")
    
    