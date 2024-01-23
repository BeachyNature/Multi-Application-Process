import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import qabstractionmodel


"""
Dialog window that appears for the user to select options on what csvs they want to load
"""
class FileDialog(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._bool = False
        self.init_ui()
    

    """
    Initalizes the main running UI for Dialog Window
    """
    def init_ui(self):
        layout = QVBoxLayout()

        btn_open_dialog = QPushButton('Open File Dialog', self)
        btn_open_dialog.clicked.connect(self.show_file_dialog)

        check_button = QCheckBox("Run all csvs in directory")
        check_button.toggled.connect(self.run_all_csv)

        layout.addWidget(btn_open_dialog)
        layout.addWidget(check_button)

        self.setLayout(layout)
        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('CSV Loader')
    

    """
    Show the file dialog window that allows the user to select what csvs they want to load
    """
    def show_file_dialog(self):
        self.dict = {}
        file_dialog = QFileDialog()
        self.tab_widget = QTabWidget()

        if not self._bool:
            # Configure the file dialog window
            file_dialog.setDirectory('/Users/tycon/Desktop/Test CSVS')
            file_dialog.setFileMode(QFileDialog.ExistingFiles)
            file_dialog.setNameFilter("CSV files (*.csv)")
            selected_files, _ = file_dialog.getOpenFileNames(self, 'Select CSVs', '')

            # Check if user selected a csv, then convert to dataframe
            if selected_files:
                for idx, file_path in enumerate (selected_files):
                    file_name = os.path.basename(file_path)
                    csv_name = file_name.rstrip('.csv')
                    self.process_csvs(file_path, csv_name, idx)
        
        elif self._bool: # Select a directory to process all CSV's inside
            directory = QFileDialog.getExistingDirectory(None, "Select a directory", ".", QFileDialog.ShowDirsOnly)
    
            if directory:
                for idx, csv_name in  enumerate (os.listdir(directory)):
                    if csv_name.endswith(".csv"):
                        file_path = os.path.join(directory, csv_name)
                        self.process_csvs(file_path, csv_name, idx)
        
        # Run the QAbstractionTable with the loaded CSVs
        self.table_model = qabstractionmodel.DataFrameViewer(self.dict)
        self.table_model.show()

        # TEST for comment documentation
        # print(self.create_table.__doc__)


    """
    Processes the CSVS into dataframes
    """
    def process_csvs(self, file_path, csv_name, idx):
        try:
            df = pd.read_csv(file_path)
            print(f"Processing {file_path}:")
        except UnicodeDecodeError:
            df = pd.DataFrame()
            print(f"Error decoding file {file_path}. File Empty.")
        except Exception as e:
            print(f"An error occurred while processing {file_path}: {e}")
        self.create_table(df, csv_name, idx)


    """
    Load the dataframes into seperate table that creates tabs for each item
    """
    def create_table(self, df, csv_name, idx):
        self.dict[csv_name] = df  


    """
    Run the main dialog window
    """
    def run_dialog(self):
        dialog = QDialog()
        dialog.setLayout(self.layout)
        dialog.exec()

    """
    If the user has the run all checkbox selected, it will process all CSVS found in a folder
    """
    def run_all_csv(self, checked):
        self._bool = checked


# THIS IS FOR TESTING
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = FileDialog()
#     ex.show()
#     sys.exit(app.exec_())

