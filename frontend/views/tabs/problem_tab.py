from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLabel, QLineEdit, QTextEdit, QPushButton, 
                            QGroupBox, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QMessageBox, QComboBox, QAbstractItemView)
from PyQt5.QtCore import Qt
from views.dialogs.alternative_dialog import AlternativeDialog
from views.dialogs.criteria_dialog import CriteriaDialog

class ProblemTab(QWidget):
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.is_loading = False  # Flag para evitar loops de carga
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Project information section
        info_group = QGroupBox("Project Information")
        info_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name")
        info_layout.addRow("Name:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter project description")
        self.description_edit.setMaximumHeight(80)
        info_layout.addRow("Description:", self.description_edit)

        self.decision_maker_edit = QLineEdit()
        self.decision_maker_edit.setPlaceholderText("Enter decision maker's name")
        info_layout.addRow("Decision Maker:", self.decision_maker_edit)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # Alternative section
        alt_group = QGroupBox("Alternatives")
        alt_layout = QVBoxLayout()

        self.alt_table = QTableWidget(0, 3)
        self.alt_table.setHorizontalHeaderLabels(["ID", "Name", "Description"])
        self.alt_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.alt_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        alt_layout.addWidget(self.alt_table)

        alt_btn_layout = QHBoxLayout()
        self.add_alt_btn = QPushButton("Add Alternative")
        self.edit_alt_btn = QPushButton("Edit Alternative")
        self.remove_alt_btn = QPushButton("Remove Alternative")

        alt_btn_layout.addWidget(self.add_alt_btn)
        alt_btn_layout.addWidget(self.edit_alt_btn)
        alt_btn_layout.addWidget(self.remove_alt_btn)

        alt_layout.addLayout(alt_btn_layout)
        alt_group.setLayout(alt_layout)
        main_layout.addWidget(alt_group)

        # Criteria section
        crit_group = QGroupBox("Criteria")
        crit_layout = QVBoxLayout()

        self.crit_table = QTableWidget(0, 5)
        self.crit_table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Weight", "Unit"])
        self.crit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.crit_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        crit_layout.addWidget(self.crit_table)

        crit_btn_layout = QHBoxLayout()
        self.add_crit_btn = QPushButton("Add Criterion")
        self.edit_crit_btn = QPushButton("Edit Criterion")
        self.remove_crit_btn = QPushButton("Remove Criterion")

        crit_btn_layout.addWidget(self.add_crit_btn)
        crit_btn_layout.addWidget(self.edit_crit_btn)
        crit_btn_layout.addWidget(self.remove_crit_btn)
        
        crit_layout.addLayout(crit_btn_layout)
        crit_group.setLayout(crit_layout)
        main_layout.addWidget(crit_group)

        # Save button at the bottom
        save_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Project")
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px;")
        save_layout.addStretch()
        save_layout.addWidget(self.save_btn)
        main_layout.addLayout(save_layout)

        self.connect_signals()
    
    def connect_signals(self):
        self.save_btn.clicked.connect(self.save_project)
        self.add_alt_btn.clicked.connect(self.add_alternative)
        self.edit_alt_btn.clicked.connect(self.edit_alternative)
        self.remove_alt_btn.clicked.connect(self.remove_alternative)
        self.add_crit_btn.clicked.connect(self.add_criterion)
        self.edit_crit_btn.clicked.connect(self.edit_criterion)
        self.remove_crit_btn.clicked.connect(self.remove_criterion)
    
    def load_project_data(self):
        """Load project data if a project is currently loaded"""
        if self.is_loading:
            return
            
        if self.project_controller.current_project_id:
            self.is_loading = True
            try:
                project = self.project_controller.get_current_project()
                if project:
                    self.name_edit.setText(project.get('name', ''))
                    self.description_edit.setText(project.get('description', ''))
                    self.decision_maker_edit.setText(project.get('decision_maker', ''))
                    
                    # Load alternatives and criteria
                    self._refresh_tables()
            finally:
                self.is_loading = False
    
    def _refresh_tables(self):
        # Load alternatives
        
        alternatives = self.project_controller.get_alternatives()
        
        self.alt_table.setRowCount(0)
        for alt in alternatives:
            self._add_alternative_to_table(alt)
        
        # Load criteria
        criteria = self.project_controller.get_criteria()
        
        self.crit_table.setRowCount(0)
        for crit in criteria:
            self._add_criterion_to_table(crit)
    
    def save_project(self):
        """Save all project data in one clean operation"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Project name cannot be empty")
            return
        
        description = self.description_edit.toPlainText().strip()
        decision_maker = self.decision_maker_edit.text().strip()
        
        try:
            # Step 1: Create or update basic project info
            if not self.project_controller.current_project_id:
                success = self.project_controller.create_project(name, description, decision_maker)
                if not success:
                    QMessageBox.critical(self, "Error", "Failed to create project")
                    return
                print(f"Created project with ID: {self.project_controller.current_project_id}")
            else:
                success = self.project_controller.update_project(name, description, decision_maker)
                if not success:
                    QMessageBox.critical(self, "Error", "Failed to update project")
                    return
            
            # Step 2: Get data from tables
            alternatives = self.get_table_alternatives()
            criteria = self.get_table_criteria()
            
            # Step 3: Save the complete project with table data
            success = self.project_controller.save_complete_project(alternatives, criteria)
            if success:
                QMessageBox.information(self, "Success", "Project saved successfully")
                self._refresh_tables()  # Refresh to show any backend changes
                
                # NUEVO: Notificar a la ventana principal que el proyecto cambió
                main_window = self.parent()
                while main_window and not hasattr(main_window, 'project_changed'):
                    main_window = main_window.parent()
                
                if main_window and hasattr(main_window, 'project_changed'):
                    main_window.project_changed()
            else:
                QMessageBox.critical(self, "Error", "Failed to save project completely")

            

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
            print(f"Save error: {str(e)}")
    
    def add_alternative(self):
        """Add a new alternative"""
        dialog = AlternativeDialog(self)
        if dialog.exec_():
            alt_data = dialog.get_data()
            
            if not alt_data['id'].strip():
                QMessageBox.warning(self, "Warning", "Alternative ID is required")
                return
                
            if not alt_data['name'].strip():
                QMessageBox.warning(self, "Warning", "Alternative name is required")
                return
            
            # Just add to table - will be saved when user clicks Save Project
            self._add_alternative_to_table(alt_data)
    
    def _add_alternative_to_table(self, alt_data):
        """Add alternative data to the table"""
        row = self.alt_table.rowCount()
        self.alt_table.insertRow(row)
        self.alt_table.setItem(row, 0, QTableWidgetItem(str(alt_data.get('id', ''))))
        self.alt_table.setItem(row, 1, QTableWidgetItem(str(alt_data.get('name', ''))))
        self.alt_table.setItem(row, 2, QTableWidgetItem(str(alt_data.get('description', ''))))
    
    def edit_alternative(self):
        """Edit the selected alternative"""
        current_row = self.alt_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an alternative to edit")
            return
        
        alt_data = {
            'id': self.alt_table.item(current_row, 0).text(),
            'name': self.alt_table.item(current_row, 1).text(),
            'description': self.alt_table.item(current_row, 2).text() if self.alt_table.item(current_row, 2) else ''
        }
        
        dialog = AlternativeDialog(self, alt_data)
        if dialog.exec_():
            new_data = dialog.get_data()
            
            # Update table
            self.alt_table.setItem(current_row, 1, QTableWidgetItem(new_data['name']))
            self.alt_table.setItem(current_row, 2, QTableWidgetItem(new_data['description']))
    
    def remove_alternative(self):
        """Remove the selected alternative"""
        current_row = self.alt_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an alternative to remove")
            return
        
        alt_id = self.alt_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     f"Are you sure you want to delete alternative '{alt_id}'?", 
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.alt_table.removeRow(current_row)
    
    def add_criterion(self):
        """Add a new criterion"""
        dialog = CriteriaDialog(self)
        if dialog.exec_():
            crit_data = dialog.get_data()
            
            if not crit_data['id'].strip():
                QMessageBox.warning(self, "Warning", "Criterion ID is required")
                return
                
            if not crit_data['name'].strip():
                QMessageBox.warning(self, "Warning", "Criterion name is required")
                return
            
            # Just add to table - will be saved when user clicks Save Project
            self._add_criterion_to_table(crit_data)
    
    def _add_criterion_to_table(self, crit_data):
        """Add criterion data to the table"""
        row = self.crit_table.rowCount()
        self.crit_table.insertRow(row)
        self.crit_table.setItem(row, 0, QTableWidgetItem(str(crit_data.get('id', ''))))
        self.crit_table.setItem(row, 1, QTableWidgetItem(str(crit_data.get('name', ''))))
        self.crit_table.setItem(row, 2, QTableWidgetItem(str(crit_data.get('optimization_type', 'maximize'))))
        self.crit_table.setItem(row, 3, QTableWidgetItem(str(crit_data.get('weight', 1.0))))
        self.crit_table.setItem(row, 4, QTableWidgetItem(str(crit_data.get('unit', ''))))
    
    def edit_criterion(self):
        """Edit the selected criterion"""
        current_row = self.crit_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a criterion to edit")
            return
        
        crit_data = {
            'id': self.crit_table.item(current_row, 0).text(),
            'name': self.crit_table.item(current_row, 1).text(),
            'optimization_type': self.crit_table.item(current_row, 2).text(),
            'weight': float(self.crit_table.item(current_row, 3).text()),
            'unit': self.crit_table.item(current_row, 4).text() if self.crit_table.item(current_row, 4) else ''
        }
        
        dialog = CriteriaDialog(self, crit_data)
        if dialog.exec_():
            new_data = dialog.get_data()
            
            # Update table
            self.crit_table.setItem(current_row, 1, QTableWidgetItem(new_data['name']))
            self.crit_table.setItem(current_row, 2, QTableWidgetItem(new_data['optimization_type']))
            self.crit_table.setItem(current_row, 3, QTableWidgetItem(str(new_data['weight'])))
            self.crit_table.setItem(current_row, 4, QTableWidgetItem(new_data['unit']))
    
    def remove_criterion(self):
        """Remove the selected criterion"""
        current_row = self.crit_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a criterion to remove")
            return
        
        crit_id = self.crit_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     f"Are you sure you want to delete criterion '{crit_id}'?", 
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.crit_table.removeRow(current_row)
    
    def get_table_alternatives(self):
        """Get all alternatives from the table"""
        alternatives = []
        for row in range(self.alt_table.rowCount()):
            alt_data = {
                'id': self.alt_table.item(row, 0).text().strip(),
                'name': self.alt_table.item(row, 1).text().strip(),
                'description': self.alt_table.item(row, 2).text().strip() if self.alt_table.item(row, 2) else ''
            }
            if alt_data['id'] and alt_data['name']:  # Only add if has required fields
                alternatives.append(alt_data)
        return alternatives
    
    def get_table_criteria(self):
        """Get all criteria from the table"""
        criteria = []
        for row in range(self.crit_table.rowCount()):
            try:
                crit_data = {
                    'id': self.crit_table.item(row, 0).text().strip(),
                    'name': self.crit_table.item(row, 1).text().strip(),
                    'optimization_type': self.crit_table.item(row, 2).text().strip(),
                    'weight': float(self.crit_table.item(row, 3).text()),
                    'unit': self.crit_table.item(row, 4).text().strip() if self.crit_table.item(row, 4) else ''
                }
                if crit_data['id'] and crit_data['name']:  # Only add if has required fields
                    criteria.append(crit_data)
            except (ValueError, AttributeError):
                continue  # Skip invalid rows
        return criteria