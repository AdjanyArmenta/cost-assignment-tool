"""
Aplicación principal - Asignador de Costos
"""
import streamlit as st
import numpy as np
import pandas as pd
import time

# Importar módulos locales
from solver import CostAssignmentSolver
from utils import (parsear_costos, parsear_objetivos, crear_csv_download, 
                   calcular_metricas, preparar_datos_tabla)
from config import (PAGE_CONFIG, HEADER_STYLE, INSTRUCCIONES_SIDEBAR)

# Configuración de la página
st.set_page_config(**PAGE_CONFIG)

def mostrar_header():
    """Muestra el header principal de la aplicación"""
    st.markdown(HEADER_STYLE, unsafe_allow_html=True)

def configurar_sidebar():
    """Configura y muestra el sidebar con instrucciones"""
    with st.sidebar:
        st.markdown("## 📋 Instrucciones")
        st.markdown(INSTRUCCIONES_SIDEBAR)
        

def obtener_inputs():
    """Muestra y obtiene los inputs del usuario"""
    col1, col2 = st.columns([1, 1])
    
    # Determinar valores default
    costos_default = ""
    objetivos_default = ""
    
    
    with col1:
        st.markdown("### 1️⃣ Costos Individuales")
        texto_costos = st.text_area(
            "Pega tus costos separados por espacios:",
            value=costos_default,
            height=150,
        )
        
        # Validación de costos
        if texto_costos:
            costos = parsear_costos(texto_costos)
            if costos:
                st.success(f"✅ {len(costos)} costos válidos | Suma: {sum(costos):.2f}")
                st.info(f"📊 Rango: {min(costos):.2f} - {max(costos):.2f} | Promedio: {np.mean(costos):.2f}")
    
    with col2:
        st.markdown("### 2️⃣ Objetivos")
        texto_objetivos = st.text_area(
            "Pega tus objetivos (NOMBRE: valor):",
            value=objetivos_default,
            height=150,
            placeholder="Ejemplo:\nPROYECTO-A: 2.50\nPROYECTO-B: 1.75"
        )
        
        # Validación de objetivos
        if texto_objetivos:
            objetivos = parsear_objetivos(texto_objetivos)
            if objetivos:
                st.success(f"✅ {len(objetivos)} objetivos válidos | Suma: {sum(objetivos.values()):.2f}")
                valores_obj = list(objetivos.values())
                st.info(f"📊 Rango: {min(valores_obj):.2f} - {max(valores_obj):.2f} | Promedio: {np.mean(valores_obj):.2f}")
    
    return texto_costos, texto_objetivos

def mostrar_info_carga(info_carga):
    """Muestra información sobre la carga de datos"""
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Suma Costos", f"{info_carga['suma_costos']:.2f}")
    with col_info2:
        st.metric("Suma Objetivos", f"{info_carga['suma_objetivos']:.2f}")
    with col_info3:
        diferencia = info_carga['diferencia']
        st.metric("Diferencia", f"{abs(diferencia):.2f}", 
                 f"{'Sobran costos' if diferencia > 0 else 'Faltan costos' if diferencia < 0 else 'Perfecto'}")
    
    # Advertencias
    if abs(diferencia) > 0.01:
        if diferencia > 0:
            st.warning(f"⚠️ La suma de costos ({info_carga['suma_costos']:.2f}) es mayor que la suma de objetivos ({info_carga['suma_objetivos']:.2f}). "
                     f"Sobran {diferencia:.2f} en costos que quedarán sin asignar.")
        else:
            st.warning(f"⚠️ La suma de objetivos ({info_carga['suma_objetivos']:.2f}) es mayor que la suma de costos ({info_carga['suma_costos']:.2f}). "
                     f"Algunos objetivos podrían quedar sin costos asignados.")
    else:
        st.success("✅ Las sumas coinciden perfectamente")

def mostrar_metricas(metricas):
    """Muestra las métricas principales del resultado"""
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    
    with col_m1:
        st.metric("🎯 Precisión", f"{metricas['precision_promedio']:.1f}%")
    with col_m2:
        st.metric("📦 Costos Usados", f"{metricas['costos_utilizados']}/{metricas['costos_utilizados'] + metricas['costos_sin_usar']}")
    with col_m3:
        st.metric("🎪 Asignaciones", f"{metricas['total_asignaciones']}")
    with col_m4:
        st.metric("👥 Grupos", f"{metricas['grupos_creados']}")
    with col_m5:
        if metricas['costos_sin_usar'] > 0:
            st.metric("📭 Sin Usar", f"{metricas['costos_sin_usar']} costos", delta=None, delta_color="inverse")
        elif metricas['objetivos_sin_asignar'] > 0:
            st.metric("❌ Sin Asignar", f"{metricas['objetivos_sin_asignar']} obj.", delta=None, delta_color="inverse")
        else:
            st.metric("✅ Completo", "100%")

def mostrar_tabla_resultados(data_display):
    """Muestra la tabla de resultados"""
    st.markdown("---")
    st.markdown("### 📋 Detalle de Asignaciones")
    
    df_display = pd.DataFrame(data_display)
    
    st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True,
        height=600,
        column_config={
            "Objetivo": st.column_config.TextColumn(
                "Objetivo",
                width="large",
            ),
            "Costos Asignados": st.column_config.TextColumn(
                "Costos Asignados",
                width="large",
            )
        }
    )

