from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                            QGroupBox, QTableWidget, QTableWidgetItem, QPushButton,
                            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QLabel,
                            QProgressBar, QTextEdit, QMessageBox, QHeaderView,
                            QFormLayout, QToolTip, QCheckBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QColor, QFont
import numpy as np


class MatrixTab(QWidget):
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.matrix_data = {}  # Store matrix values
        self.criteria_config = {}  # Store scale configuration per criterion
        self.normalized_data = {}  
        self.is_normalized_view = False  
        self.normalization_method = 'minmax'  
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
        self.is_programmatic_update = False
        
        self.init_ui()
        self.load_matrix_data()
    
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Configuration
        self.create_config_panel(splitter)
        
        # Right panel: Matrix and Analysis
        self.create_matrix_panel(splitter)
        
        # Set splitter proportions
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
    
    def create_config_panel(self, parent):
        """Create the configuration panel for criteria scales"""
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        # Title
        title_label = QLabel("Criteria Configuration")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        config_layout.addWidget(title_label)
        
        # Scroll area for criteria configuration
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.config_container = QWidget()
        self.config_container_layout = QVBoxLayout(self.config_container)
        
        scroll_area.setWidget(self.config_container)
        config_layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh from Project")
        self.refresh_btn.clicked.connect(self.refresh_from_project)
        button_layout.addWidget(self.refresh_btn)
        
        self.apply_config_btn = QPushButton("Apply Configuration")
        self.apply_config_btn.clicked.connect(self.apply_configuration)
        self.apply_config_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        button_layout.addWidget(self.apply_config_btn)
        
        self.save_matrix_btn = QPushButton("Save Matrix")
        self.save_matrix_btn.clicked.connect(self.save_matrix)
        self.save_matrix_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(self.save_matrix_btn)
        
        button_layout.addStretch()
        config_layout.addLayout(button_layout)
        
        parent.addWidget(config_widget)
    
    def create_matrix_panel(self, parent):
        """Create the matrix and analysis panel"""
        matrix_widget = QWidget()
        matrix_layout = QVBoxLayout(matrix_widget)
        
        # Status bar
        self.create_status_bar(matrix_layout)
        
        # Matrix table
        self.create_matrix_table(matrix_layout)
        
        # Analysis panel
        self.create_analysis_panel(matrix_layout)
        
        parent.addWidget(matrix_widget)
    
    def create_status_bar(self, parent_layout):
        """Create status bar with project info and completeness"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box)
        status_layout = QHBoxLayout(status_frame)
        
        # Project info
        self.project_label = QLabel("No project loaded")
        self.project_label.setFont(QFont("Arial", 10, QFont.Bold))
        status_layout.addWidget(self.project_label)
        
        status_layout.addStretch()
        
        # Completeness progress
        self.completeness_label = QLabel("Completeness:")
        status_layout.addWidget(self.completeness_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        status_layout.addWidget(self.progress_bar)
        
        self.completeness_percent = QLabel("0%")
        status_layout.addWidget(self.completeness_percent)
        
        parent_layout.addWidget(status_frame)
    
    def create_matrix_table(self, parent_layout):
        """Create the main decision matrix table"""
        matrix_group = QGroupBox("Decision Matrix")
        matrix_layout = QVBoxLayout(matrix_group)
        
        # Table controls - EXPANDIDO
        controls_layout = QHBoxLayout()
        
        # Normalization controls - NUEVO
        norm_label = QLabel("Normalization:")
        controls_layout.addWidget(norm_label)
        
        self.normalization_combo = QComboBox()
        self.normalization_combo.addItems([
            "Min-Max (0-1)",
            "Vector (Euclidean)", 
            "Sum (Proportional)",
            "Max (0-1 by max)"
        ])
        self.normalization_combo.currentTextChanged.connect(self.on_normalization_method_changed)
        controls_layout.addWidget(self.normalization_combo)
        
        self.show_normalized_cb = QCheckBox("Show Normalized View")
        self.show_normalized_cb.toggled.connect(self.toggle_normalized_view)
        controls_layout.addWidget(self.show_normalized_cb)
        
        # Info button for normalization help
        self.norm_help_btn = QPushButton("?")
        self.norm_help_btn.setMaximumWidth(25)
        self.norm_help_btn.clicked.connect(self.show_normalization_help)
        self.norm_help_btn.setToolTip("Click for normalization methods explanation")
        controls_layout.addWidget(self.norm_help_btn)
        
        controls_layout.addStretch()
        
        self.clear_all_btn = QPushButton("Clear All Values")
        self.clear_all_btn.clicked.connect(self.clear_all_values)
        controls_layout.addWidget(self.clear_all_btn)
        
        matrix_layout.addLayout(controls_layout)
        
        # Main matrix table
        self.matrix_table = QTableWidget()
        self.matrix_table.cellChanged.connect(self.on_cell_changed)
        matrix_layout.addWidget(self.matrix_table)
        
        parent_layout.addWidget(matrix_group)
    
    def on_normalization_method_changed(self, method_text):
        """Handle normalization method change"""
        method_map = {
            "Min-Max (0-1)": "minmax",
            "Vector (Euclidean)": "vector", 
            "Sum (Proportional)": "sum",
            "Max (0-1 by max)": "max"
        }
        
        old_method = self.normalization_method
        self.normalization_method = method_map.get(method_text, "minmax")
        
        # Only recalculate if method actually changed and we're in normalized view
        if old_method != self.normalization_method and self.is_normalized_view:
            self.calculate_normalized_data()
            self.update_matrix_display()
            self.update_statistics()
            
            # Show brief notification of method change
            self.project_label.setText(
                self.project_label.text().replace(" - NORMALIZED VIEW", 
                                                f" - NORMALIZED VIEW ({self.normalization_method.upper()})")
            )

    def show_normalization_help(self):
        """Show help dialog for normalization methods"""
        help_text = """
        <h3>Normalization Methods:</h3>
        
        <b>Min-Max (0-1):</b><br>
        • Scales values to 0-1 range<br>
        • Formula: (x - min) / (max - min)<br>
        • Best for: Mixed scales, easy interpretation<br><br>
        
        <b>Vector (Euclidean):</b><br>
        • Normalizes by vector length<br>
        • Formula: x / √(Σx²)<br>
        • Best for: TOPSIS method, geometric relationships<br><br>
        
        <b>Sum (Proportional):</b><br>
        • Values as proportion of total<br>
        • Formula: x / Σx<br>
        • Best for: Percentages, relative importance<br><br>
        
        <b>Max (0-1 by max):</b><br>
        • Divides by maximum value<br>
        • Formula: x / max(x)<br>
        • Best for: Preserving ratios, simple scaling<br>
        """
        
        QMessageBox.information(self, "Normalization Methods", help_text)

    def create_analysis_panel(self, parent_layout):
        """Create analysis panel with statistics"""
        analysis_group = QGroupBox("Real-time Analysis")
        analysis_layout = QHBoxLayout(analysis_group)
        
        # Statistics text
        self.statistics_text = QTextEdit()
        self.statistics_text.setMaximumHeight(120)
        self.statistics_text.setReadOnly(True)
        analysis_layout.addWidget(self.statistics_text)
        
        parent_layout.addWidget(analysis_group)
    
    
    def load_matrix_data(self):
        """Load matrix data from current project"""
        if not self.project_controller.current_project_id:
            self.project_label.setText("No project loaded - Please create or open a project first")
            self.project_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Clear matrix when no project
            self.matrix_table.setRowCount(0)
            self.matrix_table.setColumnCount(0)
            self.clear_config_panel()
            self.matrix_data.clear()
            self.update_completeness()
            return
        
        try:
            project = self.project_controller.get_current_project()
            if project:
                project_name = project.get('name', 'Unknown')
                self.project_label.setText(f"Project: {project_name}")
                self.project_label.setStyleSheet("color: green; font-weight: bold;")
                
                # Load saved matrix data
                self.load_saved_matrix_data()
                
                # Refresh from project
                self.refresh_from_project()
            else:
                self.project_label.setText("Failed to load project data")
                self.project_label.setStyleSheet("color: red; font-weight: bold;")
                
        except Exception as e:
            print(f"Error in load_matrix_data: {e}")
            self.project_label.setText("Error loading project data")
            self.project_label.setStyleSheet("color: red; font-weight: bold;")
    
    def load_saved_matrix_data(self):
        """Load saved matrix data and configuration"""
        try:
            saved_data = self.project_controller.get_decision_matrix()
            
            if saved_data:
                # Load matrix values
                self.matrix_data = saved_data.get('matrix_data', {})
                
                # Load criteria configuration
                saved_config = saved_data.get('criteria_config', {})
                
                # Apply saved configuration to UI
                for crit_id, config_data in saved_config.items():
                    if crit_id in self.criteria_config:
                        config = self.criteria_config[crit_id]
                        config['scale_type_combo'].setCurrentText(config_data.get('scale_type', 'Numeric (Continuous)'))
                        config['min_spin'].setValue(config_data.get('min_value', 0))
                        config['max_spin'].setValue(config_data.get('max_value', 100))
                        config['unit_edit'].setText(config_data.get('unit', ''))
                        
        except Exception as e:
            print(f"Error loading saved matrix data: {e}")

    def refresh_from_project(self):
        """Refresh criteria configuration from project data"""
        print("DEBUG: refresh_from_project called")
        
        if not self.project_controller.current_project_id:
            print("DEBUG: No project ID, showing warning")
            # No mostrar warning si se llama automáticamente
            return
        
        try:
            # Get alternatives and criteria
            alternatives = self.project_controller.get_alternatives()
            criteria = self.project_controller.get_criteria()
            
            print(f"DEBUG: Got {len(alternatives)} alternatives, {len(criteria)} criteria")
            
            if not alternatives and not criteria:
                # Proyecto vacío recién creado
                self.project_label.setText(f"Project loaded - Add alternatives and criteria in Project Manager first")
                self.project_label.setStyleSheet("color: orange; font-weight: bold;")
                self.clear_config_panel()
                self.matrix_table.setRowCount(0)
                self.matrix_table.setColumnCount(0)
                return
                
            if not alternatives:
                self.project_label.setText("No alternatives defined - Add alternatives in Project Manager")
                self.project_label.setStyleSheet("color: orange; font-weight: bold;")
                return
                    
            if not criteria:
                self.project_label.setText("No criteria defined - Add criteria in Project Manager")
                self.project_label.setStyleSheet("color: orange; font-weight: bold;")
                return
            
            # Todo bien, proceder normalmente
            self.project_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Clear existing configuration
            self.clear_config_panel()
            
            # Create configuration for each criterion
            for crit in criteria:
                self.create_criterion_config(crit)
            
            # Initialize matrix table structure
            self.initialize_matrix_table(alternatives, criteria)
            
        except Exception as e:
            print(f"DEBUG: Error in refresh_from_project: {e}")
            self.project_label.setText("Error refreshing from project")
            self.project_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.critical(self, "Error", f"Failed to refresh from project: {str(e)}")
    
    def clear_config_panel(self):
        """Clear the configuration panel"""
        while self.config_container_layout.count():
            child = self.config_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.criteria_config.clear()
    
    def create_criterion_config(self, criterion):
        """Create configuration widget for a single criterion"""
        config_frame = QFrame()
        config_frame.setFrameStyle(QFrame.Box)
        config_layout = QFormLayout(config_frame)
        
        crit_id = criterion['id']
        crit_name = criterion['name']
        crit_type = criterion.get('optimization_type', 'maximize')
        
        # Title
        title_label = QLabel(f"{crit_name} ({crit_id})")
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet(f"color: {'green' if crit_type == 'maximize' else 'red'};")
        config_layout.addRow(title_label)
        
        # Scale type
        scale_type_combo = QComboBox()
        scale_type_combo.addItems([
            "Numeric (Continuous)",
            "Likert 1-5",
            "Likert 1-7", 
            "Likert 1-10",
            "Percentage (0-100%)",
            "Custom Range"
        ])
        config_layout.addRow("Scale Type:", scale_type_combo)
        
        # Min/Max values
        min_spin = QDoubleSpinBox()
        min_spin.setRange(-999999, 999999)
        min_spin.setValue(0)
        config_layout.addRow("Min Value:", min_spin)
        
        max_spin = QDoubleSpinBox()
        max_spin.setRange(-999999, 999999)
        max_spin.setValue(100)
        config_layout.addRow("Max Value:", max_spin)
        
        # Unit
        unit_edit = QLineEdit(criterion.get('unit', ''))
        config_layout.addRow("Unit:", unit_edit)
        
        # Store configuration
        self.criteria_config[crit_id] = {
            'criterion': criterion,
            'scale_type_combo': scale_type_combo,
            'min_spin': min_spin,
            'max_spin': max_spin,
            'unit_edit': unit_edit
        }
        
        # Connect signals
        scale_type_combo.currentTextChanged.connect(self.on_scale_type_changed)
        
        self.config_container_layout.addWidget(config_frame)
    
    def on_scale_type_changed(self):
        """Handle scale type change"""
        sender = self.sender()
        
        # Find which criterion this belongs to
        for crit_id, config in self.criteria_config.items():
            if config['scale_type_combo'] == sender:
                scale_type = sender.currentText()
                min_spin = config['min_spin']
                max_spin = config['max_spin']
                
                # Update min/max based on scale type
                if "Likert 1-5" in scale_type:
                    min_spin.setValue(1)
                    max_spin.setValue(5)
                elif "Likert 1-7" in scale_type:
                    min_spin.setValue(1)
                    max_spin.setValue(7)
                elif "Likert 1-10" in scale_type:
                    min_spin.setValue(1)
                    max_spin.setValue(10)
                elif "Percentage" in scale_type:
                    min_spin.setValue(0)
                    max_spin.setValue(100)
                break
    
    def apply_configuration(self):
        """Apply the current configuration to the matrix"""
        if not self.criteria_config:
            QMessageBox.warning(self, "Warning", "No criteria configuration available")
            return
        
        try:
            # Rebuild matrix table with new configuration
            alternatives = self.project_controller.get_alternatives()
            criteria = self.project_controller.get_criteria()
            
            if alternatives and criteria:
                self.initialize_matrix_table(alternatives, criteria)
                QMessageBox.information(self, "Success", "Configuration applied successfully")
            else:
                QMessageBox.warning(self, "Warning", "No alternatives or criteria available")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply configuration: {str(e)}")
    
    def initialize_matrix_table(self, alternatives, criteria):
        """Initialize the matrix table with proper structure"""
        # Set flag to prevent triggering events during initialization
        self.is_programmatic_update = True
        
        try:
            # Set table dimensions
            self.matrix_table.setRowCount(len(alternatives))
            self.matrix_table.setColumnCount(len(criteria))
            
            # Set headers
            alt_headers = [f"{alt['name']} ({alt['id']})" for alt in alternatives]
            self.matrix_table.setVerticalHeaderLabels(alt_headers)
            
            crit_headers = []
            for crit in criteria:
                crit_id = crit['id']
                crit_name = crit['name']
                crit_type = crit.get('optimization_type', 'maximize')
                weight = crit.get('weight', 1.0)
                
                # Get scale info if configured
                scale_info = ""
                if crit_id in self.criteria_config:
                    config = self.criteria_config[crit_id]
                    min_val = config['min_spin'].value()
                    max_val = config['max_spin'].value()
                    unit = config['unit_edit'].text()
                    scale_info = f" [{min_val}-{max_val}]"
                    if unit:
                        scale_info += f" {unit}"
                
                # Color-code header based on criterion type
                type_indicator = "↑" if crit_type == 'maximize' else "↓"
                header_text = f"{crit_name} {type_indicator}\nWeight: {weight}{scale_info}"
                crit_headers.append(header_text)
            
            self.matrix_table.setHorizontalHeaderLabels(crit_headers)
            
            # Configure table properties
            self.matrix_table.resizeColumnsToContents()
            
            # Initialize cells with existing data or default values
            for i in range(len(alternatives)):
                for j in range(len(criteria)):
                    alt_id = alternatives[i]['id']
                    crit_id = criteria[j]['id']
                    
                    # Check if we have existing data
                    existing_value = self.matrix_data.get(f"{alt_id}_{crit_id}", "")
                    
                    item = QTableWidgetItem(str(existing_value))
                    item.setData(Qt.UserRole, {'alt_id': alt_id, 'crit_id': crit_id})
                    
                    # Style based on view mode
                    if self.is_normalized_view:
                        item.setData(Qt.UserRole + 1, "normalized")
                    else:
                        item.setData(Qt.UserRole + 1, "original")
                    
                    self.matrix_table.setItem(i, j, item)
        
        finally:
            # Always restore flag
            self.is_programmatic_update = False
        
        # Update colors and statistics (these don't trigger cellChanged)
        self.update_matrix_colors()
        self.update_statistics()
        self.update_completeness()
    
    def on_cell_changed(self, row, col):
        """Handle cell value changes with proper view handling"""
        # Ignorar cambios programáticos
        if self.is_programmatic_update:
            return
        
        # Si estamos en vista normalizada, no permitir edición
        if self.is_normalized_view:
            QMessageBox.warning(self, "Warning", 
                            "Cannot edit values in normalized view.\nSwitch to original view to edit values.")
            
            # Restaurar el valor que tenía
            self.restore_cell_value(row, col)
            return
        
        # Procesar cambio normal (solo en vista original)
        item = self.matrix_table.item(row, col)
        if not item:
            return
        
        value = item.text().strip()
        data = item.data(Qt.UserRole)
        
        if not data:
            return
        
        alt_id = data['alt_id']
        crit_id = data['crit_id']
        
        # Validate the value
        if self.validate_cell_value(value, crit_id):
            # Store the value in original data
            old_value = self.matrix_data.get(f"{alt_id}_{crit_id}", "")
            self.matrix_data[f"{alt_id}_{crit_id}"] = value
            
            # Update colors and statistics
            self.update_matrix_colors()
            self.update_statistics()
            self.update_completeness()
            
            # Auto-save individual cell change
            if value != old_value:
                self.save_cell_change(alt_id, crit_id, value)
                
        else:
            # Invalid value - revert
            QMessageBox.warning(self, "Invalid Value", 
                            f"Invalid value for criterion {crit_id}")
            item.setText(self.matrix_data.get(f"{alt_id}_{crit_id}", ""))
    
    def restore_cell_value(self, row, col):
        """Restore the correct value for a specific cell"""
        item = self.matrix_table.item(row, col)
        if item and item.data(Qt.UserRole):
            data = item.data(Qt.UserRole)
            alt_id = data['alt_id']
            crit_id = data['crit_id']
            key = f"{alt_id}_{crit_id}"
            
            # Set flag to prevent triggering on_cell_changed
            self.is_programmatic_update = True
            
            try:
                if self.is_normalized_view:
                    # Restaurar valor normalizado
                    normalized_value = self.normalized_data.get(key, "")
                    item.setText(str(normalized_value))
                else:
                    # Restaurar valor original
                    original_value = self.matrix_data.get(key, "")
                    item.setText(str(original_value))
            finally:
                self.is_programmatic_update = False

    def restore_original_values(self):
        """Restore original values to the matrix display"""
        if not self.matrix_table.rowCount() or not self.matrix_table.columnCount():
            return
        
        # Temporarily disconnect cellChanged signal
        self.matrix_table.cellChanged.disconnect()
        
        try:
            # Restore original values
            for i in range(self.matrix_table.rowCount()):
                for j in range(self.matrix_table.columnCount()):
                    item = self.matrix_table.item(i, j)
                    if item and item.data(Qt.UserRole):
                        data = item.data(Qt.UserRole)
                        alt_id = data['alt_id']
                        crit_id = data['crit_id']
                        key = f"{alt_id}_{crit_id}"
                        
                        # Restore original value
                        original_value = self.matrix_data.get(key, "")
                        item.setText(str(original_value))
                        item.setToolTip("")  # Clear tooltip
        
        finally:
            # Reconnect the signal
            self.matrix_table.cellChanged.connect(self.on_cell_changed)

    def save_cell_change(self, alt_id, crit_id, value):
        """Save individual cell change to backend"""
        try:
            updates = [{
                'alternative_id': alt_id,
                'criteria_id': crit_id,
                'value': value
            }]
            
            success = self.project_controller.update_matrix_values(updates)
            if not success:
                print(f"Warning: Failed to auto-save cell change for {alt_id}_{crit_id}")
                
        except Exception as e:
            print(f"Error auto-saving cell change: {e}")


    def validate_cell_value(self, value, crit_id):
        """Validate a cell value according to criterion configuration"""
        if not value:
            return True  # Empty values are allowed
        
        if crit_id not in self.criteria_config:
            # Basic numeric validation if no config
            try:
                float(value)
                return True
            except ValueError:
                return False
        
        config = self.criteria_config[crit_id]
        min_val = config['min_spin'].value()
        max_val = config['max_spin'].value()
        
        try:
            num_value = float(value)
            return min_val <= num_value <= max_val
        except ValueError:
            return False
    
    def update_matrix_colors(self):
        """Update cell colors based on values and criterion types"""
        if not self.criteria_config:
            return
        
        criteria = self.project_controller.get_criteria()
        
        for j, crit in enumerate(criteria):
            crit_type = crit.get('optimization_type', 'maximize')
            
            # Get all values in this column
            values = []
            for i in range(self.matrix_table.rowCount()):
                item = self.matrix_table.item(i, j)
                if item and item.text().strip():
                    try:
                        values.append(float(item.text()))
                    except ValueError:
                        continue
            
            if not values:
                continue
            
            col_min, col_max = min(values), max(values)
            
            # Apply colors with different intensity for normalized vs original
            for i in range(self.matrix_table.rowCount()):
                item = self.matrix_table.item(i, j)
                if item and item.text().strip():
                    try:
                        value = float(item.text())
                        
                        # Normalize value to 0-1 range for color calculation
                        if col_max > col_min:
                            normalized = (value - col_min) / (col_max - col_min)
                        else:
                            normalized = 0.5
                        
                        # Color intensity based on view type
                        if self.is_normalized_view:
                            # More intense colors for normalized view
                            intensity = 150
                            base_color = 200
                        else:
                            # Softer colors for original view
                            intensity = 80
                            base_color = 230
                        
                        # Apply color based on criterion type
                        if crit_type == 'maximize':
                            # Green for high values (good)
                            green = base_color + int(normalized * intensity)
                            red = base_color - int(normalized * intensity // 2)
                            blue = base_color - int(normalized * intensity // 2)
                        else:
                            # Green for low values (good for cost criteria)
                            green = base_color + int((1-normalized) * intensity)
                            red = base_color - int((1-normalized) * intensity // 2)
                            blue = base_color - int((1-normalized) * intensity // 2)
                        
                        # Ensure color values are in valid range
                        red = max(180, min(255, red))
                        green = max(180, min(255, green))
                        blue = max(180, min(255, blue))
                        
                        color = QColor(red, green, blue)
                        item.setBackground(color)
                        
                        # Add flag for styling reference
                        if self.is_normalized_view:
                            item.setData(Qt.UserRole + 1, "normalized")
                        else:
                            item.setData(Qt.UserRole + 1, "original")
                            
                    except ValueError:
                        # Clear background for invalid values
                        item.setBackground(QColor())
    
    def update_statistics(self):
        """Update the statistics panel"""
        current_data = self.normalized_data if self.is_normalized_view else self.matrix_data
        
        if not current_data:
            self.statistics_text.setText("No data available for analysis")
            return
        
        stats_text = f"Matrix Statistics {'(Normalized)' if self.is_normalized_view else '(Original)'}:\n\n"
        
        # Get alternatives and criteria
        alternatives = self.project_controller.get_alternatives()
        criteria = self.project_controller.get_criteria()
        
        if not alternatives or not criteria:
            return
        
        # Statistics by criterion
        for crit in criteria:
            crit_id = crit['id']
            crit_name = crit['name']
            
            values = []
            for alt in alternatives:
                alt_id = alt['id']
                key = f"{alt_id}_{crit_id}"
                if key in current_data and current_data[key]:
                    try:
                        values.append(float(current_data[key]))
                    except ValueError:
                        continue
            
            if values:
                min_val = min(values)
                max_val = max(values)
                avg_val = sum(values) / len(values)
                std_val = np.std(values)
                
                stats_text += f"{crit_name}:\n"
                stats_text += f"  Min={min_val:.4f}, Max={max_val:.4f}\n"
                stats_text += f"  Avg={avg_val:.4f}, Std={std_val:.4f}\n\n"
        
        # Add preliminary ranking if normalized
        if self.is_normalized_view:
            stats_text += "Preliminary Ranking (Simple Sum):\n"
            ranking = self.calculate_preliminary_ranking()
            for i, (alt_name, score) in enumerate(ranking[:5]):  # Top 5
                stats_text += f"{i+1}. {alt_name}: {score:.4f}\n"
        
        self.statistics_text.setText(stats_text)
    
    def update_completeness(self):
        """Update the completeness progress bar"""
        if not self.matrix_table.rowCount() or not self.matrix_table.columnCount():
            self.progress_bar.setValue(0)
            self.completeness_percent.setText("0%")
            return
        
        total_cells = self.matrix_table.rowCount() * self.matrix_table.columnCount()
        filled_cells = 0
        
        for i in range(self.matrix_table.rowCount()):
            for j in range(self.matrix_table.columnCount()):
                item = self.matrix_table.item(i, j)
                if item and item.text().strip():
                    filled_cells += 1
        
        completeness = int((filled_cells / total_cells) * 100)
        self.progress_bar.setValue(completeness)
        self.completeness_percent.setText(f"{completeness}%")
    
    def toggle_normalized_view(self, checked):
        """Toggle between original and normalized view"""
        self.is_normalized_view = checked
        
        if checked:
            # Calculate normalized data
            self.calculate_normalized_data()
            
            # Update status to show normalized view
            current_text = self.project_label.text()
            if " - NORMALIZED VIEW" not in current_text:
                self.project_label.setText(f"{current_text} - NORMALIZED VIEW")
            
        else:
            # Return to original view - update status
            text = self.project_label.text().replace(" - NORMALIZED VIEW", "")
            self.project_label.setText(text)
        
        # Update display for both cases
        self.update_matrix_display()
        self.update_matrix_colors()
        self.update_statistics()
    
    def calculate_normalized_data(self):
        """Calculate normalized data using selected method"""
        if not self.matrix_data:
            self.normalized_data = {}
            return
        
        try:
            # Get alternatives and criteria
            alternatives = self.project_controller.get_alternatives()
            criteria = self.project_controller.get_criteria()
            
            if not alternatives or not criteria:
                return
            
            # Create matrix from current data
            matrix = np.zeros((len(alternatives), len(criteria)))
            
            for i, alt in enumerate(alternatives):
                for j, crit in enumerate(criteria):
                    key = f"{alt['id']}_{crit['id']}"
                    if key in self.matrix_data and self.matrix_data[key]:
                        try:
                            matrix[i, j] = float(self.matrix_data[key])
                        except ValueError:
                            matrix[i, j] = 0
            
            # Apply normalization method
            normalized_matrix = self.apply_normalization(matrix, criteria)
            
            # Store normalized data
            self.normalized_data = {}
            for i, alt in enumerate(alternatives):
                for j, crit in enumerate(criteria):
                    key = f"{alt['id']}_{crit['id']}"
                    self.normalized_data[key] = f"{normalized_matrix[i, j]:.4f}"
                    
        except Exception as e:
            print(f"Error calculating normalized data: {e}")
            self.normalized_data = {}

    def apply_normalization(self, matrix, criteria):
        """Apply selected normalization method to matrix"""
        normalized = matrix.copy()
        
        for j in range(matrix.shape[1]):
            col = matrix[:, j]
            crit = criteria[j]
            is_benefit = crit.get('optimization_type', 'maximize') == 'maximize'
            
            if self.normalization_method == 'minmax':
                col_min, col_max = np.min(col), np.max(col)
                if col_max != col_min:
                    if is_benefit:
                        normalized[:, j] = (col - col_min) / (col_max - col_min)
                    else:
                        normalized[:, j] = (col_max - col) / (col_max - col_min)
                else:
                    normalized[:, j] = 1.0 if is_benefit else 0.0
                    
            elif self.normalization_method == 'vector':
                col_norm = np.sqrt(np.sum(col ** 2))
                if col_norm > 0:
                    normalized[:, j] = col / col_norm
                    if not is_benefit:
                        normalized[:, j] = 1 - normalized[:, j]
                else:
                    normalized[:, j] = 0
                    
            elif self.normalization_method == 'sum':
                col_sum = np.sum(col)
                if col_sum > 0:
                    if is_benefit:
                        normalized[:, j] = col / col_sum
                    else:
                        col_inv = 1 / (col + 1e-10)  # Avoid division by zero
                        col_inv_sum = np.sum(col_inv)
                        normalized[:, j] = col_inv / col_inv_sum
                else:
                    normalized[:, j] = 1 / len(col)
                    
            elif self.normalization_method == 'max':
                col_max = np.max(col)
                if col_max > 0:
                    if is_benefit:
                        normalized[:, j] = col / col_max
                    else:
                        col_min = np.min(col)
                        normalized[:, j] = col_min / (col + 1e-10)
                else:
                    normalized[:, j] = 0
        
        return normalized

    def update_matrix_display(self):
        """Update matrix table display based on current view WITHOUT triggering events"""
        if not self.matrix_table.rowCount() or not self.matrix_table.columnCount():
            return
        
        # Set flag to prevent triggering cellChanged events
        self.is_programmatic_update = True
        
        try:
            # Choose data source based on current view
            data_source = self.normalized_data if self.is_normalized_view else self.matrix_data
            
            # Update cell values and tooltips
            for i in range(self.matrix_table.rowCount()):
                for j in range(self.matrix_table.columnCount()):
                    item = self.matrix_table.item(i, j)
                    if item and item.data(Qt.UserRole):
                        data = item.data(Qt.UserRole)
                        alt_id = data['alt_id']
                        crit_id = data['crit_id']
                        key = f"{alt_id}_{crit_id}"
                        
                        # Get the display value
                        display_value = data_source.get(key, "")
                        
                        # Update the cell text
                        item.setText(str(display_value))
                        
                        # Set appropriate tooltip
                        if self.is_normalized_view and display_value:
                            original_value = self.matrix_data.get(key, 'N/A')
                            item.setToolTip(f"Normalized value: {display_value}\nOriginal: {original_value}\nMethod: {self.normalization_method}")
                        else:
                            item.setToolTip("")
        
        finally:
            # Always restore flag
            self.is_programmatic_update = False

    def clear_all_values(self):
        """Clear all matrix values"""
        reply = QMessageBox.question(self, "Confirm Clear", 
                                   "Are you sure you want to clear all matrix values?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.matrix_data.clear()
            
            for i in range(self.matrix_table.rowCount()):
                for j in range(self.matrix_table.columnCount()):
                    item = self.matrix_table.item(i, j)
                    if item:
                        item.setText("")
            
            self.update_matrix_colors()
            self.update_statistics()
            self.update_completeness()
    
    def save_matrix(self):
        """Save the current matrix to the project"""
        if not self.project_controller.current_project_id:
            QMessageBox.warning(self, "Warning", "No project loaded")
            return
        
        try:
            # Prepare criteria configuration data
            criteria_config_data = {}
            for crit_id, config in self.criteria_config.items():
                criteria_config_data[crit_id] = {
                    'scale_type': config['scale_type_combo'].currentText(),
                    'min_value': config['min_spin'].value(),
                    'max_value': config['max_spin'].value(),
                    'unit': config['unit_edit'].text()
                }
            
            # Save matrix data and configuration
            success = self.project_controller.save_decision_matrix(
                self.matrix_data, criteria_config_data
            )
            
            if success:
                QMessageBox.information(self, "Success", "Matrix saved successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to save matrix")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save matrix: {str(e)}")
    
    def auto_save(self):
        """Auto-save the matrix data every 30 seconds"""
        if self.matrix_data and self.project_controller.current_project_id:
            try:
                # Prepare criteria configuration data
                criteria_config_data = {}
                for crit_id, config in self.criteria_config.items():
                    criteria_config_data[crit_id] = {
                        'scale_type': config['scale_type_combo'].currentText(),
                        'min_value': config['min_spin'].value(),
                        'max_value': config['max_spin'].value(),
                        'unit': config['unit_edit'].text()
                    }
                
                # Silent auto-save
                self.project_controller.save_decision_matrix(
                    self.matrix_data, criteria_config_data
                )
                
                print("Matrix auto-saved successfully")
                
            except Exception as e:
                print(f"Auto-save failed: {e}")
    
    def calculate_preliminary_ranking(self):
        """Calculate preliminary ranking using simple weighted sum"""
        alternatives = self.project_controller.get_alternatives()
        criteria = self.project_controller.get_criteria()
        
        if not alternatives or not criteria:
            return []
        
        scores = []
        for alt in alternatives:
            total_score = 0
            valid_values = 0
            
            for crit in criteria:
                key = f"{alt['id']}_{crit['id']}"
                if key in self.normalized_data and self.normalized_data[key]:
                    try:
                        value = float(self.normalized_data[key])
                        weight = crit.get('weight', 1.0)
                        total_score += value * weight
                        valid_values += 1
                    except ValueError:
                        continue
            
            if valid_values > 0:
                scores.append((alt['name'], total_score))
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores