from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class CustomTableModel(QAbstractTableModel):
    def __init__(self, dataframe):
        super().__init__()
        self.data = dataframe

    def rowCount(self, index):
        return self.data.shape[0]

    def columnCount(self, index):
        return self.data.shape[1]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return str(self.data.iat[index.row(), index.column()])
        return None

class DataTables(QAbstractItemView):
    def __init__(self, df, csv_name, tab_layout):
        super().__init__()

        # Tableview
        table_view = QTableView(self)
        table_view.setSelectionMode(QAbstractItemView.MultiSelection)
        table_model = CustomTableModel(df)
        table_view.setModel(table_model)
        tab_layout.addWidget(table_view)

    def update_search_text(self, text):
        self.table_model.update_search_text(text)

