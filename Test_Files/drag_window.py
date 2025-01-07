import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel

class DraggableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            tab_text = event.mimeData().text()
            self.addTab(QLabel(tab_text), tab_text)
            event.acceptProposedAction()

class SecondaryWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Secondary Window')
        self.setGeometry(700, 100, 600, 400)

        self.tab_widget = DraggableTabWidget(self)

        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.startServer()

    def startServer(self):
        def handle_connection(conn):
            with conn:
                data = conn.recv(1024)
                if data:
                    tab_text = data.decode()
                    self.tab_widget.addTab(QLabel(tab_text), tab_text)

        def server():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', 65432))
                s.listen()
                while True:
                    conn, _ = s.accept()
                    threading.Thread(target=handle_connection, args=(conn,)).start()

        threading.Thread(target=server, daemon=True).start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sec_win = SecondaryWindow()
    sec_win.show()
    sys.exit(app.exec_())
