import pandas as pd
from itertools import product
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,\
                            QTableView, QCheckBox, QScrollArea, QTabWidget, QSplitter,\
                            QFileDialog


"""
Created QAbstractionTableModel that each dataframe loaded in utilizes
"""
class DataFrameTableModel(QAbstractTableModel):
    def __init__(self, dataframe, column_checkboxes, parent=None):
        super(DataFrameTableModel, self).__init__(parent)
        self.highlighted_cells = []
        self._dataframe = dataframe
        self.column_checkboxes = column_checkboxes
        self.visible_rows = 100
        self.text = None
        self._selected_indexes = set()
        self.update_visible_columns()


    """
    Row counter that factors in batch size loading
    """
    def rowCount(self, parent=None):
        return min(self.visible_rows, len(self._dataframe))


    """
    Makes columns visible or not
    """
    def update_visible_columns(self):
        if self.column_checkboxes is not None:
            self.visible_columns = [col for col, checkbox in self.column_checkboxes.items() if checkbox.isChecked()]
            self.layoutChanged.emit()


    """
    Sets up the table from the dataframes
    """
    def data(self, index, role=Qt.DisplayRole):

        if role == Qt.DisplayRole:
            if self.column_checkboxes is not None:
                column_name = self.visible_columns[index.column()]
                row_index = self._dataframe.index[index.row()]
                return str(self._dataframe.loc[row_index, column_name])
            else:
                return str(self._dataframe.iloc[index.row(), index.column()])

        if role == Qt.BackgroundRole:
            if index in self.highlighted_cells:
                return QColor("yellow")
        return None

    """
    Column total from dataframe
    """
    def columnCount(self, parent=None):
        if self.column_checkboxes:
            return len(self.visible_columns)
        else:
            return len(self._dataframe.columns)

    """
    Creates the headers for the table
    """
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if self.column_checkboxes:
                    return str(self.visible_columns[section])
                else:
                    return str(self._dataframe.columns[section])
    
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None

    """
    Sets a flag for selectable items
    """
    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    """
    Update the visible rows counter to load the next amount of rows
    """
    def update_visible_rows(self):
        self.visible_rows += 100
        self.visible_rows = min(self.visible_rows, len(self._dataframe))
        return self.visible_rows


    """
    Update the next 100 visible rows
    """
    def canFetchMore(self, index):
        return self.visible_rows < len(self._dataframe)


    """
    This fetches the next 100 rows that need to be loaded in
    """
    def fetchMore(self, index):
        remaining_rows = len(self._dataframe) - self.visible_rows
        rows_to_fetch = min(100, remaining_rows)
        self.beginInsertRows(index, self.visible_rows, self.visible_rows + rows_to_fetch - 1)
        self.visible_rows += rows_to_fetch
        self.endInsertRows()
    

    """
    Get the current dataframe from the table, this also factors in hidden rows
    """
    def get_dataframe(self):
        visible_columns = [col for col, checkbox in self.column_checkboxes.items() if checkbox.isChecked()]
        return pd.DataFrame(self._dataframe[visible_columns])


    """
    Get the column name of specific selected column
    """
    def getColumnName(self, columnIndex):
        if 0 <= columnIndex < len(self._dataframe.columns):
            return str(self._dataframe.columns[columnIndex])
        return None


    """
    Gets highlights the found text in the desired tables
    """
    def update_search_text(self):
        self.highlighted_cells = []
        if self.text:
            for row , col in product(range(self.visible_rows), range(self.columnCount())):
                item = str(self._dataframe.iat[row, col])
                if self.text and self.text in item:
                    self.highlighted_cells.append(self.index(row, col))
        self.layoutChanged.emit()
        return


    """
    Remove column from table when checked off
    """
    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            if index.isValid():
                if index in self._selected_indexes:
                    self._selected_indexes.remove(index)
                else:
                    self._selected_indexes.add(index)
                self.dataChanged.emit(index, index, [role])
                return True
        return False


