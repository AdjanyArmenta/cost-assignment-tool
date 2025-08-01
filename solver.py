"""
Módulo del solucionador de asignación de costos - Versión mejorada
"""
from dataclasses import dataclass
from itertools import combinations
import numpy as np
import streamlit as st

@dataclass
class Asignacion:
    """Clase para representar una asignación de costos a objetivos"""
    objetivo: str
    valor_objetivo: float
    costos: list
    suma: float
    diferencia: float
    precision: float
    es_grupo: bool = False
    objetivos_agrupados: list = None

class CostAssignmentSolver:
    """Solucionador para el problema de asignación de costos a objetivos"""
    
    def __init__(self):
        self.costos_originales = []
        self.objetivos_originales = {}
        self.resultado = None
        
    def cargar_datos(self, costos, objetivos):
        """Carga los datos de costos y objetivos"""
        self.costos_originales = costos.copy()
        self.objetivos_originales = objetivos.copy()
        
        # Información sobre sumas
        suma_costos = sum(costos)
        suma_objetivos = sum(objetivos.values())
        
        return {
            'suma_costos': suma_costos,
            'suma_objetivos': suma_objetivos,
            'diferencia': suma_costos - suma_objetivos
        }
        
    def resolver_completa(self):
        """Estrategia completa con agrupación de objetivos pequeños"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        costos_disponibles = self.costos_originales.copy()
        asignaciones = []
        objetivos_pendientes = list(self.objetivos_originales.items())
        
        # Análisis inicial
        costo_minimo = min(costos_disponibles) if costos_disponibles else 0
        costo_maximo = max(costos_disponibles) if costos_disponibles else 0
        costo_promedio = np.mean(costos_disponibles) if costos_disponibles else 0
        
        # Detectar objetivos extremadamente grandes
        objetivo_maximo = max(v for _, v in objetivos_pendientes) if objetivos_pendientes else 0
        objetivo_promedio = np.mean([v for _, v in objetivos_pendientes]) if objetivos_pendientes else 0
        
        # Factor de escala para detectar objetivos fuera de rango
        factor_escala = objetivo_maximo / costo_maximo if costo_maximo > 0 else 1
        
        # Clasificar objetivos según su relación con los costos disponibles
        objetivos_extremos = []  # Nueva categoría para objetivos muy grandes
        objetivos_muy_pequeños = []
        objetivos_normales = []
        
        for nombre, valor in objetivos_pendientes:
            if valor > costo_maximo * 10:  # Objetivo extremadamente grande
                objetivos_extremos.append((nombre, valor))
            elif valor < costo_minimo * 0.7:  # Objetivo mucho menor que el costo más pequeño
                objetivos_muy_pequeños.append((nombre, valor))
            else:
                objetivos_normales.append((nombre, valor))
        
        # Fase 0: Procesar objetivos extremadamente grandes primero
        if objetivos_extremos:
            status_text.text("⚡ Fase 0: Procesando objetivos extremos...")
            progress_bar.progress(5)
            
            for nombre, valor in objetivos_extremos:
                # Calcular cuántos costos necesitamos aproximadamente
                num_costos_estimado = int(valor / costo_promedio)
                
                # Usar un enfoque voraz para objetivos extremos
                costos_asignados = []
                suma_actual = 0
                
                # Ordenar costos de mayor a menor para objetivos grandes
                costos_ordenados = sorted(costos_disponibles, reverse=True)
                
                for costo in costos_ordenados:
                    if suma_actual + costo <= valor * 1.1:  # Permitir hasta 10% de exceso
                        costos_asignados.append(costo)
                        suma_actual += costo
                        
                        # Si estamos cerca del objetivo, intentar ajuste fino
                        if abs(suma_actual - valor) / valor < 0.1:
                            # Buscar si podemos mejorar con intercambios
                            mejor_encontrado = self._optimizar_asignacion_extrema(
                                costos_asignados, 
                                [c for c in costos_disponibles if c not in costos_asignados], 
                                valor
                            )
                            if mejor_encontrado:
                                costos_asignados = mejor_encontrado['costos']
                                suma_actual = mejor_encontrado['suma']
                            break
                
                if costos_asignados:
                    asignacion = Asignacion(
                        objetivo=nombre,
                        valor_objetivo=valor,
                        costos=costos_asignados,
                        suma=suma_actual,
                        diferencia=abs(suma_actual - valor),
                        precision=100 - (abs(suma_actual - valor) / valor) * 100
                    )
                    asignaciones.append(asignacion)
                    
                    # Remover costos utilizados
                    for costo in costos_asignados:
                        costos_disponibles.remove(costo)
        
        # Fase 1: Agrupar objetivos muy pequeños
        if objetivos_muy_pequeños:
            status_text.text("🔍 Fase 1: Agrupando objetivos pequeños...")
            progress_bar.progress(15)
            
            # Ordenar objetivos pequeños por valor
            objetivos_muy_pequeños.sort(key=lambda x: x[1])
            
            while objetivos_muy_pequeños and costos_disponibles:
                # Buscar el mejor grupo de objetivos pequeños
                mejor_grupo = self._encontrar_mejor_grupo(objetivos_muy_pequeños, costos_disponibles)
                
                if mejor_grupo:
                    # Crear asignación grupal
                    nombres_grupo = [obj[0] for obj in mejor_grupo['objetivos']]
                    valores_grupo = [obj[1] for obj in mejor_grupo['objetivos']]
                    suma_objetivos = sum(valores_grupo)
                    
                    # Crear nombre del grupo
                    nombre_grupo = " + ".join(nombres_grupo)
                    
                    asignacion = Asignacion(
                        objetivo=nombre_grupo,
                        valor_objetivo=suma_objetivos,
                        costos=mejor_grupo['costos'],
                        suma=mejor_grupo['suma'],
                        diferencia=abs(mejor_grupo['suma'] - suma_objetivos),
                        precision=100 - (abs(mejor_grupo['suma'] - suma_objetivos) / suma_objetivos) * 100,
                        es_grupo=True,
                        objetivos_agrupados=list(zip(nombres_grupo, valores_grupo))
                    )
                    asignaciones.append(asignacion)
                    
                    # Remover objetivos y costos utilizados
                    for obj in mejor_grupo['objetivos']:
                        objetivos_muy_pequeños.remove(obj)
                    
                    for costo in mejor_grupo['costos']:
                        costos_disponibles.remove(costo)
                else:
                    # Si no se puede formar más grupos, pasar los restantes a normales
                    objetivos_normales.extend(objetivos_muy_pequeños)
                    break
        
        # Actualizar objetivos pendientes
        objetivos_pendientes = objetivos_normales
        
        # Fase 2: Coincidencias exactas
        status_text.text("🎯 Fase 2: Búsqueda de coincidencias exactas...")
        progress_bar.progress(30)
        
        for max_elementos in [1, 2, 3]:
            i = 0
            while i < len(objetivos_pendientes):
                nombre, valor = objetivos_pendientes[i]
                coincidencia = self._buscar_coincidencia_exacta(costos_disponibles, valor, max_elementos)
                
                if coincidencia:
                    asignacion = Asignacion(
                        objetivo=nombre,
                        valor_objetivo=valor,
                        costos=coincidencia['costos'],
                        suma=coincidencia['suma'],
                        diferencia=abs(coincidencia['suma'] - valor),
                        precision=100 - (abs(coincidencia['suma'] - valor) / valor) * 100
                    )
                    asignaciones.append(asignacion)
                    
                    for costo in coincidencia['costos']:
                        costos_disponibles.remove(costo)
                    
                    objetivos_pendientes.pop(i)
                else:
                    i += 1
        
        progress_bar.progress(50)
        status_text.text(f"🎯 Fase 3: Asignando {len(objetivos_pendientes)} objetivos restantes...")
        
        # Fase 3: Objetivos por categorías con límites adaptativos
        # Recalcular promedio con costos restantes
        costo_promedio_actual = np.mean(costos_disponibles) if costos_disponibles else costo_promedio
        
        objetivos_grandes = [(n, v) for n, v in objetivos_pendientes if v > costo_promedio_actual * 2]
        objetivos_medianos = [(n, v) for n, v in objetivos_pendientes if costo_minimo <= v <= costo_promedio_actual * 2]
        objetivos_pequeños = [(n, v) for n, v in objetivos_pendientes if v < costo_minimo]
        
        # Procesar objetivos grandes con límites adaptativos
        objetivos_grandes.sort(key=lambda x: x[1], reverse=True)
        for nombre, valor in objetivos_grandes:
            if costos_disponibles:
                # Adaptar el número máximo de elementos según el tamaño del objetivo
                max_elementos_adaptativo = min(
                    len(costos_disponibles),
                    max(7, int(valor / costo_promedio_actual * 1.5))
                )
                
                combinacion = self._buscar_mejor_combinacion_adaptativa(
                    costos_disponibles, 
                    valor, 
                    max_elementos_adaptativo
                )
                
                if combinacion:
                    asignacion = Asignacion(
                        objetivo=nombre,
                        valor_objetivo=valor,
                        costos=combinacion['costos'],
                        suma=combinacion['suma'],
                        diferencia=abs(combinacion['suma'] - valor),
                        precision=100 - (abs(combinacion['suma'] - valor) / valor) * 100
                    )
                    asignaciones.append(asignacion)
                    
                    for costo in combinacion['costos']:
                        costos_disponibles.remove(costo)
        
        progress_bar.progress(70)
        
        # Procesar objetivos medianos
        for nombre, valor in objetivos_medianos:
            if len(costos_disponibles) >= 2:
                combinacion = self._buscar_mejor_combinacion_agresiva(costos_disponibles, valor)
                if combinacion:
                    asignacion = Asignacion(
                        objetivo=nombre,
                        valor_objetivo=valor,
                        costos=combinacion['costos'],
                        suma=combinacion['suma'],
                        diferencia=abs(combinacion['suma'] - valor),
                        precision=100 - (abs(combinacion['suma'] - valor) / valor) * 100
                    )
                    asignaciones.append(asignacion)
                    
                    for costo in combinacion['costos']:
                        costos_disponibles.remove(costo)
        
        progress_bar.progress(85)
        
        # Procesar objetivos pequeños restantes
        for nombre, valor in objetivos_pequeños:
            if costos_disponibles:
                mejor_costo = min(costos_disponibles, key=lambda x: abs(x - valor))
                asignacion = Asignacion(
                    objetivo=nombre,
                    valor_objetivo=valor,
                    costos=[mejor_costo],
                    suma=mejor_costo,
                    diferencia=abs(mejor_costo - valor),
                    precision=max(0, 100 - (abs(mejor_costo - valor) / valor) * 100)
                )
                asignaciones.append(asignacion)
                costos_disponibles.remove(mejor_costo)
        
        # Fase 4: Distribución forzada
        if costos_disponibles:
            status_text.text("🔄 Fase 4: Distribuyendo costos restantes...")
            self._distribuir_forzadamente(asignaciones, costos_disponibles)
        
        progress_bar.progress(100)
        status_text.text("✅ ¡Procesamiento completado!")
        
        # Asegurar que todos los objetivos estén asignados
        objetivos_asignados = set()
        for asig in asignaciones:
            if asig.es_grupo and asig.objetivos_agrupados:
                for nombre, _ in asig.objetivos_agrupados:
                    objetivos_asignados.add(nombre)
            else:
                objetivos_asignados.add(asig.objetivo)
        
        objetivos_faltantes = set(self.objetivos_originales.keys()) - objetivos_asignados
        
        for nombre_faltante in objetivos_faltantes:
            valor = self.objetivos_originales[nombre_faltante]
            asignacion_vacia = Asignacion(
                objetivo=nombre_faltante,
                valor_objetivo=valor,
                costos=[],
                suma=0,
                diferencia=valor,
                precision=0
            )
            asignaciones.append(asignacion_vacia)
        
        import time
        time.sleep(0.5)  # Pausa para que se vea el 100%
        progress_bar.empty()
        status_text.empty()
        
        return asignaciones
    
    def _optimizar_asignacion_extrema(self, costos_actuales, costos_disponibles, objetivo):
        """Optimiza una asignación para objetivos extremadamente grandes"""
        mejor_asignacion = None
        suma_actual = sum(costos_actuales)
        mejor_diferencia = abs(suma_actual - objetivo)
        
        # Intentar intercambios para mejorar la precisión
        for i, costo_actual in enumerate(costos_actuales[:10]):  # Limitar para eficiencia
            for costo_disponible in costos_disponibles[:20]:  # Limitar para eficiencia
                nueva_suma = suma_actual - costo_actual + costo_disponible
                nueva_diferencia = abs(nueva_suma - objetivo)
                
                if nueva_diferencia < mejor_diferencia:
                    nuevos_costos = costos_actuales.copy()
                    nuevos_costos[i] = costo_disponible
                    mejor_diferencia = nueva_diferencia
                    mejor_asignacion = {
                        'costos': nuevos_costos,
                        'suma': nueva_suma
                    }
        
        return mejor_asignacion
    
    def _buscar_mejor_combinacion_adaptativa(self, costos, objetivo, max_elementos):
        """Búsqueda adaptativa para objetivos de cualquier tamaño"""
        mejor_combinacion = None
        menor_diferencia_relativa = float('inf')
        
        # Para objetivos muy grandes, usar enfoque voraz primero
        if objetivo > sum(costos) * 0.3:
            # Enfoque voraz
            costos_ordenados = sorted(costos, reverse=True)
            costos_seleccionados = []
            suma_actual = 0
            
            for costo in costos_ordenados:
                if suma_actual + costo <= objetivo * 1.2:
                    costos_seleccionados.append(costo)
                    suma_actual += costo
                    
                    if abs(suma_actual - objetivo) / objetivo < 0.05:
                        return {'costos': costos_seleccionados, 'suma': suma_actual}
            
            if costos_seleccionados:
                mejor_combinacion = {'costos': costos_seleccionados, 'suma': suma_actual}
                menor_diferencia_relativa = abs(suma_actual - objetivo) / objetivo
        
        # Para objetivos más pequeños o para refinar, usar búsqueda combinatoria
        else:
            # No filtrar costos para objetivos grandes
            costos_utiles = costos if objetivo > max(costos) * 5 else [c for c in costos if c <= objetivo * 2.0]
            costos_ordenados = sorted(costos_utiles, key=lambda x: abs(x - objetivo))[:min(20, len(costos_utiles))]
            
            for num_elementos in range(1, min(max_elementos + 1, len(costos_ordenados) + 1)):
                for combo in combinations(costos_ordenados, num_elementos):
                    suma = sum(combo)
                    diferencia = abs(suma - objetivo)
                    diferencia_relativa = diferencia / objetivo
                    
                    if diferencia_relativa < menor_diferencia_relativa:
                        menor_diferencia_relativa = diferencia_relativa
                        mejor_combinacion = {'costos': list(combo), 'suma': suma}
                        
                        # Ajustar tolerancia según el tamaño del objetivo
                        tolerancia = 0.05 if objetivo > 50 else 0.15
                        if diferencia_relativa < tolerancia:
                            return mejor_combinacion
        
        return mejor_combinacion
    
    def _encontrar_mejor_grupo(self, objetivos_pequeños, costos_disponibles):
        """Encuentra el mejor grupo de objetivos pequeños para un costo disponible"""
        mejor_grupo = None
        menor_diferencia = float('inf')
        
        # Limitar la búsqueda a grupos de máximo 5 objetivos
        max_objetivos_por_grupo = min(5, len(objetivos_pequeños))
        
        for tamaño_grupo in range(2, max_objetivos_por_grupo + 1):
            for grupo in combinations(objetivos_pequeños, tamaño_grupo):
                suma_grupo = sum(obj[1] for obj in grupo)
                
                # Buscar el mejor costo o combinación de costos para este grupo
                for max_costos in [1, 2]:
                    combinacion = self._buscar_coincidencia_exacta(costos_disponibles, suma_grupo, max_costos, tolerancia=suma_grupo * 0.15)
                    
                    if combinacion:
                        diferencia = abs(combinacion['suma'] - suma_grupo)
                        if diferencia < menor_diferencia:
                            menor_diferencia = diferencia
                            mejor_grupo = {
                                'objetivos': list(grupo),
                                'costos': combinacion['costos'],
                                'suma': combinacion['suma']
                            }
                            
                            # Si encontramos una coincidencia muy buena, la tomamos
                            if diferencia / suma_grupo < 0.05:
                                return mejor_grupo
        
        return mejor_grupo
    
    def _buscar_coincidencia_exacta(self, costos, objetivo, max_elementos, tolerancia=0.001):
        """Busca combinaciones exactas"""
        for num_elementos in range(1, min(max_elementos + 1, len(costos) + 1)):
            for combinacion in combinations(costos, num_elementos):
                suma = sum(combinacion)
                if abs(suma - objetivo) <= tolerancia:
                    return {'costos': list(combinacion), 'suma': suma}
        return None
    
    def _buscar_mejor_combinacion_agresiva(self, costos, objetivo):
        """Búsqueda agresiva optimizada"""
        mejor_combinacion = None
        menor_diferencia_relativa = float('inf')
        
        costos_utiles = [c for c in costos if c <= objetivo * 2.0]
        costos_ordenados = sorted(costos_utiles, key=lambda x: abs(x - objetivo))[:20]
        
        for num_elementos in range(1, min(7, len(costos_ordenados) + 1)):
            for combo in combinations(costos_ordenados, num_elementos):
                suma = sum(combo)
                diferencia = abs(suma - objetivo)
                diferencia_relativa = diferencia / objetivo
                
                if diferencia_relativa < menor_diferencia_relativa and suma <= objetivo * 1.8:
                    menor_diferencia_relativa = diferencia_relativa
                    mejor_combinacion = {'costos': list(combo), 'suma': suma}
                    
                    if diferencia_relativa < 0.15:
                        break
            
            if mejor_combinacion and menor_diferencia_relativa < 0.15:
                break
        
        return mejor_combinacion
    
    def _distribuir_forzadamente(self, asignaciones, costos_restantes):
        """Distribución forzada de costos restantes"""
        asignaciones_ordenadas = sorted(asignaciones, key=lambda x: x.precision)
        
        for costo in costos_restantes:
            mejor_asignacion = None
            mejor_mejora = -float('inf')
            
            for asig in asignaciones_ordenadas:
                nueva_suma = asig.suma + costo
                nueva_diferencia = abs(nueva_suma - asig.valor_objetivo)
                diferencia_actual = asig.diferencia
                
                mejora = diferencia_actual - nueva_diferencia
                bonus = (100 - asig.precision) * 0.01
                mejora_total = mejora + bonus
                
                if mejora_total > mejor_mejora:
                    mejor_mejora = mejora_total
                    mejor_asignacion = asig
            
            if mejor_asignacion:
                mejor_asignacion.costos.append(costo)
                mejor_asignacion.suma += costo
                mejor_asignacion.diferencia = abs(mejor_asignacion.suma - mejor_asignacion.valor_objetivo)
                mejor_asignacion.precision = max(0, 100 - (mejor_asignacion.diferencia / mejor_asignacion.valor_objetivo) * 100)