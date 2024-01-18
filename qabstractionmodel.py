import sys
import pandas as pd
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableView, QCheckBox, QScrollArea, QTabWidget

class DataFrameTableModel(QAbstractTableModel):
    def __init__(self, dataframe, column_checkboxes, parent=None):
        super(DataFrameTableModel, self).__init__(parent)
        self.dataframe = dataframe
        self.column_checkboxes = column_checkboxes
        self.visible_rows = 100
        self.update_visible_columns()

    def rowCount(self, parent=None):
        return min(self.visible_rows, len(self.dataframe))

    def update_visible_columns(self):
        self.visible_columns = [col for col, checkbox in self.column_checkboxes.items() if checkbox.isChecked()]
        self.layoutChanged.emit()

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            column_name = self.visible_columns[index.column()]
            return str(self.dataframe.iloc[index.row()][column_name])
        return None

    def columnCount(self, parent=None):
        return len(self.visible_columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self.visible_columns[section])
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None

    def update_visible_rows(self):
        self.visible_rows += 100
        self.visible_rows = min(self.visible_rows, len(self.dataframe))

    def fetch_more_data(self):
        # Implement fetching more data
        pass

    def canFetchMore(self, index):
        return self.visible_rows < len(self.dataframe)

    def fetchMore(self, index):
        remaining_rows = len(self.dataframe) - self.visible_rows
        rows_to_fetch = min(100, remaining_rows)
        self.beginInsertRows(index, self.visible_rows, self.visible_rows + rows_to_fetch - 1)
        self.fetch_more_data()
        self.visible_rows += rows_to_fetch
        self.endInsertRows()

class ExpandableText(QWidget):
    def __init__(self, dataframe, csv_name, tab_widget):
        super().__init__()

        self.is_expanded = False
        self.dataframe = dataframe
        self.csv_name = csv_name
        self.tab_widget = tab_widget
        self.column_checkboxes = self.create_column_checkboxes()

        self.init_ui()

    def create_column_checkboxes(self):
        column_checkboxes = {}
        for column in self.dataframe.columns:
            checkbox = QCheckBox(column)
            checkbox.setChecked(True)
            checkbox.setVisible(self.is_expanded)
            checkbox.stateChanged.connect(self.update_table_content)
            column_checkboxes[column] = checkbox
        return column_checkboxes

    def init_ui(self):
        layout = QHBoxLayout()

        labels_layout = QVBoxLayout()
        label_text = f'<a href="#">{self.csv_name}</a>'
        self.label = QLabel(label_text)
        self.label.linkActivated.connect(self.toggle_expansion)
        labels_layout.addWidget(self.label, alignment=Qt.AlignTop)

        self.options_widget = QWidget()
        options_layout = QVBoxLayout(self.options_widget)
        for checkbox in self.column_checkboxes.values():
            options_layout.addWidget(checkbox)

        labels_layout.addWidget(self.options_widget)
        layout.addLayout(labels_layout)
        layout.addStretch()

        self.symbol_button = QPushButton("+")
        self.symbol_button.setFixedSize(20, 20)
        self.symbol_button.clicked.connect(self.toggle_expansion)
        layout.addWidget(self.symbol_button)

        self.setLayout(layout)

    def toggle_expansion(self):
        self.is_expanded = not self.is_expanded
        self.symbol_button.setText("-" if self.is_expanded else "+")

        for i in range(self.options_widget.layout().count()):
            option_widget = self.options_widget.layout().itemAt(i).widget()
            option_widget.setVisible(self.is_expanded)

        self.update_table_content()

    def update_table_content(self):
        tab_name = self.csv_name
        if tab_name not in self.tab_widget.tab_dict:
            model = DataFrameTableModel(self.dataframe, self.column_checkboxes)
            tab = QTableView()
            tab.setModel(model)
            self.tab_widget.addTab(tab, tab_name)
            self.tab_widget.tab_dict[tab_name] = tab

            tab.verticalScrollBar().valueChanged.connect(self.load_more_data)

            for checkbox in self.column_checkboxes.values():
                checkbox.stateChanged.connect(model.update_visible_columns)

    def load_more_data(self):
        tab = self.tab_widget.tab_dict[self.csv_name]
        model = tab.model()

        if tab.verticalScrollBar().value() == tab.verticalScrollBar().maximum():
            model.fetch_more_data()
            model.update_visible_rows()

class DataFrameViewer(QWidget):
    def __init__(self, data):
        super().__init__()

        self.init_ui(data)

    def init_ui(self, data):
        main_layout = QVBoxLayout()

        self.tab_widget = QTabWidget()
        self.tab_widget.tab_dict = {}

        scroll_area = QScrollArea()
        labels_layout = QVBoxLayout()

        for csv_name, df in data.items():
            text_widget = ExpandableText(df, csv_name, self.tab_widget)
            labels_layout.addWidget(text_widget)

        scroll_widget = QWidget()
        scroll_widget.setLayout(labels_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        main_layout.addWidget(scroll_area)
        main_layout.addWidget(self.tab_widget)

        self.setLayout(main_layout)
