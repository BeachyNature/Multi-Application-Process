import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSlider, QPushButton, QTextEdit, QAction, QListWidget, QFileDialog
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QMutex, QMutexLocker
import cv2
from PyQt5.QtGui import QPixmap, QImage, QWindow
from PIL import Image
import pytesseract

# pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

class TextCaptureThread(QThread):
    textCaptured = pyqtSignal(str)

    def __init__(self, video_captures, text_capture_window):
        super().__init__()
        self.running = False
        self.video_captures = video_captures
        self.text_capture_window = text_capture_window
        self.mutex = QMutex()

    def run(self):
        while True:
            if self.isRunning() and self.running:
                for i, video_capture in enumerate(self.video_captures):
                    ret, frame = video_capture.read()
                    if ret:
                        text = self.capture_text(frame)
                        with QMutexLocker(self.mutex):
                            self.textCaptured.emit(text)

                        self.msleep(100)  # Adjust sleep time as needed
            else:
                self.msleep(1000)  # Sleep for longer when not capturing text

    def start_capture(self):
        with QMutexLocker(self.mutex):
            self.running = True

    def stop_capture(self):
        with QMutexLocker(self.mutex):
            self.running = False

    def capture_text(self, frame):
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh_frame = cv2.threshold(gray_frame, 150, 255, cv2.THRESH_BINARY)
        pil_image = Image.fromarray(thresh_frame)
        text = pytesseract.image_to_string(pil_image)
        return text

class TextCaptureWindow(QTextEdit):
    def __init__(self):
        super().__init__()
        self.hide()

    def append_text(self, text):
        current_text = self.toPlainText()
        formatted_text = f"Captured Text:\n{text}\n{'='*30}\n"
        self.setPlainText(current_text + formatted_text)

