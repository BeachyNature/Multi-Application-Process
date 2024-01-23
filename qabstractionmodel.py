import pandas as pd
import time
from itertools import product
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,\
                            QTableView, QCheckBox, QScrollArea, QTabWidget, QSplitter,\
                            QAbstractItemView


"""
Created QAbstractionTableModel that each dataframe loaded in utilizes
"""
class DataFrameTableModel(QAbstractTableModel):
    def __init__(self, dataframe, column_checkboxes, parent=None):
        super(DataFrameTableModel, self).__init__(parent)
        self.highlighted_cells = []
        self.dataframe = dataframe
        self.column_checkboxes = column_checkboxes
        self.visible_rows = 100
        self.text = None
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
        if role == Qt.BackgroundRole:
            if index in self.highlighted_cells:
                return QColor("yellow")
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


    """
    Update the visible rows counter to load the next amount of rows
    """
    def update_visible_rows(self):
        self.visible_rows += 100
        self.visible_rows = min(self.visible_rows, len(self.dataframe))
        return self.visible_rows


    """
    Update the next 100 visible rows
    """
    def canFetchMore(self, index):
        return self.visible_rows < len(self.dataframe)


    """
    This fetches the next 100 rows that need to be loaded in
    """
    def fetchMore(self, index):
        remaining_rows = len(self.dataframe) - self.visible_rows
        rows_to_fetch = min(100, remaining_rows)
        self.beginInsertRows(index, self.visible_rows, self.visible_rows + rows_to_fetch - 1)
        self.visible_rows += rows_to_fetch
        self.endInsertRows()
    

    """
    Get the current dataframe from the table, this also factors in hidden rows
    """
    def get_dataframe(self):
        visible_columns = [col for col, checkbox in self.column_checkboxes.items() if checkbox.isChecked()]
        return pd.DataFrame(self.dataframe[visible_columns])


    """
    Get the column name of specific selected column
    """
    def getColumnName(self, columnIndex):
        if 0 <= columnIndex < len(self.dataframe.columns):
            return str(self.dataframe.columns[columnIndex])
        return None


    """
    Gets highlights the found text in the desired tables
    """
    def update_search_text(self):
        self.highlighted_cells = []
        if self.text:
            for row , col in product(range(self.visible_rows), range(self.columnCount())):
                item = str(self.dataframe.iat[row, col])
                if self.text and self.text in item:
                    self.highlighted_cells.append(self.index(row, col))
        self.layoutChanged.emit()



