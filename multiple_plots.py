import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import CheckButtons

import main_window

class StaticPlots(QWidget):
    def __init__(self):
        super().__init__()
        # instance = main_window.MainWindow()

        # self.central_widget = QWidget(self)
        self.layout = QVBoxLayout()
        self.figure, self.ax = plt.subplots(2, 2, figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        # self.central_layout.addWidget(self.central_widget)
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

        # Data setup
        t = np.arange(0.0, 2.0, 0.01)
        s0 = np.sin(2*np.pi*t)
        s1 = np.sin(4*np.pi*t)
        s2 = np.sin(6*np.pi*t)
        s3 = np.sin(8*np.pi*t)
        s4 = np.sin(10*np.pi*t)
        s5 = np.sin(12*np.pi*t)
        s6 = np.sin(14*np.pi*t)

        # Plot the multiple lineplot
        self.l0, = self.ax[0, 0].plot(t, s0, lw=2, color='black', label='1 Hz')
        self.l1, = self.ax[0, 0].plot(t, s1, lw=2, color='red', label='2 Hz')
        self.l2, = self.ax[0, 0].plot(t, s2, lw=2, color='green', label='3 Hz')
        self.l3, = self.ax[0, 0].plot(t, s3, lw=2, color='blue', label='4 Hz')

        self.lines_by_label = {l.get_label(): l for l in [self.l0, self.l1, self.l2, self.l3]}
        line_colors = [l.get_color() for l in self.lines_by_label.values()]

        # Make check buttons with all plotted lines with correct visibility
        self.rax = self.ax[0, 0].inset_axes([0.0, 0.0, 0.12, 0.2])
        self.check = CheckButtons(
            ax=self.rax,
            labels=self.lines_by_label.keys(),
            actives=[l.get_visible() for l in self.lines_by_label.values()],
            frame_props={'edgecolor': line_colors},
            check_props={'facecolor': line_colors},
        )
        self.check.on_clicked(self.callback)

        # Plot the other three plots
        self.l4, = self.ax[0, 1].plot(t, s4, lw=2, color='red', label='2 Hz')
        self.l5, = self.ax[1, 0].plot(t, s5, lw=2, color='green', label='3 Hz')
        self.l6, = self.ax[1, 1].plot(t, s3, lw=2, color='blue', label='4 Hz')

        print(f"{self.main() = }")

    def callback(self, label):
        ln = self.lines_by_label[label]
        ln.set_visible(not ln.get_visible())
        ln.figure.canvas.draw_idle()

    def main(self):
        epic = main_window.update_file()
        print(f"{epic = }")
        return epic
