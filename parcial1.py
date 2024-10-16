def leer_procesos_desde_archivo(archivo):
    procesos = []
    with open(archivo, 'r') as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith("#"):
                # Parsear la línea
                datos = linea.split(";")
                etiqueta = datos[0].strip()
                burst_time = int(datos[1].strip())
                arrival_time = int(datos[2].strip())
                queue = int(datos[3].strip())
                prioridad = int(datos[4].strip())
                
                # Crear el objeto Proceso y añadirlo a la lista
                procesos.append(Proceso(etiqueta, burst_time, arrival_time, queue, prioridad))
    return procesos


class Proceso:
    def __init__(self, etiqueta, burst_time, arrival_time, queue, prioridad):
        self.etiqueta = etiqueta
        self.burst_time = burst_time
        self.arrival_time = arrival_time
        self.queue = queue
        self.prioridad = prioridad
        self.tiempo_restante = burst_time
        self.tiempo_comienzo = None
        self.tiempo_finalizacion = None
        self.tiempo_espera = 0
        self.tiempo_respuesta = -1  # Se calculará cuando el proceso inicie por primera vez



class Cola:
    def __init__(self, politica, quantum=None):
        self.procesos = []
        self.politica = politica
        self.quantum = quantum

    def agregar_proceso(self, proceso):
        self.procesos.append(proceso)

    def tiene_procesos(self):
        return len(self.procesos) > 0

    def ejecutar(self, tiempo_actual):
        if self.politica == "FCFS":
            return self._fcfs(tiempo_actual)
        elif self.politica == "RR":
            return self._rr(tiempo_actual)
        elif self.politica == "SJF":
            return self._sjf(tiempo_actual)

    def _fcfs(self, tiempo_actual):
        if self.procesos:
            proceso = self.procesos.pop(0)
            proceso.tiempo_comienzo = tiempo_actual if proceso.tiempo_comienzo is None else proceso.tiempo_comienzo
            proceso.tiempo_espera += tiempo_actual - proceso.arrival_time
            tiempo_actual += proceso.burst_time
            proceso.tiempo_finalizacion = tiempo_actual
            return proceso, tiempo_actual

    def _rr(self, tiempo_actual):
        if self.procesos:
            proceso = self.procesos.pop(0)
            if proceso.tiempo_comienzo is None:
                proceso.tiempo_comienzo = tiempo_actual  # Registrar cuando inicia
            if proceso.tiempo_respuesta == -1:
                proceso.tiempo_respuesta = tiempo_actual - proceso.arrival_time  # Tiempo de respuesta solo la primera vez

            # Ejecutar por quantum o hasta terminar
            if proceso.tiempo_restante > self.quantum:
                proceso.tiempo_restante -= self.quantum
                tiempo_actual += self.quantum
                self.procesos.append(proceso)  # Reinsertar si no ha terminado
            else:
                tiempo_actual += proceso.tiempo_restante
                proceso.tiempo_finalizacion = tiempo_actual
                proceso.tiempo_restante = 0  # Proceso terminado

            return proceso, tiempo_actual

    def _sjf(self, tiempo_actual):
        self.procesos.sort(key=lambda x: x.burst_time)  # Ordenar por el tiempo más corto
        return self._fcfs(tiempo_actual)

    
    def _stcf(self, tiempo_actual):
        self.procesos.sort(key=lambda x: x.tiempo_restante)
        return self._fcfs(tiempo_actual)



class MLQScheduler:
    def __init__(self, colas):
        self.colas = colas
        self.tiempo_actual = 0
        self.resultados = []
        self.lista_procesos = []  # Lista de todos los procesos

    def agregar_proceso(self, proceso):
        self.lista_procesos.append(proceso)

    def ejecutar(self):
        while self.lista_procesos or any(cola.tiene_procesos() for cola in self.colas):
            # 1. Agregar procesos que hayan llegado
            self._agregar_procesos_entrantes()

            # 2. Ejecutar procesos respetando la prioridad de las colas
            proceso_ejecutado = False
            for cola in self.colas:
                if cola.tiene_procesos():
                    proceso, nuevo_tiempo = cola.ejecutar(self.tiempo_actual)
                    if proceso:
                        # Si el proceso no ha sido agregado, se agrega a los resultados
                        if proceso not in self.resultados:
                            self.resultados.append(proceso)
                        self.tiempo_actual = nuevo_tiempo
                        proceso_ejecutado = True
                        break  # Ejecutar un solo proceso por ciclo

            # Si ninguna cola tiene procesos listos, avanzar el tiempo al siguiente proceso
            if not proceso_ejecutado:
                self._avanzar_tiempo_al_siguiente_proceso()

    def _agregar_procesos_entrantes(self):
        for proceso in list(self.lista_procesos):
            if proceso.arrival_time <= self.tiempo_actual:
                self.colas[proceso.queue - 1].agregar_proceso(proceso)
                self.lista_procesos.remove(proceso)  # Eliminar de la lista de procesos pendientes

    def _avanzar_tiempo_al_siguiente_proceso(self):
        if self.lista_procesos:
            siguiente_proceso = min(self.lista_procesos, key=lambda x: x.arrival_time)
            self.tiempo_actual = siguiente_proceso.arrival_time


    def generar_reporte(self, archivo_salida):
        with open(archivo_salida, 'w') as f:
            # Escribir encabezados
            f.write("# etiqueta; BT; AT; Q; Pr; WT; CT; RT; TAT\n")

            total_wt, total_ct, total_rt, total_tat = 0, 0, 0, 0
            n = len(self.resultados)

            for proceso in self.resultados:
                # Turnaround Time: Tiempo desde la llegada hasta la finalización
                turnaround_time = proceso.tiempo_finalizacion - proceso.arrival_time

                # Tiempo de respuesta: Tiempo desde la llegada hasta que comienza a ejecutarse
                tiempo_respuesta = proceso.tiempo_comienzo - proceso.arrival_time

                # Tiempo de espera: Turnaround - Burst Time
                tiempo_espera = turnaround_time - proceso.burst_time

                # Acumular los tiempos totales
                total_wt += tiempo_espera
                total_ct += proceso.tiempo_finalizacion
                total_rt += tiempo_respuesta
                total_tat += turnaround_time

                # Escribir cada línea de resultados en el archivo
                f.write(f"{proceso.etiqueta};{proceso.burst_time};{proceso.arrival_time};{proceso.queue};{proceso.prioridad};"
                        f"{tiempo_espera};{proceso.tiempo_finalizacion};{tiempo_respuesta};{turnaround_time}\n")

            # Escribir los promedios
            f.write(f"\nWT promedio={total_wt / n}; CT promedio={total_ct / n}; RT promedio={total_rt / n}; TAT promedio={total_tat / n}\n")


cola1 = Cola("RR", quantum=3)
cola2 = Cola("SJF")
cola3 = Cola("FCFS")

scheduler = MLQScheduler([cola1, cola2, cola3])

# Leer procesos desde un archivo
procesos = leer_procesos_desde_archivo('mlq014.txt')

# Agregar los procesos leídos al scheduler
for proceso in procesos:
    scheduler.agregar_proceso(proceso)

# Ejecutar el scheduler
scheduler.ejecutar()

# Generar el reporte en un archivo de salida
scheduler.generar_reporte('mlq_resultados.txt')