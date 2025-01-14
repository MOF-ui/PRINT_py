from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np

CAM_urls = [
    "rtsp://admin:KameraNr4@192.168.178.51:554/ch1/main/av_stream",
    "rtsp://admin:KameraNr1@192.168.178.38:554/ch1/main/av_stream",
]

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(int, np.ndarray)
    cam_streams = []

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        # capture from web cam
        for url in CAM_urls:
            self.cam_streams.append(cv2.VideoCapture(url, cv2.CAP_FFMPEG))
        while self._run_flag:
            for cam_num, cam in enumerate(self.cam_streams):
                ret, cv_img = cam.read()
                if ret:
                    self.change_pixmap_signal.emit(cam_num, cv_img)
            # shut down capture system
        for cam in self.cam_streams:
            cam.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt live label demo")
        self.disply_width = 1280
        self.display_height = 1080
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(int(self.disply_width / 2), int(self.display_height / 2))
        self.image_label_2 = QLabel(self)
        self.image_label_2.resize(int(self.disply_width / 2), int(self.display_height / 2))
        # create a text label
        self.textLabel = QLabel('Webcam')

        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.textLabel)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()



    @pyqtSlot(int, np.ndarray)
    def update_image(self, cam_num, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        if cam_num:
            self.image_label.setPixmap(qt_img)
        else:
            self.image_label_2.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(int(self.disply_width / 2), int(self.display_height / 2), Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    
if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())