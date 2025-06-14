# frontend/views/tabs/method_tab.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                            QGroupBox, QListWidget, QListWidgetItem, QPushButton,
                            QTextEdit, QLabel, QProgressBar, QCheckBox, QSpinBox,
                            QDoubleSpinBox, QComboBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QScrollArea, QFrame,
                            QGridLayout, QFormLayout, QTabWidget, QDialog,
                            QDialogButtonBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPixmap, QIcon, QPalette
from typing import Dict, List, Optional, Any, Tuple
import json
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MethodExecutor(QThread):
    """Thread for executing MCDM methods asynchronously"""
    
    # Signals
    progress_updated = pyqtSignal(str, int)  # method_name, progress
    method_completed = pyqtSignal(str, dict)  # method_name, result
    method_failed = pyqtSignal(str, str)  # method_name, error
    status_updated = pyqtSignal(str, str)  # method_name, status
    all_completed = pyqtSignal(dict)  # all results
    
    def __init__(self, project_controller):
        super().__init__()
        self.project_controller = project_controller
        self.methods_to_execute = []
        self.parameters = {}
        self._is_cancelled = False
    
    def setup(self, methods: List[str], parameters: Dict[str, Dict]):
        """Setup methods and parameters for execution"""
        self.methods_to_execute = methods
        self.parameters = parameters
        self._is_cancelled = False
    
    def cancel(self):
        """Cancel execution"""
        self._is_cancelled = True
    
    def run(self):
        """Execute methods in thread"""
        results = {}
        
        for i, method_name in enumerate(self.methods_to_execute):
            if self._is_cancelled:
                break
                
            try:
                # Update status
                self.status_updated.emit(method_name, "Preparing...")
                self.progress_updated.emit(method_name, 10)
                
                # Simulate preparation
                time.sleep(0.2)
                
                # Execute method
                self.status_updated.emit(method_name, "Executing...")
                self.progress_updated.emit(method_name, 50)
                
                params = self.parameters.get(method_name, {})
                result = self.project_controller.execute_method(method_name, params)
                
                self.progress_updated.emit(method_name, 90)
                
                # Process result
                self.status_updated.emit(method_name, "Processing results...")
                time.sleep(0.1)
                
                self.progress_updated.emit(method_name, 100)
                self.status_updated.emit(method_name, "Completed")
                
                results[method_name] = result
                self.method_completed.emit(method_name, result)
                
            except Exception as e:
                logger.error(f"Error executing {method_name}: {e}")
                self.method_failed.emit(method_name, str(e))
                self.progress_updated.emit(method_name, 0)
                self.status_updated.emit(method_name, f"Failed: {str(e)}")
        
        if not self._is_cancelled:
            self.all_completed.emit(results)


