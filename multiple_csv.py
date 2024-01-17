import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import load_tables

class FileDialog(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._bool = False
        self.init_ui()

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

    def show_file_dialog(self):

        file_dialog = QFileDialog()
        self.tab_widget = QTabWidget()

        if not self._bool:
            file_dialog.setDirectory('/Users/tycon/Desktop/Test CSVS')

            # Set the dialog mode to open multiple files
            file_dialog.setFileMode(QFileDialog.ExistingFiles)

            # Set the file filter to show only CSV files
            file_dialog.setNameFilter("CSV files (*.csv)")

            # Show the dialog and get the selected file paths
            selected_files, _ = file_dialog.getOpenFileNames(self, 'Select EPs', '')

            # Check if user selected a csv, then convert to dataframe
            if selected_files:
                for idx, file_path in enumerate (selected_files):
                    file_name = os.path.basename(file_path)
                    csv_name = file_name.rstrip('.csv')
                    self.process_csvs(file_path, csv_name, idx)
        
        elif self._bool: # Select a directory to process all CSV's inside
            directory = QFileDialog.getExistingDirectory(None, "Select a directory", ".", QFileDialog.ShowDirsOnly)

            if directory:
                # Iterate through all files in the selected directory
                for idx, csv_name in  enumerate (os.listdir(directory)):
                    if csv_name.endswith(".csv"):
                        file_path = os.path.join(directory, csv_name)
                        self.process_csvs(file_path, csv_name, idx)
        
        # Run the QAbstractionTable
        self.run_dialog()

        # TEST
        # print(self.create_table.__doc__)

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
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tab_widget)

        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        self.tab_widget.addTab(tab, csv_name)

        # Make tabs red when empty
        if df.empty:
            self.tab_widget.tabBar().setTabTextColor(idx, QColor(253, 27, 27))

        # Need to make table model, different file to load in each dataframe
        load_tables.DataTables(df, csv_name, tab_layout)

    def run_dialog(self):
        dialog = QDialog()
        dialog.setLayout(self.layout)
        dialog.exec()

    def run_all_csv(self, checked):
        self._bool = checked

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = FileDialogExample()
#     ex.show()
#     sys.exit(app.exec_())