"""
Setup the expandable text checkboxes and setup their individual tables that are loaded in
"""
class ExpandableText(QWidget):
    def __init__(self, dataframe, csv_name, tab_widget, index, splitter, model_dict, table_dict, csv_button):
        super().__init__()
        self.saved_data = None
        self.is_expanded = False
        self.first_split = False
        self.dataframe = dataframe
        self.csv_name = csv_name
        self.tab_widget = tab_widget
        self.table_split = splitter
        self.model_dict = model_dict
        self.index = index
        self.table_dict = table_dict

        # Load the checkbox items and connect save csv button
        self.column_checkboxes = self.create_column_checkboxes()
        csv_button.clicked.connect(self.save_csv)

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
    def load_more_data(self, table, value):
            current_value = table.verticalScrollBar().value()
            max_value = table.verticalScrollBar().maximum()

            def is_within_range(value1, value2, range_limit=20):
                return abs(value1 - value2) <= range_limit
        
            if is_within_range(current_value, max_value):
                if len(self.dataframe) > 100:
                    self.model_dict[table].update_visible_rows()
                    self.model_dict[table].update_search_text()

    """
    Setup of the data in their respective tables and tabs
    """
    def setup_data(self):

        tab_name = self.csv_name
        if not self.dataframe.empty:
            if tab_name not in self.table_dict:
                model = DataFrameTableModel(self.dataframe, self.column_checkboxes)

                # Apply new model
                table = QTableView()
                table.setModel(model)
                table.setSelectionBehavior(QTableView.SelectItems)

                # Make tab for loaded data - save model
                self.model_dict[table] = model
                self.table_dict[self.csv_name] = table
                self.tab_widget.addTab(table, self.csv_name)

                # Initial split: add the new tab widget to the QSplitter
                if isinstance(self.index, int):
                    if not self.first_split:
                        self.first_split = True
                        self.table_split.insertWidget(1, self.tab_widget)
                    else:
                        # Subsequent double-taps: add the new tab widget to the initially split tab widget
                        self.table_split.widget(1).addTab(table, self.csv_name)

                # Signal Callers
                self.tab_widget.currentChanged.connect(self.on_tab_changed)
                table.selectionModel().selectionChanged.connect(self.update_view)
                vertical_scrollbar = table.verticalScrollBar()
                vertical_scrollbar.valueChanged.connect(lambda value, table=table: self.load_more_data(table, value))
                self.check_status(model)

        else:
            print(f"{tab_name} is empty! Table unable to load!")


    """
    Toggle the columns that the user selects in the options menu
    """
    def check_status(self, model):
        for checkbox in self.column_checkboxes.values():
            checkbox.stateChanged.connect(model.update_visible_columns)


    """
    Get the data for the user to select and save to CSV
    """
    def update_view(self, selected, deselected):
        selected_data = {}

        for tab_name, table_widget in self.table_dict.items():
            model = self.model_dict[table_widget]
            for index in table_widget.selectionModel().selectedIndexes():
                row = index.row()
                col = index.column()
                header = model.headerData(col, Qt.Horizontal)
                selected_data[header] = selected_data.get(header, []) + [model._dataframe.iloc[row, col]]

        self.saved_data = pd.DataFrame(selected_data)


    """
    Clear Selection when user changes tabs
    """
    def on_tab_changed(self):
        for tab_name, table_widget in self.table_dict.items():
            table_widget.selectionModel().clear()


    def save_csv(self):
        if self.saved_data is not None:
            if not self.saved_data.empty:
                file_dialog = QFileDialog()
                file_dialog.setAcceptMode(QFileDialog.AcceptSave)
                file_path, _ = file_dialog.getSaveFileName(self, "Save Selected Data", "", "CSV Files (*.csv)")
                if file_path:
                    self.saved_data.to_csv(file_path, index=False)
                    print("Selected Data saved to:", file_path)
                print(f"{self.saved_data = }")
        return 

