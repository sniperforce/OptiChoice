from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from application.methods.electre import ELECTREMethod
import numpy as np

def ejecutar_validacion_electre():
    print("Ejecutando validación ELECTRE para selección de proyectos de inversión...")
    
    # 1. Crear alternativas (proyectos de inversión)
    alternativas = [
        Alternative(id="A1", name="Proyecto 1"),
        Alternative(id="A2", name="Proyecto 2"),
        Alternative(id="A3", name="Proyecto 3"),
        Alternative(id="A4", name="Proyecto 4"),
        Alternative(id="A5", name="Proyecto 5")
    ]

    # 2. Crear criterios
    criterios = [
        Criteria(id="C1", name="Retorno de Inversión", optimization_type=OptimizationType.MAXIMIZE, weight=0.35),
        Criteria(id="C2", name="Riesgo", optimization_type=OptimizationType.MINIMIZE, weight=0.25),
        Criteria(id="C3", name="Impacto Social", optimization_type=OptimizationType.MAXIMIZE, weight=0.20),
        Criteria(id="C4", name="Impacto Ambiental", optimization_type=OptimizationType.MINIMIZE, weight=0.20)
    ]

    # 3. Crear matriz de decisión con valores originales
    # Valores basados en Figueira et al. (2005)
    valores = np.array([
        [8, 3, 7, 5],  # Proyecto 1
        [7, 5, 8, 6],  # Proyecto 2
        [9, 6, 6, 7],  # Proyecto 3
        [6, 4, 9, 3],  # Proyecto 4
        [8, 7, 7, 4]   # Proyecto 5
    ])

    matriz_decision = DecisionMatrix(
        name="Selección de proyectos de inversión",
        alternatives=alternativas,
        criteria=criterios,
        values=valores
    )

    # 4. Configurar parámetros del método ELECTRE
    parametros = {
        'variant': 'I',  # ELECTRE I
        'concordance_threshold': 0.65,  # Umbral de concordancia
        'discordance_threshold': 0.35,  # Umbral de discordancia
        'normalization_method': 'minimax',
        'normalize_matrix': True,
        'scoring_method': 'net_flow'
    }

    # 5. Ejecutar el método ELECTRE
    metodo_electre = ELECTREMethod()
    params_defecto = metodo_electre.get_default_parameters()
    for key, value in parametros.items():
        params_defecto[key] = value
    
    resultado = metodo_electre.execute(matriz_decision, params_defecto)

    # 6. Imprimir resultados
    print("\n===== RESULTADOS DE ELECTRE PARA SELECCIÓN DE PROYECTOS DE INVERSIÓN =====")
    
    print("\nPuntuaciones de las alternativas:")
    scores_array = resultado.scores  
    for i, alt in enumerate(alternativas):
        print(f"{alt.name}: {scores_array[i]:.4f}")

    print("\nRanking final:")
    ranking = resultado.get_sorted_alternatives()
    for idx, alt_info in enumerate(ranking):
        print(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})")

    # 7. Imprimir matriz de superación
    print("\nMatriz de Superación (Outranking):")
    outranking_matrix = resultado.get_metadata('outranking_matrix')
    for i in range(len(alternativas)):
        print(f"{alternativas[i].name}: {outranking_matrix[i]}")
    
    # 8. Imprimir núcleo (kernel) - alternativas no dominadas
    non_dominated = resultado.get_metadata('non_dominated_alternatives')
    print("\nAlternativas no dominadas (kernel):")
    for idx in non_dominated:
        print(f"- {alternativas[idx].name}")
    
    # 9. Guardar resultados en un archivo
    with open('resultados_electre_proyectos.txt', 'w') as f:
        f.write("===== RESULTADOS DE VALIDACIÓN ELECTRE: SELECCIÓN DE PROYECTOS DE INVERSIÓN =====\n")
        f.write("\nReferencia científica: Figueira, J., Greco, S., & Ehrgott, M. (2005). Multiple Criteria Decision Analysis: State of the Art Surveys. Springer Science & Business Media.\n")
        
        f.write("\nPuntuaciones de las alternativas:\n")
        for i, alt in enumerate(alternativas):
            f.write(f"{alt.name}: {resultado.scores[i]:.4f}\n")
        
        f.write("\nRanking final:\n")
        for idx, alt_info in enumerate(ranking):
            f.write(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})\n")
        
        f.write("\nMatriz de Superación (Outranking):\n")
        for i in range(len(alternativas)):
            f.write(f"{alternativas[i].name}: {outranking_matrix[i]}\n")
        
        f.write("\nAlternativas no dominadas (kernel):\n")
        for idx in non_dominated:
            f.write(f"- {alternativas[idx].name}\n")

if __name__ == "__main__":
    print("Iniciando validación del método ELECTRE para selección de proyectos de inversión...")
    try:
        ejecutar_validacion_electre()
        print("Validación completada exitosamente.")
    except Exception as e:
        print(f"ERROR: La validación falló con el siguiente error: {e}")
        import traceback
        traceback.print_exc()