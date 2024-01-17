import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider, QPushButton, QToolBar
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

class MatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget, self).__init__(parent)
        self.num = 0
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)

        self.setLayout(layout)

        self.animation_running = False
        self.paused = False
        self.zoom_point = None

    def update_plot(self, frame, data):
        self.ax.clear()

        colors = iter(['b', 'g', 'r', 'c', 'm', 'y'])  # List of colors for each line
        for traj in data:
            traj = np.array(traj)
            x = traj[:frame, 0]
            y = traj[:frame, 1]
            z = traj[:frame, 2]

            color = next(colors)
            self.ax.plot3D(x, y, z, linestyle='dashed', color=color)
            self.ax.scatter(x, y, z, s=50, color=color)  # Plot big circles at each point

        # Set dynamic axis limits based on the data range
        x_min, x_max = np.min(data[:, :, 0]), np.max(data[:, :, 0])
        y_min, y_max = np.min(data[:, :, 1]), np.max(data[:, :, 1])
        z_min, z_max = np.min(data[:, :, 2]), np.max(data[:, :, 2])

        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_zlim(z_min, z_max)

        self.ax.set_xlabel('X-axis')
        self.ax.set_ylabel('Y-axis')
        self.ax.set_zlabel('Z-axis')

        self.canvas.draw()

    def on_click(self, event):
        if self._bool:
            self.num += 1
            x, y, _, _ = self.ax.bbox.bounds
            fraction_x = (event.x - x) / self.ax.bbox.width
            fraction_y = (event.y - y) / self.ax.bbox.height
            self.ax.set_box_aspect((1, 1, 1), zoom=self.num)
            self.ax.get_proj = lambda: np.dot(Axes3D.get_proj(self.ax), np.diag([1 / fraction_x, 1 / fraction_y, 1, 1]))
            self.ax.figure.canvas.draw()
            # self._bool = False

    def zoom_in(self):
        self._bool = True
        self.click_cid = self.ax.figure.canvas.mpl_connect('button_press_event', self.on_click)

    def zoom_out(self):
        self.num -= 1
        if self.num >= 1:
            self.ax.set_box_aspect((1, 1, 1), zoom=self.num)
            self.ax.figure.canvas.draw()
        else:
            self.ax.set_box_aspect((1, 1, 1), zoom=0.9)
            self.ax.figure.canvas.draw()

class ThreeDPlot(QMainWindow):
    def __init__(self):
        super(ThreeDPlot, self).__init__()
        self.value = False
        self.central_widget = MatplotlibWidget(self)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.valueChanged.connect(self.slider_changed)

        self.start_button = QPushButton("Start Animation")
        self.start_button.clicked.connect(self.start_animation)

        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.clicked.connect(self.pause_resume_animation)

        self.zoom_in_button = QPushButton("Zoom In")
        self.zoom_in_button.clicked.connect(self.on_button_click)

        self.zoom_out_button = QPushButton("Zoom Out")
        self.zoom_out_button.clicked.connect(self.central_widget.zoom_out)

        self.pan_left_button = QPushButton("Pan Left")
        self.pan_left_button.clicked.connect(self.pan_left)

        layout = QVBoxLayout()
        layout.addWidget(self.central_widget)
        layout.addWidget(self.slider)
        layout.addWidget(self.start_button)
        layout.addWidget(self.pause_resume_button)

        toolbar = QToolBar()
        toolbar.addWidget(self.zoom_in_button)
        toolbar.addWidget(self.zoom_out_button)
        toolbar.addWidget(self.pan_left_button)

        layout.addWidget(toolbar)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate_slider)

        # Create multiple 3D trajectories for the airplanes
        self.data_3d = create_airplane_trajectories()

    def on_button_click(self):
        if self.value:
            self.value = False
            self.zoom_in_button.setStyleSheet('')
        else:
            self.value = True
            color = QColor(0, 255, 0)  # Set color to green
            self.zoom_in_button.setStyleSheet('background-color: {}'.format(color.name()))
            self.central_widget.zoom_in()

    def slider_changed(self, value):
        self.central_widget.update_plot(value, self.data_3d)

    def start_animation(self):
        if not self.central_widget.animation_running:
            self.central_widget.animation_running = True
            self.central_widget.paused = False
            self.animation_frame = 0

            total_frames = self.slider.maximum() + 1
            total_time = 5.0  # Desired total animation time in seconds
            frame_duration = total_time / total_frames
            self.animation_timer.start(int(frame_duration * 1000))  # Convert to milliseconds

    def animate_slider(self):
        if not self.central_widget.paused:
            if self.animation_frame <= self.slider.maximum():
                self.slider.setValue(self.animation_frame)
                self.animation_frame += 1
            else:
                self.animation_timer.stop()
                self.central_widget.animation_running = False

    def pause_resume_animation(self):
        if self.central_widget.animation_running:
            self.central_widget.paused = not self.central_widget.paused
            if self.central_widget.paused:
                self.pause_resume_button.setText("Resume")
            else:
                self.pause_resume_button.setText("Pause")
        else:
            self.central_widget.paused = False
            self.start_animation()

    def pan_left(self):
        self.central_widget.ax.elev = 20
        self.central_widget.ax.azim -= 10
        self.central_widget.canvas.draw()

def create_airplane_trajectories():
    np.random.seed(0)
    num_airplanes = 3
    num_frames = 100
    traj_data = []
    for _ in range(num_airplanes):
        x = np.cumsum(np.random.randn(num_frames))
        y = np.cumsum(np.random.randn(num_frames))
        z = np.cumsum(np.random.randn(num_frames))
        traj_data.append(np.column_stack((x, y, z)))
    return np.array(traj_data)

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     mainWin = ThreeDPlot()
#     mainWin.show()
#     sys.exit(app.exec_())
