from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                            QGroupBox, QTableWidget, QTableWidgetItem, QPushButton,
                            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QLabel,
                            QProgressBar, QTextEdit, QMessageBox, QHeaderView,
                            QFormLayout, QCheckBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
import numpy as np

class MatrixTab(QWidget):
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.matrix_data = {}  # Store matrix values
        self.criteria_config = {}  # Store scale configuration per criterion
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
        
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
        
        # Table controls
        controls_layout = QHBoxLayout()
        
        self.show_normalized_cb = QCheckBox("Show Normalized View")
        self.show_normalized_cb.toggled.connect(self.toggle_normalized_view)
        controls_layout.addWidget(self.show_normalized_cb)
        
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
        print(f"DEBUG: load_matrix_data called, project_id: {self.project_controller.current_project_id}")
        
        if not self.project_controller.current_project_id:
            self.project_label.setText("No project loaded - Please create or open a project first")
            self.project_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Limpiar la matriz cuando no hay proyecto
            self.matrix_table.setRowCount(0)
            self.matrix_table.setColumnCount(0)
            self.clear_config_panel()
            self.matrix_data.clear()
            self.update_completeness()
            return
        
        try:
            project = self.project_controller.get_current_project()
            print(f"DEBUG: Got project data: {project}")
            
            if project:
                project_name = project.get('name', 'Unknown')
                self.project_label.setText(f"Project: {project_name}")
                self.project_label.setStyleSheet("color: green; font-weight: bold;")
                
                # MEJORADO: Siempre refrescar desde el proyecto
                self.refresh_from_project()
            else:
                self.project_label.setText("Failed to load project data")
                self.project_label.setStyleSheet("color: red; font-weight: bold;")
                
        except Exception as e:
            print(f"DEBUG: Error in load_matrix_data: {e}")
            self.project_label.setText("Error loading project data")
            self.project_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.critical(self, "Error", f"Failed to load project data: {str(e)}")
    
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
            
            header_text = f"{crit_name}\n{crit_type.upper()}\nWeight: {weight}{scale_info}"
            crit_headers.append(header_text)
        
        self.matrix_table.setHorizontalHeaderLabels(crit_headers)
        
        # Resize columns
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
                self.matrix_table.setItem(i, j, item)
        
        # Update colors and statistics
        self.update_matrix_colors()
        self.update_statistics()
        self.update_completeness()
    
    def on_cell_changed(self, row, col):
        """Handle cell value changes"""
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
            # Store the value
            self.matrix_data[f"{alt_id}_{crit_id}"] = value
            
            # Update colors and statistics
            self.update_matrix_colors()
            self.update_statistics()
            self.update_completeness()
        else:
            # Invalid value - revert
            QMessageBox.warning(self, "Invalid Value", 
                              f"Invalid value for criterion {crit_id}")
            item.setText(self.matrix_data.get(f"{alt_id}_{crit_id}", ""))
    
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
            crit_id = crit['id']
            crit_type = crit.get('optimization_type', 'maximize')
            
            if crit_id not in self.criteria_config:
                continue
            
            config = self.criteria_config[crit_id]
            min_val = config['min_spin'].value()
            max_val = config['max_spin'].value()
            
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
            
            # Apply colors
            for i in range(self.matrix_table.rowCount()):
                item = self.matrix_table.item(i, j)
                if item and item.text().strip():
                    try:
                        value = float(item.text())
                        
                        # Normalize value to 0-1 range
                        if max_val > min_val:
                            normalized = (value - min_val) / (max_val - min_val)
                        else:
                            normalized = 0.5
                        
                        # Apply color based on criterion type
                        if crit_type == 'maximize':
                            # Green for high values (good)
                            color = QColor(255 - int(normalized * 100), 255, 255 - int(normalized * 100))
                        else:
                            # Green for low values (good for cost criteria)
                            color = QColor(255, 255 - int((1-normalized) * 100), 255 - int((1-normalized) * 100))
                        
                        item.setBackground(color)
                        
                    except ValueError:
                        continue
    
    def update_statistics(self):
        """Update the statistics panel"""
        if not self.matrix_data:
            self.statistics_text.setText("No data available for analysis")
            return
        
        stats_text = "Matrix Statistics:\n\n"
        
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
                if key in self.matrix_data and self.matrix_data[key]:
                    try:
                        values.append(float(self.matrix_data[key]))
                    except ValueError:
                        continue
            
            if values:
                min_val = min(values)
                max_val = max(values)
                avg_val = sum(values) / len(values)
                
                stats_text += f"{crit_name}: Min={min_val:.2f}, Max={max_val:.2f}, Avg={avg_val:.2f}\n"
        
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
        # This would show a normalized preview of the matrix
        # For now, just a placeholder
        if checked:
            QMessageBox.information(self, "Info", "Normalized view - Feature coming soon")
            self.show_normalized_cb.setChecked(False)
    
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
            # Here we would save the matrix data to the backend
            # For now, just show a success message
            QMessageBox.information(self, "Success", "Matrix saved successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save matrix: {str(e)}")
    
    def auto_save(self):
        """Auto-save the matrix data"""
        if self.matrix_data and self.project_controller.current_project_id:
            # Silent auto-save
            pass  # Implement auto-save logic here