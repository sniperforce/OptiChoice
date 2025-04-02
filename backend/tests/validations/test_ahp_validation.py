from ..domain.entities.alternative import Alternative
from ..domain.entities.criteria import Criteria, OptimizationType
from ..domain.entities.decision_matrix import DecisionMatrix
from ..application.methods.ahp import AHPMethod
import numpy as np

# 1. Crear alternativas
alternativas = [
    Alternative(id="A1", name="Centro Ciudad"),
    Alternative(id="A2", name="Zona Residencial"),
    Alternative(id="A3", name="Periferia")
]

# 2. Crear criterios
criterios = [
    Criteria(id="C1", name="Accesibilidad", optimization_type=OptimizationType.MAXIMIZE, weight=1.0),
    Criteria(id="C2", name="Competencia", optimization_type=OptimizationType.MINIMIZE, weight=1.0),
    Criteria(id="C3", name="Costo del terreno", optimization_type=OptimizationType.MINIMIZE, weight=1.0),
    Criteria(id="C4", name="Potencial de crecimiento", optimization_type=OptimizationType.MAXIMIZE, weight=1.0)
]

# 3. Crear matriz de decisión con valores originales
valores = np.array([
    [8, 4, 9, 6],  # Centro Ciudad
    [6, 7, 5, 8],  # Zona Residencial
    [4, 9, 3, 7]   # Periferia
])

matriz_decision = DecisionMatrix(
    name="Selección de ubicación",
    alternatives=alternativas,
    criteria=criterios,
    values=valores
)

# 4. Definir la matriz de comparación de criterios
matriz_comparacion_criterios = np.array([
    [1.00, 3.00, 5.00, 7.00],
    [0.33, 1.00, 3.00, 5.00],
    [0.20, 0.33, 1.00, 3.00],
    [0.14, 0.20, 0.33, 1.00]
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
    'normalization_method': 'minmax'
}

# 6. Ejecutar el método AHP
metodo_ahp = AHPMethod()
resultado = metodo_ahp.execute(matriz_decision, parametros)

# 7. Imprimir resultados
print("Pesos de los criterios:")
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

if __name__ == "__main__":
    print("Iniciando validación del método AHP...")
    