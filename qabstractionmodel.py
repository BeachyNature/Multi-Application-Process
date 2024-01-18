import sys
import pandas as pd
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableView, QCheckBox, QScrollArea, QTabWidget, QAbstractSlider


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

    def canFetchMore(self, index):
        return self.visible_rows < len(self.dataframe)

    def fetchMore(self, index):
        remaining_rows = len(self.dataframe) - self.visible_rows
        rows_to_fetch = min(100, remaining_rows)
        self.beginInsertRows(index, self.visible_rows, self.visible_rows + rows_to_fetch - 1)
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

from PyQt5.QtWidgets import QTabWidget, QSplitter

class DataFrameViewer(QWidget):
    def __init__(self, data):
        super().__init__()

        self.init_ui(data)

    def init_ui(self, data):
        main_layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Horizontal)  # Use QSplitter to arrange tab widgets side by side

        self.tab_widget = QTabWidget()
        self.tab_widget.tab_dict = {}

        scroll_area = QScrollArea()
        labels_layout = QVBoxLayout()

        # df1 = pd.DataFrame({
        #     'A': range(1, 1001),
        #     'B': range(1001, 2001),
        #     'C': range(2001, 3001),
        #     'D': range(3001, 4001),
        #     'E': range(4001, 5001)
        # })
        # df1.name = 'Large DataFrame 1'

        # df2 = pd.DataFrame({
        #     'X': range(5001, 6001),
        #     'Y': range(6001, 7001),
        #     'Z': range(7001, 8001),
        #     'W': range(8001, 9001),
        #     'V': range(9001, 10001)
        # })
        # df2.name = 'Large DataFrame 2'

        for csv_name, df in data.items():
            text_widget = ExpandableText(df, csv_name, self.tab_widget)
            labels_layout.addWidget(text_widget)

        scroll_widget = QWidget()
        scroll_widget.setLayout(labels_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        main_layout.addWidget(scroll_area)

        self.splitter.addWidget(self.tab_widget)
        self.splitter.addWidget(QTabWidget())  # Initially add an empty tab widget
        main_layout.addWidget(self.splitter)

        self.setLayout(main_layout)

        self.tab_widget.tabBarDoubleClicked.connect(self.load_table_double_click)

    def load_table_double_click(self, index):
        tab_name = self.tab_widget.tabText(index)
        if tab_name in self.tab_widget.tab_dict:
            model = DataFrameTableModel(self.tab_widget.tab_dict[tab_name].model().dataframe,
                                        self.tab_widget.tab_dict[tab_name].model().column_checkboxes)
            tab = QTableView()
            tab.setModel(model)

            # Create a new tab widget and add the tab to it
            new_tab_widget = QTabWidget()
            new_tab_widget.addTab(tab, tab_name + "_Duplicate")

            # Get the index of the old tab widget
            old_tab_widget_index = self.splitter.indexOf(self.tab_widget)

            # Remove the tab from the old tab widget
            self.tab_widget.removeTab(index)

            # If there are no more tabs in the old tab widget, remove the old tab widget itself
            if self.tab_widget.count() == 0:
                self.splitter.removeWidget(self.tab_widget)

            # Add the new tab widget to the QSplitter at the same index as the old tab widget
            self.splitter.insertWidget(old_tab_widget_index, new_tab_widget)

