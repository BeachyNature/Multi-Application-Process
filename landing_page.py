from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QCheckBox

import login_window
import animated_lineplot
import three_d_plot
import multiple_csv
import multiple_plots
import video_replay


"""
This is a landing page, this is for the user to select what tools they want to run. This is subject to change.
"""
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Setup data
        self._bool = False
        self.user_instance = login_window.LoginWindow()

        self.pre_window = QWidget()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Setup Buttons
        self.user_setting_btn = QPushButton('User Settings')
        self.user_setting_btn.clicked.connect(self.run_preferences)
        self.launch_btn = QPushButton('Launch')
        self.launch_btn.clicked.connect(self.run_files)

        # Checkboxes - configures the different applications that load and whats within them.
        self.check_dict = {}
        self.check_names = {'CSV Loader': multiple_csv.FileDialog,
                            '3D Plotter': three_d_plot.ThreeDPlot,
                            '2D Plotter': animated_lineplot.MainWindow,
                            'Multi-Plotter': multiple_plots.StaticPlots,
                            'Video Replayer': video_replay.VideoSelector,
                            'Plot Configure': None,
                            'Static Plot': None}
        
        self.layout.addWidget(self.user_setting_btn)
        self.layout.addWidget(self.launch_btn)
        self.define_checkbox()


    """
    Create the checkboxes and their functionaility
    """
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
        self._bool = True


    """
    Run the user preference window with the checkboxes
    """
    def run_preferences(self):
        self.pre_window.setLayout(self.layout_main)
        self.pre_window.setGeometry(300, 300, 300, 150)
        self.pre_window.setWindowTitle('User Preference Window')
        self.pre_window.show()


    """
    Change the users preferences in their created json file
    """
    def check_button_act(self, state):
        sender = self.sender()
        if sender.isEnabled() and self._bool:
            login_window.LoginWindow.save_checkbox_state(self.user_instance, sender.text(), state)


    """
    Run the Selected files based on checkbox preferences
    """
    def run_files(self):
        check_json = update_file()

        self.instances_to_show = [
            class_type() for key, class_type in self.check_names.items() if check_json.get(key) and callable(class_type)
        ]

        for instance in self.instances_to_show:
            instance.show()


"""
Gets the user configuration settings, accessible from other classes/files
"""
def update_file():
    user_instance = login_window.LoginWindow()
    user = login_window.LoginWindow.load_users(user_instance)
    config = dict(list(user.items())[1:])
    return config
