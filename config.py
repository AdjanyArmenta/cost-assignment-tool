"""
Configuraciones y constantes para el asignador de costos
"""

# Configuración de la página de Streamlit
PAGE_CONFIG = {
    "page_title": "💰 Asignador de Costos",
    "page_icon": "💰",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Estilos CSS para el header
HEADER_STYLE = """
<div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
    <h1 style="color: white; text-align: center; margin: 0; font-size: 3rem;">💰 Asignador de Costos</h1>
    <p style="color: rgba(255,255,255,0.9); text-align: center; margin: 0.5rem 0 0 0; font-size: 1.2rem;">
        Herramienta para optimizar la distribución de costos
    </p>
    </div>
</div>
"""

# Instrucciones del sidebar
INSTRUCCIONES_SIDEBAR = """
1. **Pega tus costos** separados por comas
2. **Pega tus objetivos** uno por línea 
3. **Haz click en Calcular**
4. **Descarga los resultados** en CSV

### 🆕 Agrupación Automática:
- Los objetivos muy pequeños se agrupan automáticamente
- Ejemplo: Si tienes objetivos de 0.3 y 0.2, y el costo mínimo es 1.0
- Se agruparán como "OBJ-A + OBJ-B = 0.5" y se les asignará un costo cercano
"""

# Parámetros del algoritmo
ALGORITMO_CONFIG = {
    'umbral_objetivo_pequeño': 0.7,  # Objetivos menores al 70% del costo mínimo se consideran pequeños
    'max_objetivos_por_grupo': 5,    # Máximo número de objetivos en un grupo
    'tolerancia_grupo': 0.15,         # Tolerancia del 15% para coincidencias de grupos
    'max_elementos_busqueda': 7,     # Máximo número de elementos en combinaciones
    'factor_objetivo_grande': 2.0,    # Objetivos mayores a 2x el promedio son grandes
}