import os
import sys
import polars as pl
from sqlalchemy import create_engine, MetaData
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QCheckBox, QProgressBar,\
                            QLabel, QFileDialog, QDialog, QApplication, QWidget, QTabWidget

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

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, 40, 200, 25)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

        self.label = QLabel()

        layout.addWidget(btn_open_dialog)
        layout.addWidget(check_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.label)

        self.setLayout(layout)
        self.setGeometry(500, 800, 800, 150)
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
            file_dialog.setFileMode(QFileDialog.ExistingFiles)
            file_dialog.setNameFilter("CSV files (*.csv); SQLite database files (*.db)")
    
            selected_files, _ = file_dialog.getOpenFileNames(self, 'Select Datafiles', '')
            total_files = len(selected_files)

            # Check if user selected a csv, then convert to dataframe
            if selected_files:
                for idx, file_path in enumerate (selected_files):
                    file_name = os.path.basename(file_path)
                    if file_name.endswith('.csv'):
                        csv_name = file_name.rstrip('.csv')
                        self.process_csvs(file_path, csv_name)
                    elif file_name.endswith('.db'):
                        self.process_db(file_path)
                    self.progress_status(idx, total_files)
        
        elif self._bool: # Select a directory to process all CSV's inside
            directory = QFileDialog.getExistingDirectory(None, "Select a directory", ".", QFileDialog.ShowDirsOnly)

            if directory:
                csv_files = [file for file in os.listdir(directory) if file.endswith(".csv")]
                total_files = len(csv_files)
    
                for idx, csv_name in  enumerate (csv_files):
                    if csv_name.endswith(".csv"):
                        file_path = os.path.join(directory, csv_name)
                        self.process_csvs(file_path, csv_name)
                        self.progress_status(idx, total_files)
        
        # Run the QAbstractionTable with the loaded CSVs
        self.table_model = qabstractionmodel.DataFrameViewer(self.dict)
        self.table_model.show()
        # print(self.create_table.__doc__)


    """
    Processes the CSVS into dataframes
    """
    def process_csvs(self, file_path, csv_name):
        # Make the progress bar visible
        self.progress_bar.setVisible(True)

        try:
            q = pl.scan_csv(file_path)
            data = q.collect()
            df = self.add_index(data)
            
            self.label.setText(f"Processing {file_path}")
    
        except UnicodeDecodeError:
            df = pl.DataFrame()
            self.label.setText(f"Error decoding file {file_path}.")
        except Exception as e:
            df = pl.DataFrame()
            self.label.setText(f"An error occurred while processing {file_path}: {e}")
        self.create_table(df, csv_name)


    """
    Process SQL Lite database files
    """
    def process_db(self, file_path):

        # Create a SQLAlchemy engine to connect to the SQLite database
        engine = create_engine(f"sqlite:///{file_path}")

        # Reflect database schema to MetaData
        metadata = MetaData()
        metadata.reflect(bind=engine)

        # Extract table names
        table_names = metadata.tables.keys()

        for table_name in table_names:
            data = pl.read_database(
                query=f"SELECT * FROM {table_name}",
                connection=engine
                # schema_overrides={"normalised_score": pl.UInt8},
            )

            df = self.add_index(data)
            self.create_table(df, table_name)


    """
    Load the dataframes into seperate table that creates tabs for each item
    """
    def create_table(self, df, csv_name):
        self.dict[csv_name] = df  


    """
    If the user has the run all checkbox selected, it will process all CSVS found in a folder
    """
    def run_all_csv(self, checked):
        self._bool = checked


    """
    Set the status of the progress bar
    """
    def progress_status(self, idx, total_files):
        progress_value = int((idx + 1) / total_files * 100)
        self.progress_bar.setValue(progress_value)

    
    """
    Add index column if it does not exist
    """
    def add_index(self, data) -> pl.DataFrame:
        if 'Index' not in data.columns:
            df = pl.DataFrame({'Index': range(data.height)}).hstack(data)
        else:
            return data
        return df

    
# THIS IS FOR TESTING
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileDialog()
    ex.show()
    sys.exit(app.exec_())

