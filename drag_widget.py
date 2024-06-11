import sys
import socket
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag

class DraggableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            distance = (event.pos() - self.drag_start_position).manhattanLength()
            if distance >= QApplication.startDragDistance():
                self.performDrag()
        super().mouseMoveEvent(event)

    def performDrag(self):
        drag = QDrag(self)
        mimeData = QMimeData()

        current_index = self.currentIndex()
        if current_index != -1:
            tab_text = self.tabText(current_index)
            mimeData.setText(tab_text)
            drag.setMimeData(mimeData)

            pixmap = self.widget(current_index).grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().topLeft())

            if drag.exec_(Qt.MoveAction) == Qt.MoveAction:
                self.removeTab(current_index)
                self.sendData(tab_text)

    def sendData(self, tab_text):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', 65432))
            s.sendall(tab_text.encode())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Main Window')
        self.setGeometry(100, 100, 600, 400)

        self.tab_widget = DraggableTabWidget(self)
        for i in range(3):
            self.tab_widget.addTab(QLabel(f'Tab {i + 1} Content'), f'Tab {i + 1}')

        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
