import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSlider, QPushButton, QMenuBar, QAction, QMenu, QTextEdit
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import cv2
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
import pytesseract

class TextCaptureWindow(QTextEdit):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

    def append_text(self, text):
        current_text = self.toPlainText()
        formatted_text = f"Captured Text:\n{text}\n{'='*30}\n"
        self.setPlainText(current_text + formatted_text)

class VideoPlayer(QWidget):
    def __init__(self, video_paths, main_app):
        super().__init__()
        self.main_app = main_app
        self.video_captures = [cv2.VideoCapture(video_path) for video_path in video_paths]
        self.video_labels = [QLabel(self) for _ in video_paths]
        
        self.play_pause_button = QPushButton("Start Video", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.update_slider_duration()

        layout = QVBoxLayout()
        h_layout = QHBoxLayout()

        self.playing = False
        self.playback_speed = 1  # Initial playback speed
        self.timer_interval = 33  # Initial frame update interval
        self.timer.start(self.timer_interval)

        # Create a thread for text capture
        self.text_capture_thread = TextCaptureThread(self)
        self.text_capture_thread.textCaptured.connect(self.handle_text_captured)
        self.text_capture_thread.start()

        video_durations = [int(video.get(cv2.CAP_PROP_FRAME_COUNT)) for video in self.video_captures]
        self.max_index, self.max_video_duration = max(enumerate(video_durations), key=lambda x: x[1])

        self.playback_slider = QSlider(Qt.Horizontal)
        self.playback_slider.setRange(0, self.max_video_duration)
        self.playback_slider.sliderMoved.connect(self.set_video_position)

        for label in self.video_labels:
            h_layout.addWidget(label)

        layout.addLayout(h_layout)
        layout.addWidget(self.playback_slider)
        layout.addWidget(self.play_pause_button)

        self.setLayout(layout)


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
        # video_duration = int(self.video_captures[0].get(cv2.CAP_PROP_FRAME_COUNT))
        # self.playback_slider.setRange(0, video_duration)

    def toggle_play_pause(self):
        self.playing = not self.playing
        if self.playing:
            self.play_pause_button.setText("Pause")
        else:
            self.play_pause_button.setText("Resume")

    def set_playback_speed(self, speed):
        self.playback_speed = speed
        if self.playing:
            self.timer.setInterval(int(self.timer_interval / speed))

    def reset_playback_speed(self):
        self.set_playback_speed(1)  # Reset speed to normal

    def capture_text(self, frame):
        # Convert frame to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply thresholding to enhance text
        _, thresh_frame = cv2.threshold(gray_frame, 150, 255, cv2.THRESH_BINARY)

        # Convert OpenCV image format to PIL image format
        pil_image = Image.fromarray(thresh_frame)

        # Use pytesseract to perform OCR on the PIL image
        text = pytesseract.image_to_string(pil_image)

        return text

    def handle_text_captured(self, text):
        self.main_app.text_capture_window.append_text(text)

class VideoPlayerApp(QMainWindow):
    def __init__(self, video_paths):
        super().__init__()

        self.video_player = VideoPlayer(video_paths, self)
        self.text_capture_window = TextCaptureWindow(self)
        self.create_menus()

        central_widget = QWidget()
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(self.video_player)
        self.setCentralWidget(central_widget)

        self.setGeometry(100, 100, 1200, 500)
        self.setWindowTitle('Video Player')

    def create_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('File')
        open_action = QAction('Open', self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        text_capture_action = QAction('Text Capture Window', self)
        text_capture_action.triggered.connect(self.show_text_capture_window)
        file_menu.addAction(text_capture_action)

        playback_menu = menubar.addMenu('Playback')
        play_action = QAction('Play', self)
        play_action.triggered.connect(self.start_playback)
        playback_menu.addAction(play_action)

        fast_forward_action = QAction('Fast Forward', self)
        fast_forward_action.triggered.connect(self.increment_playback_speed)
        playback_menu.addAction(fast_forward_action)

        slow_down_action = QAction('Slow Down', self)
        slow_down_action.triggered.connect(self.decrement_playback_speed)
        playback_menu.addAction(slow_down_action)

        reset_speed_action = QAction('Reset Speed', self)
        reset_speed_action.triggered.connect(self.reset_playback_speed)
        playback_menu.addAction(reset_speed_action)

    def open_file(self):
        # Add logic to open video file dialog and update video paths
        pass

    def show_text_capture_window(self):
        self.text_capture_window.show()

    def start_playback(self):
        # Add logic to start playback
        pass

    def increment_playback_speed(self):
        current_speed = self.video_player.playback_speed
        self.video_player.set_playback_speed(current_speed + 1)

    def decrement_playback_speed(self):
        current_speed = self.video_player.playback_speed
        self.video_player.set_playback_speed(max(1, current_speed - 1))

    def reset_playback_speed(self):
        self.video_player.reset_playback_speed()

class TextCaptureThread(QThread):
    textCaptured = pyqtSignal(str)

    def __init__(self, video_player):
        super().__init__()
        self.video_player = video_player

    def run(self):
        while True:
            if self.video_player.playing and self.video_player.main_app.text_capture_window.isVisible():
                for i, video_capture in enumerate(self.video_player.video_captures):
                    ret, frame = video_capture.read()
                    if ret:
                        text = self.video_player.capture_text(frame)
                        self.textCaptured.emit(text)

            # Sleep to reduce the processing load when the text capture window is not open
            self.msleep(100)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Replace 'video1.mp4', 'video2.mp4', 'video3.mp4' with your actual video file paths
    video_paths = ["C:/Users/tycon/Downloads/SampleVideo_1280x720_5mb.mp4",
                    "C:/Users/tycon/Downloads/SampleVideo_1280x720_2mb.mp4",
                    "C:/Users/tycon/Downloads/code_-_32767 (720p).mp4"]

    player_app = VideoPlayerApp(video_paths)
    player_app.show()

    sys.exit(app.exec_())
