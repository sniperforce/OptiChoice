from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                            QGroupBox, QTableWidget, QTableWidgetItem, QPushButton,
                            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QLabel,
                            QProgressBar, QTextEdit, QMessageBox, QHeaderView,
                            QFormLayout, QToolTip, QCheckBox, QFrame, QScrollArea,
                            QTreeWidget, QTreeWidgetItem, QTabWidget, QDialog,
                            QDialogButtonBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Importar el validador avanzado
try:
    from utils.matrix_validator import AdvancedMatrixValidator, ValidationSeverity
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    logger.warning("Advanced validation not available. Install advanced_matrix_validator.py")


class DataCache:
    """Gestión centralizada de cache con invalidación automática"""
    
    def __init__(self):
        self._cache = {
            'alternatives': [],
            'criteria': [],
            'last_update': None,
            'cache_duration': 300  # 5 minutos
        }
    
    def is_valid(self) -> bool:
        """Verifica si el cache es válido"""
        if not self._cache['last_update']:
            return False
        
        elapsed = (datetime.now() - self._cache['last_update']).total_seconds()
        return elapsed < self._cache['cache_duration']
    
    def get(self, key: str) -> Any:
        """Obtiene un valor del cache si es válido"""
        if self.is_valid():
            return self._cache.get(key, [])
        return []
    
    def set(self, key: str, value: Any):
        """Establece un valor en el cache"""
        self._cache[key] = value
        self._cache['last_update'] = datetime.now()
    
    def invalidate(self):
        """Invalida todo el cache"""
        self._cache['alternatives'] = []
        self._cache['criteria'] = []
        self._cache['last_update'] = None
    
    def has_data(self) -> bool:
        """Verifica si hay datos en cache"""
        return bool(self._cache['alternatives'] or self._cache['criteria'])


class StateManager:
    """Gestión centralizada de estados para evitar bucles"""
    
    def __init__(self):
        self._states = {
            'is_loading': False,
            'is_updating': False,
            'is_validating': False,
            'is_saving': False
        }
        self._locks = set()
    
    def can_proceed(self, operation: str) -> bool:
        """Verifica si se puede proceder con una operación"""
        # No permitir si ya está en progreso
        if operation in self._locks:
            return False
        
        # Reglas específicas para evitar conflictos
        if operation == 'validate' and ('update' in self._locks or 'save' in self._locks):
            return False
        
        if operation == 'save' and 'validate' in self._locks:
            return False
        
        return True
    
    def lock(self, operation: str):
        """Bloquea una operación"""
        self._locks.add(operation)
        logger.debug(f"Locked operation: {operation}")
    
    def unlock(self, operation: str):
        """Desbloquea una operación"""
        self._locks.discard(operation)
        logger.debug(f"Unlocked operation: {operation}")
    
    def is_locked(self, operation: str) -> bool:
        """Verifica si una operación está bloqueada"""
        return operation in self._locks


class TimerCoordinator:
    """Coordinación centralizada de timers"""
    
    def __init__(self):
        self._timers = {}
        self._delays = {
            'validation': 1000,    # 1 segundo
            'autosave': 3000,      # 3 segundos
            'color_update': 500    # 0.5 segundos
        }
    
    def schedule(self, name: str, callback: callable, delay: Optional[int] = None):
        """Programa una operación con delay"""
        if name in self._timers:
            self._timers[name].stop()
            self._timers[name].deleteLater()
        
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        
        actual_delay = delay if delay is not None else self._delays.get(name, 1000)
        timer.start(actual_delay)
        
        self._timers[name] = timer
        logger.debug(f"Scheduled {name} with {actual_delay}ms delay")
    
    def cancel(self, name: str):
        """Cancela una operación programada"""
        if name in self._timers:
            self._timers[name].stop()
            self._timers[name].deleteLater()
            del self._timers[name]
            logger.debug(f"Cancelled {name}")
    
    def cancel_all(self):
        """Cancela todas las operaciones programadas"""
        for name in list(self._timers.keys()):
            self.cancel(name)


