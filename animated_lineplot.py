import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QSlider
from PyQt5.QtCore import QThread, pyqtSignal, QTimer

class WorkerThread(QThread):
    update_signal = pyqtSignal(int)

    def __init__(self, func, fargs=(), interval=1000, parent=None):
        super(WorkerThread, self).__init__(parent)
        self.func = func
        self.fargs = fargs
        self.interval = interval

    def run(self):
        self.animation = FuncAnimation(
            self.fargs[0].fig,
            self.func,
            frames=self.fargs[1],
            fargs=(self.fargs[0], self.fargs[2], self.fargs[3]),
            interval=self.interval,
            repeat=False
        )

        self.animation._stop = not self.fargs[0].animation_running
        self.animation._start()


class MatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget, self).__init__(parent)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.animation_running = False

    def update_plot(self, frame):
        self.ax.clear()  # Clear previous plot
        self.ax.plot(
            np.linspace(0, 10, 100)[:frame],
            np.cumsum(np.random.randn(100))[:frame],
            label='Line 1',
            marker='o',
            linestyle='-',
            markersize=8
        )

        self.ax.plot(
            np.linspace(0, 10, 50)[:frame],
            np.cumsum(np.random.randn(50))[:frame],
            label='Line 2',
            marker='o',
            linestyle='-',
            markersize=8
        )

        # Limiter
        self.ax.set_ylim(-15, 20)
        self.ax.set_xlim(0, 10)

        self.ax.legend()
        self.canvas.draw()

    def animate_slider(self, frame, duration, slider_end_val):
        num_steps = 100
        step_size = frame / num_steps

        for i in range(num_steps + 1):
            val = i * step_size
            if not self.animation_running:
                break
            plt.pause(duration / num_steps)
            self.update_plot(int(val))

    def stop_animation(self):
        self.animation_running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.central_widget = MatplotlibWidget(self)
        self.setCentralWidget(self.central_widget)

        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.start_animation)

        self.stop_button = QPushButton('Stop', self)
        self.stop_button.clicked.connect(self.stop_animation)

        self.slider_timer = None
        self.slider = QSlider(self)
        self.slider.setOrientation(1)  # 1 represents vertical orientation
        self.slider.setRange(0, 100)
        self.slider.valueChanged.connect(self.slider_changed)

        self.init_layout()
        self.worker_thread = None

    
    #TODO: Remove 2d plot into its own window, have this as a central hub to select
    # Initialize main window items
    def init_layout(self):
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.central_widget)
        main_layout.addWidget(self.slider)

        widget = QWidget(self)
        widget.setLayout(main_layout)
        self.setGeometry(100, 100, 1600, 900)
        self.setCentralWidget(widget)

    # Starts tbe 2D Animation
    def start_animation(self):
        if not self.central_widget.animation_running:
            self.central_widget.animation_running = True

            # Increment the slider value using a QTimer
            self.slider_timer = QTimer(self)
            self.slider_timer.timeout.connect(self.increment_slider)
            self.slider_timer.start(100)  # Adjust the interval as needed

    # Increments the slider and stops when maxed out.
    def increment_slider(self):
        current_value = self.slider.value()
        if current_value < self.slider.maximum():
            self.slider.setValue(current_value + 1)
        else:
            self.slider_timer.stop()
            self.central_widget.animation_running = False

    # TODO: Program like 3d plot with resume and pause
    def stop_animation(self):
        if self.central_widget.animation_running:
            self.central_widget.stop_animation()

    # Terminate working thread if slider is interupted
    def slider_changed(self, value):
        frame = value
        self.central_widget.update_plot(frame)
        if not self.central_widget.animation_running:
            if self.worker_thread is not None:
                self.worker_thread.terminate()
                self.worker_thread = None
