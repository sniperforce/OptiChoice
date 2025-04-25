from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLabel, QLineEdit, QTextEdit, QPushButton, 
                            QGroupBox, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt

class ProblemTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

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

        self.save_info_btn = QPushButton("Save")
        info_layout.addRow("", self.save_info_btn)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        #   Alternative section
        alt_group = QGroupBox("Alternatives")
        alt_layout = QVBoxLayout()

        self.alt_table = QTableWidget(0, 3)
        self.alt_table.setHorizontalHeaderLabels(["ID", "Name", "Description"])
        self.alt_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
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

        #   Criteria section
        crit_group = QGroupBox("Criteria")
        crit_layout = QVBoxLayout()

        self.crit_table = QTableWidget(0, 5)
        self.crit_table.setHorizontalHeaderLabels(["ID","Name","Type", "Weight", "Unit"])
        self.crit_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

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

        self.connect_signals()
    
    def connect_signals(self):
        self.save_info_btn.clicked.connect(self.save_project_info)
        self.add_alt_btn.clicked.connect(self.add_alternative)
        self.edit_alt_btn.clicked.connect(self.edit_alternative)
        self.remove_alt_btn.clicked.connect(self.remove_alternative)
        self.add_crit_btn.clicked.connect(self.add_criterion)
        self.edit_crit_btn.clicked.connect(self.edit_criterion)
        self.remove_crit_btn.clicked.connect(self.remove_criterion)
    
    def save_project_info(self):
        QMessageBox.information(self, "Info", "Project information saved successfully")
    
    def add_alternative(self):
        row = self.alt_table.rowCount()
        self.alt_table.insertRow(row)
        self.alt_table.setItem(row, 0, QTableWidgetItem(f"A{row+1}"))
        self.alt_table.setItem(row, 1, QTableWidgetItem(f"Alternative {row+1}"))
        self.alt_table.setItem(row, 2, QTableWidgetItem(""))
    
    def edit_alternative(self):
        current_row = self.alt_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select an alternative to edit")
        else:
            QMessageBox.information(self, "Info", f"Editing Alternative {current_row+1}")
    
    def remove_alternative(self):
        current_row = self.alt_table.currentRow()
        if current_row >= 0:
            self.alt_table.removeRow(current_row)
        else:
            QMessageBox.warning(self, "Warning", "Please select an alternative to remove")
    
    def add_criterion(self):
        row = self.crit_table.rowCount()
        self.crit_table.insertRow(row)
        self.crit_table.setItem(row, 0, QTableWidgetItem(f"C{row+1}"))
        self.crit_table.setItem(row, 1, QTableWidgetItem(f"Criterion {row+1}"))
        self.crit_table.setItem(row, 2, QTableWidgetItem("Maximize"))
        self.crit_table.setItem(row, 3, QTableWidgetItem("1.0"))
        self.crit_table.setItem(row, 4, QTableWidgetItem(""))
    
    def edit_criterion(self):
        current_row = self.crit_table.currentRow()
        if current_row >= 0:
            QMessageBox.information(self, "Info", f"Editing criterion {current_row+1}")
        else:
            QMessageBox.warning(self, "Warning", "Please select a criterion to edit")
        
    def remove_criterion(self):
        current_row = self.crit_table.currentRow()
        if current_row >= 0:
            self.crit_table.removeRow(current_row)
        else:
            QMessageBox.warning(self, "Warning", "Please select a criterion to remove")
