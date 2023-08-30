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
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# PyQt stuff
from PyQt5.QtCore import Qt,QTimer
from PyQt5.QtWidgets import QApplication,QWidget

# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from ui.UI_daq import Ui_DAQWindow

# InfluxDB
from influxdb import InfluxDBClient

# import my own libs
import libs.PRINT_data_utilities as UTIL



#######################################   DAQ CLASS   #####################################################

class DAQWindow(QWidget, Ui_DAQWindow):
    """ setup DAQ window """

    database = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)
        self.setWindowTitle("---   PRINT_py  -  DAQ window  ---")
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.timeUpdate()

        self.PATH_btt_chgPath.pressed.connect(self.newPath)

        # self.database = InfluxDBClient( host= 'localhost', port= 8086
        #                                ,username= 'PRINT_py', password= 'print_py'
        #                                ,ssl= True, verify_ssl= True)
        # now = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        # self.database.create_database(now + '_PRINT_py')
        # self.database.switch_database(now + '_PRINT_py')
        
    
    def timeUpdate(self):
        self.PATH_disp_datetime.setText( f"{datetime.now().strftime('%Y-%m-%d    %H:%M:%S')}" )

    def newPath(self):
        self.PATH_disp_path.setText("ease off, this function doesnt exist, yet")

    def dataUpdate(self):
        self.BASIC_disp_ambTemp.setText         ( f"{UTIL.STT_datablock.ambTemp} °C" )
        self.BASIC_disp_ambHum.setText          ( f"{UTIL.STT_datablock.ambHum} rH" )
        self.BASIC_disp_delivPumpTemp.setText   ( f"{UTIL.STT_datablock.delivPumpTemp} °C" )
        self.BASIC_disp_robBaseTemp.setText     ( f"{UTIL.STT_datablock.robBaseTemp} °C" )
        self.BASIC_disp_2kPumpTemp.setText      ( f"{UTIL.STT_datablock.kPumpTemp} °C" )
        self.BASIC_disp_delivPumpPress.setText  ( f"{UTIL.STT_datablock.delivPumpPress} °C" )
        self.BASIC_disp_2kPumpPress.setText     ( f"{UTIL.STT_datablock.kPumpPress} °C" )

        self.MOT_disp_pump1Freq.setText         ( f"{UTIL.STT_datablock.PUMP1.FREQ} Hz" )
        self.MOT_disp_pump2Freq.setText         ( f"{UTIL.STT_datablock.PUMP2.FREQ} Hz" )
        self.MOT_disp_pump1Volt.setText         ( f"{UTIL.STT_datablock.PUMP1.VOLT} V" )
        self.MOT_disp_pump2Volt.setText         ( f"{UTIL.STT_datablock.PUMP2.VOLT} V" )
        self.MOT_disp_pump1Amps.setText         ( f"{UTIL.STT_datablock.PUMP1.AMPS} A" )
        self.MOT_disp_pump2Amps.setText         ( f"{UTIL.STT_datablock.PUMP2.AMPS} A" )
        self.MOT_disp_pump1Torq.setText         ( f"{UTIL.STT_datablock.PUMP1.TORQ} Nm" )
        self.MOT_disp_pump2Torq.setText         ( f"{UTIL.STT_datablock.PUMP2.TORQ} Nm" )
        self.MOT_disp_admPumpFreq.setText       ( f"{UTIL.STT_datablock.admPumpFreq} Hz" )
        self.MOT_disp_admPumpAmps.setText       ( f"{UTIL.STT_datablock.admPumpAmps} A" )
        self.MOT_disp_2kPumpFreq.setText        ( f"{UTIL.STT_datablock.kPumpFreq} Hz" )
        self.MOT_disp_2kPumpAmps.setText        ( f"{UTIL.STT_datablock.kPumpAmps} A" )

        self.ROB_disp_id.setText                ( f"{UTIL.STT_datablock.ROB.ID}" )
        self.ROB_disp_tcpSpeed.setText          ( f"{UTIL.STT_datablock.ROB.TOOL_SPEED} mm/s" )
        self.ROB_disp_xPos.setText              ( f"{UTIL.STT_datablock.ROB.POS.X} mm" )
        self.ROB_disp_yPos.setText              ( f"{UTIL.STT_datablock.ROB.POS.Y} mm" )
        self.ROB_disp_zPos.setText              ( f"{UTIL.STT_datablock.ROB.POS.Z} mm" )
        self.ROB_disp_xOri.setText              ( f"{UTIL.STT_datablock.ROB.POS.X_ori} mm" )
        self.ROB_disp_yOri.setText              ( f"{UTIL.STT_datablock.ROB.POS.Y_ori} mm" )
        self.ROB_disp_zOri.setText              ( f"{UTIL.STT_datablock.ROB.POS.Z_ori} mm" )
        self.ROB_disp_extPos.setText            ( f"{UTIL.STT_datablock.ROB.POS.EXT}  mm" )
    
    # def toInflux (self):
    #     json_point = None
    #     if(json_point is not None): self.database.write(json_point)






#######################################   STRD DIALOG    #####################################################

def daqWindow(standalone=False):
    """ shows a dialog window, text and title can be set, returns the users choice """

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