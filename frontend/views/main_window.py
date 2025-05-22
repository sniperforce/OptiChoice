import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QAction, 
                             QMenu, QToolBar, QStatusBar, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
from controllers.project_controller import ProjectController
from PyQt5.QtWidgets import QFileDialog, QInputDialog

class MCDMApplication(QMainWindow):
    """Main window for the MCDM (Multi-Criteria Decision Making) application"""
    
    def __init__(self):
        super().__init__()
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

        self.project_controller = ProjectController()
        # Problem Definition tab
        self.problem_tab = ProblemTab(self.project_controller)
        self.tab_widget.addTab(self.problem_tab, "Problem Definition")
        
        # Decision Matrix tab
        self.matrix_tab = MatrixTab(self.project_controller)
        self.tab_widget.addTab(self.matrix_tab, "Decision Matrix")
        
        # Method Selection tab
        self.method_tab = QWidget()
        self.tab_widget.addTab(self.method_tab, "Method Selection")
        
        # Results tab
        self.results_tab = QWidget()
        self.tab_widget.addTab(self.results_tab, "Results")
        
        # Visualization tab
        self.visualization_tab = QWidget()
        self.tab_widget.addTab(self.visualization_tab, "Visualization")
        
        # Sensitivity Analysis tab
        self.sensitivity_tab = QWidget()
        self.tab_widget.addTab(self.sensitivity_tab, "Sensitivity Analysis")
    
    def on_tab_changed(self, index):
        """Handle tab changes to sync data"""
        if index == 1:  # Decision Matrix tab
            # MEJORADO: Siempre actualizar la matriz cuando se cambia a esta pestaña
            if hasattr(self, 'matrix_tab'):
                self.matrix_tab.load_matrix_data()
        
        # Actualizar status bar según la pestaña
        tab_names = ["Project Manager", "Decision Matrix", "Method Selection", "Results", "Visualization", "Sensitivity Analysis"]
        if index < len(tab_names):
            self.statusBar.showMessage(f"Current tab: {tab_names[index]}")

    def project_changed(self):
        """Call this method whenever the project changes"""
        # Actualizar todas las pestañas que dependen del proyecto
        if hasattr(self, 'matrix_tab'):
            self.matrix_tab.load_matrix_data()

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