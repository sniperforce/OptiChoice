from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from application.methods.topsis import TOPSISMethod
import numpy as np

def ejecutar_validacion_topsis():
    print("Ejecutando validación TOPSIS para selección de materiales...")
    
    # 1. Crear alternativas (materiales)
    alternativas = [
        Alternative(id="M1", name="Acero Inoxidable"),
        Alternative(id="M2", name="Aleación de Titanio"),
        Alternative(id="M3", name="Aleación de Aluminio"),
        Alternative(id="M4", name="Aleación de Magnesio"),
        Alternative(id="M5", name="Compuesto de Fibra de Carbono")
    ]

    # 2. Crear criterios
    criterios = [
        Criteria(id="C1", name="Resistencia mecánica", optimization_type=OptimizationType.MAXIMIZE, weight=0.35),
        Criteria(id="C2", name="Resistencia a la corrosión", optimization_type=OptimizationType.MAXIMIZE, weight=0.25),
        Criteria(id="C3", name="Densidad", optimization_type=OptimizationType.MINIMIZE, weight=0.20),
        Criteria(id="C4", name="Costo", optimization_type=OptimizationType.MINIMIZE, weight=0.20)
    ]

    # 3. Crear matriz de decisión con valores originales
    # Valores basados en Jahan y Edwards (2013)
    valores = np.array([
        [7.5, 9.0, 7.8, 6.0],  # Acero Inoxidable
        [9.0, 8.0, 5.5, 4.0],  # Aleación de Titanio
        [5.5, 6.5, 3.5, 7.5],  # Aleación de Aluminio
        [4.5, 6.0, 2.0, 8.0],  # Aleación de Magnesio
        [8.5, 7.0, 2.5, 3.0]   # Compuesto de Fibra de Carbono
    ])

    matriz_decision = DecisionMatrix(
        name="Selección de materiales",
        alternatives=alternativas,
        criteria=criterios,
        values=valores
    )

    # 4. Configurar parámetros del método TOPSIS
    parametros = {
        'normalization_method': 'vector',
        'normalize_matrix': True,
        'distance_metric': 'euclidean',
        'apply_weights_after_normalization': True,
        'consider_criteria_type': True
    }

    # 5. Ejecutar el método TOPSIS
    metodo_topsis = TOPSISMethod()
    params_defecto = metodo_topsis.get_default_parameters()
    for key, value in parametros.items():
        params_defecto[key] = value
    
    resultado = metodo_topsis.execute(matriz_decision, params_defecto)

    # 6. Imprimir resultados
    print("\n===== RESULTADOS DE TOPSIS PARA SELECCIÓN DE MATERIALES =====")
    
    print("\nPuntuaciones de proximidad relativa (Ci):")
    for i, alt in enumerate(alternativas):
        print(f"{alt.name}: {resultado.scores[i]:.4f}")

    print("\nRanking final:")
    ranking = resultado.get_sorted_alternatives()
    for idx, alt_info in enumerate(ranking):
        print(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})")

    # 7. Imprimir detalles de cálculo
    print("\nDetalles del cálculo TOPSIS:")
    print(f"Solución ideal positiva: {resultado.get_metadata('ideal_positive')}")
    print(f"Solución ideal negativa: {resultado.get_metadata('ideal_negative')}")
    
    # 8. Guardar resultados en un archivo
    with open('resultados_topsis_materiales.txt', 'w') as f:
        f.write("===== RESULTADOS DE VALIDACIÓN TOPSIS: SELECCIÓN DE MATERIALES =====\n")
        f.write("\nReferencia científica: Jahan, A., & Edwards, K. L. (2013). Multi-criteria decision analysis for supporting the selection of engineering materials in product design. Butterworth-Heinemann.\n")
        
        f.write("\nPuntuaciones de proximidad relativa (Ci):\n")
        for i, alt in enumerate(alternativas):
            f.write(f"{alt.name}: {resultado.scores[i]:.4f}\n")
        
        f.write("\nRanking final:\n")
        for idx, alt_info in enumerate(ranking):
            f.write(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})\n")

if __name__ == "__main__":
    print("Iniciando validación del método TOPSIS para selección de materiales...")
    try:
        ejecutar_validacion_topsis()
        print("Validación completada exitosamente.")
    except Exception as e:
        print(f"ERROR: La validación falló con el siguiente error: {e}")
        import traceback
        traceback.print_exc()