from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSlider, QPushButton, QTextEdit, QAction, QListWidget, QFileDialog, QListWidgetItem
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QMutex, QMutexLocker
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
import pytesseract
import py7zr
import os
import shutil
import cv2
import atexit

######## Uncomment this if you recieved error that Tesseract is not in your Path. #############
# pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

class TextCaptureThread(QThread):
    textCaptured = pyqtSignal(str)

    def __init__(self, video_captures):
        super().__init__()
        self.running = False
        self.video_captures = video_captures
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

class VideoReaderThread(QThread):
    frameProcessed = pyqtSignal(object)

    def __init__(self, video_captures):
        super().__init__()
        self.video_captures = video_captures
        self.stopped = False

    def run(self):
        while not self.stopped:
            for video_capture in self.video_captures:
                ret, frame = video_capture.read()
                if ret:
                    self.frameProcessed.emit(frame)

    def stop(self):
        self.stopped = True

class TextCaptureWindow(QWidget):
    def __init__(self, video_player, video_paths, text_thread):
        super().__init__()
        # Set window title and size
        self.setWindowTitle("OpenCV Video Player with Text Recognition")
        self.setGeometry(100, 100, 800, 800)

        # Current Video Instance
        self.video_player = video_player

        # Create label to display recognized text
        self.text_label = QLabel("Recognized Text:")

        # Create QListWidget to display recognized text items
        self.text_list_widget = QListWidget()
        self.text_list_widget.itemClicked.connect(self.on_item_click)

        # Create layout
        layout = QVBoxLayout()
        # layout.addWidget(self.video_window)
        layout.addWidget(self.text_label)
        layout.addWidget(self.text_list_widget)
        self.setLayout(layout)

        # Timer for updating recognized text
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(1000)

    def update_text(self):
        if self.video_player.playing:
            texts = self.video_player.get_text()
            # Clear previous items in the list widget
            self.text_list_widget.clear()
            # Split text into individual words and add them as clickable items
            for text in texts:
                for word in text.split():
                    item = QListWidgetItem(word)
                    self.text_list_widget.addItem(item)

    def on_item_click(self, item):
        clicked_text = item.text()
        print("Clicked text:", clicked_text)
        self.video_player.highlight_text(clicked_text)


