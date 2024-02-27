import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget, QPushButton, QFileDialog, QTabWidget
from PyQt5.QtCore import Qt, QAbstractTableModel, QThread, pyqtSignal, QModelIndex
import pandas as pd
from queue import Queue

class CSVTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or pd.DataFrame()

    def appendData(self, data):
        start_index = self.rowCount()
        end_index = start_index + len(data) - 1
        self.beginInsertRows(QModelIndex(), start_index, end_index)
        self._data = pd.concat([self._data, data], ignore_index=True)
        self.endInsertRows()
        self.layoutChanged.emit()

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value) if not pd.isnull(value) else ""
        return None

    def rowCount(self, parent=QModelIndex()):
        return self._data.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self._data.shape[1]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(section + 1)
        return None


class Worker(QThread):
    dataLoaded = pyqtSignal(pd.DataFrame)
    finished = pyqtSignal()

    def __init__(self, file_path, chunk_size=1000, chunk_threshold=10*1024*1024):  # Default chunk threshold: 10 MB
        super().__init__()
        self.file_path = file_path
        self.chunk_size = max(1, chunk_size)  # Ensure chunk_size is at least 1
        self.chunk_threshold = chunk_threshold

    def run(self):
        try:
            file_size = os.path.getsize(self.file_path)
            if file_size > self.chunk_threshold:
                for chunk in pd.read_csv(self.file_path, chunksize=self.chunk_size):
                    self.dataLoaded.emit(chunk)
                    self.msleep(100)  # Sleep for 100 milliseconds
            else:
                data = pd.read_csv(self.file_path)
                self.dataLoaded.emit(data)
        except Exception as e:
            print("Error:", e)
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.worker_threads = []

    def initUI(self):
        self.setWindowTitle("CSV Loader")

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.load_button = QPushButton("Load CSV")
        self.load_button.clicked.connect(self.load_csv)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.load_button)
        self.layout.addWidget(self.tab_widget)

        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

    def load_csv(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        files, _ = file_dialog.getOpenFileNames(self, "Select CSV Files")

        if files:
            for file_path in files:
                self.load_csv_file(file_path)

    def load_csv_file(self, file_path):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        table_view = QTableView()
        layout.addWidget(table_view)
        tab.setLayout(layout)

        model = CSVTableModel()
        table_view.setModel(model)

        worker = Worker(file_path)
        worker.dataLoaded.connect(model.appendData)
        worker.finished.connect(lambda: self.on_worker_finished(worker))
        worker.start()

        tab_name = f"CSV {self.tab_widget.count() + 1}"
        self.tab_widget.addTab(tab, tab_name)

        self.worker_threads.append(worker)

    def on_worker_finished(self, worker):
        if worker in self.worker_threads:
            worker.finished.disconnect()
            self.worker_threads.remove(worker)
            worker.deleteLater()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec_())
