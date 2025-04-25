import os
import sys
from PyQt5.QtWidgets import QApplication
from views.main_window import MCDMApplication

# Añadir el directorio raíz del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    app = QApplication(sys.argv)
    window = MCDMApplication()
    window.show()
    sys.exit(app.exec_())

    print("Starting MCDM Application...")
if __name__ == "__main__":
    main()