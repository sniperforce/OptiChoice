# frontend/views/dialogs/criteria_dialog.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                           QLineEdit, QComboBox, QDoubleSpinBox, 
                           QPushButton, QDialogButtonBox, QLabel)

class CriteriaDialog(QDialog):
    def __init__(self, parent=None, criterion=None):
        super().__init__(parent)
        self.criterion = criterion
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Criterion" if self.criterion else "New Criterion")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.id_edit = QLineEdit()
        if self.criterion:
            self.id_edit.setText(self.criterion.get('id',''))
            self.id_edit.setReadOnly(True)
        else:
            self.id_edit.setPlaceholderText("Enter criterion ID (e.g., C1)")
        form_layout.addRow("ID:", self.id_edit)

        self.name_edit = QLineEdit()
        if self.criterion:
            self.name_edit.setText(self.criterion.get('name',''))
        else:
            self.name_edit.setPlaceholderText("Enter criterion name")
        form_layout.addRow("Name:", self.name_edit)

        self.opt_type_combo = QComboBox()
        self.opt_type_combo.addItems(["maximize", "minimize"])
        if self.criterion:
            index = self.opt_type_combo.findText(self.criterion.get('optimization_type', 'maximize'))
            if index >= 0:
                self.opt_type_combo.setCurrentIndex(index)
        form_layout.addRow("Optimization Type:", self.opt_type_combo)

        self.scale_type_combo = QComboBox()
        self.scale_type_combo.addItems(['quantitative', 'qualitative', 'fuzzy'])
        if self.criterion:
            index = self.scale_type_combo.findText(self.criterion.get('scale_type','quantitative'))
            if index >= 0:
                self.scale_type_combo.setCurrentIndex(index)
        form_layout.addRow("Scale Type:", self.scale_type_combo)

        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0.01, 10.0)
        self.weight_spin.setSingleStep(0.1)
        self.weight_spin.setValue(self.criterion.get('weight', 1.0) if self.criterion else 1.0)
        form_layout.addRow("Weight:", self.weight_spin)

        self.unit_edit = QLineEdit()
        if self.criterion:
            self.unit_edit.setText(self.criterion.get('unit', ''))
        else:
            self.unit_edit.setPlaceholderText("Enter unit (e.g., $, kg, etc)")
        form_layout.addRow("Unit:", self.unit_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)  
        button_box.rejected.connect(self.reject) 
        layout.addWidget(button_box)
    
    def get_data(self):
        return{
            'id': self.id_edit.text(),
            'name': self.name_edit.text(),
            'optimization_type': self.opt_type_combo.currentText(),
            'scale_type': self.scale_type_combo.currentText(),
            'weight': self.weight_spin.value(),
            'unit': self.unit_edit.text()
        }