class VideoPlayer(QWidget):
    def __init__(self, video_paths, text_capture_thread):
        super().__init__()

        # Variable for storing the clicked position
        self.clicked_position = None

        self.text_capture_thread = text_capture_thread
        self.video_captures = [cv2.VideoCapture(video_path, cv2.CAP_FFMPEG) for video_path in video_paths]
        self.video_labels = [QLabel(self) for _ in video_paths]

        # Layout setups
        layout = QVBoxLayout()
        h_layout = QHBoxLayout()

        # Playback setup
        self.playback_speed_label = QLabel("Playback Speed: 1x", self)
        self.play_pause_button = QPushButton("Start Video", self)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        # Timer value setup
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

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

        # # Video reader thread
        # self.video_reader_thread = VideoReaderThread(self.video_captures)
        # self.video_reader_thread.frameProcessed.connect(self.update_frame)
        # self.video_reader_thread.start()

    def update_frame(self):
        if self.playing:
            for i, video_capture in enumerate(self.video_captures):
                ret, frame = video_capture.read()
                if ret:
                    # Use pytesseract to recognize text
                    text = pytesseract.image_to_string(frame)

                    # Check if clicked text is found in the current frame
                    if self.clicked_position and self.clicked_position[i] is not None:
                        x, y, w, h = self.clicked_position[i]
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Convert frame to RGB format
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    h, w, ch = image.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qt_image)
                    self.video_labels[i].setPixmap(pixmap)


    def get_text(self):
        if self.playing:
            if self.video_captures:
                texts = []
                for video_capture in self.video_captures:
                    ret, frame = video_capture.read()
                    if ret:
                        # Convert frame to grayscale
                        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                        # Use pytesseract to recognize text
                        texts.append(pytesseract.image_to_string(gray_frame))
                return texts
            return []


    def highlight_text(self, clicked_text):
        print("Clicked text:", clicked_text)
        # Reset the clicked position
        self.clicked_position = None

        # Search for the clicked text in the current frame
        if self.playing:
            if self.video_captures:
                self.clicked_position = []
                for video_capture in self.video_captures:
                    ret, frame = video_capture.read()
                    if ret:
                        # Use pytesseract to recognize text
                        text = pytesseract.image_to_string(frame)
                        print("Recognized text:", text)

                        # Check if clicked text is found in the current frame
                        if clicked_text in text:
                            print(f"Text '{clicked_text}' found in the video frame")

                            # Find the location of the clicked text
                            x, y, w, h = self.find_text_location(frame, clicked_text)
                            print("Text position:", x, y, w, h)

                            # Store the located position
                            self.clicked_position.append((x, y, w, h))
                        else:
                            self.clicked_position.append(None)


    def find_text_location(self, frame, text):
        # Use pytesseract to recognize text and locate its bounding box
        d = pytesseract.image_to_data(frame, output_type=pytesseract.Output.DICT)
        n_boxes = len(d['text'])
        for i in range(n_boxes):
            if d['text'][i] == text:
                x, y, w, h = d['left'][i], d['top'][i], d['width'][i], d['height'][i]
                return x, y, w, h
        return None, None, None, None


    def set_video_position(self, position):
        for video_capture in self.video_captures:
            video_capture.set(cv2.CAP_PROP_POS_FRAMES, position)

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

        self.text_capture_thread = TextCaptureThread(video_captures=[cv2.VideoCapture(video_path, cv2.CAP_FFMPEG) for video_path in video_paths])
        self.text_capture_thread.start()

        # Setup main window
        self.video_player = VideoPlayer(video_paths, self.text_capture_thread)
        self.text_capture_window = TextCaptureWindow(self.video_player, video_paths,
                                                     self.text_capture_thread)
        self.create_menus()

        central_widget = QWidget()
        central_layout = QVBoxLayout()

        central_layout.addWidget(self.video_player)
        central_layout.addWidget(self.text_capture_window) # Need to have hidden at start

        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self.setGeometry(100, 100, 1200, 600)
        self.setWindowTitle('Video Player')

    """
    Create the menu options to the video player
    """
    def create_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('File')
        open_file = QAction('Open New Videos', self)
        open_file.triggered.connect(self.show_file_dialog)
        open_text = QAction('Open Text Capture', self)
        open_text.triggered.connect(self.toggle_text_capture_window)
        file_menu.addAction(open_file)
        file_menu.addAction(open_text)

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


    """
    Toggle the visibility of the text capture window
    """
    def toggle_text_capture_window(self):
        current_visibility = self.text_capture_window.isVisible()
        self.text_capture_window.setVisible(not current_visibility)

    """
    Toggle the playback by this action
    """
    def start_playback(self):
        self.video_player.toggle_play_pause()
    
    """
    Restarts the video when the user presses this action
    """
    def restart_video(self):
        self.video_player.playing = not self.video_player.playing
        self.video_player.restart_video_action()
        self.video_player.playback_slider.setValue(0)
        self.video_player.play_pause_button.setText("Start Video")

    """
    Increase the speed of the playback
    """
    def increment_playback_speed(self):
        current_speed = self.video_player.playback_speed
        self.video_player.set_playback_speed(current_speed + 1)

    """
    Slow down the speed of the playback
    """
    def decrement_playback_speed(self):
        current_speed = self.video_player.playback_speed
        self.video_player.set_playback_speed(max(1, current_speed - 1))

    """
    Return the video back to its normal speed
    """
    def reset_playback_speed(self):
        self.video_player.reset_playback_speed()

    """
    Allow the user to open up different videos
    """
    #TODO Get it to replace the current running videos
    def show_file_dialog(self):
        self.main = VideoSelector()
        self.main.show()


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

        zip_files_button = QPushButton('Load Zip File')
        zip_files_button.clicked.connect(self.open_file_dialog)

        # Temp file path
        user_path = os.path.expanduser("~")
        program_folder  = os.path.join(user_path, "MAPS-Python")
        self.extracted_folder = os.path.join(program_folder,'Temp')

        # Add widgets to the layout
        layout.addWidget(select_button)
        layout.addWidget(zip_files_button)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.process_button)
        self.setLayout(layout)
        self.setWindowTitle('Video Selector')


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



    """
    If user wants to load a zip file 
    """
    def open_file_dialog(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Open 7z Archive', '', '7z Archives (*.7z)')

        if file_path:
            self.list_files_in_7z(file_path)


    """
    Get the extracted video files
    """
    def list_files_in_7z(self, archive_path):
        try:

            # Make Temp folder
            if not os.path.exists(self.extracted_folder):
                os.makedirs(self.extracted_folder)

            # Extract the contents of the 7z archive
            with py7zr.SevenZipFile(archive_path, mode='r') as archive:
                archive.extractall(self.extracted_folder)

            # Load the MP4 filea
            self.list_widget.clear()
            for root, dirs, files in os.walk(self.extracted_folder):
                for file in files:
                    self.list_widget.addItem(os.path.join(root, file))

            self.process_button.setVisible(True)

        except Exception as e:
            self.list_widget.clear()
            self.list_widget.addItem(f"Error: {e}")


    """
    Removes extracted save files
    """
    def clear_cache(self):
        shutil.rmtree(self.extracted_folder)
