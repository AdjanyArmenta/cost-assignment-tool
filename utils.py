"""
Funciones auxiliares para el asignador de costos
"""
import pandas as pd
import streamlit as st
import io

def parsear_costos(texto_costos):
    """
    Parsea el texto de costos separados por comas
    
    Args:
        texto_costos (str): String con costos separados por comas
        
    Returns:
        list: Lista de floats con los costos, o None si hay error
    """
    try:
        costos = [float(x.strip()) for x in texto_costos.split(',') if x.strip()]
        return costos
    except ValueError:
        st.error("❌ Error: Algunos valores de costos no son números válidos")
        return None

def parsear_objetivos(texto_objetivos):
    """
    Parsea el texto de objetivos en formato NOMBRE: valor
    
    Args:
        texto_objetivos (str): String con objetivos uno por línea
        
    Returns:
        dict: Diccionario {nombre: valor}, o None si hay error
    """
    try:
        objetivos = {}
        for linea in texto_objetivos.strip().split('\n'):
            if ':' in linea:
                nombre, valor = linea.split(':', 1)
                objetivos[nombre.strip()] = float(valor.strip())
        return objetivos
    except ValueError:
        st.error("❌ Error: Algunos valores de objetivos no son números válidos")
        return None

def crear_csv_download(asignaciones):
    """
    Crea un string CSV a partir de las asignaciones para descarga
    
    Args:
        asignaciones (list): Lista de objetos Asignacion
        
    Returns:
        str: String con el contenido CSV
    """
    data = []
    for asig in asignaciones:
        # Si es un grupo, expandir en filas individuales
        if asig.es_grupo and asig.objetivos_agrupados:
            # Fila del grupo
            data.append({
                'Objetivo': asig.objetivo,
                'Valor_Objetivo': asig.valor_objetivo,
                'Costos_Asignados': ' + '.join(map(str, asig.costos)) if asig.costos else 'Sin costos',
                'Suma_Real': asig.suma,
                'Diferencia': asig.diferencia,
                'Precision_%': asig.precision,
                'Es_Grupo': 'SI'
            })
            # Filas individuales del grupo
            for nombre_ind, valor_ind in asig.objetivos_agrupados:
                data.append({
                    'Objetivo': f"  └─ {nombre_ind}",
                    'Valor_Objetivo': valor_ind,
                    'Costos_Asignados': '(parte del grupo anterior)',
                    'Suma_Real': '',
                    'Diferencia': '',
                    'Precision_%': '',
                    'Es_Grupo': ''
                })
        else:
            data.append({
                'Objetivo': asig.objetivo,
                'Valor_Objetivo': asig.valor_objetivo,
                'Costos_Asignados': ' + '.join(map(str, asig.costos)) if asig.costos else 'Sin costos',
                'Suma_Real': asig.suma,
                'Diferencia': asig.diferencia,
                'Precision_%': asig.precision,
                'Es_Grupo': 'NO'
            })
    
    df = pd.DataFrame(data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

def calcular_metricas(resultado, costos_totales):
    """
    Calcula las métricas principales del resultado
    
    Args:
        resultado (list): Lista de asignaciones
        costos_totales (int): Número total de costos
        
    Returns:
        dict: Diccionario con las métricas calculadas
    """
    import numpy as np
    
    precision_promedio = np.mean([asig.precision for asig in resultado if asig.precision > 0])
    costos_utilizados = sum(len(asig.costos) for asig in resultado)
    costos_sin_usar = costos_totales - costos_utilizados
    objetivos_sin_asignar = len([a for a in resultado if not a.costos])
    grupos_creados = len([a for a in resultado if a.es_grupo])
    
    return {
        'precision_promedio': precision_promedio,
        'costos_utilizados': costos_utilizados,
        'costos_sin_usar': costos_sin_usar,
        'objetivos_sin_asignar': objetivos_sin_asignar,
        'grupos_creados': grupos_creados
    }

def preparar_datos_tabla(resultado):
    """
    Prepara los datos para mostrar en la tabla
    
    Args:
        resultado (list): Lista de asignaciones
        
    Returns:
        list: Lista de diccionarios con los datos formateados
    """
    data_display = []
    for asig in sorted(resultado, key=lambda x: x.precision, reverse=True):
        costos_texto = ' + '.join(map(str, asig.costos)) if asig.costos else 'Sin costos'
        
        # Indicador visual para grupos
        icono = '👥 ' if asig.es_grupo else ''
        
        data_display.append({
            'Objetivo': icono + asig.objetivo,
            'Valor Objetivo': f"{asig.valor_objetivo:.2f}",
            'Costos Asignados': costos_texto,
            'Suma Real': f"{asig.suma:.2f}",
            'Diferencia': f"{asig.diferencia:.3f}",
            'Precisión': f"{asig.precision:.1f}%"
        })
    
    return data_display