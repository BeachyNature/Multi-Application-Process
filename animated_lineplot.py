from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QPushButton, QWidget, QSlider, QMessageBox, QTableWidget, QTableWidgetItem, QLabel
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import LassoSelector
from matplotlib.path import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
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

        self.animation_running = False
        self.selected_points = {}

        self.label = QLabel("EPIC")

        # Setup Plot Figure
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Connect lasso selection to the callback
        self.lasso = LassoSelector(self.ax, onselect=self.on_lasso_selection)

        # Set seed for reproducibility
        np.random.seed(42)

        # Setup data
        num_points = 100
        x_values = np.arange(num_points)
        names = ['Alice', 'Bob', 'Charlie']

        # Generate random times
        start = datetime.datetime(2022, 1, 1)
        end = datetime.datetime(2022, 12, 31)
        times = [np.random.randint(start.timestamp(), end.timestamp()) for _ in range(num_points * len(names))]
        times = [datetime.datetime.fromtimestamp(t) for t in times]

        # Repeat and tile arrays to match the length
        names_repeat = np.repeat(names, num_points)
        x_values_tile = np.tile(x_values, len(names))

        # Creating a random dataframe with 5 rows and 3 columns
        data = {'Name': names_repeat,
                'X': x_values_tile,
                'Y': np.concatenate([2 * x_values + np.random.normal(0, 5, num_points) for _ in range(len(names))]),
                'Time': times}

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
            if not self.x_data.empty:
                self.label.setText(str(self.x_data.iloc[-1]))
  
            self.ax.plot(
                self.x_data,
                self.y_data,
                label=name,
                marker='o',
                linestyle='-',
                markersize=8
            )

            # Add annotations for specific x-values
            specific_x_value = [10, 30, 50]  # Change this to the specific x-value you want to annotate
            for x, y in zip(self.x_data, self.y_data):
                if x in specific_x_value:
                    annotation_text = f'{name}'
                    self.ax.annotate(annotation_text,
                                    xy=(x, y),
                                    xytext=(0, 10),
                                    textcoords='offset points',
                                    ha='center',
                                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                                    fontsize=12)
                    
        self.ax.legend()
        self.canvas.draw()


    """
    Select the items in the line plot
    """
    def selected_values(self):
        # Clear previous highlights
        for collection in self.ax.collections:
            collection.remove()

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
Main Window that contains the lineplot
"""
class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.central_widget = MatplotlibWidget(self)

        self.label = QLabel()

        # Setup buttons
        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.toggle_animation)

        self.info_button = QPushButton('Show Info', self)
        self.info_button.clicked.connect(self.show_selected_info)

        # Progress bar to show the animation process
        self.slider_timer = None
        self.slider = QSlider(self)
        self.slider.setOrientation(1)
        self.slider.setRange(0, 100)
        self.slider.valueChanged.connect(self.slider_changed)

        # Slider timer to increment as needed
        self.animation_paused = False
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.increment_slider)

        self.worker_thread = None
        self.init_layout()


    """
    Inital window setup
    """
    def init_layout(self):
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.info_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.central_widget)
        main_layout.addWidget(self.slider)
        main_layout.addWidget(self.label)

        self.setLayout(main_layout)
        self.setGeometry(100, 100, 1600, 900)


    """
    Animation Toggler, pause, resume, restart
    """
    def toggle_animation(self):
        if self.central_widget.animation_running:
            self.central_widget.animation_running = False
            self.start_button.setText('Resume')
            self.animation_timer.stop()

        elif self.slider.value() == self.slider.maximum():
            self.central_widget.animation_running = True
            self.start_button.setText("Pause")
            self.animation_timer.start(100)
            self.slider.setValue(0)

        elif not self.central_widget.animation_running:
            self.central_widget.animation_running = True
            self.start_button.setText('Pause')
            self.animation_timer.start(100)


    """
    Increment slider to show progress of animation progress
    """
    def increment_slider(self):
        current_value = self.slider.value()
        if current_value < self.slider.maximum():
            self.slider.setValue(current_value + 1)
        elif current_value == self.slider.maximum():
            self.central_widget.animation_running = False
            self.start_button.setText("Restart")
            self.animation_timer.stop()
        else:
            self.central_widget.animation_running = False
            self.animation_timer.stop()


    """
    Update plot as the slider moves
    """
    def slider_changed(self, value):
        frame = value
        self.central_widget.update_plot(frame)
        if not self.central_widget.animation_running:
            if self.worker_thread is not None:
                self.worker_thread.terminate()
                self.worker_thread = None
    

    """
    Display a table to show additional information on selected data
    """
    def show_selected_info(self):
        data_dict = self.central_widget.selected_points
        if data_dict:
            selected_rows = []
            for key, values_list in data_dict.items():
                for x, y in values_list:
                    # Filter rows based on selected x and y values
                    selected_rows.extend(self.central_widget.df[(self.central_widget.df['Name'] == key) & (self.central_widget.df['X'] == x) & (self.central_widget.df['Y'] == y)].to_dict('records'))

            if selected_rows:
    
                # Create a DataFrame from the selected rows
                df = pd.DataFrame(selected_rows)
                
                # Setup table
                self.table_window = QWidget()
                table_widget = QTableWidget(self)
                table_widget.setColumnCount(len(df.columns))
                table_widget.setHorizontalHeaderLabels(df.columns)

                # Create layout
                layout = QVBoxLayout()
                layout.addWidget(table_widget)
                self.table_window.setLayout(layout)

                # Set the number of rows
                table_widget.setRowCount(df.shape[0])

                # Populate the QTableWidget with DataFrame data
                for i in range(df.shape[0]):
                    for j in range(df.shape[1]):
                        item = QTableWidgetItem(str(df.iloc[i, j]))
                        table_widget.setItem(i, j, item)

                # Launch the Window  to display selected indexes
                self.table_window.show()
            else:
                QMessageBox.warning(self, 'No Data Found', 'No matching data found.')
        else:
            QMessageBox.warning(self, 'No Selection', 'No points selected.')


# THIS IS FOR TESTING
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin =  MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
            