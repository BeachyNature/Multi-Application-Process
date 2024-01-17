from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QTableWidget, QVBoxLayout, QWidget, QTableWidgetItem, QLineEdit, QPushButton, QDialog, QGridLayout, QAbstractItemView
from PyQt5.QtGui import QBrush
from PyQt5.QtCore import Qt
import sys
import pandas as pd

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.tab_widget = QTabWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.tab_widget)

        # Show Highlighted Values button
        self.show_values_button = QPushButton("Show Highlighted Values", self)
        self.show_values_button.clicked.connect(self.show_highlighted_values)
        self.central_layout.addWidget(self.show_values_button)

        # Search bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.search)

        # Next button
        self.next_button = QPushButton("Next", self)
        self.next_button.clicked.connect(self.next_highlighted)

        self.central_layout.addWidget(self.search_bar)
        self.central_layout.addWidget(self.next_button)

        self.highlighted_items = []
        self.current_highlight_index = -1

        # Call a function to populate the tabs
        self.populate_tabs()


    def populate_tabs(self):
        # Create sample DataFrames
        data1 = {'Name': ['Alice', 'Bob', 'Charlie'],
                 'Age': [25, 30, 22]}
        df1 = pd.DataFrame(data1)

        data2 = {'Product': ['Apple', 'Banana', 'Orange'],
                 'Price': [1.0, 0.5, 0.75]}
        df2 = pd.DataFrame(data2)

        # Create and add tabs
        self.add_tab(df1, "Tab 1")
        self.add_tab(df2, "Tab 2")

    def add_tab(self, dataframe, tab_name):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        table_widget = QTableWidget(tab)
        table_widget.setColumnCount(dataframe.shape[1])
        table_widget.setRowCount(dataframe.shape[0])

        # Populate the table with data from the DataFrame
        for row in range(dataframe.shape[0]):
            for col in range(dataframe.shape[1]):
                item = QTableWidgetItem(str(dataframe.iat[row, col]))
                table_widget.setItem(row, col, item)

        tab_layout.addWidget(table_widget)
        self.tab_widget.addTab(tab, tab_name)

    def search(self, keyword):
        self.highlighted_items = []

        for tab_index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(tab_index)
            table_widget = tab.findChild(QTableWidget)

            for row in range(table_widget.rowCount()):
                for col in range(table_widget.columnCount()):
                    item = table_widget.item(row, col)
                    if item is not None:
                        text = item.text()
                        if keyword.lower() in text.lower():
                            item.setBackground(QBrush(Qt.yellow))
                            self.highlighted_items.append(item)
                        else:
                            item.setBackground(QBrush(Qt.white))

        self.current_highlight_index = -1

    def next_highlighted(self):
        if self.highlighted_items:
            if self.current_highlight_index >= 0:
                self.highlighted_items[self.current_highlight_index].setBackground(QBrush(Qt.yellow))
                
            self.current_highlight_index = (self.current_highlight_index + 1) % len(self.highlighted_items)
            next_item = self.highlighted_items[self.current_highlight_index]
            next_item.setBackground(QBrush(Qt.green))

            # Get the tab index where the next_item belongs
            tab_index = -1
            for tab_index in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(tab_index)
                table_widget = tab.findChild(QTableWidget)
                if next_item in table_widget.findItems(next_item.text(), Qt.MatchExactly):
                    break
            
            # Switch to the tab and scroll to the next item
            if tab_index >= 0:
                self.tab_widget.setCurrentIndex(tab_index)
                table_widget = self.tab_widget.currentWidget().findChild(QTableWidget)
                table_widget.scrollToItem(next_item, QAbstractItemView.PositionAtCenter)

    def show_highlighted_values(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Highlighted Values")

        layout = QGridLayout(dialog)

        # Create a table widget for the highlighted values
        table_widget = QTableWidget(dialog)
        table_widget.setColumnCount(1)
        table_widget.setRowCount(len(self.highlighted_items))
        table_widget.setHorizontalHeaderLabels(["Highlighted Value"])

        for index, item in enumerate(self.highlighted_items):
            value = item.text()
            table_widget.setItem(index, 0, QTableWidgetItem(value))

        layout.addWidget(table_widget)
        dialog.setLayout(layout)

        dialog.exec_()

    def focus_on_item(self, clicked_item):
        for tab_index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(tab_index)
            table_widget = tab.findChild(QTableWidget)

            for row in range(table_widget.rowCount()):
                for col in range(table_widget.columnCount()):
                    item = table_widget.item(row, col)
                    if item is not None and item.text() == clicked_item.text():
                        self.tab_widget.setCurrentIndex(tab_index)
                        table_widget.scrollToItem(item, QAbstractItemView.PositionAtCenter)
                        item.setSelected(True)
                        return



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())