class MethodConfigWidget(QWidget):
    """Widget for configuring method parameters"""
    
    def __init__(self, method_info: Dict, parent=None):
        super().__init__(parent)
        self.method_info = method_info
        self.param_widgets = {}
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Method description
        desc_label = QLabel(self.method_info.get('description', 'No description available'))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 5px;
                color: #333;
            }
        """)
        layout.addWidget(desc_label)
        
        # Parameters section
        params_group = QGroupBox("Method Parameters")
        params_layout = QFormLayout()
        
        default_params = self.method_info.get('default_parameters', {})
        
        for param_name, default_value in default_params.items():
            # Create appropriate widget based on parameter type
            widget = self.create_param_widget(param_name, default_value)
            if widget:
                # Format parameter name for display
                display_name = param_name.replace('_', ' ').title()
                params_layout.addRow(f"{display_name}:", widget)
                self.param_widgets[param_name] = widget
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Add stretch
        layout.addStretch()
    
    def create_param_widget(self, param_name: str, default_value: Any) -> Optional[QWidget]:
        """Create appropriate widget based on parameter type and name"""
        
        # Boolean parameters
        if isinstance(default_value, bool):
            widget = QCheckBox()
            widget.setChecked(default_value)
            return widget
        
        # Numeric parameters with specific ranges
        elif isinstance(default_value, (int, float)):
            if 'threshold' in param_name or 'ratio' in param_name:
                widget = QDoubleSpinBox()
                widget.setDecimals(3)
                
                if 'consistency_ratio' in param_name:
                    widget.setRange(0.0, 1.0)
                    widget.setSingleStep(0.01)
                elif 'threshold' in param_name:
                    widget.setRange(0.0, 1.0)
                    widget.setSingleStep(0.1)
                else:
                    widget.setRange(-999999, 999999)
                    widget.setSingleStep(0.1)
                
                widget.setValue(default_value)
                return widget
            
            elif 'weight' in param_name:
                widget = QDoubleSpinBox()
                widget.setRange(0.0, 1.0)
                widget.setSingleStep(0.1)
                widget.setValue(default_value)
                return widget
                
            else:
                widget = QSpinBox() if isinstance(default_value, int) else QDoubleSpinBox()
                widget.setValue(default_value)
                return widget
        
        # String parameters with predefined options
        elif isinstance(default_value, str):
            if param_name == 'variant':
                widget = QComboBox()
                if 'ELECTRE' in self.method_info.get('name', ''):
                    widget.addItems(['I', 'III'])
                elif 'PROMETHEE' in self.method_info.get('name', ''):
                    widget.addItems(['I', 'II'])
                widget.setCurrentText(default_value)
                return widget
                
            elif param_name == 'normalization_method':
                widget = QComboBox()
                widget.addItems(['minmax', 'vector', 'sum', 'max'])
                widget.setCurrentText(default_value)
                return widget
                
            elif param_name == 'distance_metric':
                widget = QComboBox()
                widget.addItems(['euclidean', 'manhattan', 'chebyshev'])
                widget.setCurrentText(default_value)
                return widget
                
            elif param_name == 'weight_calculation_method':
                widget = QComboBox()
                widget.addItems(['eigenvector', 'approximate'])
                widget.setCurrentText(default_value)
                return widget
                
            elif param_name == 'default_preference_function':
                widget = QComboBox()
                widget.addItems(['usual', 'u-shape', 'v-shape', 'level', 'v-shape-indifference', 'gaussian'])
                widget.setCurrentText(default_value)
                return widget
                
            elif param_name == 'scoring_method':
                widget = QComboBox()
                widget.addItems(['net_flow', 'pure_dominance', 'mixed'])
                widget.setCurrentText(default_value)
                return widget
                
            else:
                # Generic string parameter
                widget = QComboBox()
                widget.setEditable(True)
                widget.setEditText(default_value)
                return widget
        
        # Dictionary or None parameters - skip for now
        elif default_value is None or isinstance(default_value, dict):
            return None
        
        return None
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values"""
        params = {}
        
        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, QCheckBox):
                params[param_name] = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                params[param_name] = widget.value()
            elif isinstance(widget, QComboBox):
                params[param_name] = widget.currentText()
        
        return params


