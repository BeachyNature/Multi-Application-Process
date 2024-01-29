import sys
import os
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QComboBox, QLabel, QPushButton

import multiple_plots


"""
Plot interactor that can toggle, and save different plot runs
"""
class PlotMenu(QWidget):
    def __init__(self):
        super().__init__()

        user_path = os.path.expanduser("~")
        self.folder_path = os.path.join(user_path, "MAPS-Python/Saved Plots")
        
        self.initUI()

    def initUI(self):

        # Layout setup
        main_layout = QVBoxLayout()
        label_combo_layout = QHBoxLayout()

        # Widget Setups
        plot_label = QLabel("Selected saved plots: ")
        self.pkl_files_combo = QComboBox(self)
        start_button = QPushButton("Run Plots")
        start_button.clicked.connect(self.run_plots)
        remove_pkl_btn = QPushButton('X')
        remove_pkl_btn.clicked.connect(self.remove_save_file)

        # Adding label and combo box widgets to the label_combo_layout
        label_combo_layout.addWidget(plot_label)
        label_combo_layout.addWidget(self.pkl_files_combo)
        label_combo_layout.addWidget(remove_pkl_btn)

        # Adding the label_combo_layout and start_button to the main_layout
        main_layout.addLayout(label_combo_layout)
        main_layout.addWidget(start_button)
        self.setLayout(main_layout)

        self.setGeometry(400, 100, 400, 500)
        self.setWindowTitle('Plot Runner')

        # Initial population of the QComboBox
        self.show_directory_menu()


    """
    Get all the pkl files in the user directory
    """
    def show_directory_menu(self):
        # Get a list of all CSV files in the selected root path
        pkl_files = [file for file in os.listdir(self.folder_path) if file.endswith(".pkl")]

        # Insert an empty string at the beginning of the list
        pkl_files.insert(0, "")

        # Populate the QComboBox with CSV files
        self.pkl_files_combo.clear()
        self.pkl_files_combo.addItems(pkl_files)


    """
    Remove the saved file from the combobox and directory
    """
    def remove_save_file(self):
        try:
            index = self.pkl_files_combo.currentIndex()
            remove_path = os.path.join(self.folder_path, self.pkl_files_combo.currentText())
            self.pkl_files_combo.removeItem(index)
            os.remove(remove_path)
            print(f"{remove_path} removed!")
        except Exception:
            print("Unable to delete file, may need to manual remove.")


    """
    Run the plot runner
    """
    def run_plots(self):
        self.epic = multiple_plots.StaticPlots(self.pkl_files_combo.currentText(), self.folder_path)
        self.epic.show()
