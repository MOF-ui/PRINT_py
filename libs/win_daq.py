#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


#######################################     IMPORTS      #####################################################

# python standard libraries
import os
import sys
from datetime import datetime

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# PyQt stuff
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget

# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from ui.UI_daq import Ui_DAQWindow

# InfluxDB
from influxdb import InfluxDBClient

# import my own libs
import libs.data_utilities as du



#######################################   DAQ CLASS   #####################################################

class DAQWindow(QWidget, Ui_DAQWindow):
    """setup DAQ window"""

    Database = None

    _deliv_pump_temp_t = 0

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)
        self.setWindowTitle("---   PRINT_py  -  DAQ window  ---")
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.time_update()

        self.PATH_btt_chgPath.pressed.connect(self.new_path)

        # self.database = InfluxDBClient( host= 'localhost', port= 8086
        #                                ,username= 'PRINT_py', password= 'print_py'
        #                                ,ssl= True, verify_ssl= True)
        # now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        # self.database.create_database(now + '_PRINT_py')
        # self.database.switch_database(now + '_PRINT_py')


    def time_update(self):
        self.PATH_disp_datetime.setText(
            f"{datetime.now().strftime('%Y-%m-%d    %H:%M:%S')}"
        )


    def new_path(self):
        self.PATH_disp_path.setText("ease off, this function doesnt exist, yet")


    def data_update(self):
        self.BASIC_disp_ambTemp.setText(f"{du.STTDataBlock.amb_temp} °C")
        self.BASIC_disp_ambHum.setText(f"{du.STTDataBlock.amb_hum} rH")
        self.BASIC_disp_delivPumpTemp.setText(f"{du.STTDataBlock.deliv_pump_temp} °C")
        self.BASIC_disp_robBaseTemp.setText(f"{du.STTDataBlock.rob_base_temp} °C")
        self.BASIC_disp_2kPumpTemp.setText(f"{du.STTDataBlock.k_pump_temp} °C")
        self.BASIC_disp_delivPumpPress.setText(
            f"{du.STTDataBlock.deliv_pump_press} °C"
        )
        self.BASIC_disp_2kPumpPress.setText(f"{du.STTDataBlock.k_pump_press} °C")

        self.MOT_disp_pump1Freq.setText(f"{du.STTDataBlock.Pump1.freq} Hz")
        self.MOT_disp_pump2Freq.setText(f"{du.STTDataBlock.Pump2.freq} Hz")
        self.MOT_disp_pump1Volt.setText(f"{du.STTDataBlock.Pump1.volt} V")
        self.MOT_disp_pump2Volt.setText(f"{du.STTDataBlock.Pump2.volt} V")
        self.MOT_disp_pump1Amps.setText(f"{du.STTDataBlock.Pump1.amps} A")
        self.MOT_disp_pump2Amps.setText(f"{du.STTDataBlock.Pump2.amps} A")
        self.MOT_disp_pump1Torq.setText(f"{du.STTDataBlock.Pump1.torq} Nm")
        self.MOT_disp_pump2Torq.setText(f"{du.STTDataBlock.Pump2.torq} Nm")
        self.MOT_disp_admPumpFreq.setText(f"{du.STTDataBlock.adm_pump_freq} Hz")
        self.MOT_disp_admPumpAmps.setText(f"{du.STTDataBlock.adm_pump_amps} A")
        self.MOT_disp_2kPumpFreq.setText(f"{du.STTDataBlock.k_pump_freq} Hz")
        self.MOT_disp_2kPumpAmps.setText(f"{du.STTDataBlock.k_pump_amps} A")

        self.ROB_disp_id.setText(f"{du.STTDataBlock.Robo.id}")
        self.ROB_disp_tcpSpeed.setText(f"{du.STTDataBlock.Robo.t_speed} mm/s")
        self.ROB_disp_xPos.setText(f"{du.STTDataBlock.Robo.Coor.x} mm")
        self.ROB_disp_yPos.setText(f"{du.STTDataBlock.Robo.Coor.y} mm")
        self.ROB_disp_zPos.setText(f"{du.STTDataBlock.Robo.Coor.z} mm")
        self.ROB_disp_xOri.setText(f"{du.STTDataBlock.Robo.Coor.rx} mm")
        self.ROB_disp_yOri.setText(f"{du.STTDataBlock.Robo.Coor.ry} mm")
        self.ROB_disp_zOri.setText(f"{du.STTDataBlock.Robo.Coor.rz} mm")
        self.ROB_disp_extPos.setText(f"{du.STTDataBlock.Robo.Coor.ext}  mm")


    # def toInflux (self):
    #     json_point = None
    #     if(json_point is not None): self.database.write(json_point)



#######################################   STRD DIALOG    #####################################################

def daq_window(standalone=False):
    """shows a dialog window, text and title can be set, returns the users choice"""

    if standalone:
        # leave that here so app doesnt include the remnant of a previous QApplication instance
        daq_app = 0
        daq_app = QApplication(sys.argv)

    daq_win = DAQWindow()

    if standalone:
        daq_win.show()
        daq_app.exec()
        # sys.exit(app.exec())

    return daq_win
