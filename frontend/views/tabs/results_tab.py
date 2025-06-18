# frontend/views/tabs/results_tab.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                            QGroupBox, QTableWidget, QTableWidgetItem, QPushButton,
                            QComboBox, QLabel, QTextEdit, QTabWidget, QTreeWidget,
                            QTreeWidgetItem, QHeaderView, QMessageBox, QCheckBox,
                            QSpinBox, QLineEdit, QFrame, QScrollArea, QGridLayout,
                            QMenu, QAction, QFileDialog, QProgressDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QFont, QColor, QIcon, QPalette, QBrush

import json
import csv
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns

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
        # Alternative name + (rank, score) for each method + average
        return 1 + len(self.method_names) * 2 + 1
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:  # Alternative name
                return self.alternatives[row].get('name', '')
            elif col < len(self.method_names) * 2 + 1:  # Method results
                method_idx = (col - 1) // 2
                is_score = (col - 1) % 2 == 1
                
                method_name = self.method_names[method_idx]
                method_result = self.results_data[method_name]
                
                # Find the alternative in method results
                alt_id = self.alternatives[row]['id']
                for alt in method_result.get('alternatives', []):
                    if alt['id'] == alt_id:
                        if is_score:
                            return f"{alt.get('score', 0):.4f}"
                        else:
                            return str(alt.get('ranking', '-'))
                
                return '-'
            else:  # Average rank
                ranks = []
                alt_id = self.alternatives[row]['id']
                
                for method_name in self.method_names:
                    method_result = self.results_data[method_name]
                    for alt in method_result.get('alternatives', []):
                        if alt['id'] == alt_id:
                            ranks.append(alt.get('ranking', 0))
                            break
                
                if ranks:
                    return f"{sum(ranks) / len(ranks):.2f}"
                return '-'
        
        elif role == Qt.BackgroundRole:
            if col == 0:
                return QColor(240, 240, 240)
            elif col == self.columnCount() - 1:
                return QColor(230, 230, 250)
        
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
            elif section < len(self.method_names) * 2 + 1:
                method_idx = (section - 1) // 2
                is_score = (section - 1) % 2 == 1
                method_name = self.method_names[method_idx]
                return f"{method_name}\n{'Score' if is_score else 'Rank'}"
            else:
                return "Avg.\nRank"
        
        return QVariant()


