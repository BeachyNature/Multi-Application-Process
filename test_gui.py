import sys
import numpy as np
from PyQt5.QtCore import QRect
from PyQt5.QtCore import QPropertyAnimation
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QFrame

class SidePanel(QWidget):
    def __init__(self):
        super().__init__()
        
        self.frame = QFrame()
        self.frame.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        
        layout = QVBoxLayout()
        
        self.button = QPushButton("Close")
        self.button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.button.clicked.connect(self.toggle_panel)
        layout.addWidget(self.button)
        
        self.frame.setLayout(layout)
        
        self.panel_width = 200
        self.panel_height = 400
        self.closed_pos = QRect(-self.panel_width, 0, self.panel_width, self.panel_height)
        self.open_pos = QRect(0, 0, self.panel_width, self.panel_height)
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.frame)
        self.setLayout(self.layout)
        
        self.setGeometry(self.closed_pos)
        
    def toggle_panel(self):
        if self.geometry() == self.closed_pos:
            self.open()
        else:
            self.close()
    
    def open(self):
        self.raise_()  # Bring the panel to the front
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEndValue(self.open_pos)
        self.animation.start()
    
    def close(self):
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEndValue(self.closed_pos)
        self.animation.start()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.side_panel = SidePanel()
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(QVBoxLayout())
        self.centralWidget().layout().addWidget(self.side_panel)
        
        self.menu_button = QPushButton()
        self.menu_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                border-image: url('hamburger.png');
                width: 32px;
                height: 32px;
            }
            QPushButton:hover {
                border: 1px solid #888;
            }
            """
        )
        self.menu_button.clicked.connect(self.side_panel.toggle_panel)
        self.menu_button.setFixedSize(32, 32)
        
        self.toolbar = self.addToolBar("Menu")
        self.toolbar.addWidget(self.menu_button)
        
        self.plot_widget = PlotWidget()
        self.centralWidget().layout().addWidget(self.plot_widget)

class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.canvas)
        
        self.plot()

    def plot(self):
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        self.ax.plot(x, y)
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec_())
