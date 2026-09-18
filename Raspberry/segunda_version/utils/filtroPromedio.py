class FiltroEstabilidad:
    def __init__(self, frames_confirmacion=5, valor_inicial=None):
        """
        Un filtro genérico para evitar tartamudeos (debounce) en las lecturas.
        """
        self.historial = []
        self.frames_confirmacion = frames_confirmacion
        # Guarda el último estado que fue confirmado como "estable"
        self.estado_confirmado = valor_inicial 
        self.valorGuardado_tolerancia = None

    def actualizar_y_verificar_boolean(self, nueva_lectura):
        """
        Añade la nueva lectura al historial y verifica si hay un nuevo estado estable.
        Retorna True SOLAMENTE en el frame exacto donde ocurre un cambio de estado confirmado.
        """
        self.historial.append(nueva_lectura)
        
        # Mantenemos el tamaño del historial
        if len(self.historial) > self.frames_confirmacion:
            self.historial.pop(0)
            
        # Si no tenemos suficientes datos aún, no hacemos nada
        if len(self.historial) < self.frames_confirmacion:
            return False
            
        # Verificamos si todos los elementos del historial son idénticos a la lectura actual
        es_estable = all(estado == nueva_lectura for estado in self.historial)
        
        # Si es estable y es DIFERENTE al último estado confirmado, es un cambio válido!
        if es_estable and (nueva_lectura != self.estado_confirmado):
            self.estado_confirmado = nueva_lectura
            return True # ¡Hay un nuevo cambio oficial!
            
        return False
    def a_y_v_float_aceptacion(self, nueva_lectura, aceptacion):
        self.historial.append(nueva_lectura)
        if len(self.historial) > self.frames_confirmacion:
            self.historial.pop(0)
        sumatoria = 0
        for elemento in self.historial:
            sumatoria += elemento
        promedio = sumatoria/ len(self.historial)
        if promedio >= aceptacion:
            return True
        else:
            return False
    def a_y_v_float_valor(self, nueva_lectura, tolerancia):
        self.historial.append(nueva_lectura)
        if len(self.historial) > self.frames_confirmacion:
            self.historial.pop(0)
        sumatoria= 0
        for elemento in self.historial:
            sumatoria+= elemento
        promedio= sumatoria/ len(self.historial)
        if (self.valorGuardado_tolerancia is None) or ((promedio > self.valorGuardado_tolerancia + tolerancia)or(promedio < self.valorGuardado_tolerancia - tolerancia)):
            self.valorGuardado_tolerancia = promedio
            return True
        else:
            return False

        