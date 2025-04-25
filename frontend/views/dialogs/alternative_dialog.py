from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                           QLineEdit, QTextEdit, QPushButton,
                           QDialogButtonBox, QLabel)

class AlternativeDialog(QDialog):
    def __init__(self, parent=None, alternative=None):
        super().__init__(parent)
        self.alternative=alternative
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Alternative" if self.alternative else "New Alternative")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.id_edit = QLineEdit()
        if self.alternative:
            self.id_edit.setText(self.alternative.get('id',''))
            self.id_edit.setReadOnly(True)
        else:
            self.id_edit.setPlaceholderText("Enter alternative ID (e.g., A1)")
        form_layout.addRow("ID: ", self.id_edit)

        self.name_edit = QLineEdit()
        if self.alternative:
            self.name_edit.setText(self.alternative.get('name',''))
        else:
            self.name_edit.setPlaceholderText("Enter alternative name")
        form_layout.addRow("Name:", self.name_edit)

        self.description_edit = QTextEdit()
        if self.alternative:
            self.description_edit.setText(self.alternative.get('description', ''))
        else:
            self.description_edit.setPlaceholderText("Enter alternative description")
        form_layout.addRow("Description:", self.description_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self):
        return {
            'id': self.id_edit.text(),
            'name': self.name_edit.text(),
            'description': self.description_edit.toPlainText()
        }