class MethodCard(QFrame):
    """Professional card widget for each MCDM method"""
    
    # Signals
    execute_requested = pyqtSignal(str)
    configure_requested = pyqtSignal(str)
    info_requested = pyqtSignal(str)
    
    def __init__(self, method_info: Dict, parent=None):
        super().__init__(parent)
        self.method_info = method_info
        self.method_name = method_info['name']
        self.is_selected = False
        self.init_ui()
    
    def init_ui(self):
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            MethodCard {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                padding: 10px;
            }
            MethodCard:hover {
                border-color: #2196F3;
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header with checkbox and title
        header_layout = QHBoxLayout()
        
        self.select_cb = QCheckBox()
        self.select_cb.stateChanged.connect(self.on_selection_changed)
        header_layout.addWidget(self.select_cb)
        
        # Method icon (different for each method)
        icon_label = QLabel(self.get_method_icon())
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        # Method name
        name_label = QLabel(self.method_name)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: bold;
                padding: 2px 8px;
                background-color: #e8f5e9;
                border-radius: 3px;
            }
        """)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Full name
        full_name = QLabel(self.method_info.get('full_name', ''))
        full_name.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(full_name)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.configure_btn = QPushButton("⚙️ Configure")
        self.configure_btn.clicked.connect(lambda: self.configure_requested.emit(self.method_name))
        button_layout.addWidget(self.configure_btn)
        
        self.execute_btn = QPushButton("▶️ Execute")
        self.execute_btn.clicked.connect(lambda: self.execute_requested.emit(self.method_name))
        self.execute_btn.setStyleSheet("""
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
        button_layout.addWidget(self.execute_btn)
        
        self.info_btn = QPushButton("ℹ️")
        self.info_btn.setMaximumWidth(30)
        self.info_btn.clicked.connect(lambda: self.info_requested.emit(self.method_name))
        button_layout.addWidget(self.info_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def get_method_icon(self) -> str:
        """Get icon for each method"""
        icons = {
            'TOPSIS': '📊',
            'AHP': '🔺',
            'ELECTRE': '⚡',
            'PROMETHEE': '🏆'
        }
        return icons.get(self.method_name, '📈')
    
    def on_selection_changed(self, state):
        """Handle selection change"""
        self.is_selected = state == Qt.Checked
        if self.is_selected:
            self.setStyleSheet("""
                MethodCard {
                    border: 2px solid #2196F3;
                    border-radius: 8px;
                    background-color: #e3f2fd;
                    padding: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                MethodCard {
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    background-color: white;
                    padding: 10px;
                }
                MethodCard:hover {
                    border-color: #2196F3;
                    background-color: #f8f9fa;
                }
            """)
    
    def set_progress(self, value: int):
        """Set progress value"""
        self.progress_bar.setValue(value)
        if value > 0 and value < 100:
            self.progress_bar.show()
        elif value >= 100:
            QTimer.singleShot(1000, self.progress_bar.hide)
    
    def set_status(self, status: str):
        """Set status with appropriate styling"""
        self.status_label.setText(status)
        
        # Style based on status
        if status == "Executing...":
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #ff9800;
                    font-weight: bold;
                    padding: 2px 8px;
                    background-color: #fff3e0;
                    border-radius: 3px;
                }
            """)
        elif status == "Completed":
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-weight: bold;
                    padding: 2px 8px;
                    background-color: #e8f5e9;
                    border-radius: 3px;
                }
            """)
        elif "Failed" in status:
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #f44336;
                    font-weight: bold;
                    padding: 2px 8px;
                    background-color: #ffebee;
                    border-radius: 3px;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #2196F3;
                    font-weight: bold;
                    padding: 2px 8px;
                    background-color: #e3f2fd;
                    border-radius: 3px;
                }
            """)
    
    def set_enabled(self, enabled: bool):
        """Enable/disable interaction"""
        self.select_cb.setEnabled(enabled)
        self.configure_btn.setEnabled(enabled)
        self.execute_btn.setEnabled(enabled)


class MethodTab(QWidget):
    """Professional Method Selection and Execution Tab"""
    
    # Signals
    methods_executed = pyqtSignal(dict)
    
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.method_cards = {}
        self.method_configs = {}
        self.method_results = {}
        self.executor = MethodExecutor(project_controller)
        
        self.init_ui()
        self.connect_signals()
        self.load_methods()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header
        self.create_header(main_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Method cards
        self.create_methods_panel(splitter)
        
        # Right panel: Configuration and results
        self.create_right_panel(splitter)
        
        splitter.setSizes([500, 400])
        main_layout.addWidget(splitter)
        
        # Bottom controls
        self.create_bottom_controls(main_layout)
    
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
        title = QLabel("MCDM Method Selection & Execution")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Status info
        self.matrix_status = QLabel("⚠️ No matrix loaded")
        self.matrix_status.setStyleSheet("color: #ff9800; font-weight: bold;")
        header_layout.addWidget(self.matrix_status)
        
        parent_layout.addWidget(header_frame)
    
    def create_methods_panel(self, parent):
        """Create panel with method cards"""
        methods_widget = QWidget()
        methods_layout = QVBoxLayout(methods_widget)
        
        # Title
        title = QLabel("Available Methods")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        methods_layout.addWidget(title)
        
        # Scroll area for method cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.methods_container = QWidget()
        self.methods_container_layout = QVBoxLayout(self.methods_container)
        
        scroll_area.setWidget(self.methods_container)
        methods_layout.addWidget(scroll_area)
        
        parent.addWidget(methods_widget)
    
    def create_right_panel(self, parent):
        """Create right panel with tabs"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.right_tabs = QTabWidget()
        
        # Configuration tab
        self.config_scroll = QScrollArea()
        self.config_scroll.setWidgetResizable(True)
        self.config_widget = QWidget()
        self.config_layout = QVBoxLayout(self.config_widget)
        
        # Instructions
        instructions = QLabel("Select a method and click Configure to set parameters")
        instructions.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                padding: 10px;
                border-radius: 5px;
                color: #1976D2;
            }
        """)
        self.config_layout.addWidget(instructions)
        self.config_layout.addStretch()
        
        self.config_scroll.setWidget(self.config_widget)
        self.right_tabs.addTab(self.config_scroll, "Configuration")
        
        # Quick Results tab
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Method", "Best Alternative", "Score", "Execution Time"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_layout.addWidget(self.results_table)
        
        self.right_tabs.addTab(self.results_widget, "Quick Results")
        
        # Comparison tab
        self.comparison_widget = QWidget()
        self.comparison_layout = QVBoxLayout(self.comparison_widget)
        
        self.comparison_table = QTableWidget()
        self.comparison_layout.addWidget(self.comparison_table)
        
        self.right_tabs.addTab(self.comparison_widget, "Method Comparison")
        
        right_layout.addWidget(self.right_tabs)
        parent.addWidget(right_widget)
    
    def create_bottom_controls(self, parent_layout):
        """Create bottom control buttons"""
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        controls_layout = QHBoxLayout(controls_frame)
        
        # Select/Deselect all
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.stateChanged.connect(self.on_select_all_changed)
        controls_layout.addWidget(self.select_all_cb)
        
        controls_layout.addStretch()
        
        # Action buttons
        self.validate_btn = QPushButton("🔍 Validate Matrix")
        self.validate_btn.clicked.connect(self.validate_matrix)
        controls_layout.addWidget(self.validate_btn)
        
        self.execute_selected_btn = QPushButton("▶️ Execute Selected")
        self.execute_selected_btn.clicked.connect(self.execute_selected_methods)
        self.execute_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        controls_layout.addWidget(self.execute_selected_btn)
        
        self.execute_all_btn = QPushButton("⚡ Execute All")
        self.execute_all_btn.clicked.connect(self.execute_all_methods)
        self.execute_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        controls_layout.addWidget(self.execute_all_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_execution)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover:enabled {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        controls_layout.addWidget(self.stop_btn)
        
        parent_layout.addWidget(controls_frame)
    
    def connect_signals(self):
        """Connect executor signals"""
        self.executor.progress_updated.connect(self.on_progress_updated)
        self.executor.method_completed.connect(self.on_method_completed)
        self.executor.method_failed.connect(self.on_method_failed)
        self.executor.status_updated.connect(self.on_status_updated)
        self.executor.all_completed.connect(self.on_all_completed)
    
    def load_methods(self):
        """Load available MCDM methods"""
        try:
            methods = self.project_controller.get_available_methods()
            
            for method_info in methods:
                self.create_method_card(method_info)
                
        except Exception as e:
            logger.error(f"Error loading methods: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load methods: {str(e)}")
    
    def create_method_card(self, method_info: Dict):
        """Create a method card widget"""
        card = MethodCard(method_info)
        card.execute_requested.connect(self.execute_single_method)
        card.configure_requested.connect(self.configure_method)
        card.info_requested.connect(self.show_method_info)
        
        self.method_cards[method_info['name']] = card
        self.methods_container_layout.addWidget(card)
    
    def check_matrix_status(self) -> bool:
        """Check if matrix is ready for methods"""
        try:
            # Check if project is loaded
            if not self.project_controller.current_project_id:
                self.matrix_status.setText("⚠️ No project loaded")
                self.matrix_status.setStyleSheet("color: #ff9800; font-weight: bold;")
                return False
            
            # Check if matrix exists
            matrix_data = self.project_controller.get_decision_matrix()
            if not matrix_data or not matrix_data.get('matrix_data'):
                self.matrix_status.setText("⚠️ No decision matrix")
                self.matrix_status.setStyleSheet("color: #ff9800; font-weight: bold;")
                return False
            
            # Check completeness
            total_cells = len(matrix_data.get('alternatives', [])) * len(matrix_data.get('criteria', []))
            filled_cells = sum(1 for v in matrix_data.get('matrix_data', {}).values() if v.strip())
            
            if total_cells == 0:
                self.matrix_status.setText("⚠️ Empty matrix")
                self.matrix_status.setStyleSheet("color: #ff9800; font-weight: bold;")
                return False
            
            completeness = (filled_cells / total_cells) * 100
            
            if completeness < 100:
                self.matrix_status.setText(f"⚠️ Matrix {completeness:.0f}% complete")
                self.matrix_status.setStyleSheet("color: #ff9800; font-weight: bold;")
                
                reply = QMessageBox.question(self, "Incomplete Matrix",
                                           f"Matrix is only {completeness:.0f}% complete. Continue anyway?",
                                           QMessageBox.Yes | QMessageBox.No)
                return reply == QMessageBox.Yes
            else:
                self.matrix_status.setText("✅ Matrix ready")
                self.matrix_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
                return True
                
        except Exception as e:
            logger.error(f"Error checking matrix status: {e}")
            self.matrix_status.setText("❌ Error checking matrix")
            self.matrix_status.setStyleSheet("color: #f44336; font-weight: bold;")
            return False
    
    def validate_matrix(self):
        """Validate matrix for MCDM execution"""
        if self.check_matrix_status():
            QMessageBox.information(self, "Validation Passed", 
                                  "Matrix is valid and ready for MCDM methods!")
        else:
            QMessageBox.warning(self, "Validation Failed",
                              "Please complete the decision matrix before executing methods.")
    
    def configure_method(self, method_name: str):
        """Configure method parameters"""
        # Clear previous configuration
        while self.config_layout.count() > 1:  # Keep instructions
            child = self.config_layout.takeAt(1)
            if child.widget():
                child.widget().deleteLater()
        
        # Get method info
        method_info = next((card.method_info for card in self.method_cards.values() 
                          if card.method_name == method_name), None)
        
        if not method_info:
            return
        
        # Create configuration widget
        config_widget = MethodConfigWidget(method_info)
        self.method_configs[method_name] = config_widget
        
        # Add to layout
        self.config_layout.insertWidget(1, config_widget)
        
        # Switch to configuration tab
        self.right_tabs.setCurrentIndex(0)
    
    def show_method_info(self, method_name: str):
        """Show detailed method information"""
        method_info = next((card.method_info for card in self.method_cards.values() 
                          if card.method_name == method_name), None)
        
        if not method_info:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{method_name} - Information")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Method details
        info_text = f"""
        <h2>{method_info.get('full_name', method_name)}</h2>
        
        <h3>Description:</h3>
        <p>{method_info.get('description', 'No description available')}</p>
        
        <h3>Default Parameters:</h3>
        <ul>
        """
        
        for param, value in method_info.get('default_parameters', {}).items():
            info_text += f"<li><b>{param}:</b> {value}</li>"
        
        info_text += "</ul>"
        
        text_widget = QTextEdit()
        text_widget.setHtml(info_text)
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def execute_single_method(self, method_name: str):
        """Execute a single method"""
        if not self.check_matrix_status():
            return
        
        # Get parameters
        params = {}
        if method_name in self.method_configs:
            params = self.method_configs[method_name].get_parameters()
        
        # Setup and run executor
        self.set_execution_state(True)
        self.executor.setup([method_name], {method_name: params})
        self.executor.start()
    
    def execute_selected_methods(self):
        """Execute all selected methods"""
        if not self.check_matrix_status():
            return
        
        # Get selected methods
        selected_methods = []
        parameters = {}
        
        for method_name, card in self.method_cards.items():
            if card.is_selected:
                selected_methods.append(method_name)
                
                # Get parameters if configured
                if method_name in self.method_configs:
                    parameters[method_name] = self.method_configs[method_name].get_parameters()
        
        if not selected_methods:
            QMessageBox.warning(self, "No Selection", "Please select at least one method to execute.")
            return
        
        # Confirm execution
        reply = QMessageBox.question(self, "Confirm Execution",
                                   f"Execute {len(selected_methods)} selected method(s)?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.set_execution_state(True)
            self.executor.setup(selected_methods, parameters)
            self.executor.start()
    
    def execute_all_methods(self):
        """Execute all available methods"""
        if not self.check_matrix_status():
            return
        
        # Get all methods
        all_methods = list(self.method_cards.keys())
        parameters = {}
        
        for method_name in all_methods:
            if method_name in self.method_configs:
                parameters[method_name] = self.method_configs[method_name].get_parameters()
        
        # Confirm execution
        reply = QMessageBox.question(self, "Confirm Execution",
                                   f"Execute all {len(all_methods)} methods?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.set_execution_state(True)
            self.executor.setup(all_methods, parameters)
            self.executor.start()
    
    def stop_execution(self):
        """Stop current execution"""
        self.executor.cancel()
        self.set_execution_state(False)
        
        # Reset all progress bars
        for card in self.method_cards.values():
            card.set_progress(0)
            card.set_status("Cancelled")
    
    def set_execution_state(self, is_executing: bool):
        """Set UI state during execution"""
        # Enable/disable cards
        for card in self.method_cards.values():
            card.set_enabled(not is_executing)
        
        # Enable/disable buttons
        self.select_all_cb.setEnabled(not is_executing)
        self.validate_btn.setEnabled(not is_executing)
        self.execute_selected_btn.setEnabled(not is_executing)
        self.execute_all_btn.setEnabled(not is_executing)
        self.stop_btn.setEnabled(is_executing)
    
    def on_progress_updated(self, method_name: str, progress: int):
        """Handle progress update"""
        if method_name in self.method_cards:
            self.method_cards[method_name].set_progress(progress)
    
    def on_status_updated(self, method_name: str, status: str):
        """Handle status update"""
        if method_name in self.method_cards:
            self.method_cards[method_name].set_status(status)
    
    def on_method_completed(self, method_name: str, result: Dict):
        """Handle method completion"""
        self.method_results[method_name] = result
        
        # Add to quick results table
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        self.results_table.setItem(row, 0, QTableWidgetItem(method_name))
        
        best_alt = result.get('best_alternative', {})
        self.results_table.setItem(row, 1, QTableWidgetItem(best_alt.get('name', 'N/A')))
        self.results_table.setItem(row, 2, QTableWidgetItem(f"{best_alt.get('score', 0):.4f}"))
        
        exec_time = result.get('execution_time', 0)
        self.results_table.setItem(row, 3, QTableWidgetItem(f"{exec_time:.3f}s"))
        
        # Update comparison if multiple results
        if len(self.method_results) > 1:
            self.update_comparison()
    
    def on_method_failed(self, method_name: str, error: str):
        """Handle method failure"""
        QMessageBox.critical(self, f"{method_name} Failed", f"Error: {error}")
    
    def on_all_completed(self, results: Dict):
        """Handle all methods completion"""
        self.set_execution_state(False)
        
        # Switch to results tab
        self.right_tabs.setCurrentIndex(1)
        
        # Show summary
        QMessageBox.information(self, "Execution Complete",
                              f"Successfully executed {len(results)} method(s)!")
        
        # Emit signal for other tabs
        self.methods_executed.emit(results)
    
    def on_select_all_changed(self, state):
        """Handle select all checkbox"""
        is_checked = state == Qt.Checked
        
        for card in self.method_cards.values():
            card.select_cb.setChecked(is_checked)
    
    def update_comparison(self):
        """Update method comparison table"""
        if len(self.method_results) < 2:
            return
        
        # Get all alternatives from first result
        first_result = next(iter(self.method_results.values()))
        alternatives = first_result.get('alternatives', [])
        
        # Setup table
        self.comparison_table.clear()
        self.comparison_table.setRowCount(len(alternatives))
        self.comparison_table.setColumnCount(len(self.method_results) + 1)
        
        # Headers
        headers = ['Alternative'] + list(self.method_results.keys())
        self.comparison_table.setHorizontalHeaderLabels(headers)
        
        # Fill data
        for i, alt in enumerate(alternatives):
            # Alternative name
            self.comparison_table.setItem(i, 0, QTableWidgetItem(alt['name']))
            
            # Rankings from each method
            for j, (method_name, result) in enumerate(self.method_results.items()):
                ranking = alt.get('ranking', 'N/A')
                item = QTableWidgetItem(str(ranking))
                
                # Color code based on ranking
                if isinstance(ranking, int):
                    if ranking == 1:
                        item.setBackground(QColor(200, 255, 200))  # Green
                    elif ranking == 2:
                        item.setBackground(QColor(255, 255, 200))  # Yellow
                    elif ranking == 3:
                        item.setBackground(QColor(255, 220, 200))  # Orange
                
                self.comparison_table.setItem(i, j + 1, item)
        
        self.comparison_table.resizeColumnsToContents()
    
    def refresh_on_tab_change(self):
        """Refresh status when tab is selected"""
        self.check_matrix_status()
        
        # Clear results if project changed
        if not self.project_controller.current_project_id:
            self.results_table.setRowCount(0)
            self.comparison_table.clear()
            self.method_results.clear()