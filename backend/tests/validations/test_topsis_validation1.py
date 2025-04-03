from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from application.methods.topsis import TOPSISMethod
import numpy as np

def ejecutar_validacion_topsis_energia():
    print("Ejecutando validación TOPSIS para proyectos de energía renovable...")
    
    # 1. Crear alternativas (proyectos)
    alternativas = [
        Alternative(id="P1", name="Parque Eólico"),
        Alternative(id="P2", name="Planta Solar Fotovoltaica"),
        Alternative(id="P3", name="Planta Hidroeléctrica"),
        Alternative(id="P4", name="Planta de Biomasa"),
        Alternative(id="P5", name="Planta Geotérmica")
    ]

    # 2. Crear criterios
    criterios = [
        Criteria(id="C1", name="Inversión inicial", optimization_type=OptimizationType.MINIMIZE, weight=0.25),
        Criteria(id="C2", name="Retorno económico", optimization_type=OptimizationType.MAXIMIZE, weight=0.20),
        Criteria(id="C3", name="Reducción de emisiones CO2", optimization_type=OptimizationType.MAXIMIZE, weight=0.20),
        Criteria(id="C4", name="Creación de empleo", optimization_type=OptimizationType.MAXIMIZE, weight=0.15),
        Criteria(id="C5", name="Impacto ambiental", optimization_type=OptimizationType.MINIMIZE, weight=0.20)
    ]

    # 3. Crear matriz de decisión con valores originales
    # Valores basados en Ren et al. (2015)
    valores = np.array([
        [8.5, 7.0, 8.0, 6.5, 4.0],  # Parque Eólico
        [7.0, 6.5, 9.0, 5.0, 3.0],  # Planta Solar Fotovoltaica
        [9.5, 8.0, 7.5, 7.0, 6.5],  # Planta Hidroeléctrica
        [6.0, 6.0, 6.0, 8.0, 7.0],  # Planta de Biomasa
        [8.0, 7.5, 8.5, 6.0, 5.5]   # Planta Geotérmica
    ])

    matriz_decision = DecisionMatrix(
        name="Evaluación de proyectos de energía renovable",
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
    print("\n===== RESULTADOS DE TOPSIS PARA PROYECTOS DE ENERGÍA RENOVABLE =====")
    
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
    with open('resultados_topsis_energia.txt', 'w') as f:
        f.write("===== RESULTADOS DE VALIDACIÓN TOPSIS: PROYECTOS DE ENERGÍA RENOVABLE =====\n")
        f.write("\nReferencia científica: Ren, J., Manzardo, A., Toniolo, S., & Scipioni, A. (2015). Sustainability assessment of alternative biodiesel technologies using TOPSIS method with different weighting strategies. Energy Conversion and Management, 104, 352-364.\n")
        
        f.write("\nPuntuaciones de proximidad relativa (Ci):\n")
        for i, alt in enumerate(alternativas):
            f.write(f"{alt.name}: {resultado.scores[i]:.4f}\n")
        
        f.write("\nRanking final:\n")
        for idx, alt_info in enumerate(ranking):
            f.write(f"{idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})\n")
        
        f.write("\nDetalles del cálculo TOPSIS:\n")
        f.write(f"Solución ideal positiva: {resultado.get_metadata('ideal_positive')}\n")
        f.write(f"Solución ideal negativa: {resultado.get_metadata('ideal_negative')}\n")

if __name__ == "__main__":
    print("Iniciando validación del método TOPSIS para proyectos de energía renovable...")
    try:
        ejecutar_validacion_topsis_energia()
        print("Validación completada exitosamente.")
    except Exception as e:
        print(f"ERROR: La validación falló con el siguiente error: {e}")
        import traceback
        traceback.print_exc()