class ResultDetailsWidget(QWidget):
    """Widget to display detailed results for a single method"""
    
    def __init__(self, method_name: str, result_data: Dict, parent=None):
        super().__init__(parent)
        self.method_name = method_name
        self.result_data = result_data
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Method title
        title = QLabel(f"Method: {self.method_name}")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        # Execution info
        exec_info = QFrame()
        exec_info.setFrameStyle(QFrame.Box)
        exec_layout = QGridLayout(exec_info)
        
        # Execution time
        exec_time = self.result_data.get('execution_time', 0)
        exec_layout.addWidget(QLabel("Execution Time:"), 0, 0)
        exec_layout.addWidget(QLabel(f"{exec_time:.3f} seconds"), 0, 1)
        
        # Timestamp
        timestamp = self.result_data.get('timestamp', '')
        exec_layout.addWidget(QLabel("Timestamp:"), 0, 2)
        exec_layout.addWidget(QLabel(timestamp), 0, 3)
        
        # Method-specific parameters
        params = self.result_data.get('parameters', {})
        if params:
            exec_layout.addWidget(QLabel("Parameters:"), 1, 0)
            param_text = ", ".join([f"{k}: {v}" for k, v in params.items()])
            param_label = QLabel(param_text)
            param_label.setWordWrap(True)
            exec_layout.addWidget(param_label, 1, 1, 1, 3)
        
        layout.addWidget(exec_info)
        
        # Rankings table
        rankings_group = QGroupBox("Rankings")
        rankings_layout = QVBoxLayout()
        
        rankings_table = QTableWidget()
        alternatives = self.result_data.get('alternatives', [])
        rankings_table.setRowCount(len(alternatives))
        rankings_table.setColumnCount(3)
        rankings_table.setHorizontalHeaderLabels(["Rank", "Alternative", "Score"])
        
        # Sort by ranking
        sorted_alts = sorted(alternatives, key=lambda x: x.get('ranking', 999))
        
        for row, alt in enumerate(sorted_alts):
            # Rank
            rank_item = QTableWidgetItem(str(alt.get('ranking', '-')))
            rank_item.setTextAlignment(Qt.AlignCenter)
            
            # Color based on rank
            if alt.get('ranking') == 1:
                rank_item.setBackground(QColor(255, 215, 0))  # Gold
            elif alt.get('ranking') == 2:
                rank_item.setBackground(QColor(192, 192, 192))  # Silver
            elif alt.get('ranking') == 3:
                rank_item.setBackground(QColor(205, 127, 50))  # Bronze
            
            rankings_table.setItem(row, 0, rank_item)
            
            # Alternative name
            name_item = QTableWidgetItem(alt.get('name', ''))
            rankings_table.setItem(row, 1, name_item)
            
            # Score
            score_item = QTableWidgetItem(f"{alt.get('score', 0):.6f}")
            score_item.setTextAlignment(Qt.AlignRight)
            rankings_table.setItem(row, 2, score_item)
        
        rankings_table.resizeColumnsToContents()
        rankings_layout.addWidget(rankings_table)
        rankings_group.setLayout(rankings_layout)
        layout.addWidget(rankings_group)
        
        # Method-specific details
        self.add_method_specific_details(layout)
    
    def add_method_specific_details(self, layout):
        """Add method-specific details based on the method type"""
        details_group = QGroupBox("Method Details")
        details_layout = QVBoxLayout()
        
        if self.method_name == "AHP":
            self.add_ahp_details(details_layout)
        elif self.method_name == "TOPSIS":
            self.add_topsis_details(details_layout)
        elif self.method_name == "PROMETHEE":
            self.add_promethee_details(details_layout)
        elif self.method_name == "ELECTRE":
            self.add_electre_details(details_layout)
        
        if details_layout.count() > 0:
            details_group.setLayout(details_layout)
            layout.addWidget(details_group)
    
    def add_ahp_details(self, layout):
        """Add AHP-specific details"""
        # Consistency ratio
        cr = self.result_data.get('consistency_ratio', 0)
        cr_label = QLabel(f"Consistency Ratio: {cr:.4f}")
        
        if cr <= 0.1:
            cr_label.setStyleSheet("color: green; font-weight: bold;")
            cr_label.setText(cr_label.text() + " ✓ (Consistent)")
        else:
            cr_label.setStyleSheet("color: red; font-weight: bold;")
            cr_label.setText(cr_label.text() + " ✗ (Inconsistent)")
        
        layout.addWidget(cr_label)
        
        # Lambda max
        lambda_max = self.result_data.get('lambda_max', 0)
        layout.addWidget(QLabel(f"λ_max: {lambda_max:.4f}"))
    
    def add_topsis_details(self, layout):
        """Add TOPSIS-specific details"""
        # Ideal solutions
        ideal_positive = self.result_data.get('ideal_positive', [])
        ideal_negative = self.result_data.get('ideal_negative', [])
        
        if ideal_positive:
            layout.addWidget(QLabel("Ideal Positive Solution:"))
            pos_text = ", ".join([f"{v:.4f}" for v in ideal_positive])
            layout.addWidget(QLabel(pos_text))
        
        if ideal_negative:
            layout.addWidget(QLabel("Ideal Negative Solution:"))
            neg_text = ", ".join([f"{v:.4f}" for v in ideal_negative])
            layout.addWidget(QLabel(neg_text))
    
    def add_promethee_details(self, layout):
        """Add PROMETHEE-specific details"""
        # Preference function used
        pref_func = self.result_data.get('preference_function', 'Usual')
        layout.addWidget(QLabel(f"Preference Function: {pref_func}"))
        
        # Thresholds if any
        thresholds = self.result_data.get('thresholds', {})
        if thresholds:
            layout.addWidget(QLabel("Thresholds:"))
            for criterion, values in thresholds.items():
                layout.addWidget(QLabel(f"  {criterion}: {values}"))
    
    def add_electre_details(self, layout):
        """Add ELECTRE-specific details"""
        # Concordance threshold
        c_threshold = self.result_data.get('concordance_threshold', 0)
        layout.addWidget(QLabel(f"Concordance Threshold: {c_threshold:.3f}"))
        
        # Discordance threshold
        d_threshold = self.result_data.get('discordance_threshold', 0)
        layout.addWidget(QLabel(f"Discordance Threshold: {d_threshold:.3f}"))


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
        top_alternatives = []
        
        for method_name in method_names:
            result = self.results_data[method_name]
            alternatives = result.get('alternatives', [])
            
            # Sort by ranking
            sorted_alts = sorted(alternatives, key=lambda x: x.get('ranking', 999))
            
            # Extract rankings
            rankings = [alt.get('ranking', 0) for alt in sorted_alts]
            rankings_matrix.append(rankings)
            
            # Get top alternative
            if sorted_alts:
                top_alternatives.append(sorted_alts[0].get('id'))
        
        # Convert to numpy array
        rankings_matrix = np.array(rankings_matrix)
        n_alternatives = rankings_matrix.shape[1]
        
        # Calculate Kendall's W
        mean_rank = np.mean(rankings_matrix, axis=0)
        ss_total = np.sum((rankings_matrix - mean_rank) ** 2)
        kendalls_w = (12 * ss_total) / (n_methods ** 2 * (n_alternatives ** 3 - n_alternatives))
        
        # Calculate top alternative agreement
        top_agreement = len([x for x in top_alternatives if x == top_alternatives[0]]) / len(top_alternatives)
        
        # Calculate pairwise correlations
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
        self.method_tabs = {}
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
            "Methods Executed",
            "0",
            "#2196F3"
        )
        summary_layout.addWidget(self.methods_card)
        
        # Best alternative card
        self.best_alt_card = self.create_summary_card(
            "Best Alternative",
            "-",
            "#4CAF50"
        )
        summary_layout.addWidget(self.best_alt_card)
        
        # Consensus level card
        self.consensus_card = self.create_summary_card(
            "Consensus Level",
            "-",
            "#FF9800"
        )
        summary_layout.addWidget(self.consensus_card)
        
        # Execution time card
        self.exec_time_card = self.create_summary_card(
            "Total Exec. Time",
            "0.0s",
            "#9C27B0"
        )
        summary_layout.addWidget(self.exec_time_card)
        
        parent_layout.addWidget(summary_frame)
    
    def create_summary_card(self, label_text: str, value_text: str, color: str) -> QFrame:
        """Create a summary display card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
                min-width: 150px;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        
        label = QLabel(label_text)
        label.setStyleSheet("color: #666; font-size: 11px;")
        card_layout.addWidget(label)
        
        value_label = QLabel(value_text)
        value_label.setFont(QFont("Arial", 16, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
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
        
        # Individual method details tabs will be added dynamically
        
        # Consensus analysis tab
        self.consensus_widget = QWidget()
        self.consensus_layout = QVBoxLayout(self.consensus_widget)
        self.results_tabs.addTab(self.consensus_widget, "🤝 Consensus Analysis")
        
        # Charts tab
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
        """Load results from the project controller"""
        try:
            if not self.project_controller.current_project_id:
                self.status_label.setText("No project loaded")
                return
            
            # Get results from database
            results = self.project_controller.get_method_results()
            
            if not results:
                self.status_label.setText("No results available")
                self.results_data = {}
                self.update_display()
                return
            
            # Process results
            self.results_data = {}
            total_exec_time = 0
            
            for result in results:
                method_name = result.get('method_name', 'Unknown')
                
                # Parse result data
                result_data = json.loads(result.get('result_data', '{}'))
                result_data['timestamp'] = result.get('created_at', '')
                
                self.results_data[method_name] = result_data
                total_exec_time += result_data.get('execution_time', 0)
            
            # Update summary cards
            self.update_summary_cards(total_exec_time)
            
            # Update filters
            self.update_filters()
            
            # Update display
            self.update_display()
            
            self.status_label.setText(f"Loaded {len(self.results_data)} results")
            
        except Exception as e:
            logger.error(f"Error loading results: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load results: {str(e)}")
    
    def update_summary_cards(self, total_exec_time):
        """Update summary card values"""
        # Methods executed
        self.methods_card.value_label.setText(str(len(self.results_data)))
        
        # Best alternative (most frequent #1)
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
        
        # Consensus level (will be updated later)
        self.consensus_card.value_label.setText("-")
        
        # Execution time
        self.exec_time_card.value_label.setText(f"{total_exec_time:.2f}s")
    
    def update_filters(self):
        """Update filter options"""
        self.method_filter.clear()
        self.method_filter.addItem("All Methods")
        
        for method_name in self.results_data.keys():
            self.method_filter.addItem(method_name)
    
    def update_display(self):
        """Update all display components"""
        # Apply filters first
        self.apply_filters()
        
        # Update comparison table
        self.update_comparison_table()
        
        # Update/create individual method tabs
        self.update_method_tabs()
        
        # Update consensus analysis
        self.update_consensus_analysis()
        
        # Update visualizations
        self.update_visualizations()
    
    def apply_filters(self):
        """Apply current filters to results"""
        selected_method = self.method_filter.currentText()
        search_text = self.search_input.text().lower()
        
        if selected_method == "All Methods":
            self.filtered_results = self.results_data.copy()
        else:
            self.filtered_results = {k: v for k, v in self.results_data.items() 
                                   if k == selected_method}
        
        # Additional filtering based on search can be done here
        
        self.update_comparison_table()
    
    def update_comparison_table(self):
        """Update the comparison table with current data"""
        if not self.filtered_results:
            self.results_table.clear()
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            return
        
        # Get data structure
        method_names = list(self.filtered_results.keys())
        first_result = next(iter(self.filtered_results.values()))
        alternatives = first_result.get('alternatives', [])
        
        # Apply search filter to alternatives
        search_text = self.search_input.text().lower()
        if search_text:
            alternatives = [alt for alt in alternatives 
                          if search_text in alt.get('name', '').lower()]
        
        # Setup table
        n_cols = 1 + len(method_names) * 2 + 1  # Name + (Rank, Score) for each + Avg
        self.results_table.setRowCount(len(alternatives))
        self.results_table.setColumnCount(n_cols)
        
        # Set headers
        headers = ["Alternative"]
        for method in method_names:
            headers.extend([f"{method}\nRank", f"{method}\nScore"])
        headers.append("Avg.\nRank")
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Fill data
        for row, alt in enumerate(alternatives):
            # Alternative name
            name_item = QTableWidgetItem(alt.get('name', ''))
            name_item.setFont(QFont("Arial", 10, QFont.Bold))
            self.results_table.setItem(row, 0, name_item)
            
            col = 1
            rankings = []
            
            for method_name in method_names:
                result = self.filtered_results[method_name]
                method_alts = result.get('alternatives', [])
                
                # Find matching alternative
                found = False
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        # Rank
                        rank = method_alt.get('ranking', '-')
                        rank_item = QTableWidgetItem(str(rank))
                        rank_item.setTextAlignment(Qt.AlignCenter)
                        
                        # Color based on rank
                        if rank == 1:
                            rank_item.setBackground(QColor(255, 215, 0))
                        elif rank == 2:
                            rank_item.setBackground(QColor(192, 192, 192))
                        elif rank == 3:
                            rank_item.setBackground(QColor(205, 127, 50))
                        
                        self.results_table.setItem(row, col, rank_item)
                        
                        # Score
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
            
            # Average rank
            if rankings:
                avg_rank = sum(rankings) / len(rankings)
                avg_item = QTableWidgetItem(f"{avg_rank:.2f}")
                avg_item.setTextAlignment(Qt.AlignCenter)
                avg_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.results_table.setItem(row, col, avg_item)
        
        # Resize columns
        self.results_table.resizeColumnsToContents()
    
    def update_method_tabs(self):
        """Update individual method result tabs"""
        # Remove old method tabs
        indices_to_remove = []
        for method_name, index in self.method_tabs.items():
            if method_name not in self.results_data:
                indices_to_remove.append(index)
        
        for index in sorted(indices_to_remove, reverse=True):
            self.results_tabs.removeTab(index)
        
        # Add/update tabs for current results
        for method_name, result_data in self.results_data.items():
            if method_name not in self.method_tabs:
                # Create new tab
                details_widget = ResultDetailsWidget(method_name, result_data)
                scroll = QScrollArea()
                scroll.setWidget(details_widget)
                scroll.setWidgetResizable(True)
                
                # Insert before consensus and charts tabs
                index = self.results_tabs.count() - 2
                self.results_tabs.insertTab(index, scroll, f"📋 {method_name}")
                self.method_tabs[method_name] = index
    
    def update_consensus_analysis(self):
        """Update consensus analysis tab"""
        # Clear previous content
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
            info_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-style: italic;
                    padding: 20px;
                }
            """)
            self.consensus_layout.addWidget(info_label)
    
    def update_visualizations(self):
        """Update visualization charts"""
        # Clear previous charts
        while self.charts_content_layout.count():
            child = self.charts_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.results_data:
            return
        
        # Create rankings comparison chart
        self.create_rankings_chart()
        
        # Create scores comparison chart
        self.create_scores_chart()
        
        # Create radar chart for top alternatives
        self.create_radar_chart()
    
    def create_rankings_chart(self):
        """Create bar chart comparing rankings across methods"""
        chart = QChart()
        chart.setTitle("Rankings Comparison")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Prepare data
        series = QBarSeries()
        
        method_names = list(self.results_data.keys())
        categories = []
        
        # Get alternatives from first method
        first_result = next(iter(self.results_data.values()))
        alternatives = first_result.get('alternatives', [])[:10]  # Limit to top 10
        
        for alt in alternatives:
            categories.append(alt.get('name', '')[:20])  # Truncate long names
            
            bar_set = QBarSet(alt.get('name', ''))
            
            for method_name in method_names:
                result = self.results_data[method_name]
                method_alts = result.get('alternatives', [])
                
                # Find ranking for this alternative
                ranking = None
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        ranking = method_alt.get('ranking', 0)
                        break
                
                bar_set.append(ranking if ranking else 0)
            
            series.append(bar_set)
        
        chart.addSeries(series)
        
        # Axes
        axis_x = QBarCategoryAxis()
        axis_x.append(method_names)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, len(alternatives) + 1)
        axis_y.setLabelFormat("%d")
        axis_y.setTitleText("Ranking")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(400)
        
        self.charts_content_layout.addWidget(chart_view)
    
    def create_scores_chart(self):
        """Create line chart comparing scores across methods"""
        chart = QChart()
        chart.setTitle("Scores Comparison")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Get alternatives
        first_result = next(iter(self.results_data.values()))
        alternatives = first_result.get('alternatives', [])[:10]  # Limit to top 10
        
        # Create series for each method
        for method_name, result_data in self.results_data.items():
            series = QLineSeries()
            series.setName(method_name)
            
            method_alts = result_data.get('alternatives', [])
            
            for i, alt in enumerate(alternatives):
                # Find score for this alternative
                score = 0
                for method_alt in method_alts:
                    if method_alt['id'] == alt['id']:
                        score = method_alt.get('score', 0)
                        break
                
                series.append(i, score)
            
            chart.addSeries(series)
        
        # Axes
        axis_x = QValueAxis()
        axis_x.setRange(0, len(alternatives) - 1)
        axis_x.setLabelFormat("%d")
        axis_x.setTitleText("Alternative Index")
        chart.addAxis(axis_x, Qt.AlignBottom)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 1)
        axis_y.setTitleText("Score")
        chart.addAxis(axis_y, Qt.AlignLeft)
        
        # Attach axes to all series
        for series in chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(400)
        
        self.charts_content_layout.addWidget(chart_view)
    
    def create_radar_chart(self):
        """Create radar chart for top alternatives"""
        # This would require a custom implementation or external library
        # For now, create a placeholder
        info_label = QLabel("Radar chart visualization coming soon...")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-style: italic;
                padding: 20px;
                background-color: #f5f5f5;
                border-radius: 5px;
            }
        """)
        self.charts_content_layout.addWidget(info_label)
    
    def get_filtered_results(self) -> Dict[str, Dict]:
        """Get currently filtered results"""
        return self.filtered_results if self.filtered_results else self.results_data
    
    def export_results(self, format_type: str):
        """Export results in specified format"""
        try:
            if not self.results_data:
                QMessageBox.warning(self, "No Data", "No results available to export.")
                return
            
            # Get file path
            default_name = f"mcdm_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if format_type == 'excel':
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Export to Excel", f"{default_name}.xlsx",
                    "Excel Files (*.xlsx)")
                if file_path:
                    self.export_to_excel(file_path)
                    
            elif format_type == 'csv':
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Export to CSV", f"{default_name}.csv",
                    "CSV Files (*.csv)")
                if file_path:
                    self.export_to_csv(file_path)
                    
            elif format_type == 'json':
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Export to JSON", f"{default_name}.json",
                    "JSON Files (*.json)")
                if file_path:
                    self.export_to_json(file_path)
                    
            elif format_type == 'pdf':
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Export to PDF", f"{default_name}.pdf",
                    "PDF Files (*.pdf)")
                if file_path:
                    self.export_to_pdf(file_path)
            
        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"Failed to export results: {str(e)}")
    
    def export_to_excel(self, file_path: str):
        """Export results to Excel file"""
        with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
            # Comparison sheet
            comparison_data = self.prepare_comparison_data()
            df_comparison = pd.DataFrame(comparison_data)
            df_comparison.to_excel(writer, sheet_name='Comparison', index=False)
            
            # Individual method sheets
            for method_name, result_data in self.results_data.items():
                method_data = self.prepare_method_data(result_data)
                df_method = pd.DataFrame(method_data)
                sheet_name = method_name[:31]  # Excel sheet name limit
                df_method.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Format the Excel file
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4CAF50',
                'font_color': 'white',
                'border': 1
            })
            
            # Apply formatting to each sheet
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                worksheet.freeze_panes(1, 0)  # Freeze header row
        
        QMessageBox.information(self, "Export Complete", 
                              f"Results exported successfully to:\n{file_path}")
    
    def export_to_csv(self, file_path: str):
        """Export results to CSV file"""
        comparison_data = self.prepare_comparison_data()
        df = pd.DataFrame(comparison_data)
        df.to_csv(file_path, index=False)
        
        QMessageBox.information(self, "Export Complete", 
                              f"Results exported successfully to:\n{file_path}")
    
    def export_to_json(self, file_path: str):
        """Export results to JSON file"""
        export_data = {
            'project_id': self.project_controller.current_project_id,
            'export_timestamp': datetime.now().isoformat(),
            'methods': self.results_data,
            'summary': {
                'methods_count': len(self.results_data),
                'best_alternatives': self.get_best_alternatives_summary()
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        QMessageBox.information(self, "Export Complete", 
                              f"Results exported successfully to:\n{file_path}")
    
    def export_to_pdf(self, file_path: str):
        """Export results to PDF report"""
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2196F3'),
            spaceAfter=30
        )
        story.append(Paragraph("MCDM Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Project info
        project_data = self.project_controller.get_project_data()
        if project_data:
            story.append(Paragraph(f"Project: {project_data.get('name', 'Unknown')}", styles['Heading2']))
            story.append(Paragraph(f"Description: {project_data.get('description', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_data = [
            ['Methods Executed', str(len(self.results_data))],
            ['Best Alternative', self.best_alt_card.value_label.text()],
            ['Consensus Level', self.consensus_card.value_label.text()],
            ['Total Execution Time', self.exec_time_card.value_label.text()]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        story.append(summary_table)
        story.append(PageBreak())
        
        # Results comparison
        story.append(Paragraph("Results Comparison", styles['Heading2']))
        comparison_data = self.prepare_comparison_data()
        
        # Create table data
        table_data = [list(comparison_data.keys())]  # Headers
        for i in range(len(comparison_data['Alternative'])):
            row = [comparison_data[key][i] for key in comparison_data.keys()]
            table_data.append(row)
        
        results_table = Table(table_data)
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(results_table)
        
        # Build PDF
        doc.build(story)
        
        QMessageBox.information(self, "Export Complete", 
                              f"PDF report exported successfully to:\n{file_path}")
    
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
    
    def get_best_alternatives_summary(self) -> List[Dict]:
        """Get summary of best alternatives from each method"""
        summary = []
        
        for method_name, result_data in self.results_data.items():
            alts = result_data.get('alternatives', [])
            if alts:
                sorted_alts = sorted(alts, key=lambda x: x.get('ranking', 999))
                if sorted_alts:
                    best_alt = sorted_alts[0]
                    summary.append({
                        'method': method_name,
                        'best_alternative': best_alt.get('name', 'Unknown'),
                        'score': best_alt.get('score', 0)
                    })
        
        return summary
    
    def print_results(self):
        """Print results"""
        try:
            # Create a temporary PDF
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                self.export_to_pdf(tmp_file.name)
                
                # Open the PDF for printing
                import subprocess
                import platform
                
                if platform.system() == 'Windows':
                    subprocess.run(['start', '/print', tmp_file.name], shell=True)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['lpr', tmp_file.name])
                else:  # Linux
                    subprocess.run(['lpr', tmp_file.name])
                    
        except Exception as e:
            logger.error(f"Error printing results: {str(e)}")
            QMessageBox.critical(self, "Print Error", f"Failed to print results: {str(e)}")
    
    def refresh_on_tab_change(self):
        """Refresh when tab is selected"""
        self.load_results()
    
    def update_with_results(self, results_data: Dict[str, Dict]):
        """Update the tab with new results data"""
        self.results_data = results_data
        self.update_display()
        self.status_label.setText(f"Displaying {len(results_data)} results")