class VideoPlayer(QWidget):
    def __init__(self, video_paths, text_capture_thread, text_capture_window):
        super().__init__()

        self.text_capture_thread = text_capture_thread
        self.video_captures = [cv2.VideoCapture(video_path, cv2.CAP_FFMPEG) for video_path in video_paths]
        self.video_labels = [QLabel(self) for _ in video_paths]

        self.play_pause_button = QPushButton("Start Video", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        self.playback_speed_label = QLabel("Playback Speed: 1x", self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.update_slider_duration()

        layout = QVBoxLayout()
        h_layout = QHBoxLayout()

        self.playing = False
        self.playback_speed = 1  # Initial playback speed
        self.timer_interval = 33  # Initial frame update interval
        self.timer.start(self.timer_interval)

        video_durations = [int(video.get(cv2.CAP_PROP_FRAME_COUNT)) for video in self.video_captures]
        self.max_index, self.max_video_duration = max(enumerate(video_durations), key=lambda x: x[1])

        self.playback_slider = QSlider(Qt.Horizontal)
        self.playback_slider.setRange(0, self.max_video_duration)
        self.playback_slider.sliderMoved.connect(self.set_video_position)

        for label in self.video_labels:
            h_layout.addWidget(label)

        layout.addLayout(h_layout)
        layout.addWidget(self.playback_speed_label)
        layout.addWidget(self.playback_slider)
        layout.addWidget(self.play_pause_button)

        self.setLayout(layout)
        self.text_capture_window = text_capture_window

    def update_frame(self):
        if self.playing:
            for i, video_capture in enumerate(self.video_captures):
                ret, frame = video_capture.read()
                if ret:
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = image.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qt_image)
                    self.video_labels[i].setPixmap(pixmap)

            position = int(self.video_captures[self.max_index].get(cv2.CAP_PROP_POS_FRAMES))
            self.playback_slider.setValue(position)

    def set_video_position(self, position):
        for video_capture in self.video_captures:
            video_capture.set(cv2.CAP_PROP_POS_FRAMES, position)

    def update_slider_duration(self):
        pass

    def toggle_play_pause(self):
        self.playing = not self.playing
        if self.playing:
            self.play_pause_button.setText("Pause")
            self.text_capture_thread.start_capture()  # Start text capture thread
        else:
            self.play_pause_button.setText("Resume")
            self.text_capture_thread.stop_capture()  # Stop text capture thread

    def set_playback_speed(self, speed):
        self.playback_speed = speed
        if self.playing:
            self.timer.setInterval(int(self.timer_interval / speed))
        self.playback_speed_label.setText(f"Playback Speed: {speed}x")

    def reset_playback_speed(self):
        self.set_playback_speed(1)  # Reset speed to normal
        self.playback_speed_label.clear()
    
    def restart_video_action(self):
        video_reset = [video.set(cv2.CAP_PROP_POS_FRAMES, 0) for video in self.video_captures]
        # self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

class VideoPlayerApp(QMainWindow):
    def __init__(self, video_paths):
        super().__init__()

        # Get thread created, wait for user to open
        self.text_capture_window = TextCaptureWindow()
        self.text_capture_thread = TextCaptureThread(video_captures=[cv2.VideoCapture(video_path, cv2.CAP_FFMPEG) for video_path in video_paths], text_capture_window=self.text_capture_window)
        self.text_capture_thread.textCaptured.connect(self.handle_text_captured)
        self.text_capture_thread.start()

        # Setup main window
        self.video_player = VideoPlayer(video_paths, self.text_capture_thread, self.text_capture_window)
        self.create_menus()

        central_widget = QWidget()
        central_layout = QVBoxLayout()

        central_layout.addWidget(self.video_player)
        central_layout.addWidget(self.text_capture_window)

        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self.setGeometry(100, 100, 1200, 600)
        self.setWindowTitle('Video Player')


    #TODO Add a restqrt video button
    def create_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('File')
        open_action = QAction('Open', self)
        open_action.triggered.connect(self.toggle_text_capture_window)
        file_menu.addAction(open_action)

        playback_menu = menubar.addMenu('Playback')
        play_action = QAction('Play', self)
        play_action.triggered.connect(self.start_playback)
        playback_menu.addAction(play_action)

        restart_action = QAction('Restart Playback', self)
        restart_action.triggered.connect(self.restart_video)
        playback_menu.addAction(restart_action)

        fast_forward_action = QAction('Fast Forward', self)
        fast_forward_action.triggered.connect(self.increment_playback_speed)
        playback_menu.addAction(fast_forward_action)

        slow_down_action = QAction('Slow Down', self)
        slow_down_action.triggered.connect(self.decrement_playback_speed)
        playback_menu.addAction(slow_down_action)

        reset_speed_action = QAction('Reset Speed', self)
        reset_speed_action.triggered.connect(self.reset_playback_speed)
        playback_menu.addAction(reset_speed_action)

    def toggle_text_capture_window(self):
        current_visibility = self.text_capture_window.isVisible()
        self.text_capture_window.setVisible(not current_visibility)

    def handle_text_captured(self, text):
        self.text_capture_window.append_text(text)

    def start_playback(self):
        # Add logic to start playback
        pass
    
    # Restarts the video when the user selections option
    def restart_video(self):
        self.video_player.playing = not self.video_player.playing
        self.video_player.restart_video_action()
        self.video_player.playback_slider.setValue(0)
        self.video_player.play_pause_button.setText("Start Video")

    def increment_playback_speed(self):
        current_speed = self.video_player.playback_speed
        self.video_player.set_playback_speed(current_speed + 1)

    def decrement_playback_speed(self):
        current_speed = self.video_player.playback_speed
        self.video_player.set_playback_speed(max(1, current_speed - 1))

    def reset_playback_speed(self):
        self.video_player.reset_playback_speed()



"""
Inital window that asks user what files they want to look at.
"""
class VideoSelector(QWidget):
    def __init__(self):
        super(VideoSelector, self).__init__()

        self.init_ui()

    def init_ui(self):
        # Create a layout
        layout = QVBoxLayout()

        # Create a list widget to display selected file paths
        self.list_widget = QListWidget()

        # Create a button to open the file dialog
        self.process_button = QPushButton('Play Videos')
        self.process_button.clicked.connect(self.process_files)
        self.process_button.setVisible(False)

        select_button = QPushButton('Select Video Files')
        select_button.clicked.connect(self.show_file_dialog)

        # Add widgets to the layout
        layout.addWidget(select_button)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.process_button)
        self.setLayout(layout)


    """
    Display the window that will allow the user to load the video paths
    """
    def show_file_dialog(self):
        # Open the file dialog to select multiple files
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)

        if file_dialog.exec_():
            # Get the selected file paths
            selected_files = file_dialog.selectedFiles()

            # Display the selected file paths in the list widget
            self.list_widget.clear()
            for file_path in selected_files:
                self.list_widget.addItem(file_path)
        self.process_button.setVisible(True)


    """
    Process the file paths in the QListWidget
    """
    def process_files(self):
        video_paths = [self.list_widget.item(x).text() for x in range(self.list_widget.count())]
        self.main = VideoPlayerApp(video_paths)
        self.main.show()
        self.close()
