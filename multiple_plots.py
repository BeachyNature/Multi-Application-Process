from PyQt5.QtWidgets import QWidget, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import CheckButtons
from matplotlib import gridspec

import main_window

class StaticPlots(QWidget):
    def __init__(self):
        super().__init__()

        # User file data
        data = main_window.update_file()

        # Window Setup
        self.row = 0
        self.fig = plt.figure()
        self.canvas = FigureCanvas(self.fig)
        
        self.layout = QVBoxLayout()
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

        # Plot the multiple lineplot;
        # if user has this selected in their settings
        if data['Plot Configure'] is not False:
            self.ax = self.plot_bottom()
            self.l0, = self.ax.plot(t, s0, lw=2, color='black', label='1 Hz')
            self.l1, = self.ax.plot(t, s1, lw=2, color='red', label='2 Hz')
            self.l2, = self.ax.plot(t, s2, lw=2, color='green', label='3 Hz')
            self.l3, = self.ax.plot(t, s3, lw=2, color='blue', label='4 Hz')

            self.lines_by_label = {l.get_label(): l for l in [self.l0, self.l1, self.l2, self.l3]}
            line_colors = [l.get_color() for l in self.lines_by_label.values()]

            # Make check buttons with all plotted lines with correct visibility
            self.rax = self.ax.inset_axes([0.0, 0.0, 0.12, 0.2])
            self.check = CheckButtons(
                ax=self.rax,
                labels=self.lines_by_label.keys(),
                actives=[l.get_visible() for l in self.lines_by_label.values()],
                frame_props={'edgecolor': line_colors},
                check_props={'facecolor': line_colors},
            )
            self.check.on_clicked(self.callback)

        if data['Static Plot'] is not False:
            # Plot the other three plots
            self.plot_bottom().plot(t, s4, lw=2, color='red', label='2 Hz')
            self.plot_bottom().plot(t, s5, lw=2, color='green', label='3 Hz')
            self.plot_bottom().plot(t, s3, lw=2, color='blue', label='4 Hz')
            self.show()


    """
    Toggles selected lines in the created legend
    """
    def callback(self, label):
        ln = self.lines_by_label[label]
        ln.set_visible(not ln.get_visible())
        ln.figure.canvas.draw_idle()


    """
    Dynamically plots on new subplots whether one is removed or not
    """
    def plot_bottom(self):
        self.row += 1
        gs = gridspec.GridSpec(self.row, 1)

        # Reposition existing subplots
        for i, ax in enumerate(self.fig.axes):
            ax.set_position(gs[i].get_position(self.fig))
            ax.set_subplotspec(gs[i])

        # Add new subplot
        new_ax = self.fig.add_subplot(gs[self.row-1])
        return new_ax

