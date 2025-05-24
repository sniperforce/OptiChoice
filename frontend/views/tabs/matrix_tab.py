# frontend/views/tabs/matrix_tab.py - VERSION SIN BUCLES

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                            QGroupBox, QTableWidget, QTableWidgetItem, QPushButton,
                            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QLabel,
                            QProgressBar, QTextEdit, QMessageBox, QHeaderView,
                            QFormLayout, QToolTip, QCheckBox, QFrame, QScrollArea,
                            QTreeWidget, QTreeWidgetItem, QTabWidget, QDialog,
                            QDialogButtonBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap
import numpy as np

# Importar el validador avanzado
try:
    from utils.matrix_validator import AdvancedMatrixValidator, ValidationSeverity
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    print("Warning: Advanced validation not available. Install advanced_matrix_validator.py")


class ValidationPanel(QWidget):
    """Panel dedicado para mostrar resultados de validación"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.validation_results = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header con botones de acción
        header_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("🔍 Validate Matrix")
        self.validate_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        header_layout.addWidget(self.validate_btn)
        
        self.auto_validate_cb = QCheckBox("Auto-validate")
        self.auto_validate_cb.setChecked(True)  # CORREGIDO: Habilitado por defecto
        header_layout.addWidget(self.auto_validate_cb)
        
        header_layout.addStretch()
        
        # Summary badges
        self.summary_layout = QHBoxLayout()
        self.create_summary_badges()
        header_layout.addLayout(self.summary_layout)
        
        layout.addLayout(header_layout)
        
        # Tree widget para mostrar validaciones organizadas
        self.validation_tree = QTreeWidget()
        self.validation_tree.setHeaderLabels(["Issue", "Details", "Suggestion"])
        self.validation_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.validation_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.validation_tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        
        layout.addWidget(self.validation_tree)
        
        # Bottom status
        self.status_label = QLabel("Ready for validation")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(self.status_label)
    
    def create_summary_badges(self):
        """Create summary badges for different validation severities"""
        self.badges = {}
        
        badge_configs = [
            ('critical', '🔴', '#d32f2f', 'Critical'),
            ('error', '🟠', '#f57c00', 'Errors'), 
            ('warning', '🟡', '#ffa000', 'Warnings'),
            ('info', '🔵', '#1976d2', 'Info')
        ]
        
        for severity, icon, color, label in badge_configs:
            badge = QLabel(f"{icon} {label}: 0")
            badge.setStyleSheet(f"""
                background-color: {color}; 
                color: white; 
                padding: 4px 8px; 
                border-radius: 12px; 
                font-weight: bold;
                margin: 2px;
            """)
            badge.setMinimumWidth(80)
            badge.setAlignment(Qt.AlignCenter)
            self.badges[severity] = badge
            self.summary_layout.addWidget(badge)
    
    def update_validation_results(self, results):
        """Update the validation panel with new results"""
        self.validation_results = results
        self.update_summary_badges()
        self.populate_validation_tree()
        self.update_status()
    
    def update_summary_badges(self):
        """Update the summary badges with current counts"""
        summary = {'critical': 0, 'error': 0, 'warning': 0, 'info': 0}
        
        for result in self.validation_results:
            summary[result.severity.value] += 1
        
        badge_configs = [
            ('critical', '🔴', 'Critical'),
            ('error', '🟠', 'Errors'),
            ('warning', '🟡', 'Warnings'), 
            ('info', '🔵', 'Info')
        ]
        
        for severity, icon, label in badge_configs:
            count = summary[severity]
            self.badges[severity].setText(f"{icon} {label}: {count}")
            self.badges[severity].setVisible(count > 0)
    
    def populate_validation_tree(self):
        """Populate the validation tree with organized results"""
        self.validation_tree.clear()
        
        if not self.validation_results:
            item = QTreeWidgetItem(["✅ No issues found", "Matrix validation passed", "Ready for MCDM methods"])
            item.setBackground(0, QColor(200, 255, 200))
            self.validation_tree.addTopLevelItem(item)
            return
        
        # Group by severity
        if not VALIDATION_AVAILABLE:
            return
            
        severity_groups = {
            ValidationSeverity.CRITICAL: [],
            ValidationSeverity.ERROR: [], 
            ValidationSeverity.WARNING: [],
            ValidationSeverity.INFO: []
        }
        
        for result in self.validation_results:
            severity_groups[result.severity].append(result)
        
        # Create tree structure
        severity_configs = [
            (ValidationSeverity.CRITICAL, "🔴 Critical Issues", QColor(255, 200, 200)),
            (ValidationSeverity.ERROR, "🟠 Errors", QColor(255, 220, 200)),
            (ValidationSeverity.WARNING, "🟡 Warnings", QColor(255, 255, 200)),
            (ValidationSeverity.INFO, "🔵 Information", QColor(200, 220, 255))
        ]
        
        for severity, group_title, bg_color in severity_configs:
            results = severity_groups[severity]
            if not results:
                continue
                
            # Create group item
            group_item = QTreeWidgetItem([f"{group_title} ({len(results)})", "", ""])
            group_item.setBackground(0, bg_color)
            group_item.setFont(0, QFont("Arial", 10, QFont.Bold))
            group_item.setExpanded(severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR])
            
            # Add individual results
            for result in results:
                detail_item = QTreeWidgetItem([
                    result.message,
                    result.details,
                    result.suggestion
                ])
                
                # Add styling based on severity
                if severity == ValidationSeverity.CRITICAL:
                    detail_item.setForeground(0, QColor(150, 0, 0))
                elif severity == ValidationSeverity.ERROR:
                    detail_item.setForeground(0, QColor(200, 100, 0))
                
                group_item.addChild(detail_item)
            
            self.validation_tree.addTopLevelItem(group_item)
    
    def update_status(self):
        """Update the status label"""
        if not self.validation_results:
            self.status_label.setText("✅ Matrix validation passed - Ready for MCDM analysis")
            self.status_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        else:
            if not VALIDATION_AVAILABLE:
                return
                
            critical_count = sum(1 for r in self.validation_results if r.severity == ValidationSeverity.CRITICAL)
            error_count = sum(1 for r in self.validation_results if r.severity == ValidationSeverity.ERROR)
            
            if critical_count > 0:
                self.status_label.setText(f"❌ {critical_count} critical issue(s) prevent MCDM execution")
                self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
            elif error_count > 0:
                self.status_label.setText(f"⚠️ {error_count} error(s) may affect results quality")
                self.status_label.setStyleSheet("color: orange; font-weight: bold; padding: 5px;")
            else:
                self.status_label.setText("✅ Ready for MCDM analysis (with minor suggestions)")
                self.status_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")


class MatrixTab(QWidget):
    """Enhanced Matrix Tab with Professional Validations - NO LOOPS VERSION"""
    
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.matrix_data = {}  # Store matrix values
        self.criteria_config = {}  # Store scale configuration per criterion
        self.normalized_data = {}  
        self.is_normalized_view = False  
        self.normalization_method = 'minmax'  
        
        # CONTROL DE BUCLES
        self.is_programmatic_update = False
        self.is_loading_data = False  # NUEVO: Previene bucles durante carga
        self.cached_alternatives = []  # NUEVO: Cache para evitar requests repetitivos
        self.cached_criteria = []     # NUEVO: Cache para evitar requests repetitivos
        self.validation_in_progress = False  # NUEVO: Previene validaciones múltiples
        
        # Auto-save timer - AUMENTADO para reducir requests
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(60000)  # CAMBIADO: Cada 60 segundos en lugar de 30
        
        # Advanced validator
        if VALIDATION_AVAILABLE:
            self.validator = AdvancedMatrixValidator()
            self.last_validation_results = []
        
        self.init_ui()
        self.load_matrix_data()
    
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Configuration
        self.create_config_panel(splitter)
        
        # Center panel: Matrix ONLY (sin analysis para reducir complejidad)
        self.create_matrix_panel(splitter)
        
        # Right panel: Validation Results (solo si está disponible)
        if VALIDATION_AVAILABLE:
            self.create_validation_panel(splitter)
            splitter.setSizes([250, 500, 300])
        else:
            splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
    
    def create_validation_panel(self, parent):
        """Create the validation panel"""
        validation_widget = QWidget()
        layout = QVBoxLayout(validation_widget)
        
        # Title
        title_label = QLabel("Matrix Validation")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # Validation panel
        self.validation_panel = ValidationPanel()
        layout.addWidget(self.validation_panel)
        
        # Connect validation button
        self.validation_panel.validate_btn.clicked.connect(self.run_advanced_validation)
        
        parent.addWidget(validation_widget)
    
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
        """Create the matrix panel (SIN analysis para evitar complejidad)"""
        matrix_widget = QWidget()
        matrix_layout = QVBoxLayout(matrix_widget)
        
        # Status bar
        self.create_status_bar(matrix_layout)
        
        # Matrix table
        self.create_matrix_table(matrix_layout)
        
        # ELIMINADO: Analysis panel para reducir complejidad
        
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
        
        # Normalization controls
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
    
    # === MÉTODOS ANTI-BUCLE PRINCIPALES ===
    
    def load_matrix_data(self):
        """Load matrix data from current project - CORREGIDO"""
        if self.is_loading_data:
            return
            
        self.is_loading_data = True
        
        try:
            if not self.project_controller.current_project_id:
                self.project_label.setText("No project loaded - Please create or open a project first")
                self.project_label.setStyleSheet("color: red; font-weight: bold;")
                
                # Clear everything when no project
                self.matrix_table.setRowCount(0)
                self.matrix_table.setColumnCount(0)
                self.clear_config_panel()
                self.matrix_data.clear()
                self.cached_alternatives.clear()
                self.cached_criteria.clear()
                self.normalized_data.clear()
                self.update_completeness()
                
                # Reset validation state
                if VALIDATION_AVAILABLE:
                    self.validation_in_progress = False
                    if hasattr(self, 'validation_panel'):
                        self.validation_panel.update_validation_results([])
                return
            
            try:
                project = self.project_controller.get_current_project()
                if project:
                    project_name = project.get('name', 'Unknown')
                    self.project_label.setText(f"Project: {project_name}")
                    self.project_label.setStyleSheet("color: green; font-weight: bold;")
                    
                    # CORRIGIDO: Forzar refresh completo para proyectos existentes
                    print("DEBUG: Loading project - forcing fresh data...")
                    self.cached_alternatives.clear()  # Forzar recarga
                    self.cached_criteria.clear()     # Forzar recarga
                    
                    # Cargar alternatives y criteria PRIMERO
                    self.refresh_from_project_cached()
                    
                    # DESPUÉS cargar la matriz guardada
                    self.load_saved_matrix_data()
                    
                else:
                    self.project_label.setText("Failed to load project data")
                    self.project_label.setStyleSheet("color: red; font-weight: bold;")
                    
            except Exception as e:
                print(f"Error in load_matrix_data: {e}")
                self.project_label.setText("Error loading project data")
                self.project_label.setStyleSheet("color: red; font-weight: bold;")
        
        finally:
            self.is_loading_data = False
    
    def refresh_from_project_cached(self):
        """Refresh con CACHE para evitar requests repetitivos"""
        if self.is_loading_data:  # Extra protection
            return
            
        if not self.project_controller.current_project_id:
            return
        
        try:
            # USAR CACHE si está disponible y válido
            if not self.cached_alternatives or not self.cached_criteria:
                print("DEBUG: Loading fresh data from API...")
                self.cached_alternatives = self.project_controller.get_alternatives()
                self.cached_criteria = self.project_controller.get_criteria()
            else:
                print("DEBUG: Using cached data...")
            
            alternatives = self.cached_alternatives
            criteria = self.cached_criteria
            
            print(f"DEBUG: Got {len(alternatives)} alternatives, {len(criteria)} criteria")
            
            if not alternatives and not criteria:
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
            print(f"DEBUG: Error in refresh_from_project_cached: {e}")
            self.project_label.setText("Error refreshing from project")
            self.project_label.setStyleSheet("color: red; font-weight: bold;")
    
    def refresh_from_project(self):
        """Refresh manual - limpia cache y recarga"""
        print("DEBUG: Manual refresh - clearing cache...")
        self.cached_alternatives.clear()
        self.cached_criteria.clear()
        self.refresh_from_project_cached()
    
    def on_cell_changed(self, row, col):
        """Handle cell value changes - VERSION SIN BUCLES"""
        # Ignorar cambios programáticos
        if self.is_programmatic_update or self.is_loading_data:
            return
        
        # Si estamos en vista normalizada, no permitir edición
        if self.is_normalized_view:
            QMessageBox.warning(self, "Warning", 
                            "Cannot edit values in normalized view.\nSwitch to original view to edit values.")
            self.restore_cell_value(row, col)
            return
        
        # Procesar cambio normal
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
            old_value = self.matrix_data.get(f"{alt_id}_{crit_id}", "")
            self.matrix_data[f"{alt_id}_{crit_id}"] = value
            
            # Update colors and statistics
            self.update_matrix_colors()
            self.update_completeness()
            
            # Auto-save individual cell change - SIN BUCLES
            if value != old_value:
                self.save_cell_change_async(alt_id, crit_id, value)
            
            # VALIDACIÓN CONTROLADA: Solo si está habilitada Y no hay otra en progreso
            if (VALIDATION_AVAILABLE and 
                hasattr(self, 'validation_panel') and 
                self.validation_panel.auto_validate_cb.isChecked() and
                not self.validation_in_progress):
                
                # CORREGIDO: Timer mejorado para validación
                if not hasattr(self, 'validation_timer'):
                    self.validation_timer = QTimer()
                    self.validation_timer.setSingleShot(True)
                    self.validation_timer.timeout.connect(self.run_advanced_validation_delayed)
                
                self.validation_timer.stop()
                self.validation_timer.start(500)  # CORREGIDO: 500ms es mejor balance
                
        else:
            QMessageBox.warning(self, "Invalid Value", 
                            f"Invalid value for criterion {crit_id}")
            item.setText(self.matrix_data.get(f"{alt_id}_{crit_id}", ""))
    
    def save_cell_change_async(self, alt_id, crit_id, value):
        """Save individual cell change de manera asíncrona para evitar bucles"""
        try:
            updates = [{
                'alternative_id': alt_id,
                'criteria_id': crit_id,
                'value': value
            }]
            
            # Usar timer para hacer el save asíncrono
            if not hasattr(self, 'save_timer'):
                self.save_timer = QTimer()
                self.save_timer.setSingleShot(True)
                self.save_timer.timeout.connect(lambda: self.project_controller.update_matrix_values(updates))
            
            self.save_timer.stop()
            self.save_timer.start(500)  # Save después de 500ms
                
        except Exception as e:
            print(f"Error auto-saving cell change: {e}")
    
    def run_advanced_validation_delayed(self):
        """Método de validación diferida para auto-validación"""
        if not VALIDATION_AVAILABLE:
            return
        print("DEBUG: Running delayed validation...")
        self.run_advanced_validation()
    
    def run_advanced_validation(self):
        """Run validation - VERSION CORREGIDA SIN BUGS"""
        if not VALIDATION_AVAILABLE:
            return
            
        # CORREGIDO: Reset forzado del flag para evitar que se quede bugeado
        if self.validation_in_progress:
            print("DEBUG: Validation already in progress, forcing reset...")
            self.validation_in_progress = False
            
        self.validation_in_progress = True
        
        try:
            print("DEBUG: Starting validation...")
            
            # USAR CACHE si está disponible, sino cargar fresh
            alternatives = self.cached_alternatives
            criteria = self.cached_criteria
            
            # Si no hay cache, cargar fresh PERO sin triggear bucles
            if not alternatives or not criteria:
                print("DEBUG: No cache available, loading fresh data for validation...")
                try:
                    alternatives = self.project_controller.get_alternatives()
                    criteria = self.project_controller.get_criteria()
                    # Actualizar cache para próxima vez
                    self.cached_alternatives = alternatives
                    self.cached_criteria = criteria
                except Exception as e:
                    print(f"DEBUG: Error loading fresh data: {e}")
                    alternatives = []
                    criteria = []
            
            if not alternatives or not criteria:
                print("DEBUG: No alternatives or criteria available for validation")
                if hasattr(self, 'validation_panel'):
                    self.validation_panel.update_validation_results([])
                return
            
            print(f"DEBUG: Validating with {len(alternatives)} alternatives and {len(criteria)} criteria")
            
            # Run comprehensive validation
            validation_results = self.validator.validate_matrix_comprehensive(
                matrix_data=self.matrix_data,
                alternatives=alternatives,
                criteria=criteria,
                criteria_config=self._get_current_criteria_config()
            )
            
            print(f"DEBUG: Validation complete - {len(validation_results)} issues found")
            
            # Update validation panel
            if hasattr(self, 'validation_panel'):
                self.validation_panel.update_validation_results(validation_results)
            
            # Highlight problematic cells in matrix
            self.highlight_validation_issues(validation_results)
            
            # Store results for other uses
            self.last_validation_results = validation_results
            
        except Exception as e:
            print(f"DEBUG: Validation error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # CRÍTICO: Siempre resetear el flag
            self.validation_in_progress = False
            print("DEBUG: Validation finished, flag reset")
    
    # === RESTO DE MÉTODOS ORIGINALES (sin cambios críticos) ===
    
    def load_saved_matrix_data(self):
        """Load saved matrix data and configuration"""
        try:
            saved_data = self.project_controller.get_decision_matrix()
            
            if saved_data:
                self.matrix_data = saved_data.get('matrix_data', {})
                saved_config = saved_data.get('criteria_config', {})
                
                for crit_id, config_data in saved_config.items():
                    if crit_id in self.criteria_config:
                        config = self.criteria_config[crit_id]
                        config['scale_type_combo'].setCurrentText(config_data.get('scale_type', 'Numeric (Continuous)'))
                        config['min_spin'].setValue(config_data.get('min_value', 0))
                        config['max_spin'].setValue(config_data.get('max_value', 100))
                        config['unit_edit'].setText(config_data.get('unit', ''))
                        
        except Exception as e:
            print(f"Error loading saved matrix data: {e}")
    
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
        
        for crit_id, config in self.criteria_config.items():
            if config['scale_type_combo'] == sender:
                scale_type = sender.currentText()
                min_spin = config['min_spin']
                max_spin = config['max_spin']
                
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
        """Apply configuration with cache update"""
        if not self.criteria_config:
            QMessageBox.warning(self, "Warning", "No criteria configuration available")
            return
        
        try:
            if self.cached_alternatives and self.cached_criteria:
                self.initialize_matrix_table(self.cached_alternatives, self.cached_criteria)
                QMessageBox.information(self, "Success", "Configuration applied successfully")
            else:
                QMessageBox.warning(self, "Warning", "No alternatives or criteria available")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply configuration: {str(e)}")
    
    def initialize_matrix_table(self, alternatives, criteria):
        """Initialize the matrix table with proper structure"""
        self.is_programmatic_update = True
        
        try:
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
                
                type_indicator = "↑" if crit_type == 'maximize' else "↓"
                header_text = f"{crit_name} {type_indicator}\nWeight: {weight}{scale_info}"
                crit_headers.append(header_text)
            
            self.matrix_table.setHorizontalHeaderLabels(crit_headers)
            self.matrix_table.resizeColumnsToContents()
            
            # Initialize cells with existing data
            for i in range(len(alternatives)):
                for j in range(len(criteria)):
                    alt_id = alternatives[i]['id']
                    crit_id = criteria[j]['id']
                    
                    existing_value = self.matrix_data.get(f"{alt_id}_{crit_id}", "")
                    
                    item = QTableWidgetItem(str(existing_value))
                    item.setData(Qt.UserRole, {'alt_id': alt_id, 'crit_id': crit_id})
                    
                    if self.is_normalized_view:
                        item.setData(Qt.UserRole + 1, "normalized")
                    else:
                        item.setData(Qt.UserRole + 1, "original")
                    
                    self.matrix_table.setItem(i, j, item)
        
        finally:
            self.is_programmatic_update = False
        
        self.update_matrix_colors()
        self.update_completeness()
    
    # === MÉTODOS BÁSICOS (mantener funcionalidad mínima) ===
    
    def validate_cell_value(self, value, crit_id):
        """Validate a cell value according to criterion configuration"""
        if not value:
            return True
        
        if crit_id not in self.criteria_config:
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
        """Update cell colors - CORREGIDO: Sin celdas negras para valores vacíos"""
        if not self.criteria_config or not self.cached_criteria:
            return
        
        for j, crit in enumerate(self.cached_criteria):
            crit_type = crit.get('optimization_type', 'maximize')
            
            # Collect valid values for this column
            values = []
            valid_items = []  # Track which items have valid values
            
            for i in range(self.matrix_table.rowCount()):
                item = self.matrix_table.item(i, j)
                if item and item.text().strip():
                    try:
                        value = float(item.text())
                        values.append(value)
                        valid_items.append((i, value))
                    except ValueError:
                        continue
            
            if not values:
                continue
            
            col_min, col_max = min(values), max(values)
            
            # Apply colors only to valid items
            for i in range(self.matrix_table.rowCount()):
                item = self.matrix_table.item(i, j)
                if item:
                    # CORREGIDO: Manejar celdas vacías correctamente
                    if not item.text().strip():
                        # Celda vacía - color neutro (blanco/transparente)
                        item.setBackground(QColor(255, 255, 255))  # Blanco en lugar de negro
                        continue
                    
                    try:
                        value = float(item.text())
                        
                        # Skip validation highlighted cells
                        current_bg = item.background()
                        if (current_bg.color() == QColor(255, 200, 200) or
                            current_bg.color() == QColor(255, 220, 200) or
                            current_bg.color() == QColor(255, 255, 200)):
                            continue
                        
                        # Calculate normalized position for coloring
                        if col_max > col_min:
                            normalized = (value - col_min) / (col_max - col_min)
                        else:
                            normalized = 0.5
                        
                        # Color intensity and base
                        intensity = 60  # CORREGIDO: Reducido para colores más suaves
                        base_color = 240  # CORREGIDO: Base más clara
                        
                        if crit_type == 'maximize':
                            # Green tint for high values (good)
                            green = base_color + int(normalized * intensity)
                            red = base_color - int(normalized * intensity // 3)  # Menos contraste
                            blue = base_color - int(normalized * intensity // 3)
                        else:
                            # Green tint for low values (good for cost criteria)
                            green = base_color + int((1-normalized) * intensity)
                            red = base_color - int((1-normalized) * intensity // 3)
                            blue = base_color - int((1-normalized) * intensity // 3)
                        
                        # Ensure color values are in valid range
                        red = max(200, min(255, red))    # CORREGIDO: Mínimo más alto
                        green = max(200, min(255, green))
                        blue = max(200, min(255, blue))
                        
                        color = QColor(red, green, blue)
                        item.setBackground(color)
                            
                    except ValueError:
                        # Invalid numeric value - light gray background
                        item.setBackground(QColor(245, 245, 245))  # Gris muy claro
    
    def update_completeness(self):
        """Update completeness progress bar"""
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
    
    def save_matrix(self):
        """Save matrix with validation check"""
        if not self.project_controller.current_project_id:
            QMessageBox.warning(self, "Warning", "No project loaded")
            return
        
        # Run validation before saving if available
        if VALIDATION_AVAILABLE and hasattr(self, 'validator'):
            self.run_advanced_validation()
            
            if self.validator.has_blocking_issues():
                reply = QMessageBox.question(
                    self, "Validation Issues", 
                    "Critical validation issues detected. Save anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
        
        try:
            criteria_config_data = {}
            for crit_id, config in self.criteria_config.items():
                criteria_config_data[crit_id] = {
                    'scale_type': config['scale_type_combo'].currentText(),
                    'min_value': config['min_spin'].value(),
                    'max_value': config['max_spin'].value(),
                    'unit': config['unit_edit'].text()
                }
            
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
        """Auto-save reducido para evitar requests excesivos"""
        if (self.matrix_data and 
            self.project_controller.current_project_id and 
            not self.is_loading_data and 
            not self.is_programmatic_update):
            
            try:
                criteria_config_data = {}
                for crit_id, config in self.criteria_config.items():
                    criteria_config_data[crit_id] = {
                        'scale_type': config['scale_type_combo'].currentText(),
                        'min_value': config['min_spin'].value(),
                        'max_value': config['max_spin'].value(),
                        'unit': config['unit_edit'].text()
                    }
                
                self.project_controller.save_decision_matrix(
                    self.matrix_data, criteria_config_data
                )
                
                print("Matrix auto-saved successfully")
                
            except Exception as e:
                print(f"Auto-save failed: {e}")
    
    # === MÉTODOS RESTANTES PARA FUNCIONALIDAD COMPLETA ===
    
    def restore_cell_value(self, row, col):
        """Restore cell value"""
        item = self.matrix_table.item(row, col)
        if item and item.data(Qt.UserRole):
            data = item.data(Qt.UserRole)
            alt_id = data['alt_id']
            crit_id = data['crit_id']
            key = f"{alt_id}_{crit_id}"
            
            self.is_programmatic_update = True
            
            try:
                if self.is_normalized_view:
                    normalized_value = self.normalized_data.get(key, "")
                    item.setText(str(normalized_value))
                else:
                    original_value = self.matrix_data.get(key, "")
                    item.setText(str(original_value))
            finally:
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
            self.update_completeness()
    
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
        
        if old_method != self.normalization_method and self.is_normalized_view:
            self.calculate_normalized_data()
            self.update_matrix_display()
    
    def show_normalization_help(self):
        """Show normalization help"""
        help_text = """
        <h3>Normalization Methods:</h3>
        
        <b>Min-Max (0-1):</b><br>
        • Scales values to 0-1 range<br>
        • Formula: (x - min) / (max - min)<br><br>
        
        <b>Vector (Euclidean):</b><br>
        • Normalizes by vector length<br>
        • Formula: x / √(Σx²)<br><br>
        
        <b>Sum (Proportional):</b><br>
        • Values as proportion of total<br>
        • Formula: x / Σx<br><br>
        
        <b>Max (0-1 by max):</b><br>
        • Divides by maximum value<br>
        • Formula: x / max(x)<br>
        """
        
        QMessageBox.information(self, "Normalization Methods", help_text)
    
    def toggle_normalized_view(self, checked):
        """Toggle normalized view"""
        self.is_normalized_view = checked
        
        if checked:
            self.calculate_normalized_data()
            current_text = self.project_label.text()
            if " - NORMALIZED VIEW" not in current_text:
                self.project_label.setText(f"{current_text} - NORMALIZED VIEW")
            
        else:
            text = self.project_label.text().replace(" - NORMALIZED VIEW", "")
            self.project_label.setText(text)
        
        self.update_matrix_display()
        self.update_matrix_colors()
    
    def calculate_normalized_data(self):
        """Calculate normalized data"""
        if not self.matrix_data or not self.cached_alternatives or not self.cached_criteria:
            self.normalized_data = {}
            return
        
        try:
            alternatives = self.cached_alternatives
            criteria = self.cached_criteria
            
            matrix = np.zeros((len(alternatives), len(criteria)))
            
            for i, alt in enumerate(alternatives):
                for j, crit in enumerate(criteria):
                    key = f"{alt['id']}_{crit['id']}"
                    if key in self.matrix_data and self.matrix_data[key]:
                        try:
                            matrix[i, j] = float(self.matrix_data[key])
                        except ValueError:
                            matrix[i, j] = 0
            
            normalized_matrix = self.apply_normalization(matrix, criteria)
            
            self.normalized_data = {}
            for i, alt in enumerate(alternatives):
                for j, crit in enumerate(criteria):
                    key = f"{alt['id']}_{crit['id']}"
                    self.normalized_data[key] = f"{normalized_matrix[i, j]:.4f}"
                    
        except Exception as e:
            print(f"Error calculating normalized data: {e}")
            self.normalized_data = {}
    
    def apply_normalization(self, matrix, criteria):
        """Apply normalization method"""
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
        
        return normalized
    
    def update_matrix_display(self):
        """Update matrix display"""
        if not self.matrix_table.rowCount() or not self.matrix_table.columnCount():
            return
        
        self.is_programmatic_update = True
        
        try:
            data_source = self.normalized_data if self.is_normalized_view else self.matrix_data
            
            for i in range(self.matrix_table.rowCount()):
                for j in range(self.matrix_table.columnCount()):
                    item = self.matrix_table.item(i, j)
                    if item and item.data(Qt.UserRole):
                        data = item.data(Qt.UserRole)
                        alt_id = data['alt_id']
                        crit_id = data['crit_id']
                        key = f"{alt_id}_{crit_id}"
                        
                        display_value = data_source.get(key, "")
                        item.setText(str(display_value))
                        
                        if self.is_normalized_view and display_value:
                            original_value = self.matrix_data.get(key, 'N/A')
                            item.setToolTip(f"Normalized: {display_value}\nOriginal: {original_value}")
                        else:
                            item.setToolTip("")
        
        finally:
            self.is_programmatic_update = False
    
    # === MÉTODOS DE VALIDACIÓN (solo si está disponible) ===
    
    def _get_current_criteria_config(self):
        """Get current criteria configuration"""
        config = {}
        for crit_id, ui_config in self.criteria_config.items():
            config[crit_id] = {
                'scale_type': ui_config['scale_type_combo'].currentText(),
                'min_value': ui_config['min_spin'].value(),
                'max_value': ui_config['max_spin'].value(),
                'unit': ui_config['unit_edit'].text()
            }
        return config
    
    def highlight_validation_issues(self, validation_results):
        """Highlight validation issues"""
        if not VALIDATION_AVAILABLE:
            return
            
        self.clear_cell_highlights()
        
        for result in validation_results:
            if result.affected_cells:
                for row, col in result.affected_cells:
                    if (row < self.matrix_table.rowCount() and 
                        col < self.matrix_table.columnCount()):
                        
                        item = self.matrix_table.item(row, col)
                        if item:
                            if result.severity == ValidationSeverity.CRITICAL:
                                item.setBackground(QColor(255, 200, 200))
                            elif result.severity == ValidationSeverity.ERROR:
                                item.setBackground(QColor(255, 220, 200))
                            elif result.severity == ValidationSeverity.WARNING:
                                item.setBackground(QColor(255, 255, 200))
                            
                            item.setToolTip(f"{result.message}\n{result.suggestion}")
    
    def clear_cell_highlights(self):
        """Clear cell highlights - CORREGIDO"""
        print("DEBUG: Clearing cell highlights...")
        
        for i in range(self.matrix_table.rowCount()):
            for j in range(self.matrix_table.columnCount()):
                item = self.matrix_table.item(i, j)
                if item:
                    # Reset background to white for empty cells, or let update_matrix_colors handle it
                    if not item.text().strip():
                        item.setBackground(QColor(255, 255, 255))  # Blanco para celdas vacías
                    else:
                        item.setBackground(QColor())  # Reset para que update_matrix_colors lo maneje
                    
                    # Clear validation tooltips (keep only normalization tooltips)
                    current_tooltip = item.toolTip()
                    if current_tooltip and "Normalized:" not in current_tooltip and "Original:" not in current_tooltip:
                        item.setToolTip("")
        
        # Reapply normal matrix colors
        self.update_matrix_colors()