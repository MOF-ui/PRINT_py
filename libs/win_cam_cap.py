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
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget

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
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # UI setup
        self.setupUi(self)
        self.setWindowTitle("---   PRINT_py  -  DAQ window  ---")
        self.setWindowFlags(
            Qt.WindowMaximizeButtonHint
            | Qt.WindowMinimizeButtonHint
        )


    def new_img(self, cam_num, img) -> None:
        """"""

        match cam_num:
            case 0: display = self.CAM_disp_1
            case 1: display = self.CAM_disp_2
            case 2: display = self.CAM_disp_3
            case 3: display = self.CAM_disp_4
            case _: return
        
        display.setPixmap(img)
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