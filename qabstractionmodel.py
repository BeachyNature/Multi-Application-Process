import os
import re
import itertools
import pandas as pd
import polars as pl
from collections import defaultdict
from sqlalchemy import create_engine, MetaData
from PyQt5.QtGui import QColor, QDropEvent, QDragEnterEvent
from PyQt5.QtCore import Qt, QAbstractTableModel, QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton,\
                            QLineEdit, QTableView, QCheckBox, QScrollArea,\
                            QTabWidget, QSplitter, QFileDialog, QLabel, QDialog


"""
Searching thread to organize data into QModelIndexes
"""
class SearchThread(QThread):
    search_finished = pyqtSignal(list)

    def __init__(self, table, data_dict, visible_rows):
        super().__init__()
        self.highlighted_cells = []
        self.visible_rows = visible_rows
        self.data_dict = data_dict
        self.table = table


    """
    Recieve index values of the searched data
    """
    def run(self) -> None:
        index_values = self.search_text_in_dataframe()
        self.search_finished.emit(index_values)
        return


    """
    Store the QModelIndex objects corresponding to the matched rows in dataframe
    """
    def search_text_in_dataframe(self) -> list:
        for key, value in (
            itertools.chain.from_iterable(
                (itertools.product((k,), v) for k, v in self.data_dict.items()))):
                    self.highlighted_cells.append(self.table.index(key-1, value)) # Due to how current csv works
        return self.highlighted_cells


