#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

# python standard libraries
import os
import cv2
import sys

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# PyQt stuff
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPixmap, QImage

# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from ui.UI_cam_cap import Ui_CamCapWindow

# InfluxDB
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

# import my own libs
import libs.data_utilities as du



###########################     DAQ CLASS      ###############################

class CamCapWindow(QWidget, Ui_CamCapWindow):
    """test"""

    logEntry = pyqtSignal(str, str)
    cam_streams=[]
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # UI setup
        self.setupUi(self)
        self.setWindowTitle("---   PRINT_py  -  DAQ window  ---")
        self.setWindowFlags(
            Qt.WindowMaximizeButtonHint
            | Qt.WindowMinimizeButtonHint
        )

        for url in du.CAM_urls:
            self.cam_streams.append(cv2.VideoCapture(url, cv2.CAP_FFMPEG))
        
        self.CapTimer = QTimer()
        self.CapTimer.setInterval(1000)
        self.CapTimer.timeout.connect(self.cam_cap)
        self.CapTimer.start()

        self.logEntry.emit(
            'THRT',
            f"IPCam Thread running with {len(self.cam_streams)} streams."
        )

    
    def cam_cap(self) -> None:
        """capture an image from all streams"""

        for cam_num, cam in enumerate(self.cam_streams):
            if not isinstance(cam, cv2.VideoCapture):
                continue
            flag, frame = cam.read()
            if flag:
                # Following example from 
                # https://github.com/god233012yamil/Streaming-IP-Cameras-Using-PyQt-and-OpenCV
                # Get the frame height, width, channels, and bytes per line
                height, width, channels = frame.shape
                bytes_per_line = width * channels
                # image from BGR (cv2 default color format) to RGB (Qt default color format)
                # '.copy()' is vital as the emitted qt_image is otherwise local and 
                # slots accessing it will crash with segmentation fault
                cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                qt_image = QImage(
                    cv_image.data,
                    width,
                    height,
                    bytes_per_line,
                    QImage.Format_RGB888
                ).copy()
                self.new_img(cam_num, qt_image)


    def new_img(self, cam_num, img) -> None:
        """"""

        match cam_num:
            case 0: display = self.CAM_disp_1
            case 1: display = self.CAM_disp_2
            case 2: display = self.CAM_disp_3
            case 3: display = self.CAM_disp_4
            case _: return
        
        display.setPixmap(QPixmap.fromImage(img))
        display.setScaledContents(True)


    def closeEvent(self, event) -> None:
        """exit timer"""


        for cs in self.cam_streams:
            if isinstance(cs, cv2.VideoCapture):
                cs.release()

        self.CapTimer.stop()
        self.CapTimer.deleteLater()
        event.accept()



########################     CAMCAP WIN DIALOG      ############################

def cam_cap_window(standalone=False) -> 'CamCapWindow':
    """document
    """

    if standalone:
        # leave that here so app doesnt include the remnant of a previous 
        # QApplication instance
        daq_app = 0
        daq_app = QApplication(sys.argv)

    cam_cap_win = CamCapWindow()

    if standalone:
        cam_cap_win.show()
        daq_app.exec()
        # sys.exit(app.exec())

    return cam_cap_win