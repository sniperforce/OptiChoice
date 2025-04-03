from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from application.methods.promethee import PROMETHEEMethod
import numpy as np

def ejecutar_validacion_promethee_i():
    print("Ejecutando validación PROMETHEE I para selección de proveedores...")
    
    # 1. Crear alternativas (proveedores)
    alternativas = [
        Alternative(id="P1", name="Proveedor 1"),
        Alternative(id="P2", name="Proveedor 2"),
        Alternative(id="P3", name="Proveedor 3"),
        Alternative(id="P4", name="Proveedor 4"),
        Alternative(id="P5", name="Proveedor 5")
    ]

    # 2. Crear criterios
    criterios = [
        Criteria(id="C1", name="Calidad", optimization_type=OptimizationType.MAXIMIZE, weight=0.30),
        Criteria(id="C2", name="Precio", optimization_type=OptimizationType.MINIMIZE, weight=0.25),
        Criteria(id="C3", name="Tiempo de entrega", optimization_type=OptimizationType.MINIMIZE, weight=0.20),
        Criteria(id="C4", name="Servicio postventa", optimization_type=OptimizationType.MAXIMIZE, weight=0.15),
        Criteria(id="C5", name="Capacidad técnica", optimization_type=OptimizationType.MAXIMIZE, weight=0.10)
    ]

    # 3. Crear matriz de decisión con valores originales
    valores = np.array([
        [8, 6, 5, 7, 8],  # Proveedor 1
        [9, 8, 3, 9, 7],  # Proveedor 2
        [7, 5, 4, 6, 9],  # Proveedor 3
        [6, 7, 2, 8, 6],  # Proveedor 4
        [8, 4, 6, 7, 8]   # Proveedor 5
    ])

    matriz_decision = DecisionMatrix(
        name="Selección de proveedores",
        alternatives=alternativas,
        criteria=criterios,
        values=valores
    )

    # 4. Configurar preferencias por criterio
    # Definir tipo de función de preferencia por criterio
    preference_functions = {
        "C1": "v-shape",          # Calidad
        "C2": "v-shape",          # Precio
        "C3": "v-shape",          # Tiempo de entrega
        "C4": "level",            # Servicio postventa
        "C5": "v-shape-indifference"  # Capacidad técnica
    }
    
    # Definir umbrales de preferencia (p)
    p_thresholds = {
        "C1": 2.0,  # Para calidad
        "C2": 3.0,  # Para precio
        "C3": 2.0,  # Para tiempo de entrega
        "C4": 2.0,  # Para servicio postventa
        "C5": 2.0   # Para capacidad técnica
    }
    
    # Definir umbrales de indiferencia (q)
    q_thresholds = {
        "C1": 0.0,  # No aplica para V-shape
        "C2": 0.0,  # No aplica para V-shape
        "C3": 0.0,  # No aplica para V-shape
        "C4": 1.0,  # Para servicio postventa
        "C5": 1.0   # Para capacidad técnica
    }

    # 5. Configurar parámetros del método PROMETHEE
    parametros = {
        'variant': 'I',  # PROMETHEE I (ranking parcial)
        'default_preference_function': 'v-shape',
        'preference_functions': preference_functions,
        'p_thresholds': p_thresholds,
        'q_thresholds': q_thresholds,
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
    print("\n===== RESULTADOS DE PROMETHEE I PARA SELECCIÓN DE PROVEEDORES =====")
    
    # Obtener los flujos
    positive_flow = resultado.get_metadata('positive_flow')
    negative_flow = resultado.get_metadata('negative_flow')
    net_flow = resultado.scores
    
    print("\nFlujos de Preferencia:")
    print("Proveedor | Phi+ (Salida) | Phi- (Entrada) | Phi (Neto)")
    print("-" * 60)
    for i, alt in enumerate(alternativas):
        print(f"{alt.name}: {positive_flow[i]:.4f} | {negative_flow[i]:.4f} | {net_flow[i]:.4f}")
    
    # 8. Imprimir relaciones de superación en PROMETHEE I
    print("\nRelaciones de Superación (PROMETHEE I):")
    
    # Obtener matriz de superación si está disponible
    if 'outranking_matrix' in resultado.get_metadata('metadata'):
        outranking_matrix = resultado.get_metadata('outranking_matrix')
        for i in range(len(alternativas)):
            outranks = []
            for j in range(len(alternativas)):
                if i != j and outranking_matrix[i][j] == 1:
                    outranks.append(alternativas[j].name)
            print(f"{alternativas[i].name} supera a: {', '.join(outranks) if outranks else 'Ninguno'}")
    else:
        # Calcular relaciones de superación manualmente
        for i in range(len(alternativas)):
            outranks = []
            for j in range(len(alternativas)):
                if i != j:
                    # En PROMETHEE I, a supera a b si:
                    # Phi+(a) >= Phi+(b) y Phi-(a) <= Phi-(b), con al menos una desigualdad estricta
                    if ((positive_flow[i] > positive_flow[j] and negative_flow[i] <= negative_flow[j]) or
                        (positive_flow[i] >= positive_flow[j] and negative_flow[i] < negative_flow[j])):
                        outranks.append(alternativas[j].name)
            print(f"{alternativas[i].name} supera a: {', '.join(outranks) if outranks else 'Ninguno'}")
    
    # 9. Identificar alternativas incomparables
    print("\nPares de Alternativas Incomparables:")
    incomparable_pairs = []
    for i in range(len(alternativas)):
        for j in range(i+1, len(alternativas)):
            # a y b son incomparables si a no supera a b y b no supera a a
            a_outranks_b = ((positive_flow[i] > positive_flow[j] and negative_flow[i] <= negative_flow[j]) or
                           (positive_flow[i] >= positive_flow[j] and negative_flow[i] < negative_flow[j]))
            
            b_outranks_a = ((positive_flow[j] > positive_flow[i] and negative_flow[j] <= negative_flow[i]) or
                           (positive_flow[j] >= positive_flow[i] and negative_flow[j] < negative_flow[i]))
            
            if not a_outranks_b and not b_outranks_a:
                incomparable_pairs.append((alternativas[i].name, alternativas[j].name))
    
    if incomparable_pairs:
        for pair in incomparable_pairs:
            print(f"- {pair[0]} y {pair[1]} son incomparables")
    else:
        print("No hay alternativas incomparables")
        
    # 10. Ranking final parcial (PROMETHEE I)
    print("\nRanking Parcial (PROMETHEE I):")
    
    # Primero ordenamos por flujo neto para tener una base
    sorted_indices = np.argsort(-net_flow)
    
    for rank, idx in enumerate(sorted_indices, 1):
        incomparable_with = []
        for other_idx in sorted_indices:
            if idx != other_idx:
                idx_outranks_other = ((positive_flow[idx] > positive_flow[other_idx] and negative_flow[idx] <= negative_flow[other_idx]) or
                                    (positive_flow[idx] >= positive_flow[other_idx] and negative_flow[idx] < negative_flow[other_idx]))
                
                other_outranks_idx = ((positive_flow[other_idx] > positive_flow[idx] and negative_flow[other_idx] <= negative_flow[idx]) or
                                    (positive_flow[other_idx] >= positive_flow[idx] and negative_flow[other_idx] < negative_flow[idx]))
                
                if not idx_outranks_other and not other_outranks_idx:
                    incomparable_with.append(alternativas[other_idx].name)
        
        if incomparable_with:
            print(f"{rank}. {alternativas[idx].name} (Phi+: {positive_flow[idx]:.4f}, Phi-: {negative_flow[idx]:.4f}) - Incomparable con: {', '.join(incomparable_with)}")
        else:
            print(f"{rank}. {alternativas[idx].name} (Phi+: {positive_flow[idx]:.4f}, Phi-: {negative_flow[idx]:.4f})")
    
    # 11. Guardar resultados en un archivo
    with open('resultados_promethee_i_proveedores.txt', 'w') as f:
        f.write("===== RESULTADOS DE VALIDACIÓN PROMETHEE I: SELECCIÓN DE PROVEEDORES =====\n")
        f.write("\nReferencia científica: Brans, J.P., & Vincke, P. (1985). Note—A Preference Ranking Organisation Method: (The PROMETHEE Method for Multiple Criteria Decision-Making). Management Science, 31(6), 647-656.\n")
        
        f.write("\nFlujos de Preferencia:\n")
        f.write("Proveedor | Phi+ (Salida) | Phi- (Entrada) | Phi (Neto)\n")
        f.write("-" * 60 + "\n")
        for i, alt in enumerate(alternativas):
            f.write(f"{alt.name}: {positive_flow[i]:.4f} | {negative_flow[i]:.4f} | {net_flow[i]:.4f}\n")
        
        f.write("\nRanking Parcial (PROMETHEE I):\n")
        for rank, idx in enumerate(sorted_indices, 1):
            incomparable_with = []
            for other_idx in sorted_indices:
                if idx != other_idx:
                    idx_outranks_other = ((positive_flow[idx] > positive_flow[other_idx] and negative_flow[idx] <= negative_flow[other_idx]) or
                                       (positive_flow[idx] >= positive_flow[other_idx] and negative_flow[idx] < negative_flow[other_idx]))
                    
                    other_outranks_idx = ((positive_flow[other_idx] > positive_flow[idx] and negative_flow[other_idx] <= negative_flow[idx]) or
                                       (positive_flow[other_idx] >= positive_flow[idx] and negative_flow[other_idx] < negative_flow[idx]))
                    
                    if not idx_outranks_other and not other_outranks_idx:
                        incomparable_with.append(alternativas[other_idx].name)
            
            if incomparable_with:
                f.write(f"{rank}. {alternativas[idx].name} (Phi+: {positive_flow[idx]:.4f}, Phi-: {negative_flow[idx]:.4f}) - Incomparable con: {', '.join(incomparable_with)}\n")
            else:
                f.write(f"{rank}. {alternativas[idx].name} (Phi+: {positive_flow[idx]:.4f}, Phi-: {negative_flow[idx]:.4f})\n")

if __name__ == "__main__":
    print("Iniciando validación del método PROMETHEE I para selección de proveedores...")
    try:
        ejecutar_validacion_promethee_i()
        print("Validación completada exitosamente.")
    except Exception as e:
        print(f"ERROR: La validación falló con el siguiente error: {e}")
        import traceback
        traceback.print_exc()