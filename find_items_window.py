from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QTreeView, QMainWindow, QVBoxLayout, QWidget
import sys
import pandas as pd

class MyModel(QAbstractItemModel):
    dataChanged = pyqtSignal(QModelIndex, QModelIndex)

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        return str(self._data.iloc[index.row(), index.column()])

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._data.columns[section])
        elif orientation == Qt.Vertical:
            return str(section + 1)

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        return self.createIndex(row, column)

    def parent(self, index):
        return QModelIndex()  # This model is flat, so there are no parent indices

    def updateModel(self, data):
        rows = len(self._data)
        self.beginInsertRows(QModelIndex(), rows, rows + len(data) - 1)
        self._data = pd.concat([self._data, data])
        self.endInsertRows()

        self.dataChanged.emit(self.index(0, 0), self.index(rows + len(data) - 1, len(self._data.columns)))

class FindItemsWindow(QMainWindow):
    def __init__(self, data):
        super().__init__()

        # Initial empty data
        initial_data = {'Item': [], 'Value': []}
        self.model = MyModel(pd.DataFrame(initial_data), self)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.tree_view = QTreeView(self)
        self.layout.addWidget(self.tree_view)

        self.tree_view.setModel(self.model)

        self.updateModel(data)

    def updateModel(self, data):
        self.model.beginResetModel()
        self.model._data = data
        self.model.endResetModel()