"""
Main Viewing Window of the loaded dataframes
""" 
class DataFrameViewer(QWidget):
    def __init__(self, data):
        super().__init__()
        self.incr = 0
        self.data = data
        self._bool = False
        self.test = False
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
        self.table_dict = {}

        # Search bar and Checkbox
        search_bar = QLineEdit()
        search_bar.returnPressed.connect(self.search_tables)
        search_bar.setPlaceholderText("Search...")
        self.search_text = search_bar.text()
        self.all_table = QCheckBox("Search All Tables")

        # Buttons
        self.csv_button = QPushButton("Save Data")
        self.load_search_results_button = QPushButton("Load Search Results")
        self.load_search_results_button.clicked.connect(self.load_search_results)
        self.main_layout.addWidget(self.load_search_results_button)

        # Run the data through the expanded text list
        for csv_name, df in self.data.items():
            text_widget = ExpandableText(df, csv_name, self.tab_widget, None,
                                         self.table_split, self.model_dict,
                                         self.table_dict, self.csv_button)
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
            tab_name = self.tab_widget.tabText(index)
            self._bool = True
            self.incr += 1

            # Create new tab
            self.new_tab_widget = QTabWidget()
            self.new_tab_widget.setTabsClosable(True)
            dataframe = self.get_current_tab_dataframe()
            new_name = tab_name + '-' + str(self.incr)
        
            # Make it that the user can't remove the last tab
            if self.new_tab_widget.count() == 0:
                self.new_tab_widget.tabCloseRequested.connect(self.tabCloseRequested)

            # Ensure dataframe is not empty before creating splitter item
            if not dataframe.empty:
                ExpandableText(dataframe, new_name, self.new_tab_widget,
                               index, self.table_split, self.model_dict,
                               self.table_dict, self.csv_button)
            else:
                print("Cannot Compare, dataframe is empty!")
    
            # Remove tab that user wants to compare
            self.tab_widget.removeTab(index)

    """
    Make all tabs after the first one closable
    """
    def tabCloseRequested(self, index):
        if self.tab_widget.count() > 1:
            self.table_split.widget(1).setParent(None)


    """
    User can type a string here and search all the loaded tables to highlight them
    """
    def search_tables(self):
        self.search_text = self.sender().text()

        def run_search(tab):
            for i in range(len(tab)):
                index_table = tab.widget(i)
                if isinstance(index_table, QTableView):
                    model = index_table.model()
                    model.text = self.search_text
                    model.update_search_text()

        # Run through all the tabs if they exist
        if self.tab_widget:
            value = self.tab_widget
            run_search(value)
   
        if self._bool and self.all_table.isChecked():
            value = self.new_tab_widget
            run_search(value)


    def load_search_results(self):
        # Get the current dataframe from the active tab
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            self.current_table = self.tab_widget.widget(current_index)
            if isinstance(self.current_table, QTableView):
                model = self.current_table.model()
                if model:
                    
                    # Setup window
                    self.central_widget = QWidget()
                    self.find_items_layout = QVBoxLayout(self.central_widget)
                    
                    # Definied dataframe
                    df = model.get_dataframe()
                    
                    # Use applymap with vectorized string methods to search for the text in each cell
                    search_result = df[df.apply(lambda col: col.map(lambda x: str(x).lower().find(self.search_text.lower()) != -1))]

                    # Get all non-NaN values and create a new DataFrame with original indices and a column indicating where the item is found
                    non_nan_series = search_result.stack().dropna()
                    non_nan_df = pd.DataFrame({'value': non_nan_series.values, 'search_index': non_nan_series.index.get_level_values(0), 'column': non_nan_series.index.get_level_values(1)})


                    # Group by the index and create a list of values for each group
                    grouped_df = non_nan_df.groupby('search_index').agg({'value': list, 'column': 'first'}).reset_index()
                    
                    # Create a new QAbstractTableModel for search results
                    self.search_results_model = DataFrameTableModel(grouped_df, None)
                    self.search_results_table = QTableView()
                    self.search_results_table.setModel(self.search_results_model)

                    # Hide the vertical header (index column)
                    self.search_results_table.verticalHeader().setVisible(False)

                    # Add to layout
                    self.find_items_layout.addWidget(self.search_results_table)

                    # Signal Callers
                    self.search_results_table.setSelectionBehavior(QTableView.SelectRows)
                    self.search_results_table.selectionModel().selectionChanged.connect(self.on_clicked)

                    # Add a new tab for the search results
                    # search_results_tab_name = "Search Results"
                    # self.tab_widget.addTab(search_results_table, search_results_tab_name)
                    # self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(search_results_table))
        
        # Load the find items window
        self.central_widget.show()
    
    """
    Index to the right highlighted value when clicked
    """
    def on_clicked(self, selected, deselected):
        for index in selected.indexes():
            # Use the index to get the data
            if index.column() == 0:
                data_at_index = self.search_results_model.data(index, Qt.DisplayRole)
    
        curr_index = self.current_table.model().index(int(data_at_index), 0)
        self.current_table.scrollTo(curr_index, QTableView.PositionAtTop)
        # return self.model().data(self.model().index(row, col), Qt.DisplayRole)
