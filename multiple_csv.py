import os
import sys
import polars as pl
from sqlalchemy import create_engine, MetaData
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QCheckBox, QProgressBar,\
                            QLabel, QFileDialog, QApplication, QWidget, QTabWidget

# Local import
import qabstractionmodel

class FileDialog(QWidget):
    """
    Dialog window that appears for the user to select options on what csvs they want to load
    """
    def __init__(self, parent = None):
        super().__init__(parent)
        self._bool = False
        self.init_ui()
    
    def init_ui(self) -> None:
        """
        Initalizes the main running UI for Dialog Window
        """
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
        return
    
    def show_file_dialog(self) -> None:
        """
        Show the file dialog window that allows the user to select what csvs they want to load
        """
        self.dict = {}
        self.single_file() if not self._bool else self.multi_file()

        self.table_model = qabstractionmodel.DataFrameViewer(self.dict)
        self.table_model.show()
        return

    def single_file(self) -> None:
        """
        Process individual files that the user selects
        """
        file_dialog = QFileDialog()
        self.tab_widget = QTabWidget()
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
        return

    def multi_file(self) -> None:
        """
        Process multiple CSV files at once
        """
        directory = QFileDialog.getExistingDirectory(None, "Select a directory", ".", QFileDialog.ShowDirsOnly)

        if directory:
            csv_files = [file for file in os.listdir(directory) if file.endswith(".csv")]
            total_files = len(csv_files)

            for idx, csv_name in  enumerate (csv_files):
                if csv_name.endswith(".csv"):
                    file_path = os.path.join(directory, csv_name)
                    self.process_csvs(file_path, csv_name)
                    self.progress_status(idx, total_files)
        return

    def process_csvs(self, file_path, csv_name) -> None:
        """
        Processes the CSVS into dataframes
        """
        self.progress_bar.setVisible(True)

        try:
            data = pl.scan_csv(file_path).collect()
            df = self.add_index(data)
            self.label.setText(f"Processing {file_path}")
        except UnicodeDecodeError:
            df = pl.DataFrame()
            self.label.setText(f"Error decoding file {file_path}.")
        except Exception as e:
            df = pl.DataFrame()
            self.label.setText(f"An error occurred while processing {file_path}: {e}")
        self.create_table(df, csv_name)
        return

    def process_db(self, file_path):
        """
        Process SQL Lite database files
        """
        engine = create_engine(f"sqlite:///{file_path}")
        metadata = MetaData()
        metadata.reflect(bind=engine)

        # Extract table names
        table_names = metadata.tables.keys()
        for table_name in table_names:
            data = pl.read_database(
                query=f"SELECT * FROM {table_name}",
                connection=engine
            )

            df = self.add_index(data)
            self.create_table(df, table_name)
        return

    def create_table(self, df, csv_name) -> None:
        """
        Load the dataframes into seperate table that creates tabs for each item
        """
        self.dict[csv_name] = df
        return

    def run_all_csv(self, checked):
        """
        If the user has the run all checkbox selected, it will process all CSVS found in a folder
        """
        self._bool = checked
        return

    def progress_status(self, idx, total_files):
        """
        Set the status of the progress bar
        """
        progress_value = int((idx + 1) / total_files * 100)
        self.progress_bar.setValue(progress_value)
        return

    def add_index(self, data) -> pl.DataFrame:
        """
        Add index column if it does not exist
        """
        if 'Index' not in data.columns:
            df = pl.DataFrame({'Index': range(data.height)}).hstack(data)
            return df
        return data
    
# THIS IS FOR TESTING
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileDialog()
    ex.show()
    sys.exit(app.exec_())
