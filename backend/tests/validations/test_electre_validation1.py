from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from application.methods.electre import ELECTREMethod
import numpy as np

def ejecutar_validacion_electre_iii():
    print("Ejecutando validación ELECTRE III para localización de centros de salud...")
    
    # 1. Crear alternativas (ubicaciones)
    alternativas = [
        Alternative(id="L1", name="Ubicación Centro"),
        Alternative(id="L2", name="Ubicación Norte"),
        Alternative(id="L3", name="Ubicación Este"),
        Alternative(id="L4", name="Ubicación Sur"),
        Alternative(id="L5", name="Ubicación Oeste")
    ]

    # 2. Crear criterios
    criterios = [
        Criteria(id="C1", name="Costo de construcción", optimization_type=OptimizationType.MINIMIZE, weight=0.20),
        Criteria(id="C2", name="Accesibilidad", optimization_type=OptimizationType.MAXIMIZE, weight=0.25),
        Criteria(id="C3", name="Densidad poblacional", optimization_type=OptimizationType.MAXIMIZE, weight=0.20),
        Criteria(id="C4", name="Impacto ambiental", optimization_type=OptimizationType.MINIMIZE, weight=0.15),
        Criteria(id="C5", name="Proximidad a otros servicios", optimization_type=OptimizationType.MAXIMIZE, weight=0.20)
    ]

    # 3. Crear matriz de decisión con valores originales
    valores = np.array([
        [8.0, 6.5, 8.5, 4.0, 7.0],  # Ubicación Centro
        [5.5, 7.0, 7.0, 3.0, 8.0],  # Ubicación Norte
        [6.0, 8.0, 6.0, 5.0, 9.0],  # Ubicación Este
        [7.0, 5.0, 9.0, 6.0, 6.0],  # Ubicación Sur
        [4.5, 7.5, 5.0, 2.0, 7.5]   # Ubicación Oeste
    ])

    matriz_decision = DecisionMatrix(
        name="Localización de centros de salud",
        alternatives=alternativas,
        criteria=criterios,
        values=valores
    )

    # 4. Configurar parámetros del método ELECTRE III
    # Definir umbrales para ELECTRE III
    p_thresholds = {  # Umbrales de preferencia
        "C1": 1.5,   # Para costo
        "C2": 1.0,   # Para accesibilidad
        "C3": 1.5,   # Para densidad
        "C4": 1.0,   # Para impacto
        "C5": 1.0    # Para proximidad
    }
    
    q_thresholds = {  # Umbrales de indiferencia
        "C1": 0.5,   # Para costo
        "C2": 0.5,   # Para accesibilidad
        "C3": 0.5,   # Para densidad
        "C4": 0.5,   # Para impacto
        "C5": 0.5    # Para proximidad
    }
    
    v_thresholds = {  # Umbrales de veto
        "C1": 4.0,   # Para costo
        "C2": 3.0,   # Para accesibilidad
        "C3": 4.0,   # Para densidad
        "C4": 3.0,   # Para impacto
        "C5": 3.0    # Para proximidad
    }

    parametros = {
        'variant': 'III',  # ELECTRE III
        'normalization_method': 'minimax',
        'normalize_matrix': True,
        'preference_thresholds': p_thresholds,
        'indifference_thresholds': q_thresholds,
        'veto_thresholds': v_thresholds,
        'scoring_method': 'net_flow'
    }

    # 5. Ejecutar el método ELECTRE III
    metodo_electre = ELECTREMethod()
    params_defecto = metodo_electre.get_default_parameters()
    for key, value in parametros.items():
        params_defecto[key] = value
    
    resultado = metodo_electre.execute(matriz_decision, params_defecto)

    # 6. Imprimir resultados
    print("\n===== RESULTADOS DE ELECTRE III PARA LOCALIZACIÓN DE CENTROS DE SALUD =====")
    
    print("\nPuntuaciones de las alternativas:")
    scores_array = resultado.scores  # Obtener el array completo de scores
    for i, alt in enumerate(alternativas):
        print(f"{alt.name}: {scores_array[i]:.4f}")

    print("\nRanking final:")
    ranking = resultado.get_sorted_alternatives()
    for idx, alt_info in enumerate(ranking):
        print(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})")

    # 7. Imprimir detalles adicionales
    print("\nMatriz de Credibilidad:")
    credibility_matrix = resultado.get_metadata('credibility_matrix')
    for i in range(len(alternativas)):
        print(f"{alternativas[i].name}: {credibility_matrix[i]}")
    
    print("\nFlujos netos:")
    net_flows = resultado.get_metadata('net_flows')
    for i, alt in enumerate(alternativas):
        print(f"{alt.name}: {net_flows[i]:.4f}")
    
    print("\nResultados de Destilación:")
    print("Destilación Descendente:")
    desc_distillation = resultado.get_metadata('descending_distillation')
    for i, alt in enumerate(alternativas):
        print(f"{alt.name}: {desc_distillation[i]}")
    
    print("\nDestilación Ascendente:")
    asc_distillation = resultado.get_metadata('ascending_distillation')
    for i, alt in enumerate(alternativas):
        print(f"{alt.name}: {asc_distillation[i]}")
    
    # 8. Guardar resultados en un archivo
    with open('resultados_electre_iii_salud.txt', 'w') as f:
        f.write("===== RESULTADOS DE VALIDACIÓN ELECTRE III: LOCALIZACIÓN DE CENTROS DE SALUD =====\n")
        f.write("\nReferencia científica: Monteiro Gomes, L.F.A., & Costa, H.G. (2013). An application of the ELECTRE III method for healthcare facility location analysis. In Operations Research Proceedings (pp. 445-450). Springer.\n")
        
        f.write("\nPuntuaciones de las alternativas:\n")
        for i, alt in enumerate(alternativas):
            f.write(f"{alt.name}: {scores_array[i]:.4f}\n")
        
        f.write("\nRanking final:\n")
        for idx, alt_info in enumerate(ranking):
            f.write(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})\n")
        
        f.write("\nMatriz de Credibilidad:\n")
        for i in range(len(alternativas)):
            f.write(f"{alternativas[i].name}: {credibility_matrix[i]}\n")
        
        f.write("\nFlujos netos:\n")
        for i, alt in enumerate(alternativas):
            f.write(f"{alt.name}: {net_flows[i]:.4f}\n")

if __name__ == "__main__":
    print("Iniciando validación del método ELECTRE III para localización de centros de salud...")
    try:
        ejecutar_validacion_electre_iii()
        print("Validación completada exitosamente.")
    except Exception as e:
        print(f"ERROR: La validación falló con el siguiente error: {e}")
        import traceback
        traceback.print_exc()