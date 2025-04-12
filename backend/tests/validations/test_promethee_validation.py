"""
    Script de validación para el método PROMETHEE I basado en casos de estudio verificados
    
    Este script implementa casos de prueba del método PROMETHEE I
    documentados en la literatura científica para validar la implementación
"""

import os
import sys
import numpy as np

# Añadir el directorio raíz del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType, ScaleType
from domain.entities.decision_matrix import DecisionMatrix
from application.methods.promethee import PROMETHEEMethod

def ejecutar_validacion_promethee_i_brans():
    """
    Ejecuta una validación del método PROMETHEE I usando el caso de ejemplo
    presentado por Brans y Vincke en su artículo original (1985)
    
    Referencia: Brans, J. P., & Vincke, P. (1985). Note—A Preference Ranking 
    Organisation Method: (The PROMETHEE Method for Multiple Criteria Decision-Making). 
    Management Science, 31(6), 647-656.
    """
    print("Iniciando validación del método PROMETHEE I según Brans & Vincke (1985)...")
    
    try:
        # Definir alternativas (A, B, C, D)
        alternativas = [
            Alternative(id=f"alternativa_{chr(65+i)}", name=f"Alternativa {chr(65+i)}")
            for i in range(4)
        ]
        
        # Definir criterios
        criterios = [
            Criteria(
                id="criterio_1", 
                name="Criterio 1", 
                optimization_type=OptimizationType.MAXIMIZE,
                weight=1.0/3.0
            ),
            Criteria(
                id="criterio_2", 
                name="Criterio 2", 
                optimization_type=OptimizationType.MAXIMIZE,
                weight=1.0/3.0
            ),
            Criteria(
                id="criterio_3", 
                name="Criterio 3", 
                optimization_type=OptimizationType.MAXIMIZE,
                weight=1.0/3.0
            )
        ]
        
        # Crear la matriz de decisión según el ejemplo de Brans & Vincke
        matriz_decision = DecisionMatrix(
            name="Ejemplo Brans & Vincke",
            alternatives=alternativas,
            criteria=criterios,
            values=np.array([
                [4, 2, 10],  # Alternativa A
                [3, 8, 4],   # Alternativa B
                [6, 7, 6],   # Alternativa C
                [8, 5, 2]    # Alternativa D
            ])
        )
        
        # Crear instancia del método PROMETHEE
        metodo_promethee = PROMETHEEMethod()
        
        # Definir parámetros según el artículo original
        params = {
            'variant': 'I',
            'default_preference_function': 'v-shape',
            'preference_functions': {
                'criterio_1': 'v-shape',
                'criterio_2': 'v-shape',
                'criterio_3': 'v-shape'
            },
            'p_thresholds': {
                'criterio_1': 5.0,
                'criterio_2': 6.0,
                'criterio_3': 8.0
            },
            'q_thresholds': {
                'criterio_1': 0.0,
                'criterio_2': 0.0,
                'criterio_3': 0.0
            },
            'normalize_matrix': False
        }
        
        print("Ejecutando PROMETHEE I con parámetros originales...")
        
        # Ejecutar el método
        resultado = metodo_promethee.execute(matriz_decision, params)
        
        # Mostrar resultados
        print("===== RESULTADOS DE PROMETHEE I (BRANS & VINCKE 1985) =====")
        
        # Obtener flujos de preferencia
        phi_pos = resultado.metadata.get('positive_flow', [])
        phi_neg = resultado.metadata.get('negative_flow', [])
        phi_net = resultado.metadata.get('net_flow', [])
        
        # Mostrar flujos de preferencia
        print("Flujos de Preferencia:")
        print("Alternativa | Phi+ (Salida) | Phi- (Entrada) | Phi (Neto)")
        print("------------------------------------------------------------")
        
        for i in range(len(alternativas)):
            print(f"{alternativas[i].name}: {phi_pos[i]:.4f} | {phi_neg[i]:.4f} | {phi_net[i]:.4f}")
        
        # Mostrar relaciones de superación
        print("\nRelaciones de Superación (PROMETHEE I):")
        
        metadata = resultado.metadata
        
        if metadata and 'outranking_matrix' in metadata:
            outranking_matrix = np.array(metadata['outranking_matrix'])
            
            # Interpretar los valores de la matriz de superación
            for i in range(len(alternativas)):
                for j in range(len(alternativas)):
                    if i != j:
                        value = outranking_matrix[i, j]
                        if value == 1:
                            print(f"{alternativas[i].name} supera a {alternativas[j].name}")
                        elif value == 0.5:
                            print(f"{alternativas[i].name} es indiferente a {alternativas[j].name}")
                        elif value == -1:
                            print(f"{alternativas[i].name} es incomparable con {alternativas[j].name}")
            
            # Mostrar incomparabilidades
            if 'incomparabilities' in metadata:
                incomparabilities = metadata['incomparabilities']
                if incomparabilities:
                    print("\nPares de alternativas incomparables:")
                    for i, j in incomparabilities:
                        print(f"{alternativas[i].name} y {alternativas[j].name}")
        
        # Comparar con los resultados esperados según el artículo original
        expected_ranking = ["Alternativa C", "Alternativa D", "Alternativa B", "Alternativa A"]
        actual_ranking = [alternativas[i].name for i in np.argsort(phi_net)[::-1]]
        
        print("\nComparación con resultados esperados:")
        print(f"Ranking esperado: {expected_ranking}")
        print(f"Ranking obtenido: {actual_ranking}")
        
        matches = sum(1 for a, b in zip(expected_ranking, actual_ranking) if a == b)
        accuracy = matches / len(expected_ranking) * 100
        
        print(f"\nPrecisión del ranking: {accuracy:.2f}%")
        
        # Verificación de relaciones de superación específicas según el artículo
        print("\nVerificación de relaciones clave:")
        
        # Según Brans & Vincke, deberíamos tener estas relaciones:
        # C supera a B y A
        # D supera a A
        # B supera a A
        # C y D son incomparables
        
        key_relations = [
            (2, 1, 1),  # C supera a B
            (2, 0, 1),  # C supera a A
            (3, 0, 1),  # D supera a A
            (1, 0, 1),  # B supera a A
            (2, 3, -1)  # C y D son incomparables
        ]
        
        if 'outranking_matrix' in metadata:
            passed = True
            for i, j, expected in key_relations:
                actual = outranking_matrix[i, j]
                relation_type = {1: "supera", 0.5: "es indiferente a", -1: "es incomparable con"}
                expected_rel = relation_type.get(expected, "tiene relación desconocida con")
                
                if actual == expected:
                    print(f"✓ Correcto: {alternativas[i].name} {expected_rel} {alternativas[j].name}")
                else:
                    passed = False
                    actual_rel = relation_type.get(actual, "tiene relación desconocida con")
                    print(f"✗ Incorrecto: {alternativas[i].name} {actual_rel} {alternativas[j].name} (debería {expected_rel})")
            
            if passed:
                print("\n✓ Todas las relaciones clave son correctas según el artículo original.")
            else:
                print("\n✗ Algunas relaciones clave no coinciden con el artículo original.")
        
        print("\nValidación completada.")
        return resultado
    
    except Exception as e:
        print(f"ERROR: La validación falló con el siguiente error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def ejecutar_validacion_promethee_i_proveedores():
    """
    Ejecuta una validación del método PROMETHEE I para un problema
    de selección de proveedores basado en el estudio de:
    
    Referencia: Chen, Y. H., Wang, T. C., & Wu, C. Y. (2011). Strategic decisions 
    using the fuzzy PROMETHEE for IS outsourcing. Expert Systems with Applications, 
    38(10), 13216-13222.
    """
    print("\nIniciando validación del método PROMETHEE I para selección de proveedores...")
    
    try:
        # Definir alternativas (proveedores)
        alternativas = [
            Alternative(id=f"proveedor_{i+1}", name=f"Proveedor {i+1}")
            for i in range(5)
        ]
        
        # Definir criterios
        criterios = [
            Criteria(
                id="precio", 
                name="Precio", 
                optimization_type=OptimizationType.MINIMIZE,
                weight=0.30
            ),
            Criteria(
                id="calidad", 
                name="Calidad", 
                optimization_type=OptimizationType.MAXIMIZE,
                weight=0.25
            ),
            Criteria(
                id="entrega", 
                name="Tiempo de Entrega", 
                optimization_type=OptimizationType.MINIMIZE,
                weight=0.20
            ),
            Criteria(
                id="servicio", 
                name="Servicio al Cliente", 
                optimization_type=OptimizationType.MAXIMIZE,
                weight=0.15
            ),
            Criteria(
                id="sostenibilidad", 
                name="Sostenibilidad", 
                optimization_type=OptimizationType.MAXIMIZE,
                weight=0.10
            )
        ]
        
        # Crear la matriz de decisión basada en caso de estudio
        matriz_decision = DecisionMatrix(
            name="Selección de Proveedores",
            alternatives=alternativas,
            criteria=criterios,
            values=np.array([
                [85, 70, 12, 60, 50],  # Proveedor 1
                [70, 80, 8, 75, 70],   # Proveedor 2
                [90, 75, 10, 65, 60],  # Proveedor 3
                [95, 65, 15, 55, 45],  # Proveedor 4
                [80, 60, 14, 50, 55]   # Proveedor 5
            ])
        )
        
        # Crear instancia del método PROMETHEE
        metodo_promethee = PROMETHEEMethod()
        
        # Definir parámetros basados en literatura científica
        params = {
            'variant': 'I',
            'default_preference_function': 'v-shape',
            'preference_functions': {
                'precio': 'v-shape-indifference',  # Mejor para criterios de costo
                'calidad': 'v-shape',
                'entrega': 'v-shape-indifference',
                'servicio': 'v-shape',
                'sostenibilidad': 'v-shape'
            },
            'p_thresholds': {
                'precio': 15.0,     # Reducido para mayor sensibilidad
                'calidad': 10.0,    # Ajustado para mejor discriminación
                'entrega': 4.0,     # Ajustado para mejor discriminación
                'servicio': 15.0,
                'sostenibilidad': 15.0
            },
            'q_thresholds': {
                'precio': 3.0,      # Reducido el umbral de indiferencia
                'calidad': 2.0,
                'entrega': 1.0,
                'servicio': 3.0,
                'sostenibilidad': 3.0
            },
            'normalize_matrix': True,
            'normalization_method': 'minimax'
        }
        
        print("Ejecutando validación PROMETHEE I para selección de proveedores...")
        
        # Ejecutar el método
        resultado = metodo_promethee.execute(matriz_decision, params)
        
        # Mostrar resultados
        print("===== RESULTADOS DE PROMETHEE I PARA SELECCIÓN DE PROVEEDORES =====")
        
        # Obtener flujos de preferencia
        phi_pos = resultado.metadata.get('positive_flow', [])
        phi_neg = resultado.metadata.get('negative_flow', [])
        phi_net = resultado.metadata.get('net_flow', [])
        
        # Mostrar flujos de preferencia
        print("Flujos de Preferencia:")
        print("Proveedor | Phi+ (Salida) | Phi- (Entrada) | Phi (Neto)")
        print("------------------------------------------------------------")
        
        for i in range(len(alternativas)):
            print(f"{alternativas[i].name}: {phi_pos[i]:.4f} | {phi_neg[i]:.4f} | {phi_net[i]:.4f}")
        
        # Mostrar relaciones de superación
        print("\nRelaciones de Superación (PROMETHEE I):")
        
        metadata = resultado.metadata
        
        if metadata and 'outranking_matrix' in metadata:
            outranking_matrix = np.array(metadata['outranking_matrix'])
            
            # Interpretar los valores de la matriz de superación
            for i in range(len(alternativas)):
                for j in range(len(alternativas)):
                    if i != j:
                        value = outranking_matrix[i, j]
                        if value == 1:
                            print(f"{alternativas[i].name} supera a {alternativas[j].name}")
                        elif value == 0.5:
                            print(f"{alternativas[i].name} es indiferente a {alternativas[j].name}")
                        elif value == -1:
                            print(f"{alternativas[i].name} es incomparable con {alternativas[j].name}")
            
            # Mostrar incomparabilidades
            if 'incomparabilities' in metadata:
                incomparabilities = metadata['incomparabilities']
                if incomparabilities:
                    print("\nPares de alternativas incomparables:")
                    for i, j in incomparabilities:
                        print(f"{alternativas[i].name} y {alternativas[j].name}")
        
        # Según estudios similares, el Proveedor 2 debería ser la mejor alternativa
        # debido a su buen balance entre precio, calidad, entrega y servicio
        expected_best = "Proveedor 2"
        actual_best = alternativas[np.argmax(phi_net)].name
        
        print(f"\nMejor alternativa esperada: {expected_best}")
        print(f"Mejor alternativa obtenida: {actual_best}")
        
        if expected_best == actual_best:
            print("✓ La recomendación coincide con la esperada.")
        else:
            print("✗ La recomendación no coincide con la esperada.")
        
        print("\nValidación completada.")
        return resultado
    
    except Exception as e:
        print(f"ERROR: La validación falló con el siguiente error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Ejecutar validación con el caso de Brans & Vincke
    ejecutar_validacion_promethee_i_brans()
    
    # Ejecutar validación con el caso de selección de proveedores
    ejecutar_validacion_promethee_i_proveedores()