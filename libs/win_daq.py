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
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

# import my own libs
import libs.data_utilities as du
from libs.win_dialogs import strd_dialog



#######################################   DAQ CLASS   #####################################################

class DAQWindow(QWidget, Ui_DAQWindow):
    """setup DAQ window"""

    _Database = None
    _db_bucket = None


    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)
        self.setWindowTitle("---   PRINT_py  -  DAQ window  ---")
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.time_update()

        self.PATH_btt_chgPath.pressed.connect(self.new_path)

        self._Database = influxdb_client.InfluxDBClient(
                url=du.DB_url,
                token=du.DB_token,
                org=du.DB_org
            )
        daq_starttime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self._db_bucket = daq_starttime + "__" + du.DB_session 
        self.db_connection = self._Database.write_api(write_options=SYNCHRONOUS)

        # set up default displays
        self.PATH_disp_path.setText(du.DB_url)


    def time_update(self):
        """clock update, signal from mainframe"""

        self.PATH_disp_datetime.setText(
            f"{datetime.now().strftime('%Y-%m-%d    %H:%M:%S')}"
        )

    def data_update(self):
        """data label update, signal from robo_recv"""

        self.BASIC_disp_ambTemp.setText(f"{du.STTDataBlock.amb_temp} °C")
        self.BASIC_disp_ambHum.setText(f"{du.STTDataBlock.amb_humidity} rH")
        self.BASIC_disp_delivPumpTemp.setText(
            f"{du.STTDataBlock.msp_temp} °C"
        )
        self.BASIC_disp_delivPumpPress.setText(
            f"{du.STTDataBlock.msp_press} °C"
        )
        self.BASIC_disp_robBaseTemp.setText(f"{du.STTDataBlock.rb_temp} °C")
        self.BASIC_disp_2kPumpTemp.setText(f"{du.STTDataBlock.imp_temp} °C")
        self.BASIC_disp_2kPumpPress.setText(f"{du.STTDataBlock.imp_press} °C")

        self.MOT_disp_pump1Freq.setText(f"{du.STTDataBlock.Pump1.freq} Hz")
        self.MOT_disp_pump2Freq.setText(f"{du.STTDataBlock.Pump2.freq} Hz")
        self.MOT_disp_pump1Volt.setText(f"{du.STTDataBlock.Pump1.volt} V")
        self.MOT_disp_pump2Volt.setText(f"{du.STTDataBlock.Pump2.volt} V")
        self.MOT_disp_pump1Amps.setText(f"{du.STTDataBlock.Pump1.amps} A")
        self.MOT_disp_pump2Amps.setText(f"{du.STTDataBlock.Pump2.amps} A")
        self.MOT_disp_pump1Torq.setText(f"{du.STTDataBlock.Pump1.torq} Nm")
        self.MOT_disp_pump2Torq.setText(f"{du.STTDataBlock.Pump2.torq} Nm")
        self.MOT_disp_admPumpFreq.setText(f"{du.STTDataBlock.asp_freq} Hz")
        self.MOT_disp_admPumpAmps.setText(f"{du.STTDataBlock.asp_amps} A")
        self.MOT_disp_2kPumpFreq.setText(f"{du.STTDataBlock.imp_freq} Hz")
        self.MOT_disp_2kPumpAmps.setText(f"{du.STTDataBlock.imp_amps} A")

        self.ROB_disp_id.setText(f"{du.STTDataBlock.Robo.id}")
        self.ROB_disp_tcpSpeed.setText(f"{du.STTDataBlock.Robo.t_speed} mm/s")
        self.ROB_disp_xPos.setText(f"{du.STTDataBlock.Robo.Coor.x} mm")
        self.ROB_disp_yPos.setText(f"{du.STTDataBlock.Robo.Coor.y} mm")
        self.ROB_disp_zPos.setText(f"{du.STTDataBlock.Robo.Coor.z} mm")
        self.ROB_disp_xOri.setText(f"{du.STTDataBlock.Robo.Coor.rx} mm")
        self.ROB_disp_yOri.setText(f"{du.STTDataBlock.Robo.Coor.ry} mm")
        self.ROB_disp_zOri.setText(f"{du.STTDataBlock.Robo.Coor.rz} mm")
        self.ROB_disp_extPos.setText(f"{du.STTDataBlock.Robo.Coor.ext}  mm")


    def new_path(self):
        """write new path to du.DB_url"""
        
        # no Mutex as DB_url is only read in other functions
        new_url = self.PATH_entry_newPath.text()
        commit_dialog = strd_dialog(
            usr_text="Resetting the DB URL could result in data loss!\nAre you sure?",
            usr_title="Confirm Dialog"
        )
        commit_dialog.exec()
        print(f"DB path change: {commit_dialog.result()}")
        if commit_dialog.result() == 1:
            du.DB_url = new_url
            self.PATH_disp_path.setText(du.DB_url)


    def toInflux(self):
        """build & send an DB entry, name the measurement after current time,
        all DaqBlock entries will return None if their valid_time has passed,
        signal from (robo_recv or sensor_cycle?) 
        """

        now = datetime.now().strftime('%Y-%m-%d    %H:%M:%S')
        DBEntry = influxdb_client\
            .Point(now)\
            .tag("session:", du.DB_session)\
            .field("Amb. temp.", du.STTDataBlock.amb_temp)\
            .field("Amb. humid.", du.STTDataBlock.amb_humidity)\
            .field("MSP temp.", du.STTDataBlock.msp_temp)\
            .field("MSP press.", du.STTDataBlock.msp_press)\
            .field("ASP freq.", du.STTDataBlock.asp_freq)\
            .field("ASP amps.", du.STTDataBlock.asp_amps)\
            .field("RB temp.", du.STTDataBlock.rb_temp)\
            .field("IMP temp.", du.STTDataBlock.imp_temp)\
            .field("IMP press.", du.STTDataBlock.imp_press)\
            .field("IMP freq.", du.STTDataBlock.imp_freq)\
            .field("IMP amps.", du.STTDataBlock.imp_amps)\
            \
            .field("P1 freq.", du.STTDataBlock.Pump1.freq)\
            .field("P1 volt", du.STTDataBlock.Pump1.volt)\
            .field("P1 amps.", du.STTDataBlock.Pump1.amps)\
            .field("P1 torq.", du.STTDataBlock.Pump1.torq)\
            .field("P2 freq.", du.STTDataBlock.Pump2.freq)\
            .field("P2 volt", du.STTDataBlock.Pump2.volt)\
            .field("P2 amps.", du.STTDataBlock.Pump2.amps)\
            .field("P2 torq.", du.STTDataBlock.Pump2.torq)\
            \
            .field("ROB ID", du.STTDataBlock.Robo.id)\
            .field("ROB TCP", du.STTDataBlock.Robo.t_speed)\
            .field("ROB X", du.STTDataBlock.Robo.Coor.x)\
            .field("ROB Y", du.STTDataBlock.Robo.Coor.y)\
            .field("ROB Z", du.STTDataBlock.Robo.Coor.z)\
            .field("ROB RX", du.STTDataBlock.Robo.Coor.rx)\
            .field("ROB RY", du.STTDataBlock.Robo.Coor.ry)\
            .field("ROB RZ", du.STTDataBlock.Robo.Coor.rz)\
            .field("ROB EXT", du.STTDataBlock.Robo.Coor.ext)
        
        self.db_connection.write(bucket=self._db_bucket, org=du.DB_org, record=DBEntry)



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
