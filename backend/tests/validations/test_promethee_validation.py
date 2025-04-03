from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from application.methods.promethee import PROMETHEEMethod
import numpy as np

def ejecutar_validacion_promethee():
    print("Ejecutando validación PROMETHEE para selección de ubicación industrial...")
    
    # 1. Crear alternativas (ubicaciones)
    alternativas = [
        Alternative(id="A1", name="Ubicación Industrial A"),
        Alternative(id="A2", name="Ubicación Industrial B"),
        Alternative(id="A3", name="Ubicación Industrial C"),
        Alternative(id="A4", name="Ubicación Industrial D"),
        Alternative(id="A5", name="Ubicación Industrial E")
    ]

    # 2. Crear criterios
    criterios = [
        Criteria(id="C1", name="Costo del terreno", optimization_type=OptimizationType.MINIMIZE, weight=0.25),
        Criteria(id="C2", name="Disponibilidad de mano de obra", optimization_type=OptimizationType.MAXIMIZE, weight=0.20),
        Criteria(id="C3", name="Accesibilidad", optimization_type=OptimizationType.MAXIMIZE, weight=0.15),
        Criteria(id="C4", name="Proximidad a materias primas", optimization_type=OptimizationType.MAXIMIZE, weight=0.15),
        Criteria(id="C5", name="Regulaciones ambientales", optimization_type=OptimizationType.MINIMIZE, weight=0.10),
        Criteria(id="C6", name="Incentivos fiscales", optimization_type=OptimizationType.MAXIMIZE, weight=0.15)
    ]

    # 3. Crear matriz de decisión con valores originales
    valores = np.array([
        [7, 8, 7, 6, 5, 8],  # Ubicación A
        [5, 6, 8, 8, 7, 6],  # Ubicación B 
        [8, 7, 6, 7, 4, 9],  # Ubicación C
        [6, 9, 8, 5, 6, 7],  # Ubicación D
        [4, 5, 7, 9, 8, 5]   # Ubicación E
    ])

    matriz_decision = DecisionMatrix(
        name="Selección de ubicación industrial",
        alternatives=alternativas,
        criteria=criterios,
        values=valores
    )

    # 4. Configurar preferencias por criterio
    # Definir tipo de función de preferencia por criterio
    preference_functions = {
        "C1": "v-shape",        # Criterio 1: Función Tipo III (V-shape)
        "C2": "v-shape",        # Criterio 2: Función Tipo III (V-shape)
        "C3": "usual",          # Criterio 3: Función Tipo I (Usual)
        "C4": "v-shape",        # Criterio 4: Función Tipo III (V-shape)
        "C5": "level",          # Criterio 5: Función Tipo IV (Level)
        "C6": "v-shape-indifference"  # Criterio 6: Función Tipo V (V-shape con indiferencia)
    }
    
    # Definir umbrales de preferencia (p)
    p_thresholds = {
        "C1": 2.0,  # Para costo del terreno
        "C2": 2.0,  # Para disponibilidad de mano de obra
        "C3": 0.0,  # No aplica para función Usual
        "C4": 2.0,  # Para proximidad a materias primas
        "C5": 2.0,  # Para regulaciones ambientales
        "C6": 3.0   # Para incentivos fiscales
    }
    
    # Definir umbrales de indiferencia (q)
    q_thresholds = {
        "C1": 0.0,  # No aplica para V-shape
        "C2": 0.0,  # No aplica para V-shape
        "C3": 0.0,  # No aplica para Usual
        "C4": 0.0,  # No aplica para V-shape
        "C5": 1.0,  # Para regulaciones ambientales
        "C6": 1.0   # Para incentivos fiscales
    }
    
    # Definir umbrales de gaussiana (s)
    s_thresholds = {
        "C1": 0.0,  # No aplica para V-shape
        "C2": 0.0,  # No aplica para V-shape
        "C3": 0.0,  # No aplica para Usual
        "C4": 0.0,  # No aplica para V-shape
        "C5": 0.0,  # No aplica para Level
        "C6": 0.0   # No aplica para V-shape con indiferencia
    }

    # 5. Configurar parámetros del método PROMETHEE
    parametros = {
        'variant': 'II',
        'default_preference_function': 'v-shape',
        'preference_functions': preference_functions,
        'p_thresholds': p_thresholds,
        'q_thresholds': q_thresholds,
        's_thresholds': s_thresholds,
        'normalization_method': 'minimax',
        'normalize_matrix': True
    }

    # 6. Ejecutar el método PROMETHEE
    metodo_promethee = PROMETHEEMethod()
    params_defecto = metodo_promethee.get_default_parameters()
    for key, value in parametros.items():
        params_defecto[key] = value
    
    resultado = metodo_promethee.execute(matriz_decision, params_defecto)

    # 7. Imprimir resultados
    print("\n===== RESULTADOS DE PROMETHEE II PARA SELECCIÓN DE UBICACIÓN INDUSTRIAL =====")
    
    print("\nPuntuaciones finales (Phi neto):")
    scores_array = resultado.scores  # Obtener el array completo de scores
    for i, alt in enumerate(alternativas):
        print(f"{alt.name}: {scores_array[i]:.4f}")

    print("\nRanking final:")
    ranking = resultado.get_sorted_alternatives()
    for idx, alt_info in enumerate(ranking):
        print(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})")

    # 8. Imprimir flujos de preferencia
    preference_matrix = resultado.get_metadata('preference_matrix')
    print("\nMatriz de Preferencia Agregada:")
    for i in range(len(alternativas)):
        print(f"{alternativas[i].name}: {preference_matrix[i]}")
    
    positive_flow = resultado.get_metadata('positive_flow')
    negative_flow = resultado.get_metadata('negative_flow')
    
    print("\nFlujos de Preferencia:")
    print("Alternativa | Phi+ (Salida) | Phi- (Entrada) | Phi (Neto)")
    print("-" * 60)
    for i, alt in enumerate(alternativas):
        print(f"{alt.name}: {positive_flow[i]:.4f} | {negative_flow[i]:.4f} | {scores_array[i]:.4f}")
    
    # 9. Guardar resultados en un archivo
    with open('resultados_promethee_ubicacion.txt', 'w') as f:
        f.write("===== RESULTADOS DE VALIDACIÓN PROMETHEE: SELECCIÓN DE UBICACIÓN INDUSTRIAL =====\n")
        f.write("\nReferencia científica: Behzadian, M., Kazemzadeh, R. B., Albadvi, A., & Aghdasi, M. (2010). PROMETHEE: A comprehensive literature review on methodologies and applications. European Journal of Operational Research, 200(1), 198-215.\n")
        
        f.write("\nPuntuaciones finales (Phi neto):\n")
        for i, alt in enumerate(alternativas):
            f.write(f"{alt.name}: {scores_array[i]:.4f}\n")
        
        f.write("\nRanking final:\n")
        for idx, alt_info in enumerate(ranking):
            f.write(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})\n")
        
        f.write("\nFlujos de Preferencia:\n")
        f.write("Alternativa | Phi+ (Salida) | Phi- (Entrada) | Phi (Neto)\n")
        f.write("-" * 60 + "\n")
        for i, alt in enumerate(alternativas):
            f.write(f"{alt.name}: {positive_flow[i]:.4f} | {negative_flow[i]:.4f} | {scores_array[i]:.4f}\n")

if __name__ == "__main__":
    print("Iniciando validación del método PROMETHEE para selección de ubicación industrial...")
    try:
        ejecutar_validacion_promethee()
        print("Validación completada exitosamente.")
    except Exception as e:
        print(f"ERROR: La validación falló con el siguiente error: {e}")
        import traceback
        traceback.print_exc()