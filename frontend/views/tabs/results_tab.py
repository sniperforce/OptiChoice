# frontend/views/tabs/results_tab.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                            QGroupBox, QTableWidget, QTableWidgetItem, QPushButton,
                            QComboBox, QLabel, QTextEdit, QTabWidget, QTreeWidget,
                            QTreeWidgetItem, QHeaderView, QMessageBox, QCheckBox,
                            QSpinBox, QLineEdit, QFrame, QScrollArea, QGridLayout,
                            QMenu, QAction, QFileDialog, QProgressDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette, QBrush
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis
import json
import csv
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ResultsTableModel(QAbstractTableModel):
    """Custom table model for efficient results display"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_data = {}
        self.method_names = []
        self.alternatives = []
        self.display_mode = 'ranking'  # 'ranking' or 'score'
        
    def set_results(self, results_data: Dict[str, Dict]):
        """Set results data from multiple methods"""
        self.beginResetModel()
        self.results_data = results_data
        self.method_names = list(results_data.keys())
        
        # Extract alternatives from first method
        if self.method_names:
            first_result = results_data[self.method_names[0]]
            self.alternatives = first_result.get('alternatives', [])
        else:
            self.alternatives = []
            
        self.endResetModel()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.alternatives)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.method_names) * 2 + 2  # Name + (Rank, Score) for each method + Avg Rank
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        
        if row >= len(self.alternatives):
            return QVariant()
        
        alternative = self.alternatives[row]
        
        if role == Qt.DisplayRole:
            if col == 0:  # Alternative name
                return alternative.get('name', '')
            
            elif col == self.columnCount() - 1:  # Average ranking
                rankings = []
                for method_name in self.method_names:
                    result = self.results_data.get(method_name, {})
                    alts = result.get('alternatives', [])
                    for alt in alts:
                        if alt['id'] == alternative['id']:
                            rankings.append(alt.get('ranking', 0))
                            break
                
                if rankings:
                    avg_rank = sum(rankings) / len(rankings)
                    return f"{avg_rank:.2f}"
                return ""
            
            else:  # Method results
                method_idx = (col - 1) // 2
                is_score = (col - 1) % 2 == 1
                
                if method_idx < len(self.method_names):
                    method_name = self.method_names[method_idx]
                    result = self.results_data.get(method_name, {})
                    alts = result.get('alternatives', [])
                    
                    for alt in alts:
                        if alt['id'] == alternative['id']:
                            if is_score:
                                return f"{alt.get('score', 0):.4f}"
                            else:
                                return str(alt.get('ranking', '-'))
                
                return ""
        
        elif role == Qt.BackgroundRole:
            if col > 0 and col < self.columnCount() - 1:
                method_idx = (col - 1) // 2
                is_ranking = (col - 1) % 2 == 0
                
                if is_ranking and method_idx < len(self.method_names):
                    method_name = self.method_names[method_idx]
                    result = self.results_data.get(method_name, {})
                    alts = result.get('alternatives', [])
                    
                    for alt in alts:
                        if alt['id'] == alternative['id']:
                            ranking = alt.get('ranking', 0)
                            if ranking == 1:
                                return QBrush(QColor(200, 255, 200))  # Green
                            elif ranking == 2:
                                return QBrush(QColor(255, 255, 200))  # Yellow
                            elif ranking == 3:
                                return QBrush(QColor(255, 220, 200))  # Orange
        
        elif role == Qt.TextAlignmentRole:
            if col > 0:
                return Qt.AlignCenter
        
        elif role == Qt.FontRole:
            if col == 0 or col == self.columnCount() - 1:
                font = QFont()
                font.setBold(True)
                return font
        
        return QVariant()
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Alternative"
            elif section == self.columnCount() - 1:
                return "Avg. Rank"
            else:
                method_idx = (section - 1) // 2
                is_score = (section - 1) % 2 == 1
                
                if method_idx < len(self.method_names):
                    method_name = self.method_names[method_idx]
                    return f"{method_name}\n{'Score' if is_score else 'Rank'}"
        
        return QVariant()


class ResultDetailsWidget(QWidget):
    """Widget to show detailed results for a specific method"""
    
    def __init__(self, method_name: str, result_data: Dict, parent=None):
        super().__init__(parent)
        self.method_name = method_name
        self.result_data = result_data
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        # Method name
        method_label = QLabel(self.method_name)
        method_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(method_label)
        
        # Execution info
        exec_time = self.result_data.get('execution_time', 0)
        exec_info = QLabel(f"Execution time: {exec_time:.3f}s")
        exec_info.setStyleSheet("color: #666;")
        header_layout.addWidget(exec_info)
        
        layout.addWidget(header_frame)
        
        # Best alternative highlight
        best_alt = self.result_data.get('best_alternative', {})
        if best_alt:
            best_frame = QFrame()
            best_frame.setStyleSheet("""
                QFrame {
                    background-color: #c8e6c9;
                    border: 2px solid #4CAF50;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
            best_layout = QVBoxLayout(best_frame)
            
            best_title = QLabel("🏆 Best Alternative")
            best_title.setFont(QFont("Arial", 12, QFont.Bold))
            best_layout.addWidget(best_title)
            
            best_info = QLabel(f"{best_alt.get('name', 'Unknown')} (Score: {best_alt.get('score', 0):.4f})")
            best_layout.addWidget(best_info)
            
            layout.addWidget(best_frame)
        
        # Parameters used
        params = self.result_data.get('parameters', {})
        if params:
            params_group = QGroupBox("Parameters Used")
            params_layout = QVBoxLayout()
            
            params_text = QTextEdit()
            params_text.setReadOnly(True)
            params_text.setMaximumHeight(150)
            
            params_str = json.dumps(params, indent=2)
            params_text.setPlainText(params_str)
            
            params_layout.addWidget(params_text)
            params_group.setLayout(params_layout)
            layout.addWidget(params_group)
        
        # Detailed rankings table
        rankings_group = QGroupBox("Detailed Rankings")
        rankings_layout = QVBoxLayout()
        
        rankings_table = QTableWidget()
        alternatives = self.result_data.get('alternatives', [])
        
        rankings_table.setRowCount(len(alternatives))
        rankings_table.setColumnCount(4)
        rankings_table.setHorizontalHeaderLabels(["Rank", "Alternative", "Score", "Gap to Best"])
        
        for i, alt in enumerate(alternatives):
            rankings_table.setItem(i, 0, QTableWidgetItem(str(alt.get('ranking', '-'))))
            rankings_table.setItem(i, 1, QTableWidgetItem(alt.get('name', '')))
            
            score = alt.get('score', 0)
            score_item = QTableWidgetItem(f"{score:.4f}")
            rankings_table.setItem(i, 2, score_item)
            
            # Gap to best
            if i == 0:
                gap_item = QTableWidgetItem("-")
            else:
                best_score = alternatives[0].get('score', 0)
                gap = ((best_score - score) / best_score * 100) if best_score > 0 else 0
                gap_item = QTableWidgetItem(f"{gap:.1f}%")
            
            rankings_table.setItem(i, 3, gap_item)
            
            # Color first three rows
            if alt.get('ranking') == 1:
                for j in range(4):
                    rankings_table.item(i, j).setBackground(QColor(200, 255, 200))
            elif alt.get('ranking') == 2:
                for j in range(4):
                    rankings_table.item(i, j).setBackground(QColor(255, 255, 200))
            elif alt.get('ranking') == 3:
                for j in range(4):
                    rankings_table.item(i, j).setBackground(QColor(255, 220, 200))
        
        rankings_table.resizeColumnsToContents()
        rankings_layout.addWidget(rankings_table)
        rankings_group.setLayout(rankings_layout)
        layout.addWidget(rankings_group)


class ConsensusAnalysisWidget(QWidget):
    """Widget for consensus analysis between methods"""
    
    def __init__(self, results_data: Dict[str, Dict], parent=None):
        super().__init__(parent)
        self.results_data = results_data
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Consensus Analysis")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Calculate consensus metrics
        consensus_data = self.calculate_consensus()
        
        # Consensus indicators
        indicators_layout = QGridLayout()
        
        # Kendall's W
        kendall_card = self.create_metric_card(
            "Kendall's W",
            f"{consensus_data['kendalls_w']:.3f}",
            "Agreement between methods (0-1)",
            self.get_consensus_color(consensus_data['kendalls_w'])
        )
        indicators_layout.addWidget(kendall_card, 0, 0)
        
        # Top alternative agreement
        top_agreement_card = self.create_metric_card(
            "Top Choice Agreement",
            f"{consensus_data['top_agreement']:.0%}",
            "Methods agreeing on best alternative",
            self.get_agreement_color(consensus_data['top_agreement'])
        )
        indicators_layout.addWidget(top_agreement_card, 0, 1)
        
        # Average rank correlation
        avg_correlation_card = self.create_metric_card(
            "Avg. Rank Correlation",
            f"{consensus_data['avg_correlation']:.3f}",
            "Average Spearman correlation",
            self.get_consensus_color(consensus_data['avg_correlation'])
        )
        indicators_layout.addWidget(avg_correlation_card, 0, 2)
        
        layout.addLayout(indicators_layout)
        
        # Detailed agreement table
        agreement_group = QGroupBox("Method Agreement Matrix")
        agreement_layout = QVBoxLayout()
        
        agreement_table = QTableWidget()
        method_names = list(self.results_data.keys())
        n_methods = len(method_names)
        
        agreement_table.setRowCount(n_methods)
        agreement_table.setColumnCount(n_methods)
        agreement_table.setHorizontalHeaderLabels(method_names)
        agreement_table.setVerticalHeaderLabels(method_names)
        
        # Fill correlation matrix
        correlations = consensus_data['correlation_matrix']
        for i in range(n_methods):
            for j in range(n_methods):
                value = correlations[i][j]
                item = QTableWidgetItem(f"{value:.3f}")
                
                # Color based on correlation strength
                if i == j:
                    item.setBackground(QColor(200, 200, 200))
                else:
                    intensity = int(255 * (1 - abs(value)))
                    if value > 0:
                        item.setBackground(QColor(intensity, 255, intensity))
                    else:
                        item.setBackground(QColor(255, intensity, intensity))
                
                agreement_table.setItem(i, j, item)
        
        agreement_table.resizeColumnsToContents()
        agreement_layout.addWidget(agreement_table)
        agreement_group.setLayout(agreement_layout)
        layout.addWidget(agreement_group)
        
        # Recommendation
        recommendation = self.get_consensus_recommendation(consensus_data)
        rec_label = QLabel(recommendation)
        rec_label.setWordWrap(True)
        rec_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                font-style: italic;
            }
        """)
        layout.addWidget(rec_label)
    
    def create_metric_card(self, title: str, value: str, description: str, color: QColor) -> QFrame:
        """Create a metric display card"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color.name()};
                border-radius: 8px;
                padding: 10px;
                background-color: white;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        card_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 16, QFont.Bold))
        value_label.setStyleSheet(f"color: {color.name()};")
        card_layout.addWidget(value_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #666; font-size: 9px;")
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)
        
        return card
    
    def calculate_consensus(self) -> Dict[str, Any]:
        """Calculate consensus metrics between methods"""
        method_names = list(self.results_data.keys())
        n_methods = len(method_names)
        
        if n_methods < 2:
            return {
                'kendalls_w': 0,
                'top_agreement': 0,
                'avg_correlation': 0,
                'correlation_matrix': [[1]]
            }
        
        # Extract rankings for each method
        rankings_matrix = []
        alternatives = self.results_data[method_names[0]].get('alternatives', [])
        n_alternatives = len(alternatives)
        
        for method_name in method_names:
            result = self.results_data[method_name]
            method_rankings = []
            
            for alt in alternatives:
                alt_id = alt['id']
                # Find ranking for this alternative in this method
                method_alts = result.get('alternatives', [])
                for method_alt in method_alts:
                    if method_alt['id'] == alt_id:
                        method_rankings.append(method_alt.get('ranking', n_alternatives))
                        break
            
            rankings_matrix.append(method_rankings)
        
        rankings_array = np.array(rankings_matrix)
        
        # Calculate Kendall's W
        mean_rank = np.mean(rankings_array, axis=0)
        ss_total = np.sum((rankings_array - mean_rank) ** 2)
        kendalls_w = (12 * ss_total) / (n_methods ** 2 * (n_alternatives ** 3 - n_alternatives))
        
        # Calculate top alternative agreement
        top_choices = [np.argmin(rankings) for rankings in rankings_matrix]
        most_common_top = max(set(top_choices), key=top_choices.count)
        top_agreement = top_choices.count(most_common_top) / n_methods
        
        # Calculate correlation matrix
        correlation_matrix = np.zeros((n_methods, n_methods))
        for i in range(n_methods):
            for j in range(n_methods):
                if i == j:
                    correlation_matrix[i, j] = 1.0
                else:
                    # Spearman correlation
                    correlation_matrix[i, j] = 1 - (6 * np.sum((rankings_matrix[i] - rankings_matrix[j]) ** 2)) / (n_alternatives * (n_alternatives ** 2 - 1))
        
        # Average correlation (excluding diagonal)
        mask = np.ones_like(correlation_matrix, dtype=bool)
        np.fill_diagonal(mask, 0)
        avg_correlation = np.mean(correlation_matrix[mask])
        
        return {
            'kendalls_w': kendalls_w,
            'top_agreement': top_agreement,
            'avg_correlation': avg_correlation,
            'correlation_matrix': correlation_matrix.tolist()
        }
    
    def get_consensus_color(self, value: float) -> QColor:
        """Get color based on consensus value"""
        if value >= 0.8:
            return QColor(76, 175, 80)  # Green
        elif value >= 0.6:
            return QColor(255, 193, 7)  # Amber
        else:
            return QColor(244, 67, 54)  # Red
    
    def get_agreement_color(self, value: float) -> QColor:
        """Get color based on agreement percentage"""
        if value >= 0.75:
            return QColor(76, 175, 80)  # Green
        elif value >= 0.5:
            return QColor(255, 193, 7)  # Amber
        else:
            return QColor(244, 67, 54)  # Red
    
    def get_consensus_recommendation(self, consensus_data: Dict) -> str:
        """Generate recommendation based on consensus analysis"""
        kendalls_w = consensus_data['kendalls_w']
        top_agreement = consensus_data['top_agreement']
        
        if kendalls_w >= 0.8 and top_agreement >= 0.75:
            return "💚 Strong consensus detected! The methods show high agreement on the rankings. The results are highly reliable for decision making."
        elif kendalls_w >= 0.6:
            return "🟡 Moderate consensus detected. The methods show reasonable agreement, but some differences exist. Consider reviewing the methods with divergent results."
        else:
            return "🔴 Low consensus detected. The methods show significant disagreement. It's recommended to analyze why methods differ and possibly adjust parameters or criteria weights."


