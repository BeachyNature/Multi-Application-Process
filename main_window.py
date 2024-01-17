from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QCheckBox

import user_config
import animated_lineplot
import three_d_plot
import multiple_csv
import multiple_plots

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Setup data
        self._bool = False
        self.user_instance = user_config.LoginWindow()

        self.pre_window = QWidget()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Setup Buttons
        self.user_setting_btn = QPushButton('User Settings')
        self.user_setting_btn.clicked.connect(self.run_preferences)
        self.launch_btn = QPushButton('Launch')
        self.launch_btn.clicked.connect(self.run_files)

        # Checkboxes
        self.check_dict = {}
        self.check_names = {'CSV Loader': multiple_csv.FileDialogExample(),
                            '3D Plotter': three_d_plot.ThreeDPlot(),
                            '2D Plotter': animated_lineplot.MainWindow(),
                            'Multi-Plotter': multiple_plots.StaticPlots(),
                            'Video Replayer': None,
                            'Plot Configure': None}
        
        self.layout.addWidget(self.user_setting_btn)
        self.layout.addWidget(self.launch_btn)
        self.define_checkbox()

    def define_checkbox(self):
        self.layout_main = QVBoxLayout()

        data = update_file()
        for key, value in self.check_names.items():
            if key in data:
                self.check_dict[key] = [QCheckBox(key), data[key], value]
                checkboxes = self.check_dict[key][0]
                checkboxes.toggled.connect(self.check_button_act)
                checkboxes.setChecked(data[key])
                self.layout_main.addWidget(checkboxes)
            else:
                # Not checked fields
                self.check_dict[key] = [QCheckBox(key), False, value]
                checkboxes = self.check_dict[key][0]
                checkboxes.toggled.connect(self.check_button_act)
                self.layout_main.addWidget(checkboxes)

    def run_preferences(self):
        self._bool = True
        self.pre_window.setLayout(self.layout_main)
        self.pre_window.setGeometry(300, 300, 300, 150)
        self.pre_window.setWindowTitle('User Preference Window')
        self.pre_window.show()

    def check_button_act(self, state):
        sender = self.sender()
        if sender.isEnabled() and self._bool:
            user_config.LoginWindow.save_checkbox_state(self.user_instance, sender.text(), state)

    def run_files(self):
        check_json = update_file()
        for key in check_json:
            if check_json[key] == True:
                self.run = self.check_dict[key][2]
                if self.run is not None:
                    self.run.show()


"""
Gets the user configuration settings, accessible from other classes
"""
def update_file():
    user_instance = user_config.LoginWindow()
    user = user_config.LoginWindow.load_users(user_instance)
    config = dict(list(user.items())[1:])
    return config
