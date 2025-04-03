from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from application.methods.ahp import AHPMethod
import numpy as np

def ejecutar_validacion_proveedores():
    print("Ejecutando validación AHP para selección de proveedores...")
    
    # 1. Crear alternativas (proveedores)
    alternativas = [
        Alternative(id="P1", name="Proveedor A"),
        Alternative(id="P2", name="Proveedor B"),
        Alternative(id="P3", name="Proveedor C"),
        Alternative(id="P4", name="Proveedor D")
    ]

    # 2. Crear criterios
    criterios = [
        Criteria(id="C1", name="Calidad", optimization_type=OptimizationType.MAXIMIZE, weight=1.0),
        Criteria(id="C2", name="Capacidad de respuesta", optimization_type=OptimizationType.MAXIMIZE, weight=1.0),
        Criteria(id="C3", name="Precio", optimization_type=OptimizationType.MINIMIZE, weight=1.0),
        Criteria(id="C4", name="Desempeño ambiental", optimization_type=OptimizationType.MAXIMIZE, weight=1.0),
        Criteria(id="C5", name="Capacidad técnica", optimization_type=OptimizationType.MAXIMIZE, weight=1.0)
    ]

    # 3. Crear matriz de decisión con valores originales
    valores = np.array([
        [9, 7, 5, 6, 8],  # Proveedor A
        [7, 8, 7, 4, 7],  # Proveedor B
        [8, 6, 8, 8, 6],  # Proveedor C
        [6, 9, 6, 7, 5]   # Proveedor D
    ])

    matriz_decision = DecisionMatrix(
        name="Selección de proveedores",
        alternatives=alternativas,
        criteria=criterios,
        values=valores
    )

    # 4. Definir la matriz de comparación de criterios
    # Basada en Handfield et al. (2002)
    matriz_comparacion_criterios = np.array([
        [1.00, 2.00, 3.00, 4.00, 2.00],  # Calidad
        [0.50, 1.00, 2.00, 3.00, 1.00],  # Capacidad de respuesta
        [0.33, 0.50, 1.00, 2.00, 0.50],  # Precio
        [0.25, 0.33, 0.50, 1.00, 0.33],  # Desempeño ambiental
        [0.50, 1.00, 2.00, 3.00, 1.00]   # Capacidad técnica
    ])

    # 5. Configurar parámetros del método AHP
    parametros = {
        'criteria_comparison_matrix': matriz_comparacion_criterios,
        'alternatives_comparison_matrices': None,  # Usaremos los valores directos
        'consistency_ratio_threshold': 0.1,
        'weight_calculation_method': 'eigenvector',
        'use_pairwise_comparison_for_alternatives': False,  # Usar valores directos
        'show_consistency_details': True,
        'normalize_before_comparison': True,
        'normalization_method': 'minimax'
    }

    # 6. Ejecutar el método AHP
    metodo_ahp = AHPMethod()
    # Obtener parámetros por defecto y actualizarlos
    params_defecto = metodo_ahp.get_default_parameters()
    for key, value in parametros.items():
        params_defecto[key] = value
    
    # Ejecutar con los parámetros combinados
    resultado = metodo_ahp.execute(matriz_decision, params_defecto)

    # 7. Imprimir resultados
    print("\n===== RESULTADOS DE AHP PARA SELECCIÓN DE PROVEEDORES =====")
    print("\nPesos de los criterios:")
    pesos_criterios = resultado.get_metadata('criteria_weights')
    for i, criterio in enumerate(criterios):
        print(f"{criterio.name}: {pesos_criterios[i]:.4f}")

    print("\nPuntuaciones de las alternativas:")
    for i, alt in enumerate(alternativas):
        print(f"{alt.name}: {resultado.scores[i]:.4f}")

    print("\nRanking final:")
    ranking = resultado.get_sorted_alternatives()
    for idx, alt_info in enumerate(ranking):
        print(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})")

    # 8. Verificar la consistencia
    consistencia = resultado.get_metadata('consistency_info')
    print(f"\nÍndice de Consistencia: {consistencia['criteria_consistency']['consistency_index']:.4f}")
    print(f"Ratio de Consistencia: {consistencia['criteria_consistency']['consistency_ratio']:.4f}")
    print(f"¿Es consistente? {consistencia['criteria_consistency']['is_consistent']}")
    
    # Guardar resultados en un archivo
    with open('resultados_ahp_proveedores.txt', 'w') as f:
        f.write("===== RESULTADOS DE VALIDACIÓN AHP: SELECCIÓN DE PROVEEDORES =====\n")
        f.write("\nReferencia científica: Handfield, R., Walton, S.V., Sroufe, R., & Melnyk, S.A. (2002). Applying environmental criteria to supplier assessment: A study in the application of the Analytical Hierarchy Process. European Journal of Operational Research, 141(1), 70-87.\n")
        f.write("\nPesos de los criterios:\n")
        for i, criterio in enumerate(criterios):
            f.write(f"{criterio.name}: {pesos_criterios[i]:.4f}\n")
        
        f.write("\nPuntuaciones de las alternativas:\n")
        for i, alt in enumerate(alternativas):
            f.write(f"{alt.name}: {resultado.scores[i]:.4f}\n")
        
        f.write("\nRanking final:\n")
        for idx, alt_info in enumerate(ranking):
            f.write(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})\n")
        
        f.write(f"\nÍndice de Consistencia: {consistencia['criteria_consistency']['consistency_index']:.4f}\n")
        f.write(f"Ratio de Consistencia: {consistencia['criteria_consistency']['consistency_ratio']:.4f}\n")
        f.write(f"¿Es consistente? {consistencia['criteria_consistency']['is_consistent']}\n")

if __name__ == "__main__":
    print("Iniciando validación del método AHP para selección de proveedores...")
    try:
        ejecutar_validacion_proveedores()
        print("Validación completada exitosamente.")
    except Exception as e:
        print(f"ERROR: La validación falló con el siguiente error: {e}")
        import traceback
        traceback.print_exc()