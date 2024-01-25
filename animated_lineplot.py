from PyQt5.QtWidgets import QApplication, QVBoxLayout, QPushButton, QWidget, QSlider, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys

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
        self.selected_points = {}

        # Connect lasso selection to the callback
        self.lasso = LassoSelector(self.ax, onselect=self.on_lasso_selection)

        # Set seed for reproducibility
        np.random.seed(42)

        #SETUP
        num_points = 100
        x_values = np.arange(num_points)
        names = ['Alice', 'Bob', 'Charlie']

        # Creating a random dataframe with 5 rows and 3 columns
        data = {'Name': np.concatenate([[name] * num_points for name in names]),
                'X': np.tile(x_values, len(names)),
                'Y': np.concatenate([2 * x_values + np.random.normal(0, 5, num_points) for _ in range(len(names))])}

        self.df = pd.DataFrame(data)


    """
    User is able to select items in the plot
    """
    def on_lasso_selection(self, verts):
        # Callback function for lasso selection
        path = Path(verts)
        selected_points_data = {}

        for name, group in self.df.groupby('Name'):
            x_data = group['X'].tolist()
            y_data = group['Y'].tolist()

            points_inside_lasso = [i for i in range(len(x_data)) if path.contains_point((x_data[i], y_data[i]))]

            for i in points_inside_lasso:
                if name in selected_points_data:
                    selected_points_data[name].append([x_data[i], y_data[i]])
                else:
                    selected_points_data[name] = [[x_data[i], y_data[i]]]

        self.selected_points = selected_points_data
        self.selected_values()


    """
    Update the plot by animating
    """
    def update_plot(self, frame):
        self.ax.clear()
        for name, group in self.df.groupby('Name'):
            self.x_data = group['X'][:frame]
            self.y_data = group['Y'][:frame]
            
            self.ax.plot(
                self.x_data,
                self.y_data,
                label=name,
                marker='o',
                linestyle='-',
                markersize=8
            )

        self.ax.legend()
        self.canvas.draw()


    """
    Select the items in the line plot
    """
    def selected_values(self):
        # Highlight selected points with a different marker or color
        if self.selected_points:
            for key, value in self.selected_points.items():
                # Separating first and second values
                x_value, y_value = zip(*value)
    
                self.ax.scatter(
                    x_value,
                    y_value,
                    marker='X',
                    color='red',
                    s=100
                )

        self.canvas.draw()


    """
    Move the slider with the animation frames
    """
    def animate_slider(self, frame, duration, slider_end_val):
        num_steps = 100
        step_size = frame / num_steps

        for i in range(num_steps + 1):
            val = i * step_size
            if not self.animation_running:
                break
            plt.pause(duration / num_steps)
            self.update_plot(int(val))


    """
    Stops the animation from playing
    """
    def stop_animation(self):
        self.animation_running = False


"""
Main Window that contains the lineplot
"""
class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.central_widget = MatplotlibWidget(self)

        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.start_animation)

        self.stop_button = QPushButton('Stop', self)
        self.stop_button.clicked.connect(self.stop_animation)

        self.info_button = QPushButton('Show Info', self)
        self.info_button.clicked.connect(self.show_selected_info)

        self.slider_timer = None
        self.slider = QSlider(self)
        self.slider.setOrientation(1)
        self.slider.setRange(0, 100)
        self.slider.valueChanged.connect(self.slider_changed)

        self.init_layout()
        self.worker_thread = None

    def init_layout(self):
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.info_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.central_widget)
        main_layout.addWidget(self.slider)

        self.setLayout(main_layout)
        self.setGeometry(100, 100, 1600, 900)

    def start_animation(self):
        if not self.central_widget.animation_running:
            self.central_widget.animation_running = True
            self.slider_timer = QTimer(self)
            self.slider_timer.timeout.connect(self.increment_slider)
            self.slider_timer.start(100)

    def increment_slider(self):
        current_value = self.slider.value()
        if current_value < self.slider.maximum():
            self.slider.setValue(current_value + 1)
        else:
            self.slider_timer.stop()
            self.central_widget.animation_running = False

    def stop_animation(self):
        if self.central_widget.animation_running:
            self.central_widget.stop_animation()

    def slider_changed(self, value):
        frame = value
        self.central_widget.update_plot(frame)
        if not self.central_widget.animation_running:
            if self.worker_thread is not None:
                self.worker_thread.terminate()
                self.worker_thread = None
    
    def show_selected_info(self):
        data_dict = self.central_widget.selected_points
        if data_dict:
             # Use list comprehension to flatten the data
            rows = [(key, x, y) for key, values_list in data_dict.items() for x, y in values_list]
            df = pd.DataFrame(rows, columns=self.central_widget.df.columns)
        else:          
            QMessageBox.warning(self, 'No Selection', 'No points selected.')
            df = self.central_widget.df

        # Setup table
        self.table_window = QWidget()
        table_widget = QTableWidget(self)
        table_widget.setColumnCount(2)
        table_widget.setHorizontalHeaderLabels(['X', 'Y'])

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(table_widget)
        self.table_window.setLayout(layout)

        # Set the number of rows and columns
        table_widget.setRowCount(df.shape[0])
        table_widget.setColumnCount(df.shape[1])

        # Set column headers
        table_widget.setHorizontalHeaderLabels(df.columns)

        # Populate the QTableWidget with DataFrame data
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iloc[i, j]))
                table_widget.setItem(i, j, item)

        # Launch the Window  to display selected indexes
        self.table_window.show()



# THIS IS FOR TESTING
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin =  MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
            