"""
Created QAbstractionTableModel that each dataframe loaded in utilizes
"""
class DataFrameTableModel(QAbstractTableModel):
    def __init__(self, dataframe, column_checkboxes, parent=None):
        super(DataFrameTableModel, self).__init__(parent)

        # Define Values
        self.text = None
        self._bool = False
        self.highlighted_cells = []
        self.result = pl.DataFrame()
        self._selected_indexes = set()

        # Dataframe configure/setup
        self.column_checkboxes = column_checkboxes
        self._dataframe = dataframe
        self.visible_rows = 500
        
        # Set the visible row count
        self.update_visible_columns()


    """
    Row counter that factors in batch size loading
    """
    def rowCount(self, parent=None) -> int:
        # TODO: Use with checkbox
        return min(self.visible_rows, len(self._dataframe))


    """
    Makes columns visible or not
    """
    def update_visible_columns(self) -> None:
        if self.column_checkboxes is not None:
            self.visible_columns = [col for col, checkbox in self.column_checkboxes.items() if checkbox.isChecked()]
            self.layoutChanged.emit()
        return

    """
    Sets up the table from the dataframes
    """
    def data(self, index, role=Qt.DisplayRole):

        if role == Qt.DisplayRole:
            if self.column_checkboxes is not None:
                return str(self._dataframe[index.row(), index.column()])
        
        # Check if the same row is called more than once
        if role == Qt.BackgroundRole:
            if index in self.highlighted_cells:
                # Check if more than one occurrence of the same row
                # row_counts = sum(1 for cell_index in self.highlighted_cells if cell_index.row() == index.row())
                # if row_counts > 1:
                #     return QColor("green")
                return QColor("yellow")
        return None

    """
    Column total from dataframe
    """
    def columnCount(self, parent=None) -> int:
        if self.column_checkboxes:
            return len(self.visible_columns)
        else:
            return len(self._dataframe.columns)


    """
    Creates the headers for the table
    """
    def headerData(self, section, orientation, role=Qt.DisplayRole) -> None:
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
    Update the visible rows counter to load the next amount of rows
    """
    def update_visible_rows(self) -> int:
        self.visible_rows += 500
        self.visible_rows = min(self.visible_rows, len(self._dataframe))
        return self.visible_rows
    

    """
    Get the current dataframe from the table, this also factors in hidden rows
    """
    def get_dataframe(self) -> pl.DataFrame:
        visible_columns = [col for col, checkbox in self.column_checkboxes.items() if checkbox.isChecked()]
        return pl.DataFrame(self._dataframe[visible_columns])


    """
    Get the column name of specific selected column
    """
    def getColumnName(self, columnIndex) -> None:
        if 0 <= columnIndex < len(self._dataframe.columns):
            return str(self._dataframe.columns[columnIndex])
        return None


    """
    Uncheck all the columns that are not being filtered    
    """
    def uncheck_all_other_columns(self, col_name) -> None:
        for name, checkbox in self.column_checkboxes.items():
            if name != col_name and self._bool:
                checkbox.setChecked(False)
            else:
                checkbox.setChecked(True)
        return


    """
    Update the searched results by highlighting specific columns
    """
    def update_search_text(self) -> int:
        data_dict = {}
        combined_filter = None
        
        # Chunked Dataframe
        self.result = self._dataframe[:self.visible_rows]

        # Newly created dataframe based on conditions
        if re.search(r'[()]', self.text) is not None:
            value = re.findall(r'\((.*?)\)', self.text)
        
        # Values outside of parentheses
        value = re.findall(r'\([^()]*\)|[^()]+', self.text)
    
        for val in value:
            data_dict, found_items = self.match_bool(val, data_dict, combined_filter) 

        # Start the search thread
        self.search_thread = SearchThread(self, data_dict, self.visible_rows)
        self.search_thread.search_finished.connect(self.handle_search_results)
        self.search_thread.start()
        return found_items


    """
    Fill in the data dictionary with row indexes and column index for each found item
    """
    def index_row(self, columns, data_dict) -> dict:
        rows = self.result['Index'].to_list()
        cols = self.result.get_column_index(columns)
    
        for row in rows:
            if row in data_dict:
                data_dict[row].append(cols)
            else:
                data_dict[row] = [cols]
        return data_dict


    """
    Dynamically setup the expressions
    """
    def dynamic_expr(self, operator, value, column, filter_expr) -> filter:
        if value.isdigit():
            match operator:
                case '=':
                    filter_expr = pl.col(column) == int(value)
                case '>':
                    filter_expr = pl.col(column) > int(value)
                case '<':
                    filter_expr = pl.col(column) < int(value)
                case '>=':
                    filter_expr = pl.col(column) >= int(value)
                case '<=':
                    filter_expr = pl.col(column) <= int(value)
                case '!=':
                    filter_expr = pl.col(column) != int(value)
                case _ :
                    print(f"Invalid operator: {operator}")
        else:
            match operator:
                case '=': 
                    filter_expr = pl.col(column) == value
                case '!=':
                    filter_expr = pl.col(column) != value
                case _ :
                    print(f"Invalid operator: {operator}")
        return filter_expr


    """
    Process dataframe and index rows
    """
    def process_filter(self, col, data_dict, combined_filter):
        self.result = self.result.filter(combined_filter)
        data_dict = self.index_row(col, data_dict)
        return data_dict


    """
    Split the conditions up into sets and combine back together
    """
    def condition_set(self, init_val, condition, pattern,
                    combined_filter, data_dict, _bool) -> dict:

        for cond_set in condition:
            matches = re.findall(pattern, cond_set)
            for match in matches:
                col = re.sub(r"\(|\)", "", match[0].strip())
                op = re.sub(r"\(|\)", "", match[1].strip())
                val = re.sub(r"\(|\)", "", match[2].strip())
            filter_expr = self.dynamic_expr(op, val, col, None)

            if _bool:
                combined_filter = filter_expr if combined_filter is None else combined_filter | filter_expr
            else:
                combined_filter = filter_expr if combined_filter is None else combined_filter & filter_expr

            if re.search(r'[()]', init_val) is not None:
                data_dict = self.process_filter(col, data_dict, combined_filter)

        data_dict = self.process_filter(col, data_dict, combined_filter)
        total_items = self.found_items(combined_filter)
        return data_dict, total_items


    """
    Detect whether the condition is split between and/or condition or none
    """
    def match_bool(self, val, data_dict, combined_filter) -> dict:

        # Split based on boolean conditional
        pattern = r'\s*([^\s=><!]+)\s*([=><!]+)\s*([^\s=><!]+)\s*'

        if 'and' in val:
            condition = re.split(r'(?:and|&|,)', val)
            return self.condition_set(val, condition, pattern,
                                      combined_filter, data_dict, False)

        elif 'or' in val:
            condition = re.split(r'\bor\b', val)
            return self.condition_set(val, condition, pattern,
                                      combined_filter, data_dict, True)

        else:
            col, op, val = map(str.strip, val.split())
            filter_expr = self.dynamic_expr(op, val, col, None)

        # If there is no AND / OR statement
        if filter_expr is not None:
            self.result = self.result.filter(filter_expr)
            total_items = self.found_items(filter_expr)
            
            # Fill in data dict of indexes
            data_dict = self.index_row(col, data_dict)
            return data_dict, total_items
        return


    """
    Get total found items to fill in the index label
    """
    def found_items(self, dynam_expr):
        return len(self._dataframe.filter(dynam_expr))


    """
    Apply the newly converted dataframe index values to qmodelindex to be highlighted
    """
    def handle_search_results(self, index_values):
        self.highlighted_cells = index_values
        self.layoutChanged.emit()


    """
    Populate the results window
    """
    def get_result(self) -> pl.DataFrame:
        return self.result



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
        self.table_dict = table_dict
        self.csv_button = csv_button
        self.index = index
        self.setAcceptDrops(True)

        # Setup save CSV button in ExpandedTextView
        self.csv_button.clicked.connect(self.save_csv)
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

        if not self.dataframe.is_empty():
            self.check_button.setStyleSheet('border: none; color: black; font-size: 24px;')
        else:
            self.check_button.setStyleSheet('border: none; color: red; font-size: 24px;')

        # Setup the column selection buttons
        self.options_widget = QWidget()
        options_layout = QVBoxLayout(self.options_widget)
        for checkbox in self.column_checkboxes.values():
            options_layout.addWidget(checkbox)

        # Apply widgets
        button_layout.addWidget(self.check_button)
        button_layout.addWidget(self.options_widget)
        # button_layout.addWidget(self.csv_button) # TODO add to bottom of vertical bar
        layout.addLayout(button_layout)
        layout.addStretch()
        layout.update()
        self.setLayout(layout)


    """
    Enable drag and drop event for CSV and DB files
    """
    def dragEnterEvent(self, event: QDragEnterEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = [url.toLocalFile().lower() for url in mime_data.urls()]
            if all(url.endswith(('.csv', '.db')) for url in urls):
                event.acceptProposedAction()


    """
    Register the drop event and handle the new data 
    """
    def dropEvent(self, event: QDropEvent):
        # Retrieve the file URLs from the mime data
        mime_data = event.mimeData()
        urls = mime_data.urls()

        # Process each file URL
        for url in urls:
            file_path = url.toLocalFile()
            file_name = os.path.basename(file_path)

            if file_name.endswith(".csv"):
                drag_data = pl.scan_csv(file_path)
                df = drag_data.collect()
                table_name = os.path.basename(file_path).rstrip('.csv')
                self.add_dragged_file(df, table_name)

            elif file_path.endswith(".db"):
                engine = create_engine(f"sqlite:///{file_path}")

                # Reflect database schema to MetaData
                metadata = MetaData()
                metadata.reflect(bind=engine)

                # Extract table names
                self.table_names = list(metadata.tables.keys())

                dialog = QDialog()
                layout = QVBoxLayout()

                # Process database tables
                load_db_button = QPushButton("Load Tables")
                load_db_button.clicked.connect(lambda: self.load_db_table(engine, dialog))
                
                for table_name in self.table_names:
                    check_button = QCheckBox(table_name)
                    check_button.setChecked(True)
                    
                    check_button.stateChanged.connect(self.handle_checkbox)
                    layout.addWidget(check_button)
                
                layout.addWidget(load_db_button)
                dialog.setLayout(layout)
                dialog.exec_()
  
        # Accept action to add new csv
        event.acceptProposedAction()


    """
    Load user selected files
    """
    def load_db_table(self, engine, dialog):
        for table_name in self.table_names:
            df = pl.read_database(
                    query=f"SELECT * FROM {table_name}",
                    connection=engine)
            self.add_dragged_file(df, table_name)
        dialog.close()


    """
    Handle what tables user wants to load in
    """
    def handle_checkbox(self, state) -> None:
        sender = self.sender()
        if state == 0:
            self.table_names.remove(sender.text())
        else:
             self.table_names.append(sender.text())


    """
    Return dragged items
    """
    def add_dragged_file(self, df, table_name):
        # Create a new instance with the new data
        new_instance = ExpandableText(df, table_name, self.tab_widget, None,
                                    self.table_split, self.model_dict,
                                    self.table_dict, self.csv_button)
                    
        # Find the existing vertical layout in the current layout
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and isinstance(item.layout(), QVBoxLayout):
                existing_vertical_layout = item.layout()
                break

        # If there is an existing vertical layout, add the new instance to it
        if existing_vertical_layout:
            existing_vertical_layout.addWidget(new_instance)

    
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
        self.check_button.setText(self.csv_name + " -" if self.is_expanded else self.csv_name + " +")

        for i in range(self.options_widget.layout().count()):
            option_widget = self.options_widget.layout().itemAt(i).widget()
            option_widget.setVisible(self.is_expanded)

        self.setup_data()


    """
    Tells the model to load the next 500 rows
    """
    def load_more_data(self, table, value):
            max_value = table.verticalScrollBar().maximum()
            current_value = table.verticalScrollBar().value()

            def is_within_range(value1, value2, range_limit=20):
                return abs(value1 - value2) <= range_limit
        
            if is_within_range(current_value, max_value):
                if len(self.dataframe) > 500:
                    self.model_dict[table].update_visible_rows()
                    self.model_dict[table].update_search_text()


    """
    Setup of the data in their respective tables and tabs
    """
    def setup_data(self):
        if not self.dataframe.is_empty():
            if self.csv_name not in self.table_dict:
                model = DataFrameTableModel(self.dataframe, self.column_checkboxes)

                # Apply new model
                table = QTableView()
                table.setModel(model)
                table.setSelectionBehavior(QTableView.SelectItems)
                table.verticalHeader().setVisible(False)

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
                        self.table_split.widget(1).addTab(table, self.csv_name)

                # Signal Callers
                self.tab_widget.currentChanged.connect(self.on_tab_changed)
                table.selectionModel().selectionChanged.connect(self.update_view)
                table.verticalScrollBar().valueChanged.connect(lambda value, table=table: self.load_more_data(table, value))
                self.check_status(model)
        else:
            print(f"{self.csv_name} is empty! Table unable to load!")


    """
    Toggle the columns that the user selects in the options menu
    """
    def check_status(self, model):
        for checkbox in self.column_checkboxes.values():
            checkbox.stateChanged.connect(model.update_visible_columns)


    """
    Get the data for the user to select and save to CSV
    """
    def update_view(self) -> pl.DataFrame:
        selected_data = {}

        for table_widget in self.table_dict.values():
            model = self.model_dict[table_widget]
            for index in table_widget.selectionModel().selectedIndexes():
                row = index.row()
                col = index.column()
                header = model.headerData(col, Qt.Horizontal)
                selected_data[header] = selected_data.get(header, []) + [model._dataframe[row, col]]
        self.saved_data = pl.DataFrame(selected_data)


    """
    Clear Selection when user changes tabs
    """
    def on_tab_changed(self) -> None:
        for table_widget in self.table_dict.values():
            table_widget.selectionModel().clear()
        return


    """
    Save CSV based on what user selected in table
    """
    def save_csv(self) -> None:
        if self.saved_data is not None:
            if not self.saved_data.is_empty():
                file_dialog = QFileDialog()
                file_dialog.setAcceptMode(QFileDialog.AcceptSave)
                file_path, _ = file_dialog.getSaveFileName(self, "Save Selected Data", "", "CSV Files (*.csv)")
                self.saved_data.write_csv(file_path)
                print("Selected Data saved to:", file_path)
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
        self.init_ui()


    """
    Setup the main window display
    """
    def init_ui(self) -> None:
        
        # Windiow Size
        self.resize(1920, 1080)
    
        # Setup Layouts
        main_layout = QVBoxLayout()
        labels_layout = QVBoxLayout()
        center_layout = QHBoxLayout()

        self.main_splitter = QSplitter()
        self.table_split = QSplitter(Qt.Horizontal)

        # Setup Widgets
        self.tab_widget = QTabWidget()
        scroll_area = QScrollArea()
        scroll_widget = QWidget()

        # Setup tab dictionary
        self.model_dict = {}
        self.table_dict = {}
        self.label_dict = defaultdict(int)

        # Search bar handler
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search...")
        search_bar.returnPressed.connect(self.search_tables)

        # Label & Checkbox initalizers
        label_layout = QVBoxLayout()
        checkbox_layout = QHBoxLayout()

        self.index_label = QLabel("")
        self.split_search = QCheckBox("Search Splitter")
        self.all_table = QCheckBox("Search All Tables")

        label_layout.addWidget(self.index_label)
        checkbox_layout.addLayout(label_layout)
        checkbox_layout.addWidget(self.split_search)
        checkbox_layout.addWidget(self.all_table)
        checkbox_layout.addStretch()

        # Buttons
        self.csv_button = QPushButton("Save Data")
        self.results_button = QPushButton("Load Search Results")
        self.results_button.clicked.connect(self.load_search_results)

        # Run the data through the expanded text list
        for csv_name, df in self.data.items():
            text_widget = ExpandableText(df, csv_name, self.tab_widget, None,
                                        self.table_split, self.model_dict,
                                        self.table_dict, self.csv_button)
            labels_layout.addWidget(text_widget)

        # Configure layouts
        scroll_widget.setLayout(labels_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(500)

        # Create Splitter 
        self.table_split.addWidget(self.tab_widget)
        
        # Layout configure
        self.main_splitter.addWidget(scroll_area)
        self.main_splitter.addWidget(self.table_split)
        self.main_splitter.setStretchFactor(0, 1)

        # Main Layout
        center_layout.addWidget(self.main_splitter)
        main_layout.addWidget(self.results_button)
        main_layout.addWidget(search_bar)
        main_layout.addLayout(checkbox_layout)
        main_layout.addLayout(center_layout)
        self.setLayout(main_layout)

        # Tab widget, double click to compare and able to be removed
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabBarDoubleClicked.connect(self.load_splitter)
        self.tab_widget.tabCloseRequested.connect(self.maintabCloseRequested)
        return


    """
    Get the current dataframe of the modified table, hidden columns and all
    """
    def get_current_tab_dataframe(self) -> pl.DataFrame:
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            current_tab = self.tab_widget.widget(current_index)
            if isinstance(current_tab, QTableView):
                model = current_tab.model()
            return model.get_dataframe()
        return pl.DataFrame()


    """
    This allows for the user to double click on the tab and be able to compare a tab on the side
    """
    def load_splitter(self, index) -> None:
        self._bool = True

        # Get tab name on widget that needs split
        tab_name = self.tab_widget.tabText(index)
    
        # Create new tab
        self.new_tab_widget = QTabWidget()
        dataframe = self.get_current_tab_dataframe()

        self.new_tab_widget.setTabsClosable(True)
        self.new_tab_widget.tabCloseRequested.connect(self.tabCloseRequested)

        # Ensure dataframe is not empty before creating splitter item
        if not dataframe.is_empty():
            new_name = f"{tab_name} - {index}"
            ExpandableText(dataframe, new_name, self.new_tab_widget,
                            index, self.table_split, self.model_dict,
                            self.table_dict, self.csv_button)
        return

    """
    Make all tabs after the first one closable
    """
    def tabCloseRequested(self) -> None:
        if self.tab_widget.count() > 1:
            self.table_split.widget(1).setParent(None)
        return


    """
    Main tab widget closable and search total label from label dict
    """
    def maintabCloseRequested(self, index) -> None:
        # Allows for a new instance of key to be added
        del_tab = self.tab_widget.tabText(index)
        if self.table_dict.get(del_tab):
            del self.table_dict[del_tab]
            del self.label_dict[index]

        self.tab_widget.removeTab(index)
        return


    """
    User can type a string here and search all the loaded tables to highlight them
    """
    def search_tables(self) -> None:
        self.search_text = self.sender().text()

        """
        Check if user is search all existing tables or not
        """
        def run_search(tab):
            if self.all_table.isChecked():
                for idx in range(len(tab)):
                    index_table = tab.widget(idx)
                    self.table_model_set(index_table)

            else:
                current_tab = tab.currentIndex()
                index_table = tab.widget(current_tab)
                return self.table_model_set(index_table)

        # Run through all the tabs if they exist
        if self.tab_widget:
           run_search(self.tab_widget)
   
        # Check if user is searching all split tables
        if self._bool and self.split_search.isChecked():
            run_search(self.new_tab_widget)
        return


    """
    Check if index table is valid before searching
    """
    def table_model_set(self, index_table) -> QAbstractTableModel:
        if isinstance(index_table, QTableView):
            model = index_table.model()
            model.text = self.search_text
            search = model.update_search_text()

            # Populate the found items label and label dict
            self.found_items(search, index_table)
        return model
    

    """
    Process the number of found items in a table
    """
    def found_items(self, search, index_table) -> None: 
        # Populate label dictionary to know how many fields found in each table
        index = self.tab_widget.indexOf(index_table)
        self.label_dict[index] = search

        # Total found items
        total_found = sum(self.label_dict.values())

        # Update dictionary based on index
        curr_index = self.tab_widget.currentIndex()
    
        # Update Label and indexing
        if len(self.label_dict) > 1:
            self.index_label.setText(f"{self.label_dict[curr_index]} of {total_found} total found in table..")
        else:
            self.index_label.setText(f"{self.label_dict[curr_index]} found items..")
        return


    """
    Load the search results into the results window
    """
    def load_search_results(self) -> None:

        # Add to layout to tab
        self.tab_dict = {}
        self.result_tab = QTabWidget()
        self.central_widget = QWidget()
        find_items_layout = QVBoxLayout(self.central_widget)

        # Iterate through each tab and their table
        for index in range(self.tab_widget.count()):
            tab_name = self.tab_widget.tabText(index)
            model = self.tab_widget.widget(index).model()
            data = model.get_result()

            # # If user is searching with a conditional or not
            # if not model._bool:
            #     # Use applymap with vectorized string methods to search for the text in each cell
            #     search_result = data[data.apply(lambda col: col.map(lambda x: str(x).lower().find(self.search_text.lower()) != -1))]
            
            #     # Get all non-NaN values and create a new DataFrame with original indices and a column indicating where the item is found
            #     non_nan = search_result.stack().dropna()
            #     df = pd.DataFrame({'value': non_nan.values,
            #                        'search_index': non_nan.index.get_level_values(0)})
            #     data = df.groupby('search_index').agg({'value': list}).reset_index()

            # else:
            #     print(f"Conditional Search processing in {tab_name}...")


            # Make table model and apply
            model = DataFrameTableModel(data, None)
            
            print(f"{data = }")
            self.results_table = QTableView()
            self.results_table.setModel(model)

            # Formatters
            self.results_table.verticalHeader().setVisible(False)

            # Add new tab
            find_items_layout.addWidget(self.result_tab)
            self.result_tab.addTab(self.results_table, tab_name)

            # Signal Callers
            self.results_table.setSelectionBehavior(QTableView.SelectRows)
            self.results_table.selectionModel().selectionChanged.connect(self.on_clicked)

            # Defined model and data
            if self.tab_widget.tabText(index) not in self.tab_dict:
                self.tab_dict[tab_name] = [index, self.results_table]
            else:
                return
        
        # Load the find items window
        self.central_widget.show()


    """
    Index to the right highlighted value when clicked
    """
    def on_clicked(self):

        # Go to current table index
        current_index = self.result_tab.currentIndex()
        tab_item = self.tab_dict[self.result_tab.tabText(current_index)]
        self.tab_widget.setCurrentIndex(tab_item[0])

        # Defined tables
        current_table = self.tab_widget.widget(tab_item[0])
        results_table = self.result_tab.widget(tab_item[0])

        # Go to selected table index
        selected_indexes = tab_item[1].selectionModel().selectedIndexes()
        if selected_indexes:
            index = results_table.model().data(selected_indexes[0], Qt.DisplayRole)

            # Scroll through the batch size value to get to the value of interest
            val = current_table.verticalScrollBar()
            for _ in range(int(index)):
                val.setValue(val.maximum())
            current_table.selectRow(int(index)-1)
        else:
            return