class ValidationPanel(QWidget):
    """Panel mejorado para mostrar resultados de validación"""
    
    # Señales
    validation_requested = pyqtSignal()
    auto_validate_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.validation_results = []
        self._is_auto_validate = True
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header con botones de acción
        header_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("🔍 Validate Matrix")
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.validate_btn.clicked.connect(self.validation_requested.emit)
        header_layout.addWidget(self.validate_btn)
        
        self.auto_validate_cb = QCheckBox("Auto-validate")
        self.auto_validate_cb.setChecked(self._is_auto_validate)
        self.auto_validate_cb.toggled.connect(self._on_auto_validate_changed)
        header_layout.addWidget(self.auto_validate_cb)
        
        header_layout.addStretch()
        
        # Summary badges
        self.summary_layout = QHBoxLayout()
        self.create_summary_badges()
        header_layout.addLayout(self.summary_layout)
        
        layout.addLayout(header_layout)
        
        # Tree widget para mostrar validaciones
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
    
    def _on_auto_validate_changed(self, checked: bool):
        """Maneja el cambio de estado de auto-validación"""
        self._is_auto_validate = checked
        self.auto_validate_changed.emit(checked)
        logger.info(f"Auto-validation {'enabled' if checked else 'disabled'}")
    
    def is_auto_validate_enabled(self) -> bool:
        """Retorna si la auto-validación está habilitada"""
        return self._is_auto_validate
    
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
                QLabel {{
                    background-color: {color}; 
                    color: white; 
                    padding: 4px 8px; 
                    border-radius: 12px; 
                    font-weight: bold;
                    margin: 2px;
                }}
            """)
            badge.setMinimumWidth(80)
            badge.setAlignment(Qt.AlignCenter)
            badge.hide()  # Ocultar inicialmente
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
            badge = self.badges[severity]
            badge.setText(f"{icon} {label}: {count}")
            badge.setVisible(count > 0)
    
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
    """Professional Matrix Tab with Enterprise-Grade Features"""
    
    # Señales personalizadas
    matrix_changed = pyqtSignal()
    validation_completed = pyqtSignal(list)
    
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        
        # Data storage
        self.matrix_data = {}  
        self.criteria_config = {}
        self.normalized_data = {}  
        
        # View state
        self.is_normalized_view = False  
        self.normalization_method = 'minmax'
        
        # Managers
        self.cache = DataCache()
        self.state_manager = StateManager()
        self.timer_coordinator = TimerCoordinator()
        
        # Validator
        if VALIDATION_AVAILABLE:
            self.validator = AdvancedMatrixValidator()
            self.last_validation_results = []
        
        # Tracking cambios
        self.pending_changes = set()  # Track cells with pending changes
        
        # Auto-save timer principal (no por celda)
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._perform_auto_save)
        self.auto_save_timer.start(120000)  # 2 minutos
        
        self.init_ui()
        
        # Cargar datos iniciales
        QTimer.singleShot(100, self.load_matrix_data)
    
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Configuration
        self.create_config_panel(splitter)
        
        # Center panel: Matrix
        self.create_matrix_panel(splitter)
        
        # Right panel: Validation Results
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
        self.validation_panel.validation_requested.connect(self.run_validation_manual)
        self.validation_panel.auto_validate_changed.connect(self._on_auto_validate_changed)
        layout.addWidget(self.validation_panel)
        
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
        
        self.refresh_btn = QPushButton("🔄 Refresh from Project")
        self.refresh_btn.clicked.connect(self.refresh_from_project)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                font-weight: bold;
            }
        """)
        button_layout.addWidget(self.refresh_btn)
        
        self.apply_config_btn = QPushButton("⚙️ Apply Configuration")
        self.apply_config_btn.clicked.connect(self.apply_configuration)
        self.apply_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(self.apply_config_btn)
        
        self.save_matrix_btn = QPushButton("💾 Save Matrix")
        self.save_matrix_btn.clicked.connect(self.save_matrix_manual)
        self.save_matrix_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        button_layout.addWidget(self.save_matrix_btn)
        
        button_layout.addStretch()
        config_layout.addLayout(button_layout)
        
        parent.addWidget(config_widget)
    
    def create_matrix_panel(self, parent):
        """Create the matrix panel"""
        matrix_widget = QWidget()
        matrix_layout = QVBoxLayout(matrix_widget)
        
        # Status bar
        self.create_status_bar(matrix_layout)
        
        # Matrix table
        self.create_matrix_table(matrix_layout)
        
        parent.addWidget(matrix_widget)
    
    def create_status_bar(self, parent_layout):
        """Create status bar with project info and completeness"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        
        # Project info
        self.project_label = QLabel("No project loaded")
        self.project_label.setFont(QFont("Arial", 10, QFont.Bold))
        status_layout.addWidget(self.project_label)
        
        status_layout.addStretch()
        
        # Auto-save indicator
        self.autosave_indicator = QLabel("💾 Auto-save: ON")
        self.autosave_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self.autosave_indicator)
        
        # Completeness progress
        self.completeness_label = QLabel("Completeness:")
        status_layout.addWidget(self.completeness_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        
        self.completeness_percent = QLabel("0%")
        self.completeness_percent.setFont(QFont("Arial", 9, QFont.Bold))
        status_layout.addWidget(self.completeness_percent)
        
        parent_layout.addWidget(status_frame)
    
    def create_matrix_table(self, parent_layout):
        """Create the main decision matrix table"""
        matrix_group = QGroupBox("Decision Matrix")
        matrix_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
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
        self.norm_help_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        controls_layout.addWidget(self.norm_help_btn)
        
        controls_layout.addStretch()
        
        self.clear_all_btn = QPushButton("🗑️ Clear All Values")
        self.clear_all_btn.clicked.connect(self.clear_all_values)
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        controls_layout.addWidget(self.clear_all_btn)
        
        matrix_layout.addLayout(controls_layout)
        
        # Main matrix table
        self.matrix_table = QTableWidget()
        self.matrix_table.cellChanged.connect(self.on_cell_changed)
        self.matrix_table.setAlternatingRowColors(True)
        self.matrix_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #1976D2;
                color: white;
            }
        """)
        matrix_layout.addWidget(self.matrix_table)
        
        parent_layout.addWidget(matrix_group)
    
    # === MÉTODOS PRINCIPALES MEJORADOS ===
    
    def load_matrix_data(self):
        """Load matrix data with proper state management"""
        if not self.state_manager.can_proceed('load'):
            logger.debug("Cannot proceed with load - operation locked")
            return
        
        self.state_manager.lock('load')
        
        try:
            if not self.project_controller.current_project_id:
                self._handle_no_project()
                return
            
            project = self.project_controller.get_current_project()
            if not project:
                self._handle_no_project()
                return
            
            # Update project info
            project_name = project.get('name', 'Unknown')
            self.project_label.setText(f"Project: {project_name}")
            self.project_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
            
            # Invalidate cache to force refresh
            self.cache.invalidate()
            
            # Load alternatives and criteria
            self._load_project_structure()
            
            # Load saved matrix data
            self._load_saved_matrix_data()
            
            # Update UI
            self.update_completeness()
            
            # Run initial validation if enabled
            if VALIDATION_AVAILABLE and hasattr(self, 'validation_panel'):
                if self.validation_panel.is_auto_validate_enabled():
                    self.timer_coordinator.schedule('validation', self.run_validation_auto, 500)
                    
        except Exception as e:
            logger.error(f"Error loading matrix data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load matrix data: {str(e)}")
        finally:
            self.state_manager.unlock('load')
    
    def _handle_no_project(self):
        """Handle the case when no project is loaded"""
        self.project_label.setText("No project loaded - Please create or open a project first")
        self.project_label.setStyleSheet("color: #f44336; font-weight: bold;")
        
        # Clear everything
        self.matrix_table.setRowCount(0)
        self.matrix_table.setColumnCount(0)
        self.clear_config_panel()
        self.matrix_data.clear()
        self.normalized_data.clear()
        self.cache.invalidate()
        self.pending_changes.clear()
        
        # Clear validation
        if VALIDATION_AVAILABLE and hasattr(self, 'validation_panel'):
            self.validation_panel.update_validation_results([])
    
    def _load_project_structure(self):
        """Load alternatives and criteria with caching"""
        # Try cache first
        alternatives = self.cache.get('alternatives')
        criteria = self.cache.get('criteria')
        
        if not alternatives or not criteria:
            # Load from API
            logger.info("Loading fresh data from API...")
            alternatives = self.project_controller.get_alternatives()
            criteria = self.project_controller.get_criteria()
            
            # Update cache
            self.cache.set('alternatives', alternatives)
            self.cache.set('criteria', criteria)
        else:
            logger.info("Using cached data...")
        
        if not alternatives or not criteria:
            msg = "Add alternatives and criteria in Project Manager first"
            self.project_label.setText(f"Project loaded - {msg}")
            self.project_label.setStyleSheet("color: #ff9800; font-weight: bold;")
            return
        
        # Clear and recreate configuration
        self.clear_config_panel()
        for crit in criteria:
            self.create_criterion_config(crit)
        
        # Initialize matrix table
        self.initialize_matrix_table(alternatives, criteria)
    
    def _load_saved_matrix_data(self):
        """Load saved matrix data and configuration"""
        try:
            saved_data = self.project_controller.get_decision_matrix()
            
            if saved_data:
                self.matrix_data = saved_data.get('matrix_data', {})
                saved_config = saved_data.get('criteria_config', {})
                
                # Apply saved configuration
                for crit_id, config_data in saved_config.items():
                    if crit_id in self.criteria_config:
                        config = self.criteria_config[crit_id]
                        config['scale_type_combo'].setCurrentText(config_data.get('scale_type', 'Numeric (Continuous)'))
                        config['min_spin'].setValue(config_data.get('min_value', 0))
                        config['max_spin'].setValue(config_data.get('max_value', 100))
                        config['unit_edit'].setText(config_data.get('unit', ''))
                
                # Update table with saved values
                self._update_table_values()
                
        except Exception as e:
            logger.error(f"Error loading saved matrix data: {e}")
    
    def refresh_from_project(self):
        """Manual refresh - clears cache and reloads"""
        if not self.state_manager.can_proceed('refresh'):
            return
        
        reply = QMessageBox.question(self, "Confirm Refresh", 
                                   "This will reload all data from the project. Continue?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            logger.info("Manual refresh - clearing cache...")
            self.cache.invalidate()
            self.pending_changes.clear()
            self.load_matrix_data()
    
    def on_cell_changed(self, row, col):
        """Handle cell value changes with proper validation"""
        if not self.state_manager.can_proceed('cell_change'):
            return
        
        # Skip if in normalized view
        if self.is_normalized_view:
            QMessageBox.warning(self, "Warning", 
                            "Cannot edit values in normalized view.\nSwitch to original view to edit values.")
            self.restore_cell_value(row, col)
            return
        
        item = self.matrix_table.item(row, col)
        if not item:
            return
        
        value = item.text().strip()
        data = item.data(Qt.UserRole)
        
        if not data:
            return
        
        alt_id = data['alt_id']
        crit_id = data['crit_id']
        key = f"{alt_id}_{crit_id}"
        
        # Validate the value
        if self.validate_cell_value(value, crit_id):
            old_value = self.matrix_data.get(key, "")
            
            if value != old_value:
                self.matrix_data[key] = value
                self.pending_changes.add(key)
                
                # Programar actualización de colores
                self.timer_coordinator.schedule('color_update', self._update_display)
                
                # Programar auto-save
                self.timer_coordinator.schedule('autosave', self._perform_auto_save)
                
                # Programar validación si está habilitada
                if VALIDATION_AVAILABLE and hasattr(self, 'validation_panel'):
                    if self.validation_panel.is_auto_validate_enabled():
                        self.timer_coordinator.schedule('validation', self.run_validation_auto)
                
                # Emitir señal de cambio
                self.matrix_changed.emit()
        else:
            QMessageBox.warning(self, "Invalid Value", 
                            f"Invalid value for criterion {crit_id}")
            item.setText(self.matrix_data.get(key, ""))
    
    def validate_cell_value(self, value: str, crit_id: str) -> bool:
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
    
    def _update_display(self):
        """Update display elements (colors, completeness)"""
        self.update_matrix_colors()
        self.update_completeness()
    
    def run_validation_manual(self):
        """Run validation manually (from button)"""
        if VALIDATION_AVAILABLE:
            self._run_validation()
    
    def run_validation_auto(self):
        """Run validation automatically (from timer)"""
        if VALIDATION_AVAILABLE and self.validation_panel.is_auto_validate_enabled():
            self._run_validation()
    
    def _run_validation(self):
        """Core validation logic with proper state management"""
        if not self.state_manager.can_proceed('validate'):
            logger.debug("Cannot proceed with validation - operation locked")
            return
        
        self.state_manager.lock('validate')
        
        try:
            logger.info("Running matrix validation...")
            
            # Get data
            alternatives = self.cache.get('alternatives')
            criteria = self.cache.get('criteria')
            
            if not alternatives or not criteria:
                # Try loading fresh
                alternatives = self.project_controller.get_alternatives()
                criteria = self.project_controller.get_criteria()
                
                if not alternatives or not criteria:
                    self.validation_panel.update_validation_results([])
                    return
            
            # Run validation
            validation_results = self.validator.validate_matrix_comprehensive(
                matrix_data=self.matrix_data,
                alternatives=alternatives,
                criteria=criteria,
                criteria_config=self._get_current_criteria_config()
            )
            
            # Update UI
            self.validation_panel.update_validation_results(validation_results)
            self.highlight_validation_issues(validation_results)
            
            # Store results
            self.last_validation_results = validation_results
            
            # Emit signal
            self.validation_completed.emit(validation_results)
            
            logger.info(f"Validation complete - {len(validation_results)} issues found")
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
        finally:
            self.state_manager.unlock('validate')
    
    def _on_auto_validate_changed(self, enabled: bool):
        """Handle auto-validation toggle"""
        if enabled:
            logger.info("Auto-validation enabled")
            # Run validation immediately
            self.timer_coordinator.schedule('validation', self.run_validation_auto, 100)
        else:
            logger.info("Auto-validation disabled")
            # Cancel any pending validation
            self.timer_coordinator.cancel('validation')
    
    def save_matrix_manual(self):
        """Manual save from button"""
        self._save_matrix(show_success=True)
    
    def _perform_auto_save(self):
        """Auto-save logic"""
        if self.pending_changes and self.project_controller.current_project_id:
            logger.info(f"Auto-saving {len(self.pending_changes)} changes...")
            self._save_matrix(show_success=False)
            
            # Update indicator
            self.autosave_indicator.setText("💾 Auto-saved")
            QTimer.singleShot(2000, lambda: self.autosave_indicator.setText("💾 Auto-save: ON"))
    
    def _save_matrix(self, show_success: bool = False):
        """Core save logic with state management"""
        if not self.state_manager.can_proceed('save'):
            return
        
        if not self.project_controller.current_project_id:
            if show_success:
                QMessageBox.warning(self, "Warning", "No project loaded")
            return
        
        self.state_manager.lock('save')
        
        try:
            # Check for blocking validation issues
            if VALIDATION_AVAILABLE and hasattr(self, 'validator'):
                if self.last_validation_results:
                    critical_issues = [r for r in self.last_validation_results 
                                     if r.severity == ValidationSeverity.CRITICAL]
                    
                    if critical_issues and show_success:
                        reply = QMessageBox.question(
                            self, "Validation Issues", 
                            f"{len(critical_issues)} critical issue(s) detected. Save anyway?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            return
            
            # Prepare data
            criteria_config_data = self._get_current_criteria_config()
            
            # Save
            success = self.project_controller.save_decision_matrix(
                self.matrix_data, criteria_config_data
            )
            
            if success:
                self.pending_changes.clear()
                if show_success:
                    QMessageBox.information(self, "Success", "Matrix saved successfully")
                logger.info("Matrix saved successfully")
            else:
                if show_success:
                    QMessageBox.critical(self, "Error", "Failed to save matrix")
                logger.error("Failed to save matrix")
                
        except Exception as e:
            logger.error(f"Save error: {e}")
            if show_success:
                QMessageBox.critical(self, "Error", f"Failed to save matrix: {str(e)}")
        finally:
            self.state_manager.unlock('save')
    
    # === MÉTODOS DE CONFIGURACIÓN ===
    
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
        config_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                margin: 2px;
            }
        """)
        config_layout = QFormLayout(config_frame)
        
        crit_id = criterion['id']
        crit_name = criterion['name']
        crit_type = criterion.get('optimization_type', 'maximize')
        
        # Title
        title_label = QLabel(f"{crit_name} ({crit_id})")
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet(f"color: {'#2e7d32' if crit_type == 'maximize' else '#d32f2f'};")
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
        unit_edit.setPlaceholderText("e.g., $, kg, %")
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
        scale_type_combo.currentTextChanged.connect(
            lambda: self.on_scale_type_changed(crit_id)
        )
        
        self.config_container_layout.addWidget(config_frame)
    
    def on_scale_type_changed(self, crit_id):
        """Handle scale type change for a specific criterion"""
        config = self.criteria_config.get(crit_id)
        if not config:
            return
        
        scale_type = config['scale_type_combo'].currentText()
        min_spin = config['min_spin']
        max_spin = config['max_spin']
        
        # Set default values based on scale type
        scale_defaults = {
            "Likert 1-5": (1, 5),
            "Likert 1-7": (1, 7),
            "Likert 1-10": (1, 10),
            "Percentage (0-100%)": (0, 100)
        }
        
        if scale_type in scale_defaults:
            min_val, max_val = scale_defaults[scale_type]
            min_spin.setValue(min_val)
            max_spin.setValue(max_val)
    
    def apply_configuration(self):
        """Apply configuration changes"""
        if not self.criteria_config:
            QMessageBox.warning(self, "Warning", "No criteria configuration available")
            return
        
        reply = QMessageBox.question(self, "Apply Configuration", 
                                   "This will recreate the matrix table. Continue?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                alternatives = self.cache.get('alternatives')
                criteria = self.cache.get('criteria')
                
                if alternatives and criteria:
                    self.initialize_matrix_table(alternatives, criteria)
                    QMessageBox.information(self, "Success", "Configuration applied successfully")
                else:
                    QMessageBox.warning(self, "Warning", "No alternatives or criteria available")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to apply configuration: {str(e)}")
    
    # === MÉTODOS DE TABLA ===
    
    def initialize_matrix_table(self, alternatives, criteria):
        """Initialize the matrix table with proper structure"""
        if not self.state_manager.can_proceed('update'):
            return
        
        self.state_manager.lock('update')
        
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
            
            # Initialize cells
            self._populate_table_cells(alternatives, criteria)
            
        finally:
            self.state_manager.unlock('update')
    
    def _populate_table_cells(self, alternatives, criteria):
        """Populate table cells with data"""
        for i, alt in enumerate(alternatives):
            for j, crit in enumerate(criteria):
                alt_id = alt['id']
                crit_id = crit['id']
                key = f"{alt_id}_{crit_id}"
                
                existing_value = self.matrix_data.get(key, "")
                
                item = QTableWidgetItem(str(existing_value))
                item.setData(Qt.UserRole, {'alt_id': alt_id, 'crit_id': crit_id})
                item.setTextAlignment(Qt.AlignCenter)
                
                # Set tooltip
                if existing_value:
                    item.setToolTip(f"Alternative: {alt['name']}\nCriterion: {crit['name']}\nValue: {existing_value}")
                
                self.matrix_table.setItem(i, j, item)
        
        self._update_display()
    
    def _update_table_values(self):
        """Update table values from matrix_data"""
        for i in range(self.matrix_table.rowCount()):
            for j in range(self.matrix_table.columnCount()):
                item = self.matrix_table.item(i, j)
                if item and item.data(Qt.UserRole):
                    data = item.data(Qt.UserRole)
                    key = f"{data['alt_id']}_{data['crit_id']}"
                    value = self.matrix_data.get(key, "")
                    
                    # Temporarily disconnect signal to avoid triggering on_cell_changed
                    self.matrix_table.cellChanged.disconnect()
                    item.setText(str(value))
                    self.matrix_table.cellChanged.connect(self.on_cell_changed)
    
    def update_matrix_colors(self):
        """Update cell colors with improved logic"""
        if not self.criteria_config or not self.cache.has_data():
            return
        
        criteria = self.cache.get('criteria')
        if not criteria:
            return
        
        for j, crit in enumerate(criteria):
            if j >= self.matrix_table.columnCount():
                continue
                
            crit_type = crit.get('optimization_type', 'maximize')
            
            # Collect valid values for this column
            values = []
            cell_items = []
            
            for i in range(self.matrix_table.rowCount()):
                item = self.matrix_table.item(i, j)
                if item and item.text().strip():
                    try:
                        value = float(item.text())
                        values.append(value)
                        cell_items.append((i, item, value))
                    except ValueError:
                        continue
            
            if not values:
                continue
            
            col_min, col_max = min(values), max(values)
            
            # Apply colors
            for i, item, value in cell_items:
                # Skip if cell has validation highlight
                current_bg = item.background()
                if (current_bg.color() == QColor(255, 200, 200) or  # Critical
                    current_bg.color() == QColor(255, 220, 200) or  # Error
                    current_bg.color() == QColor(255, 255, 200)):   # Warning
                    continue
                
                # Calculate color based on value
                if col_max > col_min:
                    normalized = (value - col_min) / (col_max - col_min)
                else:
                    normalized = 0.5
                
                # Determine color
                if crit_type == 'maximize':
                    # Green for high values (good)
                    hue = 120  # Green
                    saturation = int(normalized * 50 + 20)
                    lightness = 240 - int(normalized * 40)
                else:
                    # Green for low values (good for cost criteria)
                    hue = 120  # Green
                    saturation = int((1-normalized) * 50 + 20)
                    lightness = 240 - int((1-normalized) * 40)
                
                color = QColor.fromHsl(hue, saturation, lightness)
                item.setBackground(color)
            
            # Handle empty cells
            for i in range(self.matrix_table.rowCount()):
                item = self.matrix_table.item(i, j)
                if item and not item.text().strip():
                    item.setBackground(QColor(255, 255, 255))  # White for empty
    
    def update_completeness(self):
        """Update completeness progress bar"""
        if not self.matrix_table.rowCount() or not self.matrix_table.columnCount():
            self.progress_bar.setValue(0)
            self.completeness_percent.setText("0%")
            return
        
        total_cells = self.matrix_table.rowCount() * self.matrix_table.columnCount()
        filled_cells = sum(1 for value in self.matrix_data.values() if value.strip())
        
        completeness = int((filled_cells / total_cells) * 100) if total_cells > 0 else 0
        
        self.progress_bar.setValue(completeness)
        self.completeness_percent.setText(f"{completeness}%")
        
        # Update color based on completeness
        if completeness < 30:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk { background-color: #f44336; }
            """)
        elif completeness < 70:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk { background-color: #ff9800; }
            """)
        else:
            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk { background-color: #4CAF50; }
            """)
    
    # === MÉTODOS DE NORMALIZACIÓN ===
    
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
    
    def toggle_normalized_view(self, checked):
        """Toggle between original and normalized view"""
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
        self.timer_coordinator.schedule('color_update', self._update_display, 100)
    
    def calculate_normalized_data(self):
        """Calculate normalized data based on current method"""
        alternatives = self.cache.get('alternatives')
        criteria = self.cache.get('criteria')
        
        if not alternatives or not criteria or not self.matrix_data:
            self.normalized_data = {}
            return
        
        try:
            # Build numerical matrix
            matrix = np.zeros((len(alternatives), len(criteria)))
            
            for i, alt in enumerate(alternatives):
                for j, crit in enumerate(criteria):
                    key = f"{alt['id']}_{crit['id']}"
                    if key in self.matrix_data and self.matrix_data[key]:
                        try:
                            matrix[i, j] = float(self.matrix_data[key])
                        except ValueError:
                            matrix[i, j] = 0
            
            # Apply normalization
            normalized_matrix = self.apply_normalization(matrix, criteria)
            
            # Store normalized values
            self.normalized_data = {}
            for i, alt in enumerate(alternatives):
                for j, crit in enumerate(criteria):
                    key = f"{alt['id']}_{crit['id']}"
                    self.normalized_data[key] = f"{normalized_matrix[i, j]:.4f}"
                    
        except Exception as e:
            logger.error(f"Error calculating normalized data: {e}")
            self.normalized_data = {}
    
    def apply_normalization(self, matrix, criteria):
        """Apply selected normalization method"""
        normalized = matrix.copy()
        
        for j in range(matrix.shape[1]):
            col = matrix[:, j]
            crit = criteria[j]
            is_benefit = crit.get('optimization_type', 'maximize') == 'maximize'
            
            # Skip columns with all zeros
            if np.all(col == 0):
                continue
            
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
                norm = np.linalg.norm(col)
                if norm > 0:
                    normalized[:, j] = col / norm
                    if not is_benefit:
                        normalized[:, j] = 1 - normalized[:, j]
                        
            elif self.normalization_method == 'sum':
                col_sum = np.sum(col)
                if col_sum > 0:
                    normalized[:, j] = col / col_sum
                    if not is_benefit:
                        normalized[:, j] = 1 - normalized[:, j]
                        
            elif self.normalization_method == 'max':
                col_max = np.max(col)
                if col_max > 0:
                    normalized[:, j] = col / col_max
                    if not is_benefit:
                        normalized[:, j] = 1 - normalized[:, j]
        
        return normalized
    
    def update_matrix_display(self):
        """Update matrix display based on current view mode"""
        if not self.matrix_table.rowCount() or not self.matrix_table.columnCount():
            return
        
        data_source = self.normalized_data if self.is_normalized_view else self.matrix_data
        
        # Temporarily disconnect signal
        self.matrix_table.cellChanged.disconnect()
        
        try:
            for i in range(self.matrix_table.rowCount()):
                for j in range(self.matrix_table.columnCount()):
                    item = self.matrix_table.item(i, j)
                    if item and item.data(Qt.UserRole):
                        data = item.data(Qt.UserRole)
                        key = f"{data['alt_id']}_{data['crit_id']}"
                        
                        display_value = data_source.get(key, "")
                        item.setText(str(display_value))
                        
                        # Update tooltip
                        if self.is_normalized_view and display_value:
                            original_value = self.matrix_data.get(key, 'N/A')
                            item.setToolTip(f"Normalized: {display_value}\nOriginal: {original_value}")
                        else:
                            alternatives = self.cache.get('alternatives')
                            criteria = self.cache.get('criteria')
                            alt_name = next((a['name'] for a in alternatives if a['id'] == data['alt_id']), 'Unknown')
                            crit_name = next((c['name'] for c in criteria if c['id'] == data['crit_id']), 'Unknown')
                            item.setToolTip(f"Alternative: {alt_name}\nCriterion: {crit_name}\nValue: {display_value}")
        
        finally:
            # Reconnect signal
            self.matrix_table.cellChanged.connect(self.on_cell_changed)
    
    # === MÉTODOS DE VALIDACIÓN ===
    
    def highlight_validation_issues(self, validation_results):
        """Highlight cells with validation issues"""
        if not VALIDATION_AVAILABLE:
            return
        
        # Clear previous highlights
        self.clear_validation_highlights()
        
        # Apply new highlights
        for result in validation_results:
            if result.affected_cells:
                for row, col in result.affected_cells:
                    if (0 <= row < self.matrix_table.rowCount() and 
                        0 <= col < self.matrix_table.columnCount()):
                        
                        item = self.matrix_table.item(row, col)
                        if item:
                            # Set background color based on severity
                            color_map = {
                                ValidationSeverity.CRITICAL: QColor(255, 200, 200),
                                ValidationSeverity.ERROR: QColor(255, 220, 200),
                                ValidationSeverity.WARNING: QColor(255, 255, 200),
                                ValidationSeverity.INFO: QColor(200, 220, 255)
                            }
                            
                            color = color_map.get(result.severity, QColor())
                            item.setBackground(color)
                            
                            # Add tooltip
                            existing_tooltip = item.toolTip()
                            validation_tooltip = f"\n\n⚠️ {result.message}\n💡 {result.suggestion}"
                            item.setToolTip(existing_tooltip + validation_tooltip)
    
    def clear_validation_highlights(self):
        """Clear validation highlights from cells"""
        for i in range(self.matrix_table.rowCount()):
            for j in range(self.matrix_table.columnCount()):
                item = self.matrix_table.item(i, j)
                if item:
                    # Remove validation colors
                    current_bg = item.background().color()
                    validation_colors = [
                        QColor(255, 200, 200),  # Critical
                        QColor(255, 220, 200),  # Error
                        QColor(255, 255, 200),  # Warning
                        QColor(200, 220, 255)   # Info
                    ]
                    
                    if current_bg in validation_colors:
                        item.setBackground(QColor())
                    
                    # Remove validation tooltip
                    tooltip = item.toolTip()
                    if "⚠️" in tooltip:
                        # Remove validation part
                        parts = tooltip.split("\n\n⚠️")
                        item.setToolTip(parts[0])
    
    # === MÉTODOS AUXILIARES ===
    
    def restore_cell_value(self, row, col):
        """Restore original cell value"""
        item = self.matrix_table.item(row, col)
        if item and item.data(Qt.UserRole):
            data = item.data(Qt.UserRole)
            key = f"{data['alt_id']}_{data['crit_id']}"
            
            if self.is_normalized_view:
                value = self.normalized_data.get(key, "")
            else:
                value = self.matrix_data.get(key, "")
            
            # Temporarily disconnect signal
            self.matrix_table.cellChanged.disconnect()
            item.setText(str(value))
            self.matrix_table.cellChanged.connect(self.on_cell_changed)
    
    def clear_all_values(self):
        """Clear all matrix values with confirmation"""
        reply = QMessageBox.question(self, "Confirm Clear", 
                                   "Are you sure you want to clear all matrix values?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.matrix_data.clear()
            self.normalized_data.clear()
            self.pending_changes.clear()
            
            # Clear table
            for i in range(self.matrix_table.rowCount()):
                for j in range(self.matrix_table.columnCount()):
                    item = self.matrix_table.item(i, j)
                    if item:
                        # Temporarily disconnect signal
                        self.matrix_table.cellChanged.disconnect()
                        item.setText("")
                        self.matrix_table.cellChanged.connect(self.on_cell_changed)
            
            self._update_display()
            
            # Clear validation
            if VALIDATION_AVAILABLE and hasattr(self, 'validation_panel'):
                self.validation_panel.update_validation_results([])
            
            logger.info("All matrix values cleared")
    
    def show_normalization_help(self):
        """Show detailed normalization help"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Normalization Methods Help")
        help_dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(help_dialog)
        
        help_text = """
        <h2>Normalization Methods</h2>
        
        <h3>Min-Max (0-1)</h3>
        <p><b>Formula:</b> (x - min) / (max - min) for benefit criteria<br>
        (max - x) / (max - min) for cost criteria</p>
        <p><b>Use when:</b> You want all values scaled to [0,1] range</p>
        
        <h3>Vector (Euclidean)</h3>
        <p><b>Formula:</b> x / √(Σx²)</p>
        <p><b>Use when:</b> Preserving proportions is important</p>
        
        <h3>Sum (Proportional)</h3>
        <p><b>Formula:</b> x / Σx</p>
        <p><b>Use when:</b> Values represent parts of a whole</p>
        
        <h3>Max (0-1 by max)</h3>
        <p><b>Formula:</b> x / max(x)</p>
        <p><b>Use when:</b> Maximum value should be the reference point</p>
        
        <p><i>Note: Cost criteria are automatically inverted during normalization</i></p>
        """
        
        text_widget = QTextEdit()
        text_widget.setHtml(help_text)
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(help_dialog.accept)
        layout.addWidget(close_btn)
        
        help_dialog.exec_()
    
    def _get_current_criteria_config(self) -> Dict[str, Dict]:
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
    
    def closeEvent(self, event):
        """Handle tab close event"""
        # Cancel all timers
        self.timer_coordinator.cancel_all()
        
        # Stop auto-save timer
        self.auto_save_timer.stop()
        
        # Save any pending changes
        if self.pending_changes:
            reply = QMessageBox.question(self, "Unsaved Changes", 
                                       "Save changes before closing?",
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.Yes:
                self._save_matrix(show_success=False)
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        event.accept()