import sys
import cv2
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QToolBar, QAction, QSizePolicy

class VideoPlayer(QWidget):
    def __init__(self, video_paths):
        super().__init__()

        self.video_paths = video_paths
        self.caps = [cv2.VideoCapture(video_path) for video_path in video_paths]
        self.fps_list = [cap.get(cv2.CAP_PROP_FPS) for cap in self.caps]
        self.delays = [int(1000 / fps) for fps in self.fps_list]
        self.min_delay = min(self.delays)

        self.main_video_index = None
        self.image_labels = [QLabel() for _ in video_paths]
        self.toolbar_actions = []

        for label, cap in zip(self.image_labels, self.caps):
            label.setScaledContents(True)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            label.mousePressEvent = self.create_mouse_event_handler(label)
            if cap.isOpened():
                action = self.create_toolbar_action(label)
                if action:
                    self.toolbar_actions.append(action)

        self.main_layout = QVBoxLayout()
        self.video_layout = QHBoxLayout()
        for label in self.image_labels:
            self.video_layout.addWidget(label)
        self.main_layout.addLayout(self.video_layout)

        self.toolbar = QToolBar()
        for action in self.toolbar_actions:
            self.toolbar.addAction(action)
        self.main_layout.addWidget(self.toolbar)

        self.setLayout(self.main_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(self.min_delay)

    def create_mouse_event_handler(self, label):
        def mouse_event_handler(event):
            if event.button() == Qt.LeftButton:
                index = self.image_labels.index(label)
                if self.main_video_index is None:
                    self.main_video_index = index
                    self.switch_to_main(index)
                else:
                    self.switch_to_main(index)
        return mouse_event_handler

    def create_toolbar_action(self, label):
        index = self.image_labels.index(label)
        pixmap = self.get_video_frame(index)
        if pixmap:
            action = QAction(QIcon(pixmap), "", self)
            action.triggered.connect(lambda: self.switch_to_main(index))
            return action

    def get_video_frame(self, index):
        cap = self.caps[index]
        if cap is not None:
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                return pixmap.scaled(QSize(100, 100), Qt.KeepAspectRatio)
            else:
                cap.release()
                self.caps[index] = None
        return None

    def switch_to_main(self, index):
        if self.main_video_index is not None:
            current_main_label = self.image_labels[self.main_video_index]
            self.video_layout.removeWidget(current_main_label)
            current_main_label.setParent(None)
            if self.main_video_index < len(self.toolbar_actions):
                action = self.toolbar_actions[self.main_video_index]
                if action:
                    self.toolbar.addAction(action)

        self.main_video_index = index
        new_main_label = self.image_labels[index]
        if index < len(self.toolbar_actions):
            action = self.toolbar_actions[index]
            if action:
                self.toolbar.removeAction(action)
        self.video_layout.addWidget(new_main_label)

    def update_frames(self):
        for i, cap in enumerate(self.caps):
            if cap is not None:
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = frame.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qt_image)
                    self.image_labels[i].setPixmap(pixmap)
                    if i != self.main_video_index:
                        action = self.toolbar_actions[i]
                        if action:
                            action.setIcon(QIcon(pixmap.scaled(QSize(100, 100), Qt.KeepAspectRatio)))
                else:
                    cap.release()
                    self.caps[i] = None

        if all(cap is None for cap in self.caps):
            self.timer.stop()
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    video_paths = [
        "C:/Users/tycon/Downloads/Vids/video0_45_1.mp4",  # Replace with your first video file path
        "C:/Users/tycon/Downloads/Vids/doomcoomer.mp4",  # Replace with your second video file path
        "C:/Users/tycon/Downloads/Vids/party_time.mp4"    # Replace with your third video file path
    ]
    player = VideoPlayer(video_paths)
    player.show()
    sys.exit(app.exec_())