"""
Setup the expandable text checkboxes and setup their individual tables that are loaded in
"""
class ExpandableText(QWidget):
    def __init__(self, dataframe, csv_name, tab_widget, index, splitter, dict):
        super().__init__()
        self.epic = {}
        self.is_expanded = False
        self.first_split = False
        self.dataframe = dataframe
        self.csv_name = csv_name
        self.tab_widget = tab_widget
        self.table_split = splitter
        self.dict = dict
        self.index = index

        # Load the checkbox items
        self.column_checkboxes = self.create_column_checkboxes()

        # If the table is for inital setup or comparison load in
        if isinstance(self.index, int):
            self.setup_data()
        else:
            self.init_ui()


    """
    Setup each table and tab for the loaded dataframes
    """
    def init_ui(self):

        layout = QHBoxLayout()
        button_layout = QVBoxLayout()

        # Button setups and styles
        self.check_button = QPushButton(self.csv_name + " +")
        self.check_button.clicked.connect(self.toggle_expansion)
        if not self.dataframe.empty:
            self.check_button.setStyleSheet('border: none; color: black; font-size: 24px;')
        else:
            self.check_button.setStyleSheet('border: none; color: red; font-size: 24px;')

        # Setup the column selection buttons
        self.options_widget = QWidget()
        options_layout = QVBoxLayout(self.options_widget)
        for checkbox in self.column_checkboxes.values():
            options_layout.addWidget(checkbox)

        button_layout.addWidget(self.check_button, alignment=Qt.AlignTop)
        button_layout.addWidget(self.options_widget)
        layout.addLayout(button_layout)
        layout.addStretch()
        self.setLayout(layout)


    """
    Create the checkboxes that allows for user to toggle columns in dataframe table
    """
    def create_column_checkboxes(self):
        column_checkboxes = {}
    
        for column in self.dataframe.columns:
            checkbox = QCheckBox(column)
            checkbox.setChecked(True)
            checkbox.setVisible(self.is_expanded)
            checkbox.stateChanged.connect(self.setup_data)
            column_checkboxes[column] = checkbox

        return column_checkboxes
    

    """
    Setups of the column selection items
    """
    def toggle_expansion(self):
        self.is_expanded = not self.is_expanded
        self.check_button.setText(self.csv_name + " -" if self.is_expanded else  self.csv_name + " +")

        for i in range(self.options_widget.layout().count()):
            option_widget = self.options_widget.layout().itemAt(i).widget()
            option_widget.setVisible(self.is_expanded)

        self.setup_data()


    """
    Tells the model to load the next 100 rows
    """
    def load_more_data(self):
        tab = self.tab_widget.tab_dict[self.csv_name]

        model = tab.model()
        
        current_value = tab.verticalScrollBar().value()
        max_value = tab.verticalScrollBar().maximum()

        def is_within_range(value1, value2, range_limit=20):
            return abs(value1 - value2) <= range_limit

        # Checks if the scroll value is within the maximum value
        if is_within_range(current_value, max_value):
            if len(self.dataframe) > 100:
                model.update_visible_rows()
                model.update_search_text()



    """
    Setup of the data in their respective tables and tabs
    """
    def setup_data(self):

        tab_name = self.csv_name
        if not self.dataframe.empty:
            if tab_name not in self.tab_widget.tab_dict:
                model = DataFrameTableModel(self.dataframe, self.column_checkboxes)

                # Apply new model
                table = QTableView()
                table.setModel(model)
                table.setSelectionMode(QAbstractItemView.ExtendedSelection)

                # Make tab for loaded data - save model
                self.dict[table] = model
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
                
                # Allow for batch scrolling to work for any of the tables
                for i, j in self.dict.items():
                    i.verticalScrollBar().valueChanged.connect(self.load_more_data)
                    self.check_status(j)

            # Enable multi-selection for tables
            for tab_name, table_widget in self.tab_widget.tab_dict.items():
                    selection_model = table_widget.selectionModel()
                    selection_model.selectionChanged.connect(self.handle_selection_changed)
        else:
            print(f"{tab_name} is empty! Table unable to load!")


    """
    Toggle the columns that the user selects in the options menu
    """
    def check_status(self, model):
        for checkbox in self.column_checkboxes.values():
            checkbox.stateChanged.connect(model.update_visible_columns)


    """
    Create a dictionary for what the user selects in the table of interest
    """
    def handle_selection_changed(self):

        #TODO: Need to get user selections working
        current_index = self.tab_widget.currentIndex()
        current_tab_name = self.tab_widget.tabText(current_index)
        table = self.tab_widget.tab_dict[current_tab_name]
        model = self.dict[table]

        # # Get the index selection values
        # selected_indexes = table.selectionModel().selectedIndexes()
        # for index in selected_indexes:
        #     row = index.row()
        #     col = index.column()
        #     columnName = model.getColumnName(col)
        #     index = model.index(row, col)

        # # Setup Data
        # if index:
        #     value = model.data(index)

        #     if columnName in self.epic:
        #         self.epic[columnName].append(value)
        #     else:
        #         self.epic[columnName] = [value]

        #     # dataframe = pd.DataFrame(self.epic)
        #     print(f"{self.epic = }")

        #     # # selected_data = model.selected_data
        #     # selected_dataframe = pd.DataFrame(self.epic)
        #     # print(selected_dataframe)


