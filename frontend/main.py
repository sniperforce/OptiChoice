import os
import sys
from PyQt5.QtWidgets import QApplication
from views.main_window import MCDMApplication

def main():
    app = QApplication(sys.argv)
    window = MCDMApplication()
    window.show()
    sys.exit(app.exec_())

    print("Starting MCDM Application...")
if __name__ == "__main__":
    main()