import sys
import pandas as pd
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableView, QCheckBox, QScrollArea, QTabWidget, QSplitter

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
    
    def get_dataframe(self):
        visible_columns = [col for col, checkbox in self.column_checkboxes.items() if checkbox.isChecked()]
        return pd.DataFrame(self.dataframe[visible_columns])


class ExpandableText(QWidget):
    def __init__(self, dataframe, csv_name, tab_widget, index, splitter, dict):
        super().__init__()

        self.is_expanded = False
        self.first_split = False
        self.dataframe = dataframe
        self.csv_name = csv_name
        self.tab_widget = tab_widget
        self.splitter = splitter
        self.dict = dict
        self.index = index

        self.column_checkboxes = self.create_column_checkboxes()

        if isinstance(self.index, int):
            self.setup_data()
        else:
            self.init_ui()

    def create_column_checkboxes(self):
        column_checkboxes = {}
        for column in self.dataframe.columns:
            checkbox = QCheckBox(column)
            checkbox.setChecked(True)
            checkbox.setVisible(self.is_expanded)
            checkbox.stateChanged.connect(self.setup_data)
            column_checkboxes[column] = checkbox
        return column_checkboxes

    def init_ui(self):

        # Layouts
        layout = QHBoxLayout()
        button_layout = QVBoxLayout()

        # Button setups
        self.check_button = QPushButton(self.csv_name + " +")
        if not self.dataframe.empty:
            self.check_button.setStyleSheet('border: none; color: black; font-size: 24px;')
        else:
            self.check_button.setStyleSheet('border: none; color: red; font-size: 24px;')

        self.check_button.clicked.connect(self.toggle_expansion)
        button_layout.addWidget(self.check_button, alignment=Qt.AlignTop)

        self.options_widget = QWidget()
        options_layout = QVBoxLayout(self.options_widget)
        for checkbox in self.column_checkboxes.values():
            options_layout.addWidget(checkbox)

        button_layout.addWidget(self.options_widget)
        layout.addLayout(button_layout)
        layout.addStretch()
        self.setLayout(layout)

    def toggle_expansion(self):
        self.is_expanded = not self.is_expanded
        self.check_button.setText(self.csv_name + " -" if self.is_expanded else  self.csv_name + " +")

        for i in range(self.options_widget.layout().count()):
            option_widget = self.options_widget.layout().itemAt(i).widget()
            option_widget.setVisible(self.is_expanded)

        self.setup_data()

    def load_more_data(self):
        tab = self.tab_widget.tab_dict[self.csv_name]
        model = tab.model()

        if tab.verticalScrollBar().value() == tab.verticalScrollBar().maximum():
            if len(self.dataframe) > 100:
                model.fetchMore()
                model.update_visible_rows()

    def setup_data(self):
        tab_name = self.csv_name
        if tab_name not in self.tab_widget.tab_dict:
            model = DataFrameTableModel(self.dataframe, self.column_checkboxes)
            table = QTableView()
            table.setModel(model)

            self.dict[table] = model

            self.tab_widget.addTab(table, self.csv_name)
            self.tab_widget.tab_dict[self.csv_name] = table

            # Initial split: add the new tab widget to the QSplitter
            if isinstance(self.index, int):
                if not self.first_split:
                    self.first_split = True
                    self.splitter.insertWidget(1, self.tab_widget)
                else:
                    # Subsequent double-taps: add the new tab widget to the initially split tab widget
                    self.splitter.widget(1).addTab(table, self.csv_name)
            
            for i, j in self.dict.items():
                i.verticalScrollBar().valueChanged.connect(self.load_more_data)
                self.check_status(j)

    def check_status(self, model):
        for checkbox in self.column_checkboxes.values():
            checkbox.stateChanged.connect(model.update_visible_columns)



class DataFrameViewer(QWidget):
    def __init__(self, data):
        super().__init__()
        self.incr = 0
        self.init_ui(data)

    def init_ui(self, data):
        
        # Setup Layouts
        self.main_layout = QVBoxLayout()
        labels_layout = QVBoxLayout()
        self.splitter = QSplitter(Qt.Horizontal)

        # Setup Widgets
        self.tab_widget = QTabWidget()
        scroll_widget = QWidget()
        scroll_area = QScrollArea()

        # Setup tab dictionary
        self.model_dict = {}
        self.tab_widget.tab_dict = {}

        # Run the data through the expanded text list
        for csv_name, df in data.items():
            text_widget = ExpandableText(df, csv_name, self.tab_widget, None, self.splitter, self.model_dict)
            labels_layout.addWidget(text_widget)

        # Configure layouts
        scroll_widget.setLayout(labels_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(scroll_area)
        self.splitter.addWidget(self.tab_widget)
        self.main_layout.addWidget(self.splitter)
        self.setLayout(self.main_layout)

        # Tab widget, double click to compare and able to be removed
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabBarDoubleClicked.connect(self.load_table_double_click)
    
    def get_current_tab_dataframe(self):
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            current_tab = self.tab_widget.widget(current_index)
            if isinstance(current_tab, QTableView):
                model = current_tab.model()
                if model:
                    return model.get_dataframe()
        return pd.DataFrame()  # Return an empty DataFrame if no data is available

    def load_table_double_click(self, index):

        # Remove the tab that you want to switch over
        if self.tab_widget.count() > 1:
            self.incr += 1
            tab_name = self.tab_widget.tabText(index)
            self.tab_widget.tab_dict.pop(tab_name)
            self.tab_widget.removeTab(index)

            # Create new tab
            new_tab_widget = QTabWidget()
            new_tab_widget.setTabsClosable(True)
            new_tab = tab_name + "-" + str(self.incr)
            new_tab_widget.tab_dict = {}
            dataframe = self.get_current_tab_dataframe()

            if new_tab_widget.count() == 0:
                new_tab_widget.tabCloseRequested.connect(self.tabCloseRequested)
                # dummy_widget = QWidget()
                # self.splitter.replaceWidget(new_tab_widget, dummy_widget)

            if not dataframe.empty:
                ExpandableText(dataframe, new_tab, new_tab_widget, index, self.splitter, self.model_dict)
            else:
                print("Cannot Compare, dataframe is empty!")

    def tabCloseRequested(self, index):
        if self.tab_widget.count() > 1:
            self.splitter.widget(1).setParent(None)