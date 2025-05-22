from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QTableWidget, QTableWidgetItem, QPushButton, 
                           QDialogButtonBox, QLineEdit, QLabel, QHeaderView,
                           QMessageBox, QAbstractItemView)
from PyQt5.QtCore import Qt
from datetime import datetime

class ProjectListDialog(QDialog):
    def __init__(self, project_controller, parent=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.selected_project_id = None
        self.projects_data = []
        self.init_ui()
        self.load_projects()
    
    def init_ui(self):
        self.setWindowTitle("Open Project")
        self.setMinimumSize(800, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Search section
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by project name or description...")
        self.search_edit.textChanged.connect(self.filter_projects)
        search_layout.addWidget(self.search_edit)
        
        layout.addLayout(search_layout)
        
        # Projects table
        self.projects_table = QTableWidget(0, 5)
        self.projects_table.setHorizontalHeaderLabels([
            "Name", "Description", "Decision Maker", "Created", "Updated"
        ])
        
        # Configure table
        header = self.projects_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Name
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Description
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Decision Maker
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Created
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Updated
        
        self.projects_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.projects_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.projects_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Connect double-click to accept
        self.projects_table.itemDoubleClicked.connect(self.accept)
        
        layout.addWidget(self.projects_table)
        
        # Info label
        self.info_label = QLabel("Select a project and click Open, or double-click to open directly.")
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.info_label)
        
        # Buttons
        button_box = QDialogButtonBox()
        
        self.open_button = QPushButton("Open")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_box.addButton(self.open_button, QDialogButtonBox.AcceptRole)
        button_box.addButton(cancel_button, QDialogButtonBox.RejectRole)
        
        layout.addWidget(button_box)
        
        # Connect selection change
        self.projects_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def load_projects(self):
        """Load all projects from the backend"""
        try:
            self.projects_data = self.project_controller.get_all_projects()
            self.populate_table(self.projects_data)
            
            if not self.projects_data:
                self.info_label.setText("No projects found. Create a new project first.")
                self.info_label.setStyleSheet("color: #ff6b35; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load projects: {str(e)}")
            self.info_label.setText("Error loading projects.")
            self.info_label.setStyleSheet("color: red; font-weight: bold;")
    
    def populate_table(self, projects):
        """Populate the table with project data"""
        self.projects_table.setRowCount(len(projects))
        
        for row, project in enumerate(projects):
            # Name
            name_item = QTableWidgetItem(project.get('name', 'Unnamed Project'))
            name_item.setData(Qt.UserRole, project.get('id'))  # Store ID in item
            self.projects_table.setItem(row, 0, name_item)
            
            # Description
            description = project.get('description', '')
            if len(description) > 50:
                description = description[:47] + "..."
            self.projects_table.setItem(row, 1, QTableWidgetItem(description))
            
            # Decision Maker
            decision_maker = project.get('decision_maker', '')
            self.projects_table.setItem(row, 2, QTableWidgetItem(decision_maker))
            
            # Created Date
            created_at = project.get('created_at', '')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    created_str = created_at[:16] if len(created_at) > 16 else created_at
            else:
                created_str = 'Unknown'
            self.projects_table.setItem(row, 3, QTableWidgetItem(created_str))
            
            # Updated Date
            updated_at = project.get('updated_at', '')
            if updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    updated_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    updated_str = updated_at[:16] if len(updated_at) > 16 else updated_at
            else:
                updated_str = 'Unknown'
            self.projects_table.setItem(row, 4, QTableWidgetItem(updated_str))
    
    def filter_projects(self):
        """Filter projects based on search text"""
        search_text = self.search_edit.text().lower()
        
        if not search_text:
            # Show all projects
            filtered_projects = self.projects_data
        else:
            # Filter projects
            filtered_projects = []
            for project in self.projects_data:
                name = project.get('name', '').lower()
                description = project.get('description', '').lower()
                decision_maker = project.get('decision_maker', '').lower()
                
                if (search_text in name or 
                    search_text in description or 
                    search_text in decision_maker):
                    filtered_projects.append(project)
        
        self.populate_table(filtered_projects)
        
        # Update info
        if not filtered_projects and search_text:
            self.info_label.setText(f"No projects found matching '{search_text}'")
            self.info_label.setStyleSheet("color: #ff6b35;")
        else:
            self.info_label.setText("Select a project and click Open, or double-click to open directly.")
            self.info_label.setStyleSheet("color: #666; font-style: italic;")
    
    def on_selection_changed(self):
        """Handle selection change in the table"""
        selected_rows = self.projects_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            name_item = self.projects_table.item(row, 0)
            if name_item:
                self.selected_project_id = name_item.data(Qt.UserRole)
                self.open_button.setEnabled(True)
                
                # Update info with project details
                project_name = name_item.text()
                self.info_label.setText(f"Selected: {project_name}")
                self.info_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            self.selected_project_id = None
            self.open_button.setEnabled(False)
            self.info_label.setText("Select a project and click Open, or double-click to open directly.")
            self.info_label.setStyleSheet("color: #666; font-style: italic;")
    
    def get_selected_project_id(self):
        """Return the selected project ID"""
        return self.selected_project_id