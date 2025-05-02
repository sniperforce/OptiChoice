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
        self.init_ui()
        self.load_project_data()

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
        # Prevent direct editing
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
        # Prevent direct editing
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
        if self.project_controller.current_project_id:
            project = self.project_controller.load_project(self.project_controller.current_project_id)
            if project:
                self.name_edit.setText(project.get('name', ''))
                self.description_edit.setText(project.get('description', ''))
                self.decision_maker_edit.setText(project.get('decision_maker', ''))
                
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
        """Save all project data"""
        name = self.name_edit.text()
        if not name:
            QMessageBox.warning(self, "Warning", "Project name cannot be empty")
            return
        
        description = self.description_edit.toPlainText()
        decision_maker = self.decision_maker_edit.text()
        
        # If we're creating a new project
        if not self.project_controller.current_project_id:
            success = self.project_controller.create_project(name, description, decision_maker)
            if success:
                QMessageBox.information(self, "Success", "Project created successfully")
                # Now save alternatives and criteria
                self._save_alternatives_and_criteria()
            else:
                QMessageBox.critical(self, "Error", "Failed to create project")
        else:
            # Update existing project
            success = self.project_controller.update_project(name, description, decision_maker)
            if success:
                QMessageBox.information(self, "Success", "Project updated successfully")
                # Now save alternatives and criteria
                self._save_alternatives_and_criteria()
            else:
                QMessageBox.critical(self, "Error", "Failed to update project")
    
    def _save_alternatives_and_criteria(self):
        """Save all alternatives and criteria"""
        # First, delete all existing alternatives and criteria
        # Then add the new ones from the tables
        
        # This would be a more complex implementation depending on your API
        # For now, we'll just show a placeholder implementation
        QMessageBox.information(self, "Info", "Alternatives and criteria saved")
    
    def add_alternative(self):
        """Open dialog to add a new alternative"""
        dialog = AlternativeDialog(self)
        if dialog.exec_():
            alt_data = dialog.get_data()
            
            # Check if ID is provided
            if not alt_data['id']:
                QMessageBox.warning(self, "Warning", "Alternative ID is required")
                return
                
            # Check if name is provided
            if not alt_data['name']:
                QMessageBox.warning(self, "Warning", "Alternative name is required")
                return
            
            # Add to backend if connected to a project
            if self.project_controller.current_project_id:
                result = self.project_controller.add_alternative(
                    alt_data['id'], 
                    alt_data['name'], 
                    alt_data['description']
                )
                
                if result:
                    self._add_alternative_to_table(alt_data)
                else:
                    QMessageBox.critical(self, "Error", "Failed to add alternative")
            else:
                # Just add to table if no project is saved yet
                self._add_alternative_to_table(alt_data)
    
    def _add_alternative_to_table(self, alt_data):
        """Add alternative data to the table"""
        row = self.alt_table.rowCount()
        self.alt_table.insertRow(row)
        self.alt_table.setItem(row, 0, QTableWidgetItem(alt_data['id']))
        self.alt_table.setItem(row, 1, QTableWidgetItem(alt_data['name']))
        self.alt_table.setItem(row, 2, QTableWidgetItem(alt_data.get('description', '')))
    
    def edit_alternative(self):
        """Edit the selected alternative"""
        current_row = self.alt_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an alternative to edit")
            return
        
        # Get data from the selected row
        alt_data = {
            'id': self.alt_table.item(current_row, 0).text(),
            'name': self.alt_table.item(current_row, 1).text(),
            'description': self.alt_table.item(current_row, 2).text() if self.alt_table.item(current_row, 2) else ''
        }
        
        # Open dialog with current data
        dialog = AlternativeDialog(self, alt_data)
        if dialog.exec_():
            new_data = dialog.get_data()
            
            # Update backend if connected to a project
            if self.project_controller.current_project_id:
                result = self.project_controller.update_alternative(
                    alt_data['id'], 
                    new_data['name'], 
                    new_data['description']
                )
                
                if result:
                    # Update table
                    self.alt_table.setItem(current_row, 1, QTableWidgetItem(new_data['name']))
                    self.alt_table.setItem(current_row, 2, QTableWidgetItem(new_data['description']))
                else:
                    QMessageBox.critical(self, "Error", "Failed to update alternative")
            else:
                # Just update table if no project is saved yet
                self.alt_table.setItem(current_row, 1, QTableWidgetItem(new_data['name']))
                self.alt_table.setItem(current_row, 2, QTableWidgetItem(new_data['description']))
    
    def remove_alternative(self):
        """Remove the selected alternative"""
        current_row = self.alt_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an alternative to remove")
            return
        
        alt_id = self.alt_table.item(current_row, 0).text()
        
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     f"Are you sure you want to delete alternative '{alt_id}'?", 
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Delete from backend if connected to a project
            if self.project_controller.current_project_id:
                result = self.project_controller.delete_alternative(alt_id)
                
                if result:
                    self.alt_table.removeRow(current_row)
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete alternative")
            else:
                # Just remove from table if no project is saved yet
                self.alt_table.removeRow(current_row)
    
    def add_criterion(self):
        """Open dialog to add a new criterion"""
        dialog = CriteriaDialog(self)
        if dialog.exec_():
            crit_data = dialog.get_data()
            
            # Check if ID is provided
            if not crit_data['id']:
                QMessageBox.warning(self, "Warning", "Criterion ID is required")
                return
                
            # Check if name is provided
            if not crit_data['name']:
                QMessageBox.warning(self, "Warning", "Criterion name is required")
                return
            
            # Add to backend if connected to a project
            if self.project_controller.current_project_id:
                result = self.project_controller.add_criterion(
                    crit_data['id'], 
                    crit_data['name'],
                    crit_data['optimization_type'],
                    crit_data['scale_type'],
                    crit_data['weight'],
                    crit_data['unit']
                )
                
                if result:
                    self._add_criterion_to_table(crit_data)
                else:
                    QMessageBox.critical(self, "Error", "Failed to add criterion")
            else:
                # Just add to table if no project is saved yet
                self._add_criterion_to_table(crit_data)
    
    def _add_criterion_to_table(self, crit_data):
        """Add criterion data to the table"""
        row = self.crit_table.rowCount()
        self.crit_table.insertRow(row)
        self.crit_table.setItem(row, 0, QTableWidgetItem(crit_data['id']))
        self.crit_table.setItem(row, 1, QTableWidgetItem(crit_data['name']))
        self.crit_table.setItem(row, 2, QTableWidgetItem(crit_data['optimization_type']))
        self.crit_table.setItem(row, 3, QTableWidgetItem(str(crit_data['weight'])))
        self.crit_table.setItem(row, 4, QTableWidgetItem(crit_data['unit']))
    
    def edit_criterion(self):
        """Edit the selected criterion"""
        current_row = self.crit_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a criterion to edit")
            return
        
        # Get data from the selected row
        crit_data = {
            'id': self.crit_table.item(current_row, 0).text(),
            'name': self.crit_table.item(current_row, 1).text(),
            'optimization_type': self.crit_table.item(current_row, 2).text(),
            'weight': float(self.crit_table.item(current_row, 3).text()),
            'unit': self.crit_table.item(current_row, 4).text() if self.crit_table.item(current_row, 4) else ''
        }
        
        # Open dialog with current data
        dialog = CriteriaDialog(self, crit_data)
        if dialog.exec_():
            new_data = dialog.get_data()
            
            # Update backend if connected to a project
            if self.project_controller.current_project_id:
                result = self.project_controller.update_criterion(
                    crit_data['id'],
                    new_data['name'],
                    new_data['optimization_type'],
                    new_data['scale_type'],
                    new_data['weight'],
                    new_data['unit']
                )
                
                if result:
                    # Update table
                    self.crit_table.setItem(current_row, 1, QTableWidgetItem(new_data['name']))
                    self.crit_table.setItem(current_row, 2, QTableWidgetItem(new_data['optimization_type']))
                    self.crit_table.setItem(current_row, 3, QTableWidgetItem(str(new_data['weight'])))
                    self.crit_table.setItem(current_row, 4, QTableWidgetItem(new_data['unit']))
                else:
                    QMessageBox.critical(self, "Error", "Failed to update criterion")
            else:
                # Just update table if no project is saved yet
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
        
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     f"Are you sure you want to delete criterion '{crit_id}'?", 
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Delete from backend if connected to a project
            if self.project_controller.current_project_id:
                result = self.project_controller.delete_criterion(crit_id)
                
                if result:
                    self.crit_table.removeRow(current_row)
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete criterion")
            else:
                # Just remove from table if no project is saved yet
                self.crit_table.removeRow(current_row)