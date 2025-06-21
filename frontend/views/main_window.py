import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QAction, 
                             QMenu, QToolBar, QStatusBar, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont
from controllers.project_controller import ProjectController
from PyQt5.QtWidgets import QFileDialog, QInputDialog
import logging

logger = logging.getLogger(__name__)

class MCDMApplication(QMainWindow):
    """Main window for the MCDM (Multi-Criteria Decision Making) application"""
    
    def __init__(self):
        super().__init__()
        self.previous_tab_index = 0  # NUEVO: Para rastrear la pestaña anterior
        self.init_ui()
        
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("OptiChoice - MCDM Software")
        self.setMinimumSize(1024, 768)
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Initialize tabs
        self.init_tabs()

        # IMPORTANTE: Conectar aboutToChange para guardar antes de cambiar
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
    def create_menu_bar(self):
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        new_action = QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_menu = file_menu.addMenu("&Export")
        export_pdf = QAction("PDF", self)
        export_pdf.triggered.connect(lambda: self.export_results("pdf"))
        export_menu.addAction(export_pdf)
        
        export_excel = QAction("Excel", self)
        export_excel.triggered.connect(lambda: self.export_results("excel"))
        export_menu.addAction(export_excel)
        
        export_csv = QAction("CSV", self)
        export_csv.triggered.connect(lambda: self.export_results("csv"))
        export_menu.addAction(export_csv)
        
        file_menu.addSeparator()
        
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = self.menuBar().addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_action)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo_action)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        edit_matrix_action = QAction("Edit Decision &Matrix", self)
        edit_matrix_action.triggered.connect(self.edit_matrix)
        edit_menu.addAction(edit_matrix_action)
        
        edit_weights_action = QAction("Edit Criteria &Weights", self)
        edit_weights_action.triggered.connect(self.edit_weights)
        edit_menu.addAction(edit_weights_action)
        
        # View menu
        view_menu = self.menuBar().addMenu("&View")
        
        view_matrix_action = QAction("Decision &Matrix", self)
        view_matrix_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(view_matrix_action)
        
        view_results_action = QAction("&Results", self)
        view_results_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        view_menu.addAction(view_results_action)
        
        view_charts_action = QAction("&Charts", self)
        view_charts_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
        view_menu.addAction(view_charts_action)
        
        view_sensitivity_action = QAction("&Sensitivity Analysis", self)
        view_sensitivity_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(5))
        view_menu.addAction(view_sensitivity_action)
        
        # Methods menu
        methods_menu = self.menuBar().addMenu("&Methods")
        
        ahp_action = QAction("&AHP", self)
        ahp_action.triggered.connect(lambda: self.execute_method("AHP"))
        methods_menu.addAction(ahp_action)
        
        topsis_action = QAction("&TOPSIS", self)
        topsis_action.triggered.connect(lambda: self.execute_method("TOPSIS"))
        methods_menu.addAction(topsis_action)
        
        promethee_action = QAction("&PROMETHEE", self)
        promethee_action.triggered.connect(lambda: self.execute_method("PROMETHEE"))
        methods_menu.addAction(promethee_action)
        
        electre_action = QAction("&ELECTRE", self)
        electre_action.triggered.connect(lambda: self.execute_method("ELECTRE"))
        methods_menu.addAction(electre_action)
        
        methods_menu.addSeparator()
        
        compare_action = QAction("&Compare All Methods", self)
        compare_action.triggered.connect(self.compare_methods)
        methods_menu.addAction(compare_action)
        
        # Data menu
        data_menu = self.menuBar().addMenu("&Data")
        
        import_excel_action = QAction("Import from &Excel", self)
        import_excel_action.triggered.connect(lambda: self.import_data("excel"))
        data_menu.addAction(import_excel_action)
        
        import_csv_action = QAction("Import from &CSV", self)
        import_csv_action.triggered.connect(lambda: self.import_data("csv"))
        data_menu.addAction(import_csv_action)
        
        data_menu.addSeparator()
        
        normalize_action = QAction("&Normalize Data", self)
        normalize_action.triggered.connect(self.normalize_data)
        data_menu.addAction(normalize_action)
        
        # Analysis menu
        analysis_menu = self.menuBar().addMenu("&Analysis")
        
        run_selected_action = QAction("Run &Selected Method", self)
        run_selected_action.triggered.connect(self.run_selected_method)
        analysis_menu.addAction(run_selected_action)
        
        run_all_action = QAction("Run &All Methods", self)
        run_all_action.triggered.connect(self.run_all_methods)
        analysis_menu.addAction(run_all_action)
        
        analysis_menu.addSeparator()
        
        sensitivity_action = QAction("&Sensitivity Analysis", self)
        sensitivity_action.triggered.connect(self.sensitivity_analysis)
        analysis_menu.addAction(sensitivity_action)
        
        concordance_action = QAction("&Concordance Analysis", self)
        concordance_action.triggered.connect(self.concordance_analysis)
        analysis_menu.addAction(concordance_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        user_manual_action = QAction("&User Manual", self)
        user_manual_action.triggered.connect(self.show_user_manual)
        help_menu.addAction(user_manual_action)
        
        tutorials_action = QAction("&Tutorials", self)
        tutorials_action.triggered.connect(self.show_tutorials)
        help_menu.addAction(tutorials_action)
        
        references_action = QAction("&Method References", self)
        references_action.triggered.connect(self.show_references)
        help_menu.addAction(references_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def init_tabs(self):
        from views.tabs.problem_tab import ProblemTab
        from views.tabs.matrix_tab import MatrixTab 
        from views.tabs.method_tab import MethodTab
        from views.tabs.results_tab import ResultsTab

        self.project_controller = ProjectController()

        # Problem Definition tab
        self.problem_tab = ProblemTab(self.project_controller)
        self.tab_widget.addTab(self.problem_tab, "Problem Definition")
        
        # Decision Matrix tab
        self.matrix_tab = MatrixTab(self.project_controller)
        self.tab_widget.addTab(self.matrix_tab, "Decision Matrix")
        
        # Method Selection tab
        self.method_tab = MethodTab(self.project_controller)
        self.tab_widget.addTab(self.method_tab, "Method Selection")

        # Connect Signals
        self.matrix_tab.matrix_changed.connect(self.on_matrix_changed)
        self.method_tab.methods_executed.connect(self.on_methods_executed)
    
        # Results tab
        self.results_tab = ResultsTab(self.project_controller)
        self.tab_widget.addTab(self.results_tab, "Results")
        
        # Visualization tab
        self.visualization_tab = QWidget()
        self.tab_widget.addTab(self.visualization_tab, "Visualization")
        
        # Sensitivity Analysis tab
        self.sensitivity_tab = QWidget()
        self.tab_widget.addTab(self.sensitivity_tab, "Sensitivity Analysis")
    
    def on_tab_changed(self, index):
        """Handle tab changes to sync data - FIXED VERSION"""
        
        # CORRECCIÓN: Mejorar la lógica de guardado
        if self.previous_tab_index == 1 and hasattr(self, 'matrix_tab'):
            # Solo guardar si hay cambios pendientes O datos significativos
            if self.matrix_tab.pending_changes or self._has_matrix_data():
                logger.info("Saving matrix data before tab change...")
                try:
                    # Bloquear cambio de pestañas temporalmente
                    self.tab_widget.blockSignals(True)
                    
                    # Forzar guardado sincrónico
                    save_success = self.matrix_tab.save_matrix(show_success=False)
                    
                    if save_success:
                        # CORRECCIÓN: Esperar más tiempo y forzar sincronización
                        from PyQt5.QtWidgets import QApplication
                        QApplication.processEvents()
                        import time
                        time.sleep(0.5)  # Aumentar tiempo de espera
                        
                        # Forzar recarga del proyecto para asegurar sincronización
                        if self.project_controller.current_project_id:
                            self.project_controller.load_project(self.project_controller.current_project_id)
                    else:
                        from PyQt5.QtWidgets import QMessageBox
                        reply = QMessageBox.question(
                            self, 
                            'Save Failed',
                            'Failed to save matrix data. Continue anyway?',
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            # Restaurar pestaña anterior
                            self.tab_widget.setCurrentIndex(self.previous_tab_index)
                            self.tab_widget.blockSignals(False)
                            return
                            
                except Exception as e:
                    logger.error(f"Error saving matrix on tab change: {e}")
                finally:
                    self.tab_widget.blockSignals(False)
        
        # Actualizar índice de pestaña anterior
        self.previous_tab_index = index
        
        # CORRECCIÓN: Recargar datos en las pestañas según corresponda
        if index == 2 and hasattr(self, 'method_tab'):
            # Pestaña de Method Selection - verificar estado de la matriz
            # Dar tiempo para que se complete el guardado
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.method_tab.check_matrix_status)
        
        elif index == 3 and hasattr(self, 'results_tab'):
            # Pestaña de Results - cargar resultados si existen
            try:
                project = self.project_controller.get_current_project()
                if project and 'method_results' in project:
                    # Actualizar la pestaña de resultados con los datos guardados
                    self.results_tab.update_with_results(project['method_results'])
                    logger.info("Loaded saved results into results tab")
            except Exception as e:
                logger.error(f"Error loading results: {e}")
        
        # Mostrar nombre de la pestaña actual
        tab_names = ["Project Manager", "Problem Definition", "Decision Matrix", 
                    "Method Selection", "Results", "Visualization", "Sensitivity Analysis"]
        if 0 <= index < len(tab_names):
            self.statusBar.showMessage(f"Current tab: {tab_names[index]}")

    def on_matrix_changed(self):
        """Handle matrix changes"""
        # Refresh method tab status if it's active
        if self.tab_widget.currentIndex() == 2 and hasattr(self, 'method_tab'):
            self.method_tab.check_matrix_status()

    def on_methods_executed(self, results):
        """Handle methods execution completion - Enhanced version"""
        try:
            if not results:
                logger.warning("No results to display")
                return
                
            # Log para debugging
            logger.info(f"Received {len(results)} method results")
            
            # Guardar resultados en el proyecto
            if self.project_controller.current_project_id:
                try:
                    # Obtener proyecto actual
                    project = self.project_controller.get_current_project()
                    if project:
                        # Merge con resultados existentes si los hay
                        existing_results = project.get('method_results', {})
                        existing_results.update(results)
                        project['method_results'] = existing_results
                        
                        # Guardar proyecto
                        if self.project_controller.save_project(project):
                            logger.info("Results saved to project successfully")
                        else:
                            logger.error("Failed to save results to project")
                    else:
                        logger.error("Could not get current project")
                except Exception as e:
                    logger.error(f"Error saving results: {e}")
                    # Continuar aunque falle el guardado
            
            # Cambiar a la pestaña de resultados
            self.tab_widget.setCurrentIndex(3)
            
            # Actualizar la pestaña de resultados
            if hasattr(self, 'results_tab') and hasattr(self.results_tab, 'update_with_results'):
                self.results_tab.update_with_results(results)
                
                # Actualizar status bar
                methods_str = ", ".join(results.keys())
                self.statusBar.showMessage(f"Executed: {methods_str}")
            else:
                logger.error("Results tab not properly initialized")
                QMessageBox.critical(
                    self, 
                    "Error", 
                    "Results tab is not properly initialized.\n"
                    "Please restart the application."
                )
                
        except Exception as e:
            logger.error(f"Error updating results: {str(e)}")
            import traceback
            traceback.print_exc()
            
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to display results:\n{str(e)}\n\n"
                "Results may have been saved but cannot be displayed."
            )
            self.statusBar.showMessage("Error displaying results")

    def _has_matrix_data(self):
        """Check if matrix has any significant data"""
        if not hasattr(self, 'matrix_tab'):
            return False
        
        # Verificar si hay datos en la matriz
        if self.matrix_tab.matrix_data:
            # Contar valores no vacíos
            non_empty_values = sum(1 for v in self.matrix_tab.matrix_data.values() if v.strip())
            return non_empty_values > 0
        
        return False

    # Actualizar el método execute_method en los menús
    def execute_method(self, method_name):
        """Execute a specific method from menu"""
        try:
            self.statusBar.showMessage(f"Executing {method_name} method...")
            
            # Switch to method tab
            self.tab_widget.setCurrentIndex(2)
            
            # Execute the method
            if hasattr(self, 'method_tab'):
                # Select and execute the specific method
                if method_name in self.method_tab.method_cards:
                    card = self.method_tab.method_cards[method_name]
                    card.select_cb.setChecked(True)
                    self.method_tab.execute_single_method(method_name)
            else:
                QMessageBox.warning(self, "Warning", "Method tab not initialized")
                
        except Exception as e:
            logger.error(f"Error executing method {method_name}: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to execute {method_name}: {str(e)}")
            self.statusBar.showMessage("Error executing method")

    def project_changed(self):
        """Call this method whenever the project changes"""
        if hasattr(self, 'matrix_tab'):
            self.matrix_tab.load_matrix_data()
        
        if hasattr(self, 'results_tab'):
            # NO limpiar los resultados, solo marcar que necesita recarga
            self.results_tab.status_label.setText("Project changed - refresh to load results")

    def closeEvent(self, event):
        """Handle application close event"""
        # Guardar cualquier cambio pendiente antes de cerrar
        if hasattr(self, 'matrix_tab') and self.matrix_tab.pending_changes:
            reply = QMessageBox.question(self, 'Save Changes?',
                                       'You have unsaved changes in the decision matrix. Save before closing?',
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.Yes:
                self.matrix_tab.save_matrix(show_success=False)
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    # File menu actions
    def new_project(self):
        self.statusBar.showMessage("Creating new project...")
        
        # Clear the current project
        self.project_controller.current_project_id = None
        
        # NUEVO: Cambiar automáticamente a la pestaña Project Manager
        self.tab_widget.setCurrentIndex(0)  # Project Manager es la pestaña 0
        
        # Reset the problem tab
        self.problem_tab.name_edit.clear()
        self.problem_tab.description_edit.clear()
        self.problem_tab.decision_maker_edit.clear()
        self.problem_tab.alt_table.setRowCount(0)
        self.problem_tab.crit_table.setRowCount(0)
        
        # NUEVO: También limpiar la matriz
        if hasattr(self, 'matrix_tab'):
            self.matrix_tab.load_matrix_data()
        
        self.statusBar.showMessage("New project created")
        
    def open_project(self):
        """Open project using professional project list dialog"""
        self.statusBar.showMessage("Loading projects...")
        
        try:
            # Import the new dialog
            from views.dialogs.project_list_dialog import ProjectListDialog
            
            # Create and show the dialog
            dialog = ProjectListDialog(self.project_controller, self)
            
            if dialog.exec_() == dialog.Accepted:
                project_id = dialog.get_selected_project_id()
                
                if project_id:
                    # Load the selected project
                    project = self.project_controller.load_project(project_id)
                    
                    if project:
                        # NUEVO: Cambiar automáticamente a la pestaña Project Manager
                        self.tab_widget.setCurrentIndex(0)  # Project Manager es la pestaña 0
                        
                        # Refresh the problem tab with the loaded project
                        self.problem_tab.load_project_data()
                        
                        # NUEVO: También actualizar la matriz automáticamente
                        if hasattr(self, 'matrix_tab'):
                            self.matrix_tab.load_matrix_data()
                        
                        self.statusBar.showMessage(f"Project '{project.get('name', '')}' loaded successfully")
                    else:
                        QMessageBox.critical(self, "Error", "Failed to load the selected project")
                        self.statusBar.showMessage("Failed to load project")
                else:
                    self.statusBar.showMessage("No project selected")
            else:
                self.statusBar.showMessage("Open project cancelled")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening project dialog: {str(e)}")
            self.statusBar.showMessage("Error opening project dialog")
        
    def save_project(self):
        self.statusBar.showMessage("Saving project...")
        self.problem_tab.save_project_info()
        self.statusBar.showMessage("Project saved successfully")
            
    def save_project_as(self):
        self.statusBar.showMessage("Saving project as...")
        # TODO: Implement save as functionality
        
    def export_results(self, format_type):
        self.statusBar.showMessage(f"Exporting results to {format_type}...")
        # TODO: Implement export functionality
        
    def open_settings(self):
        self.statusBar.showMessage("Opening settings...")
        # TODO: Implement settings dialog
    
    # Edit menu actions
    def undo_action(self):
        self.statusBar.showMessage("Undo")
        # TODO: Implement undo functionality
        
    def redo_action(self):
        self.statusBar.showMessage("Redo")
        # TODO: Implement redo functionality
        
    def edit_matrix(self):
        self.statusBar.showMessage("Editing decision matrix...")
        self.tab_widget.setCurrentIndex(1)  # Switch to matrix tab
        
    def edit_weights(self):
        self.statusBar.showMessage("Editing criteria weights...")
        # TODO: Implement weights editor
    
    # Methods actions
    def execute_method(self, method_name):
        self.statusBar.showMessage(f"Executing {method_name} method...")
        # TODO: Implement method execution
        
    def compare_methods(self):
        self.statusBar.showMessage("Comparing all methods...")
        # TODO: Implement method comparison
    
    # Data menu actions
    def import_data(self, format_type):
        self.statusBar.showMessage(f"Importing data from {format_type}...")
        # TODO: Implement data import
        
    def normalize_data(self):
        self.statusBar.showMessage("Normalizing data...")
        # TODO: Implement data normalization
    
    # Analysis menu actions
    def run_selected_method(self):
        self.statusBar.showMessage("Running selected method...")
        # TODO: Implement method execution
        
    def run_all_methods(self):
        self.statusBar.showMessage("Running all methods...")
        # TODO: Implement all methods execution
        
    def sensitivity_analysis(self):
        self.statusBar.showMessage("Performing sensitivity analysis...")
        self.tab_widget.setCurrentIndex(5)  # Switch to sensitivity tab
        
    def concordance_analysis(self):
        self.statusBar.showMessage("Performing concordance analysis...")
        # TODO: Implement concordance analysis
    
    # Help menu actions
    def show_user_manual(self):
        self.statusBar.showMessage("Showing user manual...")
        # TODO: Implement user manual display
        
    def show_tutorials(self):
        self.statusBar.showMessage("Showing tutorials...")
        # TODO: Implement tutorials display
        
    def show_references(self):
        self.statusBar.showMessage("Showing method references...")
        # TODO: Implement references display
        
    def show_about(self):
        QMessageBox.about(self, "About OptiChoice", 
                         "OptiChoice 1.0.0\n\nA Multi-Criteria Decision Making Software\n\nDeveloped by Juan Diego Sera Rodríguez")

def main():
    app = QApplication(sys.argv)
    window = MCDMApplication()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()