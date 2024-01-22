import sys
import pandas as pd
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,\
                            QTableView, QCheckBox, QScrollArea, QTabWidget, QSplitter, QFileDialog, QAbstractItemView

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

    def getColumnName(self, columnIndex):
        if 0 <= columnIndex < len(self.dataframe.columns):
            return str(self.dataframe.columns[columnIndex])
        return None

class ExpandableText(QWidget):
    def __init__(self, dataframe, csv_name, tab_widget, index, splitter, dict):
        super().__init__()

        self.is_expanded = False
        self.first_split = False
        self.dataframe = dataframe
        self.csv_name = csv_name
        self.tab_widget = tab_widget
        self.table_split = splitter
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
        self.epic = {}
        self.nice = []
        tab_name = self.csv_name
        if tab_name not in self.tab_widget.tab_dict:
            model = DataFrameTableModel(self.dataframe, self.column_checkboxes)

            # Apply new model
            table = QTableView()
            table.setModel(model)
            table.setSelectionMode(QAbstractItemView.ExtendedSelection)
            # table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.dict[table] = model

            # Make tab
            self.tab_widget.addTab(table, self.csv_name)
            self.tab_widget.tab_dict[self.csv_name] = table

            # Initial split: add the new tab widget to the QSplitter
            if isinstance(self.index, int):
                if not self.first_split:
                    self.first_split = True
                    self.table_split.insertWidget(1, self.tab_widget)
                else:
                    # Subsequent double-taps: add the new tab widget to the initially split tab widget
                    self.table_split.widget(1).addTab(table, self.csv_name)
            
            for i, j in self.dict.items():
                i.verticalScrollBar().valueChanged.connect(self.load_more_data)
                self.check_status(j)

        # Enable multi-selection for tables
        for tab_name, table_widget in self.tab_widget.tab_dict.items():
                selection_model = table_widget.selectionModel()
                selection_model.selectionChanged.connect(self.handle_selection_changed)
    
    def check_status(self, model):
        for checkbox in self.column_checkboxes.values():
            checkbox.stateChanged.connect(model.update_visible_columns)

    def handle_selection_changed(self):

        # Get the correct table
        current_index = self.tab_widget.currentIndex()
        current_tab_name = self.tab_widget.tabText(current_index)
        table = self.tab_widget.tab_dict[current_tab_name]
        model = self.dict[table]


        selected_indexes = table.selectionModel().selectedIndexes()
        for index in selected_indexes:
            row = index.row()
            col = index.column()
            columnName = model.getColumnName(col)
            index = model.index(row, col)

        # Setup Data
        value = model.data(index)

        if columnName in self.epic:
            self.epic[columnName].append(value)
        else:
            self.epic[columnName] = [value]

        # dataframe = pd.DataFrame(self.epic)
        print(f"{self.epic = }")
        # self.nice.append(current_tab_name)

        # # selected_data = model.selected_data
        # selected_dataframe = pd.DataFrame(self.epic)
        # print(selected_dataframe)

        
        
class DataFrameViewer(QWidget):
    def __init__(self, data):
        super().__init__()
        self.incr = 0
        self.init_ui(data)

    def init_ui(self, data):

        # Setup Layouts
        self.main_layout = QHBoxLayout()
        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()

        labels_layout = QVBoxLayout()
        self.main_splitter = QSplitter()
        self.table_split = QSplitter(Qt.Horizontal)

        # Setup Widgets
        self.tab_widget = QTabWidget()
        scroll_widget = QWidget()
        scroll_area = QScrollArea()

        # Setup tab dictionary
        self.model_dict = {}
        self.tab_widget.tab_dict = {}

        # CSV Save Button
        self.csv_button = QPushButton("Save Data")
        self.csv_button.clicked.connect(self.save_csv)

        # Run the data through the expanded text list
        for csv_name, df in data.items():
            text_widget = ExpandableText(df, csv_name, self.tab_widget, None,
                                         self.table_split, self.model_dict)
            labels_layout.addWidget(text_widget)

        # Configure layouts
        scroll_widget.setLayout(labels_layout)
        scroll_area.setFixedWidth(500)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        # Create Splitter 
        self.table_split.addWidget(self.tab_widget)

        # Main Layout
        labels_layout.addWidget(self.csv_button)
        self.main_layout.addWidget(self.main_splitter)
        self.setLayout(self.main_layout)

        # Layout configure
        self.main_splitter.addWidget(scroll_area)
        self.main_splitter.addWidget(self.table_split)
        self.main_splitter.setStretchFactor(0, 1)

        # Set layouts for the placeholder widgets
        self.main_splitter.widget(0).setLayout(self.right_layout)
        self.main_splitter.widget(1).setLayout(self.right_layout)

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

    """
    This allows for the user to double click on the tab and be able to compare a tab on the side
    """
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

            # Make it that the user can't remove the last tab
            if new_tab_widget.count() == 0:
                new_tab_widget.tabCloseRequested.connect(self.tabCloseRequested)

            # Ensure dataframe is not empty before creating splitter item
            if not dataframe.empty:
                ExpandableText(dataframe, new_tab, new_tab_widget, index, self.table_split, self.model_dict)
            else:
                print("Cannot Compare, dataframe is empty!")
    
    # Remove the splitter when removed speicifc tab
    def tabCloseRequested(self, index):
        if self.tab_widget.count() > 1:
            self.table_split.widget(1).setParent(None)

    """
    User can save a csv based on what they have selected in a table
    """
    def save_csv(self):
        pass
        # # Get the correct table
        # current_index = self.tab_widget.currentIndex()
        # current_tab_name = self.tab_widget.tabText(current_index)
        # table = self.tab_widget.tab_dict[current_tab_name]
        # model = self.model_dict[table]

        # selected_indexes = table.selectionModel().selectedIndexes()
        # for index in selected_indexes:
        #     row = index.row()
        #     col = index.column()
        #     columnName = model.getColumnName(col)
        #     index = model.index(row, col)
        #     value = model.data(index)

        #     print(f"{columnName = }")
        #     print(f"{value = }")
        # nice = ExpandableText.handle_selection_changed(ExpandableText)
        # print(nice)
        # df.to_csv(file_name, encoding='utf-8', index=False)