class ResultsTab(QWidget):
    """Professional Results Visualization Tab"""
    
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.results_data = {}
        self.filtered_results = {}
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header
        self.create_header(main_layout)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Top section: Summary and filters
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        self.create_summary_section(top_layout)
        self.create_filter_section(top_layout)
        
        splitter.addWidget(top_widget)
        
        # Bottom section: Detailed results
        self.create_results_section(splitter)
        
        splitter.setSizes([300, 400])
        main_layout.addWidget(splitter)
        
        # Export controls
        self.create_export_controls(main_layout)
    
    def create_header(self, parent_layout):
        """Create header with title and status"""
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
        
        # Title
        title = QLabel("MCDM Results Analysis")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh Results")
        self.refresh_btn.clicked.connect(self.load_results)
        header_layout.addWidget(self.refresh_btn)
        
        # Status
        self.status_label = QLabel("No results loaded")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        header_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(header_frame)
    
    def create_summary_section(self, parent_layout):
        """Create summary cards section"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)
        
        # Methods executed card
        self.methods_card = self.create_summary_card(
            "📊 Methods",
            "0",
            "Executed",
            QColor(33, 150, 243)
        )
        summary_layout.addWidget(self.methods_card)
        
        # Alternatives evaluated card
        self.alternatives_card = self.create_summary_card(
            "🎯 Alternatives",
            "0",
            "Evaluated",
            QColor(76, 175, 80)
        )
        summary_layout.addWidget(self.alternatives_card)
        
        # Consensus level card
        self.consensus_card = self.create_summary_card(
            "🤝 Consensus",
            "N/A",
            "Agreement",
            QColor(255, 152, 0)
        )
        summary_layout.addWidget(self.consensus_card)
        
        # Best alternative card
        self.best_alt_card = self.create_summary_card(
            "🏆 Best Choice",
            "None",
            "Top Alternative",
            QColor(156, 39, 176)
        )
        summary_layout.addWidget(self.best_alt_card)
        
        parent_layout.addWidget(summary_frame)
    
    def create_summary_card(self, icon: str, value: str, label: str, color: QColor) -> QFrame:
        """Create a summary information card"""
        card = QFrame()
        card.setMinimumHeight(100)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color.name()};
                border-radius: 8px;
                padding: 15px;
            }}
            QFrame:hover {{
                background-color: #f8f9fa;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        # Icon and label
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 20))
        header_layout.addWidget(icon_label)
        
        label_text = QLabel(label)
        label_text.setStyleSheet("color: #666;")
        header_layout.addWidget(label_text)
        header_layout.addStretch()
        
        card_layout.addLayout(header_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 18, QFont.Bold))
        value_label.setStyleSheet(f"color: {color.name()};")
        card_layout.addWidget(value_label)
        
        # Store labels for updates
        card.value_label = value_label
        card.label_text = label_text
        
        return card
    
    def create_filter_section(self, parent_layout):
        """Create filtering controls"""
        filter_group = QGroupBox("Filters & Display Options")
        filter_layout = QHBoxLayout()
        
        # Method filter
        method_label = QLabel("Method:")
        filter_layout.addWidget(method_label)
        
        self.method_filter = QComboBox()
        self.method_filter.addItem("All Methods")
        self.method_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.method_filter)
        
        # Display mode
        mode_label = QLabel("Display:")
        filter_layout.addWidget(mode_label)
        
        self.display_mode = QComboBox()
        self.display_mode.addItems(["Rankings & Scores", "Rankings Only", "Scores Only", "Normalized Scores"])
        self.display_mode.currentTextChanged.connect(self.update_display)
        filter_layout.addWidget(self.display_mode)
        
        filter_layout.addStretch()
        
        # Search
        search_label = QLabel("Search:")
        filter_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter alternatives...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)
        
        filter_group.setLayout(filter_layout)
        parent_layout.addWidget(filter_group)
    
    def create_results_section(self, parent):
        """Create main results display section"""
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # Tab widget for different views
        self.results_tabs = QTabWidget()
        
        # Comparison table tab
        self.comparison_widget = QWidget()
        comparison_layout = QVBoxLayout(self.comparison_widget)
        
        self.results_table = QTableWidget()
        self.results_model = ResultsTableModel()
        comparison_layout.addWidget(self.results_table)
        
        self.results_tabs.addTab(self.comparison_widget, "📊 Comparison Table")
        
        # Individual method details tabs
        self.method_tabs = {}
        
        # Consensus analysis tab
        self.consensus_widget = QWidget()
        self.consensus_layout = QVBoxLayout(self.consensus_widget)
        self.results_tabs.addTab(self.consensus_widget, "🤝 Consensus Analysis")
        
        # Charts tab
        self.charts_widget = QWidget()
        self.charts_layout = QVBoxLayout(self.charts_widget)
        self.results_tabs.addTab(self.charts_widget, "📈 Visualizations")
        
        results_layout.addWidget(self.results_tabs)
        parent.addWidget(results_widget)
    
    def create_export_controls(self, parent_layout):
        """Create export control buttons"""
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
        
        # Export buttons
        self.export_excel_btn = QPushButton("📊 Excel")
        self.export_excel_btn.clicked.connect(lambda: self.export_results('excel'))
        export_layout.addWidget(self.export_excel_btn)
        
        self.export_csv_btn = QPushButton("📄 CSV")
        self.export_csv_btn.clicked.connect(lambda: self.export_results('csv'))
        export_layout.addWidget(self.export_csv_btn)
        
        self.export_json_btn = QPushButton("🔧 JSON")
        self.export_json_btn.clicked.connect(lambda: self.export_results('json'))
        export_layout.addWidget(self.export_json_btn)
        
        self.export_pdf_btn = QPushButton("📑 PDF Report")
        self.export_pdf_btn.clicked.connect(lambda: self.export_results('pdf'))
        self.export_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        export_layout.addWidget(self.export_pdf_btn)
        
        export_layout.addStretch()
        
        # Print button
        self.print_btn = QPushButton("🖨️ Print")
        self.print_btn.clicked.connect(self.print_results)
        export_layout.addWidget(self.print_btn)
        
        parent_layout.addWidget(export_frame)
    
    def load_results(self):
        """Load results from project controller"""
        try:
            if not self.project_controller.current_project_id:
                self.status_label.setText("No project loaded")
                return
            
            # Get all results
            self.results_data = self.project_controller.get_method_results()
            
            if not self.results_data:
                self.status_label.setText("No results available")
                return
            
            # Update UI
            self.update_summary()
            self.update_filters()
            self.update_results_display()
            self.update_consensus_analysis()
            self.create_visualizations()
            
            self.status_label.setText(f"Loaded {len(self.results_data)} method results")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
        except Exception as e:
            logger.error(f"Error loading results: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load results: {str(e)}")
    
    def update_summary(self):
        """Update summary cards"""
        n_methods = len(self.results_data)
        self.methods_card.value_label.setText(str(n_methods))
        
        # Get alternatives count
        if self.results_data:
            first_result = next(iter(self.results_data.values()))
            n_alternatives = len(first_result.get('alternatives', []))
            self.alternatives_card.value_label.setText(str(n_alternatives))
            
            # Find most common best alternative
            best_alternatives = {}
            for method_name, result in self.results_data.items():
                best_alt = result.get('best_alternative', {})
                best_name = best_alt.get('name', 'Unknown')
                best_alternatives[best_name] = best_alternatives.get(best_name, 0) + 1
            
            if best_alternatives:
                most_common = max(best_alternatives, key=best_alternatives.get)
                count = best_alternatives[most_common]
                self.best_alt_card.value_label.setText(most_common)
                self.best_alt_card.label_text.setText(f"Chosen by {count}/{n_methods} methods")
    
    def update_filters(self):
        """Update filter options"""
        self.method_filter.clear()
        self.method_filter.addItem("All Methods")
        
        for method_name in self.results_data.keys():
            self.method_filter.addItem(method_name)
    
    def update_results_display(self):
        """Update main results display"""
        # Update comparison table
        self.update_comparison_table()
        
        # Create/update individual method tabs
        for method_name, result_data in self.results_data.items():
            if method_name not in self.method_tabs:
                # Create new tab
                details_widget = ResultDetailsWidget(method_name, result_data)
                scroll = QScrollArea()
                scroll.setWidget(details_widget)
                scroll.setWidgetResizable(True)
                
                index = self.results_tabs.insertTab(
                    self.results_tabs.count() - 2,  # Before consensus and charts
                    scroll,
                    f"📋 {method_name}"
                )
                self.method_tabs[method_name] = index
    
    def update_comparison_table(self):
        """Update the comparison table"""
        # Prepare data for table
        self.results_table.clear()
        
        if not self.results_data:
            return
        
        # Get filtered results
        filtered_results = self.get_filtered_results()
        
        # Setup table structure
        method_names = list(filtered_results.keys())
        if not method_names:
            return
        
        first_result = filtered_results[method_names[0]]
        alternatives = first_result.get('alternatives', [])
        
        # Apply search filter to alternatives
        search_text = self.search_input.text().lower()
        if search_text:
            alternatives = [alt for alt in alternatives 
                          if search_text in alt.get('name', '').lower()]
        
        # Configure table
        n_cols = len(method_names) * 2 + 2  # Name + (Rank, Score) for each + Avg
        self.results_table.setRowCount(len(alternatives))
        self.results_table.setColumnCount(n_cols)
        
        # Set headers
        headers = ["Alternative"]
        for method in method_names:
            headers.extend([f"{method}\nRank", f"{method}\nScore"])
        headers.append("Avg. Rank")
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Fill data
        for row, alt in enumerate(alternatives):
            # Alternative name
            self.results_table.setItem(row, 0, QTableWidgetItem(alt['name']))
            
            # Method results
            col = 1
            rankings = []
            
            for method_name in method_names:
                result = filtered_results[method_name]
                method_alts = result.get('alternatives', [])
                
                # Find this alternative in method results
                found = False
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        # Ranking
                        rank_item = QTableWidgetItem(str(method_alt.get('ranking', '-')))
                        rank_item.setTextAlignment(Qt.AlignCenter)
                        
                        # Color based on ranking
                        ranking = method_alt.get('ranking', 0)
                        if ranking == 1:
                            rank_item.setBackground(QColor(200, 255, 200))
                        elif ranking == 2:
                            rank_item.setBackground(QColor(255, 255, 200))
                        elif ranking == 3:
                            rank_item.setBackground(QColor(255, 220, 200))
                        
                        self.results_table.setItem(row, col, rank_item)
                        
                        # Score
                        score_item = QTableWidgetItem(f"{method_alt.get('score', 0):.4f}")
                        score_item.setTextAlignment(Qt.AlignCenter)
                        self.results_table.setItem(row, col + 1, score_item)
                        
                        rankings.append(ranking)
                        found = True
                        break
                
                if not found:
                    self.results_table.setItem(row, col, QTableWidgetItem("-"))
                    self.results_table.setItem(row, col + 1, QTableWidgetItem("-"))
                
                col += 2
            
            # Average ranking
            if rankings:
                avg_rank = sum(rankings) / len(rankings)
                avg_item = QTableWidgetItem(f"{avg_rank:.2f}")
                avg_item.setTextAlignment(Qt.AlignCenter)
                avg_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.results_table.setItem(row, col, avg_item)
        
        # Resize columns
        self.results_table.resizeColumnsToContents()
    
    def update_consensus_analysis(self):
        """Update consensus analysis"""
        # Clear previous analysis
        while self.consensus_layout.count():
            child = self.consensus_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if len(self.results_data) >= 2:
            # Create consensus widget
            consensus_widget = ConsensusAnalysisWidget(self.results_data)
            self.consensus_layout.addWidget(consensus_widget)
            
            # Update consensus card
            consensus_data = consensus_widget.calculate_consensus()
            kendalls_w = consensus_data['kendalls_w']
            self.consensus_card.value_label.setText(f"{kendalls_w:.3f}")
            
            # Update card color based on consensus level
            if kendalls_w >= 0.8:
                color = QColor(76, 175, 80)
            elif kendalls_w >= 0.6:
                color = QColor(255, 193, 7)
            else:
                color = QColor(244, 67, 54)
            
            self.consensus_card.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 2px solid {color.name()};
                    border-radius: 8px;
                    padding: 15px;
                }}
            """)
        else:
            info_label = QLabel("Consensus analysis requires at least 2 executed methods")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-style: italic;
                    padding: 20px;
                }
            """)
            self.consensus_layout.addWidget(info_label)
    
    def create_visualizations(self):
        """Create chart visualizations"""
        # Clear previous charts
        while self.charts_layout.count():
            child = self.charts_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.results_data:
            return
        
        # Create rankings comparison chart
        self.create_rankings_chart()
        
        # Create scores comparison chart
        self.create_scores_chart()
    
    def create_rankings_chart(self):
        """Create bar chart for rankings comparison"""
        chart = QChart()
        chart.setTitle("Rankings Comparison")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Prepare data
        method_names = list(self.results_data.keys())
        if not method_names:
            return
        
        first_result = next(iter(self.results_data.values()))
        alternatives = first_result.get('alternatives', [])[:5]  # Top 5
        
        # Create bar sets for each alternative
        bar_sets = []
        for alt in alternatives:
            bar_set = QBarSet(alt['name'])
            
            for method_name in method_names:
                result = self.results_data[method_name]
                method_alts = result.get('alternatives', [])
                
                # Find ranking for this alternative
                ranking = 0
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        ranking = method_alt.get('ranking', 0)
                        break
                
                bar_set.append(ranking)
            
            bar_sets.append(bar_set)
        
        # Create series
        series = QBarSeries()
        for bar_set in bar_sets:
            series.append(bar_set)
        
        chart.addSeries(series)
        
        # Configure axes
        axis_x = QBarCategoryAxis()
        axis_x.append(method_names)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Ranking")
        axis_y.setReverse(True)  # Lower ranking is better
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(chart_view.Antialiasing)
        chart_view.setMinimumHeight(300)
        
        self.charts_layout.addWidget(chart_view)
    
    def create_scores_chart(self):
        """Create bar chart for scores comparison"""
        # Similar implementation for scores
        # TODO: Implement scores chart
        pass
    
    def get_filtered_results(self) -> Dict[str, Dict]:
        """Get filtered results based on current filters"""
        if self.method_filter.currentText() == "All Methods":
            return self.results_data
        else:
            method_name = self.method_filter.currentText()
            if method_name in self.results_data:
                return {method_name: self.results_data[method_name]}
            return {}
    
    def apply_filters(self):
        """Apply current filters"""
        self.update_comparison_table()
    
    def update_display(self):
        """Update display based on selected mode"""
        # TODO: Implement different display modes
        self.update_comparison_table()
    
    def export_results(self, format_type: str):
        """Export results in specified format"""
        if not self.results_data:
            QMessageBox.warning(self, "No Data", "No results to export")
            return
        
        # Get file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"MCDM_Results_{timestamp}"
        
        if format_type == 'excel':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to Excel", f"{default_name}.xlsx",
                "Excel Files (*.xlsx)")
        elif format_type == 'csv':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to CSV", f"{default_name}.csv",
                "CSV Files (*.csv)")
        elif format_type == 'json':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to JSON", f"{default_name}.json",
                "JSON Files (*.json)")
        elif format_type == 'pdf':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to PDF", f"{default_name}.pdf",
                "PDF Files (*.pdf)")
        else:
            return
        
        if not file_path:
            return
        
        try:
            # Show progress dialog
            progress = QProgressDialog("Exporting results...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            if format_type == 'excel':
                self.export_to_excel(file_path, progress)
            elif format_type == 'csv':
                self.export_to_csv(file_path, progress)
            elif format_type == 'json':
                self.export_to_json(file_path, progress)
            elif format_type == 'pdf':
                self.export_to_pdf(file_path, progress)
            
            progress.setValue(100)
            QMessageBox.information(self, "Export Complete", 
                                  f"Results exported successfully to:\n{file_path}")
            
        except Exception as e:
            logger.error(f"Export error: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    def export_to_excel(self, file_path: str, progress: QProgressDialog):
        """Export results to Excel file"""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Number of Methods', 'Number of Alternatives', 'Best Alternative'],
                'Value': [
                    len(self.results_data),
                    len(next(iter(self.results_data.values())).get('alternatives', [])),
                    self.best_alt_card.value_label.text()
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            progress.setValue(20)
            
            # Comparison sheet
            comparison_data = self.prepare_comparison_data()
            pd.DataFrame(comparison_data).to_excel(writer, sheet_name='Comparison', index=False)
            progress.setValue(50)
            
            # Individual method sheets
            for i, (method_name, result) in enumerate(self.results_data.items()):
                method_data = self.prepare_method_data(result)
                pd.DataFrame(method_data).to_excel(writer, sheet_name=method_name, index=False)
                progress.setValue(50 + (40 * (i + 1) / len(self.results_data)))
    
    def export_to_csv(self, file_path: str, progress: QProgressDialog):
        """Export results to CSV file"""
        comparison_data = self.prepare_comparison_data()
        df = pd.DataFrame(comparison_data)
        df.to_csv(file_path, index=False)
        progress.setValue(100)
    
    def export_to_json(self, file_path: str, progress: QProgressDialog):
        """Export results to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.results_data, f, indent=2)
        progress.setValue(100)
    
    def export_to_pdf(self, file_path: str, progress: QProgressDialog):
        """Export results to PDF report"""
        # TODO: Implement PDF export with reportlab
        progress.setValue(100)
        QMessageBox.information(self, "PDF Export", "PDF export not yet implemented")
    
    def prepare_comparison_data(self) -> Dict[str, List]:
        """Prepare comparison data for export"""
        data = {'Alternative': []}
        
        if not self.results_data:
            return data
        
        method_names = list(self.results_data.keys())
        first_result = next(iter(self.results_data.values()))
        alternatives = first_result.get('alternatives', [])
        
        # Initialize columns
        for method in method_names:
            data[f'{method}_Rank'] = []
            data[f'{method}_Score'] = []
        data['Average_Rank'] = []
        
        # Fill data
        for alt in alternatives:
            data['Alternative'].append(alt['name'])
            rankings = []
            
            for method_name in method_names:
                result = self.results_data[method_name]
                method_alts = result.get('alternatives', [])
                
                found = False
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        data[f'{method_name}_Rank'].append(method_alt.get('ranking', '-'))
                        data[f'{method_name}_Score'].append(method_alt.get('score', 0))
                        rankings.append(method_alt.get('ranking', 0))
                        found = True
                        break
                
                if not found:
                    data[f'{method_name}_Rank'].append('-')
                    data[f'{method_name}_Score'].append(0)
            
            avg_rank = sum(rankings) / len(rankings) if rankings else 0
            data['Average_Rank'].append(avg_rank)
        
        return data
    
    def prepare_method_data(self, result: Dict) -> Dict[str, List]:
        """Prepare individual method data for export"""
        alternatives = result.get('alternatives', [])
        
        data = {
            'Rank': [alt.get('ranking', '-') for alt in alternatives],
            'Alternative': [alt.get('name', '') for alt in alternatives],
            'Score': [alt.get('score', 0) for alt in alternatives]
        }
        
        return data
    
    def print_results(self):
        """Print results"""
        # TODO: Implement printing functionality
        QMessageBox.information(self, "Print", "Print functionality not yet implemented")
    
    def refresh_on_tab_change(self):
        """Refresh when tab is selected"""
        self.load_results()