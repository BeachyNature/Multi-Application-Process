import sys
import os
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QWidget, QComboBox, QLabel, QPushButton

import multiple_plots

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

        # Adding label and combo box widgets to the label_combo_layout
        label_combo_layout.addWidget(plot_label)
        label_combo_layout.addWidget(self.pkl_files_combo)

        # Adding the label_combo_layout and start_button to the main_layout
        main_layout.addLayout(label_combo_layout)
        main_layout.addWidget(start_button)
        self.setLayout(main_layout)

        self.setGeometry(400, 100, 400, 500)
        self.setWindowTitle('Plot Runner')

        # Initial population of the QComboBox
        self.show_directory_menu()

    def show_directory_menu(self):
        # Get a list of all CSV files in the selected root path
        pkl_files = [file for file in os.listdir(self.folder_path) if file.endswith(".pkl")]

        # Insert an empty string at the beginning of the list
        pkl_files.insert(0, "")

        # Populate the QComboBox with CSV files
        self.pkl_files_combo.clear()
        self.pkl_files_combo.addItems(pkl_files)

    """
    Run the plot runner
    """
    def run_plots(self):
        self.epic = multiple_plots.StaticPlots(self.pkl_files_combo.currentText())
        self.epic.show()
            