def mostrar_detalle_grupos(resultado):
    """Muestra el detalle de grupos si existen"""
    grupos = [a for a in resultado if a.es_grupo]
    if grupos:
        st.info("👥 = Grupo de objetivos agrupados automáticamente")
        
        with st.expander("👥 Ver Detalle de Grupos"):
            for grupo in grupos:
                st.markdown(f"**Grupo:** {grupo.objetivo}")
                st.markdown(f"**Valor Total:** {grupo.valor_objetivo:.2f}")
                st.markdown(f"**Costos Asignados:** {' + '.join(map(str, grupo.costos))}")
                st.markdown(f"**Suma Real:** {grupo.suma:.2f}")
                st.markdown("**Componentes:**")
                for nombre, valor in grupo.objetivos_agrupados:
                    st.markdown(f"  - {nombre}: {valor:.2f}")
                st.markdown("---")

def mostrar_costos_no_utilizados(costos, resultado, costos_sin_usar):
    """Muestra los costos no utilizados si los hay"""
    if costos_sin_usar > 0:
        with st.expander(f"📭 Costos No Utilizados ({costos_sin_usar})"):
            costos_usados = []
            for asig in resultado:
                costos_usados.extend(asig.costos)
            
            costos_no_usados = [c for c in costos if c not in costos_usados]
            # Eliminar duplicados manteniendo el orden
            costos_finales = []
            for c in costos:
                if c in costos_no_usados and c not in costos_finales:
                    costos_finales.append(c)
                elif c in costos_no_usados:
                    costos_usados.append(c)
                    costos_no_usados.remove(c)
            
            st.write("Costos que no pudieron ser asignados:")
            st.write(", ".join([f"{c:.2f}" for c in costos_finales]))
            st.write(f"**Suma total no utilizada:** {sum(costos_finales):.2f}")

def mostrar_estadisticas_detalladas(resultado, grupos_creados):
    """Muestra estadísticas adicionales en un expander"""
    with st.expander("📈 Estadísticas Detalladas"):
        perfectas = len([a for a in resultado if a.precision >= 99.9])
        excelentes = len([a for a in resultado if a.precision >= 90])
        buenas = len([a for a in resultado if a.precision >= 70])
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("🏆 Asignaciones Perfectas", perfectas)
        with col_s2:
            st.metric("⭐ Asignaciones Excelentes", excelentes)
        with col_s3:
            st.metric("👍 Asignaciones Buenas", buenas)
        
        # Análisis de agrupaciones
        if grupos_creados > 0:
            st.markdown("---")
            st.markdown("#### 📊 Análisis de Agrupaciones")
            grupos = [a for a in resultado if a.es_grupo]
            total_objetivos_agrupados = sum(len(g.objetivos_agrupados) for g in grupos)
            st.write(f"Se agruparon {total_objetivos_agrupados} objetivos en {grupos_creados} grupos")
            
            # Eficiencia de grupos
            precision_grupos = np.mean([g.precision for g in grupos]) if grupos else 0
            st.metric("🎯 Precisión Promedio de Grupos", f"{precision_grupos:.1f}%")

def main():
    """Función principal de la aplicación"""
    # Mostrar componentes de UI
    mostrar_header()
    configurar_sidebar()
    
    # Obtener inputs
    texto_costos, texto_objetivos = obtener_inputs()
    
    # Botón principal
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    
    with col_btn2:
        calcular_clicked = st.button("🚀 Calcular Asignación Óptima", type="primary", use_container_width=True)
    
    # Procesar si se hizo click
    if calcular_clicked:
        # Validar datos
        costos = parsear_costos(texto_costos) if texto_costos else None
        objetivos = parsear_objetivos(texto_objetivos) if texto_objetivos else None
        
        if not costos or not objetivos:
            st.error("❌ Por favor ingresa costos y objetivos válidos")
        else:
            # Crear solver y procesar
            solver = CostAssignmentSolver()
            
            try:
                # Cargar datos
                info_carga = solver.cargar_datos(costos, objetivos)
                mostrar_info_carga(info_carga)
                
                # Advertencia si hay objetivos muy pequeños
                costo_minimo = min(costos)
                objetivos_pequeños = [(n, v) for n, v in objetivos.items() if v < costo_minimo * 0.7]
                if objetivos_pequeños:
                    st.info(f"ℹ️ Se detectaron {len(objetivos_pequeños)} objetivos menores al 70% del costo mínimo. Se aplicará agrupación automática.")
                
                # Procesar
                resultado = solver.resolver_completa()
                
                # Mostrar resultados
                st.markdown("---")
                st.markdown("## 📊 Resultados")
                
                # Calcular y mostrar métricas
                metricas = calcular_metricas(resultado, len(costos))
                metricas['total_asignaciones'] = len(resultado)
                mostrar_metricas(metricas)
                
                # Preparar y mostrar tabla
                data_display = preparar_datos_tabla(resultado)
                mostrar_tabla_resultados(data_display)
                
                # Mostrar información adicional
                mostrar_detalle_grupos(resultado)
                mostrar_costos_no_utilizados(costos, resultado, metricas['costos_sin_usar'])
                
                # Botón de descarga
                csv_data = crear_csv_download(resultado)
                st.download_button(
                    label="📄 Descargar Resultados CSV",
                    data=csv_data,
                    file_name=f"asignacion_costos_{int(time.time())}.csv",
                    mime="text/csv",
                    type="secondary",
                    use_container_width=True
                )
                
                # Estadísticas detalladas
                mostrar_estadisticas_detalladas(resultado, metricas['grupos_creados'])
                
            except Exception as e:
                st.error(f"❌ Error en el procesamiento: {str(e)}")

if __name__ == "__main__":
    main()