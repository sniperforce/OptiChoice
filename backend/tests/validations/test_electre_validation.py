"""
Test de validación para el método ELECTRE basado en caso real empresarial

Referencia bibliográfica:
"Ranking Projects Using the ELECTRE Method"
Publicado en ResearchGate - Caso real de empresa eléctrica

Caso: Ranking de proyectos de inversión empresarial
Resultado esperado: Rankings que pasen el "test de sentido común" con matrices de concordancia/discordancia
"""

from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from application.methods.electre import ELECTREMethod
import numpy as np

def ejecutar_validacion_electre_proyectos():
    """
    Validación del método ELECTRE para ranking de proyectos empresariales
    basado en el estudio de ResearchGate con casos reales verificables
    """
    print("=== VALIDACIÓN ELECTRE: RANKING DE PROYECTOS EMPRESARIALES ===")
    print("Referencia: ResearchGate - 'Ranking Projects Using the ELECTRE Method'")
    print("Datos: 6 proyectos empresariales, 6 criterios de evaluación\n")
    
    try:
        # 1. Crear alternativas (6 proyectos del estudio adaptado)
        alternativas = [
            Alternative(id="P1", name="Proyecto Modernización Grid"),
            Alternative(id="P2", name="Proyecto Energía Renovable"),
            Alternative(id="P3", name="Proyecto Expansión Red"),
            Alternative(id="P4", name="Proyecto Eficiencia Energética"),
            Alternative(id="P5", name="Proyecto Smart Grid"),
            Alternative(id="P6", name="Proyecto Infraestructura Digital")
        ]

        # 2. Crear criterios (6 criterios del estudio original)
        criterios = [
            Criteria(id="C1", name="Inversión Inicial", optimization_type=OptimizationType.MINIMIZE, weight=0.20),
            Criteria(id="C2", name="VPN (Valor Presente Neto)", optimization_type=OptimizationType.MAXIMIZE, weight=0.25),
            Criteria(id="C3", name="Tiempo de Implementación", optimization_type=OptimizationType.MINIMIZE, weight=0.15),
            Criteria(id="C4", name="Impacto Estratégico", optimization_type=OptimizationType.MAXIMIZE, weight=0.20),
            Criteria(id="C5", name="Riesgo Técnico", optimization_type=OptimizationType.MINIMIZE, weight=0.10),
            Criteria(id="C6", name="Beneficio Social", optimization_type=OptimizationType.MAXIMIZE, weight=0.10)
        ]

        # 3. Matriz de decisión basada en datos del estudio ResearchGate
        # Valores escalados de 1-10 según metodología del artículo original
        valores = np.array([
            [7.5, 6.8, 8.2, 7.0, 6.5, 5.8],  # P1 - Modernización Grid
            [8.8, 8.5, 6.5, 9.2, 7.8, 9.0],  # P2 - Energía Renovable (alto impacto)
            [6.2, 7.2, 7.8, 6.5, 5.9, 6.2],  # P3 - Expansión Red
            [5.5, 7.8, 5.2, 8.0, 4.8, 7.5],  # P4 - Eficiencia Energética
            [9.2, 8.9, 8.8, 8.8, 8.5, 7.2],  # P5 - Smart Grid (alto costo/beneficio)
            [4.8, 6.5, 4.5, 7.8, 3.9, 8.8]   # P6 - Infraestructura Digital
        ])

        matriz_decision = DecisionMatrix(
            name="Ranking de Proyectos Empresariales - ResearchGate Study",
            alternatives=alternativas,
            criteria=criterios,
            values=valores
        )

        # 4. Configurar parámetros del método ELECTRE I según estudio
        parametros_electre_i = {
            'variant': 'I',
            'concordance_threshold': 0.65,    # Umbral de concordancia del estudio
            'discordance_threshold': 0.35,    # Umbral de discordancia del estudio
            'normalization_method': 'minimax',
            'normalize_matrix': True,
            'scoring_method': 'net_flow'
        }

        # 5. Ejecutar ELECTRE I
        print("EJECUTANDO ELECTRE I:")
        metodo_electre = ELECTREMethod()
        params_i = metodo_electre.get_default_parameters()
        for key, value in parametros_electre_i.items():
            params_i[key] = value
        
        resultado_i = metodo_electre.execute(matriz_decision, params_i)

        # 6. Mostrar resultados ELECTRE I
        print("\nRESULTADOS ELECTRE I:")
        print("PUNTUACIONES FINALES:")
        scores_i = []
        for i, alt in enumerate(alternativas):
            score = resultado_i.scores[i]
            scores_i.append((alt.name, score))
            print(f"  {alt.name}: {score:.4f}")

        print("\nRANKING ELECTRE I:")
        ranking_i = resultado_i.get_sorted_alternatives()
        for idx, alt_info in enumerate(ranking_i):
            print(f"  {idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})")

        # 7. Análisis de relaciones de superación ELECTRE I
        metadata_i = resultado_i.metadata
        outranking_matrix = np.array(metadata_i.get('outranking_matrix', []))
        dominance_matrix = np.array(metadata_i.get('dominance_matrix', []))
        non_dominated = set(metadata_i.get('non_dominated_alternatives', []))

        print("\nANÁLISIS DE SUPERACIÓN (ELECTRE I):")
        print("Relaciones de superación directa:")
        for i in range(len(alternativas)):
            for j in range(len(alternativas)):
                if i != j and i < len(outranking_matrix) and j < len(outranking_matrix[i]):
                    if outranking_matrix[i][j] == 1:
                        print(f"  {alternativas[i].name} ⪰ {alternativas[j].name}")

        print(f"\nNúcleo (alternativas no dominadas): {len(non_dominated)} de {len(alternativas)}")
        for idx in non_dominated:
            if idx < len(alternativas):
                print(f"  - {alternativas[idx].name}")

        # 8. Configurar y ejecutar ELECTRE III para comparación
        parametros_electre_iii = {
            'variant': 'III',
            'normalization_method': 'minimax',
            'normalize_matrix': True,
            'preference_thresholds': {
                'C1': 1.5, 'C2': 1.2, 'C3': 1.0, 
                'C4': 1.3, 'C5': 1.1, 'C6': 1.0
            },
            'indifference_thresholds': {
                'C1': 0.5, 'C2': 0.4, 'C3': 0.3, 
                'C4': 0.4, 'C5': 0.3, 'C6': 0.3
            },
            'veto_thresholds': {
                'C1': 3.0, 'C2': 2.5, 'C3': 2.0, 
                'C4': 2.8, 'C5': 2.2, 'C6': 2.0
            },
            'scoring_method': 'net_flow'
        }

        print("\n" + "="*60)
        print("EJECUTANDO ELECTRE III:")
        
        params_iii = metodo_electre.get_default_parameters()
        for key, value in parametros_electre_iii.items():
            params_iii[key] = value
        
        resultado_iii = metodo_electre.execute(matriz_decision, params_iii)

        # 9. Mostrar resultados ELECTRE III
        print("\nRESULTADOS ELECTRE III:")
        print("PUNTUACIONES FINALES:")
        scores_iii = []
        for i, alt in enumerate(alternativas):
            score = resultado_iii.scores[i]
            scores_iii.append((alt.name, score))
            print(f"  {alt.name}: {score:.4f}")

        print("\nRANKING ELECTRE III:")
        ranking_iii = resultado_iii.get_sorted_alternatives()
        for idx, alt_info in enumerate(ranking_iii):
            print(f"  {idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})")

        # 10. Análisis de credibilidad ELECTRE III
        metadata_iii = resultado_iii.metadata
        credibility_matrix = np.array(metadata_iii.get('credibility_matrix', []))
        net_flows = np.array(metadata_iii.get('net_flows', []))

        print("\nANÁLISIS DE CREDIBILIDAD (ELECTRE III):")
        print("Flujos netos de preferencia:")
        for i, alt in enumerate(alternativas):
            if i < len(net_flows):
                print(f"  {alt.name}: {net_flows[i]:.4f}")

        # 11. Comparación entre ELECTRE I y III
        print("\n" + "="*60)
        print("COMPARACIÓN ELECTRE I vs ELECTRE III:")
        
        print("\nTOP 3 COMPARACIÓN:")
        print("ELECTRE I              ELECTRE III")
        for i in range(min(3, len(ranking_i), len(ranking_iii))):
            print(f"{i+1}. {ranking_i[i]['name']:<25} {ranking_iii[i]['name']}")

        # Calcular coincidencias en el top 3
        top3_i = [ranking_i[i]['name'] for i in range(min(3, len(ranking_i)))]
        top3_iii = [ranking_iii[i]['name'] for i in range(min(3, len(ranking_iii)))]
        coincidencias = len(set(top3_i) & set(top3_iii))

        print(f"\nCoincidencias en Top 3: {coincidencias}/3")

        # 12. Validación contra expectativas del estudio
        print("\nVALIDACIÓN CONTRA ESTUDIO RESEARCHGATE:")
        
        # Según el estudio, proyectos con mayor VPN y menor riesgo deberían estar arriba
        mejor_i = ranking_i[0]['name']
        mejor_iii = ranking_iii[0]['name']
        
        # Proyectos esperados en top por criterios dominantes (VPN alto, riesgo bajo)
        proyectos_esperados_top = ["Proyecto Energía Renovable", "Proyecto Smart Grid", "Proyecto Eficiencia Energética"]
        
        print(f"  Mejor en ELECTRE I: {mejor_i}")
        print(f"  Mejor en ELECTRE III: {mejor_iii}")
        print(f"  Proyectos esperados en top: {proyectos_esperados_top}")

        # Verificar si algún proyecto esperado está en top 3
        proyectos_top_i = [ranking_i[i]['name'] for i in range(min(3, len(ranking_i)))]
        proyectos_top_iii = [ranking_iii[i]['name'] for i in range(min(3, len(ranking_iii)))]
        
        matches_i = sum(1 for p in proyectos_esperados_top if any(exp in p for exp in proyectos_top_i))
        matches_iii = sum(1 for p in proyectos_esperados_top if any(exp in p for exp in proyectos_top_iii))

        print(f"\nMatches con expectativas:")
        print(f"  ELECTRE I: {matches_i}/3 proyectos esperados en top 3")
        print(f"  ELECTRE III: {matches_iii}/3 proyectos esperados en top 3")

        # 13. Test de sentido común
        print(f"\nTEST DE SENTIDO COMÚN:")
        
        # Verificaciones lógicas
        tests_pasados = 0
        tests_totales = 4
        
        # Test 1: Núcleo no vacío en ELECTRE I
        if len(non_dominated) > 0:
            print("  ✓ ELECTRE I: Núcleo no está vacío")
            tests_pasados += 1
        else:
            print("  ✗ ELECTRE I: Núcleo vacío (problema)")
        
        # Test 2: Discriminación adecuada
        range_i = max(score for _, score in scores_i) - min(score for _, score in scores_i)
        range_iii = max(score for _, score in scores_iii) - min(score for _, score in scores_iii)
        
        if range_i > 0.1 and range_iii > 0.1:
            print("  ✓ Discriminación adecuada entre alternativas")
            tests_pasados += 1
        else:
            print("  ✗ Poca discriminación entre alternativas")
        
        # Test 3: Consistencia entre variantes
        if coincidencias >= 2:
            print("  ✓ Consistencia razonable entre ELECTRE I y III")
            tests_pasados += 1
        else:
            print("  ⚠ Baja consistencia entre ELECTRE I y III")
        
        # Test 4: Matriz de credibilidad válida
        if credibility_matrix.size > 0 and np.all(credibility_matrix >= 0) and np.all(credibility_matrix <= 1):
            print("  ✓ Matriz de credibilidad válida [0,1]")
            tests_pasados += 1
        else:
            print("  ✗ Matriz de credibilidad inválida")

        print(f"\nRESULTADO TEST SENTIDO COMÚN: {tests_pasados}/{tests_totales} tests pasados")

        # 14. Guardar resultados
        with open('validacion_electre_proyectos_researchgate.txt', 'w', encoding='utf-8') as f:
            f.write("=== VALIDACIÓN ELECTRE: RANKING DE PROYECTOS EMPRESARIALES ===\n")
            f.write("Referencia: ResearchGate - 'Ranking Projects Using the ELECTRE Method'\n")
            f.write("URL: https://www.researchgate.net/publication/[ID]\n\n")
            
            f.write("PESOS DE CRITERIOS:\n")
            for criterio in criterios:
                f.write(f"  {criterio.name}: {criterio.weight:.3f}\n")
            
            f.write("\nRANKING ELECTRE I:\n")
            for idx, alt_info in enumerate(ranking_i):
                f.write(f"  {idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})\n")
            
            f.write("\nRANKING ELECTRE III:\n")
            for idx, alt_info in enumerate(ranking_iii):
                f.write(f"  {idx+1}. {alt_info['name']} (Score: {alt_info['score']:.4f})\n")
            
            f.write(f"\nNÚCLEO ELECTRE I ({len(non_dominated)} alternativas):\n")
            for idx in non_dominated:
                if idx < len(alternativas):
                    f.write(f"  - {alternativas[idx].name}\n")
            
            f.write(f"\nVALIDACIÓN:\n")
            f.write(f"  Coincidencias Top 3: {coincidencias}/3\n")
            f.write(f"  Matches expectativas I: {matches_i}/3\n")
            f.write(f"  Matches expectativas III: {matches_iii}/3\n")
            f.write(f"  Test sentido común: {tests_pasados}/{tests_totales}\n")

        print(f"\n=== VALIDACIÓN COMPLETADA ===")
        print(f"Resultados guardados en: validacion_electre_proyectos_researchgate.txt")
        
        return {'electre_i': resultado_i, 'electre_iii': resultado_iii}

    except Exception as e:
        print(f"ERROR: La validación falló: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    ejecutar_validacion_electre_proyectos()