import os
import re
import itertools
import polars as pl
from collections import defaultdict
from sqlalchemy import create_engine, MetaData
from PyQt5.QtGui import QColor, QDropEvent, QDragEnterEvent
from PyQt5.QtCore import Qt, QAbstractTableModel, QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton,\
                            QLineEdit, QTableView, QCheckBox, QScrollArea,\
                            QTabWidget, QSplitter, QFileDialog, QLabel, QDialog


class SearchThread(QThread):
    """
    Searching thread to organize data into QModelIndexes
    """
    search_finished = pyqtSignal(list)

    def __init__(self, table, data_dict):
        super().__init__()
        self.data_dict = data_dict
        self.table = table
        self.data_dict = data_dict

    def run(self) -> None:
        """
        Recieve index values of the searched data
        """
        index_values = self.search_text_in_dataframe([])
        self.search_finished.emit(index_values)
        return

    def search_text_in_dataframe(self, highlighted_cells) -> list:  
        """
        Store the QModelIndex objects corresponding to the matched rows in dataframe
        """
        for key, value in (
            itertools.chain.from_iterable(
                (itertools.product((k,), v) for k, v in self.data_dict.items()))):
                    highlighted_cells.append(self.table.index(key-1, value))
        return highlighted_cells

class DataFrameTableModel(QAbstractTableModel):
    """
    Created QAbstractionTableModel that each dataframe loaded in utilizes
    """
    def __init__(self, dataframe, column_checkboxes, parent=None):
        super(DataFrameTableModel, self).__init__(parent)

        # Define Values
        self.text = None
        self._bool = False
        self.highlighted_cells = []
        self.result = pl.DataFrame()

        # Dataframe configure/setup
        self.column_checkboxes = column_checkboxes
        self._dataframe = dataframe
        self.visible_rows = 500
        
        # Set the visible row count
        self.update_visible_columns()

    def rowCount(self, parent=None) -> int:    
        """
        Row counter that factors in batch size loading
        """
        # TODO: Use with checkbox
        return min(self.visible_rows, len(self._dataframe))
    
    def update_visible_columns(self) -> None: 
        """
        Makes columns visible or not
        """
        if self.column_checkboxes is not None:
            self.visible_columns = [col for col, checkbox in self.column_checkboxes.items() if checkbox.isChecked()]
            self.layoutChanged.emit()
        return

    def data(self, index, role=Qt.DisplayRole) -> None:
        """
        Sets up the table from the dataframes
        """
        if role == Qt.DisplayRole:
            if self.column_checkboxes is not None:
                column_name = self.visible_columns[index.column()]
                return str(self._dataframe[index.row(), column_name])
            return str(self._dataframe[index.row(), index.column()])

        if role == Qt.BackgroundRole:
            if index in self.highlighted_cells:
                return QColor("yellow")
        return

    def columnCount(self, parent=None) -> int:
        """
        Column total from dataframe
        """
        return len(self.visible_columns) if self.column_checkboxes else len(self._dataframe.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> None:
        """
        Creates the headers for the table
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if self.column_checkboxes:
                    return str(self.visible_columns[section])
                return str(self._dataframe.columns[section])
    
    def current_dataframe(self) -> pl.DataFrame:
        """
        Get the current dataframe from the table, this also factors in hidden rows
        """
        visible_columns = [col for col, checkbox in self.column_checkboxes.items() if checkbox.isChecked()]
        return pl.DataFrame(self._dataframe[visible_columns])

    def getColumnName(self, columnIndex) -> None:
        """
        Get the column name of specific selected column
        """
        if 0 <= columnIndex < len(self._dataframe.columns):
            return str(self._dataframe.columns[columnIndex])
        return

    def uncheck_all_other_columns(self, col_name) -> None:
        """
        Uncheck all the columns that are not being filtered    
        """
        for name, checkbox in self.column_checkboxes.items():
            checkbox.setChecked(True)
            if name != col_name and self._bool:
                checkbox.setChecked(False)
        return

    def canFetchMore(self, index):
        """
        Update the next 100 visible rows
        """
        return self.visible_rows < len(self._dataframe)

    def fetchMore(self, index):
        """
        This fetches the next 100 rows that need to be loaded in
        """
        remaining_rows = len(self._dataframe) - self.visible_rows
        rows_to_fetch = min(100, remaining_rows)
        self.beginInsertRows(index, self.visible_rows, len(self._dataframe) - 1)
        self.visible_rows += rows_to_fetch
        self.endInsertRows()
    
    def update_search_text(self) -> int:
        """
        Update the searched results by highlighting specific columns
        """
        data_dict = {}

        # Newly created dataframe based on conditions
        text = self.text.lower()
        if re.search(r'[()]', text) is not None:
            value = re.findall(r'\((.*?)\)', text)
        
        value = re.findall(r'\([^()]*\)|[^()]+', text)
    
        for val in value:
            self.index_dict, found_items = self.match_bool(val, data_dict) 

        # Start the search thread
        self.search_thread = SearchThread(self, self.index_dict)
        self.search_thread.search_finished.connect(self.handle_search_results)
        self.search_thread.start()
        return found_items

    def index_row(self, df, columns, data_dict) -> dict:
        """
        Fill in the data dictionary with row indexes and column index for each found item
        """

        if columns not in df.columns:
            return
        
    def index_row(self, df, columns, data_dict) -> dict:
        """
        Fill in the data dictionary with row indexes and column index for each found item
        """
        rows = df['index'].to_list()
        cols = df.get_column_index(columns)
    
        for row in rows:
            if row in data_dict:
                data_dict[row].append(cols)
            else:
                data_dict[row] = [cols]
        return data_dict


    def dynamic_expr(self, operator, value, column, filter_expr) -> filter:
        """
        Dynamically setup the expressions
        """
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

    def process_filter(self, df, col, data_dict, combined_filter):      
        """
        Process dataframe and index rows
        """
        df = df.filter(combined_filter)
        data_dict = self.index_row(df, col, data_dict)
        return data_dict
    
    def multi_filter(self, _bool, filter_expr, combined_filter) -> filter:
        """
        Process the and/or operations and return expression
        """
        if not _bool:
            combined_filter = filter_expr if combined_filter is None else combined_filter & filter_expr
        else:
            combined_filter = filter_expr if combined_filter is None else combined_filter | filter_expr
        return combined_filter


    def condition_set(self, val, df, condition, pattern,
                      combined_filter, data_dict, _bool) -> dict:
        """
        Split the conditions up into sets and combine back together
        """
        pattern = r'\s*([^\s=><!]+)\s*([=><!]+)\s*([^\s=><!]+)\s*'

        for cond_set in condition:
            matches = re.findall(pattern, cond_set)
            for match in matches:
                col = re.sub(r"\(|\)", "", match[0].strip())
                op = re.sub(r"\(|\)", "", match[1].strip())
                val = re.sub(r"\(|\)", "", match[2].strip())
            
            # Process multi-conditions
            filter_expr = self.dynamic_expr(op, val, col, None)
            combined_filter = self.multi_filter(_bool, filter_expr, combined_filter)
            data_dict = self.process_filter(df, col, data_dict, combined_filter)

        data_dict = self.process_filter(df, col, data_dict, combined_filter)
        total_items = self.found_items(combined_filter)
        return data_dict, total_items

    def match_bool(self, val, data_dict) -> dict:
        """
        Detect whether the condition is split between and/or condition or none
        """
        # Chunked Dataframe
        combined_filter = None
        df = self.current_dataframe()[:self.visible_rows]

        if 'and' in val:
            condition = re.split(r'(?:and|&|,)', val)
            return self.condition_set(val, df, condition, 
                                      combined_filter,
                                      data_dict, False)
        elif 'or' in val:
            condition = re.split(r'\bor\b', val)
            return self.condition_set(val, df, condition,
                                      combined_filter,
                                      data_dict, True)
        else:
            col, op, val = map(str.strip, val.split())
            filter_expr = self.dynamic_expr(op, val, col, None)

        # If there is no AND / OR statement
        if filter_expr is not None:
            df = df.filter(filter_expr)
            total_items = self.found_items(filter_expr)
            data_dict = self.index_row(df, col, data_dict)
            return data_dict, total_items
        return

    def found_items(self, dynam_expr):
        """
        Get total found items to fill in the index label
        """
        return len(self._dataframe.filter(dynam_expr))

    def handle_search_results(self, index_values):
        """
        Apply the newly converted dataframe index values to qmodelindex to be highlighted
        """
        self.highlighted_cells = index_values
        self.layoutChanged.emit()

    def get_result(self) -> pl.DataFrame:
        """
        Populate the results window
        """
        return pl.concat([self._dataframe[key-1] for key in self.index_dict]) if self.text else pl.DataFrame()

class ExpandableText(QWidget):
    """
    Setup the expandable text checkboxes and setup their individual tables that are loaded in
    """
    def __init__(self, data_obj, tab_widget, dataframe, csv_name, index):
        super().__init__()
        self.saved_data = None
        self.is_expanded = False
        self.first_split = False

        self.data_obj = data_obj
        self.table_split = data_obj.table_split
        self.model_dict = data_obj.model_dict
        self.table_dict = data_obj.table_dict
        self.tab_widget = tab_widget
        self.dataframe = dataframe
        self.csv_name = csv_name
        self.index = index

        self.column_checkboxes = self.create_column_checkboxes()
        self.setAcceptDrops(True)
        self.run_tab()

    def run_tab(self) -> None:
        """
        Run the tabs and know when to split or not
        """
        # If the table is for inital setup or comparison load in
        if isinstance(self.index, int):
            self.setup_data()
            return
        self.init_ui()
        return

    def init_ui(self) -> None:
        """
        Setup each table and tab for the loaded dataframes
        """
        layout = QHBoxLayout()
        button_layout = QVBoxLayout()

        # Button setups and styles
        self.check_button = QPushButton(f"{self.csv_name}  +")
        self.check_button.clicked.connect(self.toggle_expansion)
        
        self.check_button.setStyleSheet('border: none; color: black; font-size: 24px;')
        if self.dataframe.is_empty():
            self.check_button.setStyleSheet('border: none; color: red; font-size: 24px;')

        # Setup the column selection buttons
        self.options_widget = QWidget()
        options_layout = QVBoxLayout(self.options_widget)
        for checkbox in self.column_checkboxes.values():
            options_layout.addWidget(checkbox)

        # Apply widgets
        button_layout.addWidget(self.check_button)
        button_layout.addWidget(self.options_widget)
        layout.addLayout(button_layout)
        layout.addStretch()
        self.setLayout(layout)
        return

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Enable drag and drop event for CSV and DB files
        """
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = [url.toLocalFile().lower() for url in mime_data.urls()]
            if all(url.endswith(('.csv', '.db')) for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Register the drop event and handle the new data 
        """
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
        return

    def load_db_table(self, engine, dialog) -> None:
        """
        Load user selected files
        """
        for table_name in self.table_names:
            df = pl.read_database(
                    query=f"SELECT * FROM {table_name}",
                    connection=engine)
            self.add_dragged_file(df, table_name)
        dialog.close()
        return

    def handle_checkbox(self, state) -> None:
        """
        Handle what tables user wants to load in
        """
        sender = self.sender()
        if not state:
            self.table_names.remove(sender.text())
            return
        self.table_names.append(sender.text())
        return

    def add_dragged_file(self, df, table_name):
        """
        Return dragged items
        """
        # Create a new instance with the new data
        new_instance = ExpandableText(self.data_obj, self.tab_widget, df, table_name, None)
                    
        # Find the existing vertical layout in the current layout
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and isinstance(item.layout(), QVBoxLayout):
                existing_vertical_layout = item.layout()
                break

        # If there is an existing vertical layout, add the new instance to it
        if existing_vertical_layout:
            existing_vertical_layout.addWidget(new_instance)
        return

    def create_column_checkboxes(self) -> QCheckBox:
        """
        Create the checkboxes that allows for user to toggle columns in dataframe table
        """
        column_checkboxes = {}
        for column in self.dataframe.columns:
            checkbox = QCheckBox(column)
            checkbox.setChecked(True)
            checkbox.setVisible(self.is_expanded)
            checkbox.stateChanged.connect(self.setup_data)
            column_checkboxes[column] = checkbox
        return column_checkboxes
    
    def toggle_expansion(self) -> None:
        """
        Setups of the column selection items
        """
        self.is_expanded = not self.is_expanded
        self.check_button.setText(self.csv_name + " -" if self.is_expanded else self.csv_name + " +")

        for i in range(self.options_widget.layout().count()):
            option_widget = self.options_widget.layout().itemAt(i).widget()
            option_widget.setVisible(self.is_expanded)
        self.setup_data()
        return

    def load_more_data(self, table, value) -> None:
        """
        Tells the model to load the next 500 rows
        """
        max_value = table.verticalScrollBar().maximum()
        current_value = table.verticalScrollBar().value()

        def is_within_range(value1, value2, range_limit=20):
            return abs(value1 - value2) <= range_limit
    
        if is_within_range(current_value, max_value):
            if len(self.dataframe) > 500:
                self.model_dict[table].update_search_text()
                return

    def setup_data(self) -> None:
        """
        Setup of the data in their respective tables and tabs
        """
        if self.dataframe.is_empty():
            print(f"{self.csv_name} is empty! Table unable to load!")
            return
        
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
            table.selectionModel().selectionChanged.connect(self.update_view)
            table.verticalScrollBar().valueChanged.connect(lambda value, table=table: self.load_more_data(table, value))
            self.check_status(model)
        return

    def check_status(self, model) -> None:
        """
        Toggle the columns that the user selects in the options menu
        """
        for checkbox in self.column_checkboxes.values():
            checkbox.stateChanged.connect(model.update_visible_columns)
        return

    def update_view(self) -> pl.DataFrame:
        """
        Get the data for the user to select and save to CSV
        """
        selected_data = {}

        for table_widget in self.table_dict.values():
            model = self.model_dict[table_widget]
            for index in table_widget.selectionModel().selectedIndexes():
                row = index.row()
                col = index.column()
                header = model.headerData(col, Qt.Horizontal)
                selected_data[header] = selected_data.get(header, []) + [model._dataframe[row, col]]
        self.saved_data = pl.DataFrame(selected_data)
        return

    def save_csv(self) -> None:
        """
        Save CSV based on what user selected in table
        """
        if self.saved_data is not None:
            if not self.saved_data.is_empty():
                file_dialog = QFileDialog()
                file_dialog.setAcceptMode(QFileDialog.AcceptSave)
                file_path, _ = file_dialog.getSaveFileName(self, "Save Selected Data", "", "CSV Files (*.csv)")
                self.saved_data.write_csv(file_path)
                print("Selected Data saved to:", file_path)
        return 


class DataFrameViewer(QWidget):
    """
    Main Viewing Window of the loaded dataframes
    """ 
    def __init__(self, data):
        super().__init__()
        self.data = data

        self._bool = False
        self.model_dict = {}
        self.table_dict = {}
        self.label_dict = defaultdict(int)
        self.init_ui()

    def init_ui(self) -> None:
        """
        Setup the main window display
        """
        self.resize(1920, 1080)
    
        # Setup Layouts
        main_layout = QVBoxLayout()
        labels_layout = QVBoxLayout()
        center_layout = QHBoxLayout()

        self.tab_widget = QTabWidget()
        scroll_area = QScrollArea()
        scroll_widget = QWidget()

        main_splitter = QSplitter()
        self.table_split = QSplitter(Qt.Horizontal)

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

        # Buttons
        csv_button = QPushButton("Save Data") #TODO Make a better placement
        results_button = QPushButton("Load Search Results")
        results_button.clicked.connect(self.load_search_results)

        # Run the data through the expanded text list
        for csv_name, df in self.data.items():
            df = df.rename({col: col.lower() for col in df.columns})
            text_widget = ExpandableText(self, self.tab_widget, df, csv_name, None)
            labels_layout.addWidget(text_widget)

        # Configure layouts
        label_layout.addWidget(self.index_label)
        checkbox_layout.addLayout(label_layout)
        checkbox_layout.addWidget(self.split_search)
        checkbox_layout.addWidget(self.all_table)
        checkbox_layout.addStretch()

        scroll_widget.setLayout(labels_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(500)

        # Create Splitter 
        self.table_split.addWidget(self.tab_widget)
        main_splitter.addWidget(scroll_area)
        main_splitter.addWidget(self.table_split)
        main_splitter.setStretchFactor(0, 1)

        # Main Layout
        center_layout.addWidget(main_splitter)
        main_layout.addWidget(results_button)
        main_layout.addWidget(search_bar)
        main_layout.addLayout(checkbox_layout)
        main_layout.addLayout(center_layout)
        self.setLayout(main_layout)
        self.tab_configure()
        return

    def tab_configure(self) -> None:
        """
        Configure the tab functionaility
        """
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.currentChanged.connect(self.update_label)
        self.tab_widget.tabBarDoubleClicked.connect(self.load_splitter)
        self.tab_widget.tabCloseRequested.connect(self.maintabCloseRequested)
        return
    
    def get_current_tab_dataframe(self) -> pl.DataFrame:
        """
        Get the current dataframe of the modified table, hidden columns and all
        """
        current_index = self.tab_widget.currentIndex()
        if current_index != -1:
            current_tab = self.tab_widget.widget(current_index)
            if isinstance(current_tab, QTableView):
                model = current_tab.model()
            return model.current_dataframe()
        return pl.DataFrame()


    def load_splitter(self, index) -> None:
        """
        This allows for the user to double click on the tab and be able to compare a tab on the side
        """
        self._bool = True
        self.new_tab_widget = QTabWidget()
        dataframe = self.get_current_tab_dataframe()

        self.new_tab_widget.setTabsClosable(True)
        self.new_tab_widget.tabCloseRequested.connect(self.tabCloseRequested)

        # Ensure dataframe is not empty before creating splitter item
        if not dataframe.is_empty():
            new_name = f"{self.tab_widget.tabText(index)} - {index}"
            ExpandableText(self, self.new_tab_widget, dataframe, new_name, index)
        return

    def tabCloseRequested(self) -> None:
        """
        Make all tabs after the first one closable
        """
        self.table_split.widget(1).setParent(None)
        return

    def maintabCloseRequested(self, index) -> None:
        """
        Main tab widget closable and search total label from label dict
        """
        del_tab = self.tab_widget.tabText(index)
        if self.table_dict.get(del_tab):
            del self.table_dict[del_tab]
            del self.label_dict[index]

        self.tab_widget.removeTab(index)
        return

    def search_tables(self) -> None:
        """
        User can type a string here and search all the loaded tables to highlight them
        """
        self.search_text = self.sender().text()
        def run_search(tab) -> None:
            """
            Check if user is search all existing tables or not
            """
            if self.all_table.isChecked():
                for idx in range(len(tab)):
                    index_table = tab.widget(idx)
                    self.table_model_set(index_table)
                return
            
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

    def table_model_set(self, index_table) -> QAbstractTableModel:
        """
        Check if index table is valid before searching
        """
        if isinstance(index_table, QTableView):
            model = index_table.model()
            model.text = self.search_text
            search = model.update_search_text()

            # Populate the found items label and label dict
            self.found_items(search, index_table)
        return model
    
    def found_items(self, search, index_table) -> None: 
        """
        Process the number of found items in a table
        """
        index = self.tab_widget.indexOf(index_table)
        self.label_dict[index] = search

        # Update dictionary based on index
        curr_index = self.tab_widget.currentIndex()
        self.update_label(curr_index)
        return

    def update_label(self, index) -> None:
        """
        Display the proper found items for individual tables focused
        """
        if not self.label_dict:
            self.index_label.setText("No items found.")
            return

        label_val = self.label_dict[index]
        total_found = sum(self.label_dict.values())
        self.index_label.setText(f"{label_val} of {total_found} total found in table.")
        return
    
    def load_search_results(self) -> None:
        """
        Load the search results into the results window
        """
        self.tab_dict = {}
        self.result_tab = QTabWidget()
        self.central_widget = QWidget()
        find_items_layout = QVBoxLayout(self.central_widget)

        # Iterate through each tab and their table
        for index in range(self.tab_widget.count()):
            tab_name = self.tab_widget.tabText(index)
            model = self.tab_widget.widget(index).model()
            data = model.get_result()

            # Make table model and apply
            model = DataFrameTableModel(data, None)

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
            return
        
        # Load the find items window
        self.central_widget.show()
        return

    def on_clicked(self) -> None:
        """
        Index to the right highlighted value when clicked
        """
        current_index = self.result_tab.currentIndex()
        tab_item = self.tab_dict[self.result_tab.tabText(current_index)]
        self.tab_widget.setCurrentIndex(tab_item[0])

        # Defined tables
        current_table = self.tab_widget.widget(tab_item[0])
        results_table = self.result_tab.widget(tab_item[0])

        # Go to selected table index
        selected_indexes = tab_item[1].selectionModel().selectedIndexes()
        if not selected_indexes:
            return
        
        index = results_table.model().data(selected_indexes[0], Qt.DisplayRole)

        # Scroll through the batch size value to get to the value of interest
        val = current_table.verticalScrollBar()
        for _ in range(int(index)):
            val.setValue(val.maximum())
        current_table.selectRow(int(index)-1)
        return