"""
Main Viewing Window of the loaded dataframes
""" 
class DataFrameViewer(QWidget):
    def __init__(self, data):
        super().__init__()
        self.incr = 0
        self.data = data
        self._bool = False
        self.init_ui()


    """
    Setup the main window display
    """
    def init_ui(self):

        # Setup Layouts
        self.center_layout = QHBoxLayout()
        self.main_layout = QVBoxLayout()

        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()

        labels_layout = QVBoxLayout()
        self.main_splitter = QSplitter()
        self.table_split = QSplitter(Qt.Horizontal)

        # Setup Widgets
        self.tab_widget = QTabWidget()
        scroll_area = QScrollArea()
        scroll_widget = QWidget()

        # Setup tab dictionary
        self.model_dict = {}
        self.tab_widget.tab_dict = {}

        # Search bar and Checkbox
        search_bar = QLineEdit()
        search_bar.returnPressed.connect(self.search_tables)
        search_bar.setPlaceholderText("Search...")
        self.all_table = QCheckBox("Search All Tables")

        # CSV Save Button
        self.csv_button = QPushButton("Save Data")
        self.csv_button.clicked.connect(self.save_csv)

        # Run the data through the expanded text list
        for csv_name, df in self.data.items():
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
        self.main_layout.addWidget(search_bar)
        self.main_layout.addWidget(self.all_table)
        self.center_layout.addWidget(self.main_splitter)
        self.main_layout.addLayout(self.center_layout)
        self.setLayout(self.main_layout)

        # Layout configure
        self.main_splitter.addWidget(scroll_area)
        self.main_splitter.addWidget(self.table_split)
        self.main_splitter.setStretchFactor(0, 1)

        # Tab widget, double click to compare and able to be removed
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabBarDoubleClicked.connect(self.load_table_double_click)
    

    """
    Get the current dataframe of the modified table, hidden columns and all
    """
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
            self._bool = True
            self.incr += 1

            # Create new tab

            self.new_tab_widget = QTabWidget()
            self.new_tab_widget.tab_dict = {}
            self.new_tab_widget.setTabsClosable(True)
            dataframe = self.get_current_tab_dataframe()
            tab_name = self.tab_widget.tabText(index) + '-' + str(self.incr)
        
            # Make it that the user can't remove the last tab
            if self.new_tab_widget.count() == 0:
                self.new_tab_widget.tabCloseRequested.connect(self.tabCloseRequested)

            # Ensure dataframe is not empty before creating splitter item
            if not dataframe.empty:
                ExpandableText(dataframe, tab_name, self.new_tab_widget,\
                               index, self.table_split,\
                               self.model_dict, self.all_table)
            else:
                print("Cannot Compare, dataframe is empty!")
    
            # Remove tab that user wants to compare
            self.tab_widget.tab_dict.pop(tab_name)
            self.tab_widget.removeTab(index)

    """
    Make all tabs after the first one closable
    """
    def tabCloseRequested(self, index):
        if self.tab_widget.count() > 1:
            self.table_split.widget(1).setParent(None)


    """
    User can save a csv based on what they have selected in a table
    """
    def save_csv(self):
        print("Saved CSV!")
        pass

        # nice = ExpandableText.handle_selection_changed(ExpandableText)
        # print(nice)
        # df.to_csv(file_name, encoding='utf-8', index=False)

    """
    User can type a string here and search all the loaded tables to highlight them
    """
    def search_tables(self):
        text = self.sender().text()

        def run_search(tab):
            for i in range(len(tab)):
                index_table = tab.widget(i)
                if isinstance(index_table, QTableView):
                    model = index_table.model()
                    model.text = text
                    model.update_search_text()

        # Run through all the tabs if they exist
        if self.tab_widget:
            value = self.tab_widget
            run_search(value)
   
        if self._bool and self.all_table.isChecked():
            value = self.new_tab_widget
            run_search(value)
