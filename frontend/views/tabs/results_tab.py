# frontend/views/tabs/results_tab.py

# Importaciones principales de PyQt5
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, 
    QTableWidget, QTableWidgetItem, QPushButton, QComboBox, 
    QLabel, QTextEdit, QTabWidget, QHeaderView, QMessageBox, 
    QCheckBox, QLineEdit, QFrame, QScrollArea, QGridLayout,
    QFileDialog, QProgressDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QFont, QColor, QBrush

# Importaciones estándar de Python
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging

# Importaciones de librerías de terceros
import numpy as np
import pandas as pd

# Importaciones para visualización con matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

# Crear logger
logger = logging.getLogger(__name__)


class MatplotlibCanvas(FigureCanvas):
    """Canvas para mostrar gráficos de matplotlib en PyQt5"""
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)


class ResultsTableModel(QAbstractTableModel):
    """Modelo de tabla personalizado para mostrar resultados eficientemente"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_data = {}
        self.method_names = []
        self.alternatives = []
        self.display_mode = 'ranking'
        
    def set_results(self, results_data: Dict[str, Dict]):
        """Establecer datos de resultados de múltiples métodos"""
        self.beginResetModel()
        self.results_data = results_data
        self.method_names = list(results_data.keys())
        
        if self.method_names:
            first_result = results_data[self.method_names[0]]
            self.alternatives = first_result.get('alternatives', [])
        else:
            self.alternatives = []
            
        self.endResetModel()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.alternatives)
    
    def columnCount(self, parent=QModelIndex()):
        return 1 + len(self.method_names) * 2 + 1
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:
                return self.alternatives[row].get('name', '')
            elif col < len(self.method_names) * 2 + 1:
                method_idx = (col - 1) // 2
                is_score = (col - 1) % 2 == 1
                
                if method_idx < len(self.method_names):
                    method_name = self.method_names[method_idx]
                    method_data = self.results_data.get(method_name, {})
                    alts = method_data.get('alternatives', [])
                    
                    alt_id = self.alternatives[row].get('id')
                    for alt in alts:
                        if alt.get('id') == alt_id:
                            if is_score:
                                return f"{alt.get('score', 0):.4f}"
                            else:
                                return str(alt.get('ranking', '-'))
                    
                return '-'
            else:
                ranks = []
                alt_id = self.alternatives[row].get('id')
                
                for method_name in self.method_names:
                    method_data = self.results_data.get(method_name, {})
                    alts = method_data.get('alternatives', [])
                    
                    for alt in alts:
                        if alt.get('id') == alt_id:
                            rank = alt.get('ranking')
                            if rank:
                                ranks.append(rank)
                            break
                
                if ranks:
                    return f"{sum(ranks) / len(ranks):.2f}"
                return '-'
                
        elif role == Qt.TextAlignmentRole:
            if col > 0:
                return Qt.AlignCenter
                
        elif role == Qt.BackgroundRole:
            if col > 0 and col < len(self.method_names) * 2 + 1:
                if (col - 1) % 2 == 0:
                    value = self.data(index, Qt.DisplayRole)
                    if value == '1':
                        return QBrush(QColor(255, 215, 0, 80))
                    elif value == '2':
                        return QBrush(QColor(192, 192, 192, 80))
                    elif value == '3':
                        return QBrush(QColor(205, 127, 50, 80))
        
        elif role == Qt.FontRole:
            if col == self.columnCount() - 1:
                font = QFont()
                font.setBold(True)
                return font
        
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Alternative"
            elif section < len(self.method_names) * 2 + 1:
                method_idx = (section - 1) // 2
                is_score = (section - 1) % 2 == 1
                method_name = self.method_names[method_idx]
                return f"{method_name}\n{'Score' if is_score else 'Rank'}"
            else:
                return "Avg.\nRank"
        
        return QVariant()


class ResultDetailsWidget(QWidget):
    """Widget para mostrar resultados detallados de un método"""
    
    def __init__(self, method_name: str, result_data: Dict, parent=None):
        super().__init__(parent)
        self.method_name = method_name
        self.result_data = result_data
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Título del método
        title = QLabel(f"Method: {self.method_name}")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Información de ejecución
        exec_info = QFrame()
        exec_info.setFrameStyle(QFrame.Box)
        exec_layout = QGridLayout(exec_info)
        
        exec_time = self.result_data.get('execution_time', 0)
        exec_layout.addWidget(QLabel("Execution Time:"), 0, 0)
        exec_layout.addWidget(QLabel(f"{exec_time:.3f} seconds"), 0, 1)
        
        timestamp = self.result_data.get('timestamp', '')
        exec_layout.addWidget(QLabel("Timestamp:"), 0, 2)
        exec_layout.addWidget(QLabel(timestamp), 0, 3)
        
        params = self.result_data.get('parameters', {})
        if params:
            exec_layout.addWidget(QLabel("Parameters:"), 1, 0)
            param_text = ", ".join([f"{k}: {v}" for k, v in params.items()])
            param_label = QLabel(param_text)
            param_label.setWordWrap(True)
            exec_layout.addWidget(param_label, 1, 1, 1, 3)
        
        layout.addWidget(exec_info)
        
        # Tabla de resultados
        results_table = QTableWidget()
        alternatives = self.result_data.get('alternatives', [])
        results_table.setRowCount(len(alternatives))
        results_table.setColumnCount(3)
        results_table.setHorizontalHeaderLabels(['Rank', 'Alternative', 'Score'])
        
        for i, alt in enumerate(alternatives):
            results_table.setItem(i, 0, QTableWidgetItem(str(alt.get('ranking', '-'))))
            results_table.setItem(i, 1, QTableWidgetItem(alt.get('name', '')))
            results_table.setItem(i, 2, QTableWidgetItem(f"{alt.get('score', 0):.4f}"))
        
        results_table.resizeColumnsToContents()
        layout.addWidget(results_table)


class SummaryCard(QFrame):
    """Widget de tarjeta para mostrar resumen de información"""
    
    def __init__(self, title: str, value: str = "-", icon: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                min-width: 150px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Ícono y título
        title_layout = QHBoxLayout()
        if icon:
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Arial", 16))
            title_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setStyleSheet("color: #666;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Valor
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.value_label)


class ConsensusAnalysisWidget(QWidget):
    """Widget para análisis de consenso entre métodos"""
    
    def __init__(self, results_data: Dict[str, Dict], parent=None):
        super().__init__(parent)
        self.results_data = results_data
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Calcular consenso
        consensus_data = self.calculate_consensus()
        
        # Mostrar métricas
        metrics_layout = QHBoxLayout()
        
        kendalls_w = consensus_data['kendalls_w']
        w_card = SummaryCard("Kendall's W", f"{kendalls_w:.3f}", "📊")
        metrics_layout.addWidget(w_card)
        
        agreement = consensus_data['agreement_percentage']
        agree_card = SummaryCard("Agreement", f"{agreement:.1f}%", "🤝")
        metrics_layout.addWidget(agree_card)
        
        metrics_layout.addStretch()
        layout.addLayout(metrics_layout)
        
        # Interpretación
        interpretation = QTextEdit()
        interpretation.setReadOnly(True)
        interpretation.setMaximumHeight(100)
        interpretation.setHtml(f"<p>{self.interpret_consensus(kendalls_w)}</p>")
        layout.addWidget(interpretation)
        
        # Tabla de correlación
        corr_table = self.create_correlation_table(consensus_data['correlations'])
        layout.addWidget(corr_table)
    
    def calculate_consensus(self) -> Dict[str, Any]:
        """Calcular métricas de consenso entre métodos"""
        method_names = list(self.results_data.keys())
        n_methods = len(method_names)
        
        if n_methods < 2:
            return {'kendalls_w': 0, 'agreement_percentage': 0, 'correlations': {}}
        
        # Extraer rankings
        rankings = []
        for method_name in method_names:
            method_rankings = []
            result = self.results_data[method_name]
            alts = result.get('alternatives', [])
            
            alt_dict = {alt['id']: alt['ranking'] for alt in alts}
            sorted_ids = sorted(alt_dict.keys())
            
            for alt_id in sorted_ids:
                method_rankings.append(alt_dict[alt_id])
            
            rankings.append(method_rankings)
        
        rankings = np.array(rankings)
        
        # Calcular Kendall's W
        n_items = rankings.shape[1]
        sum_ranks = np.sum(rankings, axis=0)
        mean_rank = np.mean(sum_ranks)
        
        s = np.sum((sum_ranks - mean_rank) ** 2)
        kendalls_w = (12 * s) / (n_methods ** 2 * (n_items ** 3 - n_items))
        
        # Calcular correlaciones
        correlations = {}
        for i in range(n_methods):
            for j in range(i + 1, n_methods):
                corr = np.corrcoef(rankings[i], rankings[j])[0, 1]
                correlations[f"{method_names[i]}-{method_names[j]}"] = corr
        
        # Porcentaje de acuerdo (top 3)
        agreement = 0
        for col in range(min(3, n_items)):
            top_alternatives = [np.argmin(rankings[i]) for i in range(n_methods)]
            if len(set(top_alternatives)) == 1:
                agreement += 33.33
        
        return {
            'kendalls_w': kendalls_w,
            'agreement_percentage': agreement,
            'correlations': correlations
        }
    
    def create_correlation_table(self, correlations: Dict[str, float]) -> QTableWidget:
        """Crear tabla de correlaciones"""
        table = QTableWidget()
        table.setRowCount(len(correlations))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['Method Pair', 'Correlation'])
        
        for i, (pair, corr) in enumerate(correlations.items()):
            table.setItem(i, 0, QTableWidgetItem(pair))
            corr_item = QTableWidgetItem(f"{corr:.3f}")
            
            # Colorear según correlación
            if corr >= 0.8:
                corr_item.setBackground(QColor(76, 175, 80, 100))
            elif corr >= 0.6:
                corr_item.setBackground(QColor(255, 193, 7, 100))
            else:
                corr_item.setBackground(QColor(244, 67, 54, 100))
            
            table.setItem(i, 1, corr_item)
        
        table.resizeColumnsToContents()
        return table
    
    def interpret_consensus(self, kendalls_w: float) -> str:
        """Interpretar el nivel de consenso"""
        if kendalls_w >= 0.8:
            return "🟢 <b>High consensus detected!</b> The methods show high agreement on the rankings."
        elif kendalls_w >= 0.6:
            return "🟡 <b>Moderate consensus detected.</b> The methods show reasonable agreement."
        else:
            return "🔴 <b>Low consensus detected.</b> The methods show significant disagreement."


class ResultsTab(QWidget):
    """Pestaña profesional de visualización de resultados"""
    
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.results_data = {}
        self.filtered_results = {}
        self.method_tabs = {}
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Encabezado
        self.create_header(main_layout)
        
        # Contenido principal con splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Sección superior: Resumen y filtros
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        self.create_summary_section(top_layout)
        self.create_filter_section(top_layout)
        
        splitter.addWidget(top_widget)
        
        # Sección inferior: Resultados detallados
        self.create_results_section(splitter)
        
        splitter.setSizes([300, 400])
        main_layout.addWidget(splitter)
        
        # Controles de exportación
        self.create_export_controls(main_layout)
    
    def create_header(self, parent_layout):
        """Crear encabezado con título y estado"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        title = QLabel("MCDM Results Analysis")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Refresh Results")
        self.refresh_btn.clicked.connect(self.load_results)
        header_layout.addWidget(self.refresh_btn)
        
        self.status_label = QLabel("No results loaded")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        header_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(header_frame)
    
    def create_summary_section(self, parent_layout):
        """Crear sección de resumen"""
        summary_frame = QFrame()
        summary_layout = QHBoxLayout(summary_frame)
        
        self.methods_card = SummaryCard("Methods Executed", "0", "⚙️")
        summary_layout.addWidget(self.methods_card)
        
        self.best_alt_card = SummaryCard("Best Alternative", "-", "🏆")
        summary_layout.addWidget(self.best_alt_card)
        
        self.consensus_card = SummaryCard("Consensus Level", "-", "🤝")
        summary_layout.addWidget(self.consensus_card)
        
        self.exec_time_card = SummaryCard("Total Time", "0s", "⏱️")
        summary_layout.addWidget(self.exec_time_card)
        
        summary_layout.addStretch()
        parent_layout.addWidget(summary_frame)
    
    def create_filter_section(self, parent_layout):
        """Crear sección de filtros"""
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Method:"))
        self.method_filter = QComboBox()
        self.method_filter.addItem("All Methods")
        self.method_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.method_filter)
        
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search alternatives...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        parent_layout.addWidget(filter_group)
    
    def create_results_section(self, parent):
        """Crear sección principal de resultados"""
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        self.results_tabs = QTabWidget()
        
        # Pestaña de tabla comparativa
        self.comparison_widget = QWidget()
        comparison_layout = QVBoxLayout(self.comparison_widget)
        
        self.results_table = QTableWidget()
        self.results_model = ResultsTableModel()
        comparison_layout.addWidget(self.results_table)
        
        self.results_tabs.addTab(self.comparison_widget, "📊 Comparison Table")
        
        # Pestaña de análisis de consenso
        self.consensus_widget = QWidget()
        self.consensus_layout = QVBoxLayout(self.consensus_widget)
        self.results_tabs.addTab(self.consensus_widget, "🤝 Consensus Analysis")
        
        # Pestaña de gráficos
        self.charts_widget = QWidget()
        self.charts_layout = QVBoxLayout(self.charts_widget)
        self.charts_scroll = QScrollArea()
        self.charts_scroll.setWidgetResizable(True)
        self.charts_content = QWidget()
        self.charts_content_layout = QVBoxLayout(self.charts_content)
        self.charts_scroll.setWidget(self.charts_content)
        self.charts_layout.addWidget(self.charts_scroll)
        self.results_tabs.addTab(self.charts_widget, "📈 Visualizations")
        
        results_layout.addWidget(self.results_tabs)
        parent.addWidget(results_widget)
    
    def create_export_controls(self, parent_layout):
        """Crear controles de exportación"""
        export_frame = QFrame()
        export_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        export_layout = QHBoxLayout(export_frame)
        
        export_label = QLabel("Export Results:")
        export_layout.addWidget(export_label)
        
        self.export_excel_btn = QPushButton("📊 Excel")
        self.export_excel_btn.clicked.connect(lambda: self.export_results('excel'))
        export_layout.addWidget(self.export_excel_btn)
        
        self.export_csv_btn = QPushButton("📄 CSV")
        self.export_csv_btn.clicked.connect(lambda: self.export_results('csv'))
        export_layout.addWidget(self.export_csv_btn)
        
        self.export_json_btn = QPushButton("📋 JSON")
        self.export_json_btn.clicked.connect(lambda: self.export_results('json'))
        export_layout.addWidget(self.export_json_btn)
        
        self.print_btn = QPushButton("🖨️ Print")
        self.print_btn.clicked.connect(self.print_results)
        export_layout.addWidget(self.print_btn)
        
        export_layout.addStretch()
        parent_layout.addWidget(export_frame)
    
    def load_results(self):
        """Cargar y mostrar resultados de archivos guardados"""
        try:
            if not self.project_controller.current_project_id:
                self.status_label.setText("No project selected")
                return
            
            project = self.project_controller.get_current_project()
            if not project:
                self.status_label.setText("Failed to load project")
                return
            
            self.results_data = {}
            
            if 'method_results' in project:
                self.results_data = project['method_results']
                results_loaded = len(self.results_data)
                
                total_exec_time = sum(
                    result.get('execution_time', 0) 
                    for result in self.results_data.values()
                )
                
                if results_loaded > 0:
                    self.status_label.setText(f"Loaded {results_loaded} results")
                    self.update_summary_cards(total_exec_time)
                    self.update_filters()
                    self.update_display()
                else:
                    self.status_label.setText("No results found for this project")
                    self.clear_displays()
            else:
                self.status_label.setText("No results found for this project")
                self.clear_displays()
                
        except Exception as e:
            logger.error(f"Error loading results: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load results: {str(e)}")
            self.status_label.setText("Error loading results")
    
    def clear_displays(self):
        """Limpiar todos los componentes de visualización"""
        self.methods_card.value_label.setText("0")
        self.best_alt_card.value_label.setText("-")
        self.consensus_card.value_label.setText("-")
        self.exec_time_card.value_label.setText("0s")
        
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        
        for i in reversed(range(self.consensus_layout.count())): 
            self.consensus_layout.itemAt(i).widget().setParent(None)
        
        for i in reversed(range(self.charts_content_layout.count())): 
            self.charts_content_layout.itemAt(i).widget().setParent(None)
        
        for method_name, index in list(self.method_tabs.items()):
            self.results_tabs.removeTab(index)
        self.method_tabs.clear()
    
    def update_with_results(self, results_data: Dict[str, Dict]):
        """Actualizar con nuevos datos de resultados"""
        try:
            logger.info(f"Updating results tab with {len(results_data)} results")
            
            if self.project_controller.current_project_id:
                project = self.project_controller.get_current_project()
                if project:
                    project['method_results'] = results_data
                    self.project_controller.save_project(project)
            
            self.results_data = results_data
            
            total_exec_time = sum(result.get('execution_time', 0) for result in results_data.values())
            
            self.update_summary_cards(total_exec_time)
            self.update_filters()
            self.update_display()
            
            self.status_label.setText(f"Displaying {len(results_data)} results")
            
        except Exception as e:
            logger.error(f"Error updating results: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update results: {str(e)}")
            self.status_label.setText("Error updating results")
    
    def update_summary_cards(self, total_exec_time):
        """Actualizar valores de las tarjetas de resumen"""
        self.methods_card.value_label.setText(str(len(self.results_data)))
        
        if self.results_data:
            best_alternatives = []
            for result in self.results_data.values():
                alts = result.get('alternatives', [])
                if alts:
                    sorted_alts = sorted(alts, key=lambda x: x.get('ranking', 999))
                    if sorted_alts:
                        best_alternatives.append(sorted_alts[0].get('name', 'Unknown'))
            
            if best_alternatives:
                from collections import Counter
                most_common = Counter(best_alternatives).most_common(1)[0]
                self.best_alt_card.value_label.setText(most_common[0])
            else:
                self.best_alt_card.value_label.setText("-")
        else:
            self.best_alt_card.value_label.setText("-")
        
        self.consensus_card.value_label.setText("-")
        self.exec_time_card.value_label.setText(f"{total_exec_time:.2f}s")
    
    def update_filters(self):
        """Actualizar opciones de filtro"""
        self.method_filter.clear()
        self.method_filter.addItem("All Methods")
        
        for method_name in self.results_data.keys():
            self.method_filter.addItem(method_name)
    
    def update_display(self):
        """Actualizar todos los componentes de visualización"""
        self.apply_filters()
        self.update_comparison_table()
        self.update_method_tabs()
        self.update_consensus_analysis()
        self.update_visualizations()
    
    def apply_filters(self):
        """Aplicar filtros actuales a los resultados"""
        selected_method = self.method_filter.currentText()
        search_text = self.search_input.text().lower()
        
        if selected_method == "All Methods":
            self.filtered_results = self.results_data.copy()
        else:
            self.filtered_results = {k: v for k, v in self.results_data.items() 
                                   if k == selected_method}
        
        # Aplicar búsqueda si hay texto
        if search_text and self.filtered_results:
            for method_name, result in self.filtered_results.items():
                filtered_alts = [alt for alt in result.get('alternatives', [])
                               if search_text in alt.get('name', '').lower()]
                if filtered_alts:
                    self.filtered_results[method_name]['alternatives'] = filtered_alts
    
    def update_comparison_table(self):
        """Actualizar tabla de comparación"""
        if not self.filtered_results:
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            return
        
        first_result = next(iter(self.filtered_results.values()))
        alternatives = first_result.get('alternatives', [])
        
        if not alternatives:
            return
        
        n_methods = len(self.filtered_results)
        self.results_table.setRowCount(len(alternatives))
        self.results_table.setColumnCount(1 + n_methods * 2 + 1)
        
        headers = ['Alternative']
        for method_name in self.filtered_results.keys():
            headers.extend([f'{method_name}\nRank', f'{method_name}\nScore'])
        headers.append('Avg.\nRank')
        self.results_table.setHorizontalHeaderLabels(headers)
        
        for row, alt in enumerate(alternatives):
            self.results_table.setItem(row, 0, QTableWidgetItem(alt.get('name', '')))
            
            rankings = []
            col = 1
            
            for method_name in self.filtered_results.keys():
                result = self.filtered_results[method_name]
                method_alts = result.get('alternatives', [])
                
                found = False
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        rank = method_alt.get('ranking', '-')
                        rank_item = QTableWidgetItem(str(rank))
                        rank_item.setTextAlignment(Qt.AlignCenter)
                        
                        if rank == 1:
                            rank_item.setBackground(QColor(255, 215, 0))
                        elif rank == 2:
                            rank_item.setBackground(QColor(192, 192, 192))
                        elif rank == 3:
                            rank_item.setBackground(QColor(205, 127, 50))
                        
                        self.results_table.setItem(row, col, rank_item)
                        
                        score = method_alt.get('score', 0)
                        score_item = QTableWidgetItem(f"{score:.4f}")
                        score_item.setTextAlignment(Qt.AlignRight)
                        self.results_table.setItem(row, col + 1, score_item)
                        
                        if isinstance(rank, (int, float)):
                            rankings.append(rank)
                        
                        found = True
                        break
                
                if not found:
                    self.results_table.setItem(row, col, QTableWidgetItem("-"))
                    self.results_table.setItem(row, col + 1, QTableWidgetItem("-"))
                
                col += 2
            
            if rankings:
                avg_rank = sum(rankings) / len(rankings)
                avg_item = QTableWidgetItem(f"{avg_rank:.2f}")
                avg_item.setTextAlignment(Qt.AlignCenter)
                avg_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.results_table.setItem(row, col, avg_item)
        
        self.results_table.resizeColumnsToContents()
    
    def update_method_tabs(self):
        """Actualizar pestañas de métodos individuales"""
        indices_to_remove = []
        for method_name, index in self.method_tabs.items():
            if method_name not in self.results_data:
                indices_to_remove.append(index)
        
        for index in sorted(indices_to_remove, reverse=True):
            self.results_tabs.removeTab(index)
        
        for method_name, result_data in self.results_data.items():
            if method_name not in self.method_tabs:
                details_widget = ResultDetailsWidget(method_name, result_data)
                scroll = QScrollArea()
                scroll.setWidget(details_widget)
                scroll.setWidgetResizable(True)
                
                index = self.results_tabs.count() - 2
                self.results_tabs.insertTab(index, scroll, f"📋 {method_name}")
                self.method_tabs[method_name] = index
    
    def update_consensus_analysis(self):
        """Actualizar análisis de consenso"""
        while self.consensus_layout.count():
            child = self.consensus_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if len(self.results_data) >= 2:
            consensus_widget = ConsensusAnalysisWidget(self.results_data)
            self.consensus_layout.addWidget(consensus_widget)
            
            consensus_data = consensus_widget.calculate_consensus()
            kendalls_w = consensus_data['kendalls_w']
            self.consensus_card.value_label.setText(f"{kendalls_w:.3f}")
            
            if kendalls_w >= 0.8:
                color = "#4CAF50"
            elif kendalls_w >= 0.6:
                color = "#FF9800"
            else:
                color = "#f44336"
            
            self.consensus_card.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 2px solid {color};
                    border-radius: 8px;
                    padding: 15px;
                    min-width: 150px;
                }}
            """)
            self.consensus_card.value_label.setStyleSheet(f"color: {color}; font: bold 16px Arial;")
        else:
            info_label = QLabel("Consensus analysis requires at least 2 executed methods")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            self.consensus_layout.addWidget(info_label)
    
    def update_visualizations(self):
        """Actualizar gráficos de visualización usando matplotlib"""
        while self.charts_content_layout.count():
            child = self.charts_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.results_data:
            return
        
        self.create_rankings_chart_matplotlib()
        self.charts_content_layout.addSpacing(20)
        self.create_scores_chart_matplotlib()
        self.charts_content_layout.addSpacing(20)
        self.create_consensus_heatmap()
    
    def create_rankings_chart_matplotlib(self):
        """Crear gráfico de barras comparando rankings usando matplotlib"""
        canvas = MatplotlibCanvas(self, width=10, height=6)
        ax = canvas.fig.add_subplot(111)
        
        method_names = list(self.results_data.keys())
        first_result = next(iter(self.results_data.values()))
        alternatives = first_result.get('alternatives', [])[:10]
        alt_names = [alt.get('name', '')[:20] for alt in alternatives]
        
        rankings_data = {}
        for method_name in method_names:
            rankings_data[method_name] = []
            result = self.results_data[method_name]
            method_alts = result.get('alternatives', [])
            
            for alt in alternatives:
                ranking = None
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        ranking = method_alt.get('ranking', 0)
                        break
                rankings_data[method_name].append(ranking if ranking else 0)
        
        x = np.arange(len(alt_names))
        width = 0.8 / len(method_names)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(method_names)))
        
        for i, (method_name, rankings) in enumerate(rankings_data.items()):
            offset = (i - len(method_names)/2) * width + width/2
            bars = ax.bar(x + offset, rankings, width, label=method_name, color=colors[i])
            
            for bar, rank in zip(bars, rankings):
                if rank > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                           str(int(rank)), ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel('Alternatives', fontsize=12)
        ax.set_ylabel('Ranking Position', fontsize=12)
        ax.set_title('Rankings Comparison Across Methods', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(alt_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        ax.invert_yaxis()
        
        canvas.fig.tight_layout()
        self.charts_content_layout.addWidget(canvas)
    
    def create_scores_chart_matplotlib(self):
        """Crear gráfico de líneas comparando scores usando matplotlib"""
        canvas = MatplotlibCanvas(self, width=10, height=6)
        ax = canvas.fig.add_subplot(111)
        
        first_result = next(iter(self.results_data.values()))
        alternatives = first_result.get('alternatives', [])[:10]
        alt_names = [alt.get('name', '')[:20] for alt in alternatives]
        
        x = np.arange(len(alternatives))
        
        for method_name, result_data in self.results_data.items():
            scores = []
            method_alts = result_data.get('alternatives', [])
            
            for alt in alternatives:
                score = 0
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        score = method_alt.get('score', 0)
                        break
                scores.append(score)
            
            ax.plot(x, scores, marker='o', label=method_name, linewidth=2, markersize=8)
        
        ax.set_xlabel('Alternatives', fontsize=12)
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title('Scores Comparison Across Methods', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(alt_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        canvas.fig.tight_layout()
        self.charts_content_layout.addWidget(canvas)
    
    def create_consensus_heatmap(self):
        """Crear mapa de calor de correlación entre métodos"""
        if len(self.results_data) < 2:
            return
        
        canvas = MatplotlibCanvas(self, width=8, height=6)
        ax = canvas.fig.add_subplot(111)
        
        method_names = list(self.results_data.keys())
        first_result = next(iter(self.results_data.values()))
        alternatives = first_result.get('alternatives', [])
        
        ranking_matrix = []
        for method_name in method_names:
            method_rankings = []
            result = self.results_data[method_name]
            method_alts = result.get('alternatives', [])
            
            for alt in alternatives:
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        method_rankings.append(method_alt.get('ranking', 0))
                        break
            
            ranking_matrix.append(method_rankings)
        
        ranking_matrix = np.array(ranking_matrix)
        correlation_matrix = np.corrcoef(ranking_matrix)
        
        im = ax.imshow(correlation_matrix, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
        
        ax.set_xticks(np.arange(len(method_names)))
        ax.set_yticks(np.arange(len(method_names)))
        ax.set_xticklabels(method_names, rotation=45, ha='right')
        ax.set_yticklabels(method_names)
        
        cbar = canvas.fig.colorbar(im, ax=ax)
        cbar.set_label('Correlation Coefficient', rotation=270, labelpad=15)
        
        for i in range(len(method_names)):
            for j in range(len(method_names)):
                text = ax.text(j, i, f'{correlation_matrix[i, j]:.2f}',
                             ha='center', va='center', 
                             color='black' if abs(correlation_matrix[i, j]) < 0.5 else 'white')
        
        ax.set_title('Method Correlation Matrix', fontsize=14, fontweight='bold')
        canvas.fig.tight_layout()
        self.charts_content_layout.addWidget(canvas)
    
    def export_results(self, format_type: str):
        """Exportar resultados en el formato especificado"""
        try:
            if not self.results_data:
                QMessageBox.warning(self, "No Data", "No results available to export.")
                return
            
            # Diálogo para seleccionar archivo
            if format_type == 'excel':
                filename, _ = QFileDialog.getSaveFileName(
                    self, "Export to Excel", "", "Excel Files (*.xlsx)")
                if filename:
                    self.export_to_excel(filename)
            elif format_type == 'csv':
                filename, _ = QFileDialog.getSaveFileName(
                    self, "Export to CSV", "", "CSV Files (*.csv)")
                if filename:
                    self.export_to_csv(filename)
            elif format_type == 'json':
                filename, _ = QFileDialog.getSaveFileName(
                    self, "Export to JSON", "", "JSON Files (*.json)")
                if filename:
                    self.export_to_json(filename)
                    
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    def export_to_excel(self, filename: str):
        """Exportar a Excel"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for method_name, result in self.results_data.items():
                df = self.result_to_dataframe(result)
                df.to_excel(writer, sheet_name=method_name[:31], index=False)
            
            # Hoja de resumen
            summary_df = self.create_summary_dataframe()
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        QMessageBox.information(self, "Success", f"Results exported to {filename}")
    
    def export_to_csv(self, filename: str):
        """Exportar a CSV"""
        df = self.create_summary_dataframe()
        df.to_csv(filename, index=False)
        QMessageBox.information(self, "Success", f"Results exported to {filename}")
    
    def export_to_json(self, filename: str):
        """Exportar a JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results_data, f, indent=2, ensure_ascii=False)
        QMessageBox.information(self, "Success", f"Results exported to {filename}")
    
    def result_to_dataframe(self, result: Dict) -> pd.DataFrame:
        """Convertir resultado a DataFrame"""
        alternatives = result.get('alternatives', [])
        data = {
            'Ranking': [alt.get('ranking', '-') for alt in alternatives],
            'Alternative': [alt.get('name', '') for alt in alternatives],
            'Score': [alt.get('score', 0) for alt in alternatives]
        }
        return pd.DataFrame(data)
    
    def create_summary_dataframe(self) -> pd.DataFrame:
        """Crear DataFrame de resumen"""
        if not self.results_data:
            return pd.DataFrame()
        
        first_result = next(iter(self.results_data.values()))
        alternatives = first_result.get('alternatives', [])
        
        data = {'Alternative': [alt.get('name', '') for alt in alternatives]}
        
        for method_name, result in self.results_data.items():
            method_alts = result.get('alternatives', [])
            rankings = []
            scores = []
            
            for alt in alternatives:
                found = False
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        rankings.append(method_alt.get('ranking', '-'))
                        scores.append(method_alt.get('score', 0))
                        found = True
                        break
                if not found:
                    rankings.append('-')
                    scores.append(0)
            
            data[f'{method_name}_Rank'] = rankings
            data[f'{method_name}_Score'] = scores
        
        return pd.DataFrame(data)
    
    def print_results(self):
        """Imprimir resultados"""
        try:
            # Por ahora, solo mostrar un mensaje
            QMessageBox.information(self, "Print", 
                                  "Print functionality would be implemented here.\n" +
                                  "For now, please export to PDF and print from there.")
        except Exception as e:
            logger.error(f"Error printing results: {str(e)}")
            QMessageBox.critical(self, "Print Error", f"Failed to print: {str(e)}")
    
    def refresh_on_tab_change(self):
        """Refrescar cuando se selecciona la pestaña"""
        self.load_results()