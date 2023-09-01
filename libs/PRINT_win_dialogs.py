#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as  
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


#######################################     IMPORTS      #####################################################

# python standard libraries
import os
import sys

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# PyQt stuff
from PyQt5.QtWidgets import QApplication,QDialog,QFileDialog

# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from ui.UI_dialogs import Ui_Dialog, Ui_FileDialog, Ui_ConnDialog




#######################################   DIALOG CLASS   #####################################################

class StandardDialog(QDialog,Ui_Dialog):
    """  default dialog class for PRINT_py with OK and ABBRECHEN buttons and setable text """

    def __init__( self
                 ,text      = ''
                 ,title     = 'default window'
                 ,parent    = None):
        
        super().__init__(parent)
        
        self.setupUi(self)
        self.label.setText(text)
        self.setWindowTitle(title)




class FileDialog(QFileDialog,Ui_FileDialog):
    """  default dialog class for PRINT_py with OK and ABBRECHEN buttons and setable text """

    def __init__( self
                 ,title     = 'default window'
                 ,parent    = None):
        
        super().__init__(parent)
        
        self.setupUi(self)
        self.setWindowTitle(title)
        self.setFileMode(1)     # enum for "ExistingFile"
        self.setDirectory(r"C:\Users\Max\Desktop\MultiCarb3D\CAD2RAPID")
        self.setNameFilters({"GCode files (*.gcode)",
                             "RAPID files (*.mod)"})
        
        # uncomment here if you want a custom sidebar
        # self.setOption(QFileDialog.DontUseNativeDialog,on = True)
        # self.setSidebarUrls([QUrl.fromLocalFile("/Users/Max/Desktop/MultiCarb3D/CAD2RAPID"),
        #                      QUrl.fromLocalFile(QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)),
        #                      QUrl.fromLocalFile(QStandardPaths.writableLocation(QStandardPaths.RuntimeLocation))])
        # 
        # self.setStyleSheet("QWidget {font-family: \"Bahnschrift\"; font-size: 10pt; background-color: #f2f4f3;} \
        #                     QPushButton {background-color: #FFBA00; border-radius: 5px; font-size: 14pt; min-width: 100px;} \
        #                     QPushButton::hover {background-color: #FFC300;} \
        #                     QPushButton::pressed {background-color: #88AB75;} \
        #                     ")


class ConnDialog(QDialog,Ui_ConnDialog):
    """  default dialog class to costumize connection settings """

    DEF_robTcp   = None
    DEF_pump1Tcp = None
    DEF_pump2Tcp = None

    SET_robTcp   = None
    SET_pump1Tcp = None
    SET_pump2Tcp = None
    SET_connDef1 = None
    SET_connDef2 = None



    def __init__( self
                 ,title     = 'default window'
                 ,rob_DEF   = None
                 ,pump1_DEF = None
                 ,pump2_DEF = None
                 ,parent    = None):
        
        super().__init__(parent)
        
        self.setupUi(self)
        self.setWindowTitle(title)

        if( (rob_DEF is None)   or   (pump1_DEF is None)   or   (pump2_DEF is None) ):    
            self.close()

        else:
            self.DEF_robTcp = rob_DEF
            self.DEF_pump1Tcp = pump1_DEF
            self.DEF_pump2Tcp = pump2_DEF
            self.setDefault()
            self.TCP_btt_default.pressed.connect    (self.setDefault)
            self.buttonBox.accepted.connect         (self.setOutput)
            
        

    def setDefault(self):
        self.TCP_ROB_entry_ip.setText           ( str(self.DEF_robTcp["IP"]) )
        self.TCP_ROB_entry_port.setText         ( str(self.DEF_robTcp["PORT"]) )
        self.TCP_ROB_num_tio_conn.setValue      ( int(self.DEF_robTcp["C_TOUT"]) )
        self.TCP_ROB_num_bytesToRead.setValue   ( int(self.DEF_robTcp["R_BL"]) )
        self.TCP_ROB_num_tio_rw.setValue        ( int(self.DEF_robTcp["RW_TOUT"]) )
        
        self.TCP_PUMP1_entry_ip.setText         ( str(self.DEF_pump1Tcp["IP"]) )
        self.TCP_PUMP1_entry_port.setText       ( str(self.DEF_pump1Tcp["PORT"]) )
        self.TCP_PUMP1_num_tio_conn.setValue    ( int(self.DEF_pump1Tcp["C_TOUT"]) )
        self.TCP_PUMP1_num_bytesToRead.setValue ( int(self.DEF_pump1Tcp["R_BL"]) )
        self.TCP_PUMP1_num_tio_rw.setValue      ( int(self.DEF_pump1Tcp["RW_TOUT"]) )
        
        self.TCP_PUMP2_entry_ip.setText         ( str(self.DEF_pump2Tcp["IP"]) )
        self.TCP_PUMP2_entry_port.setText       ( str(self.DEF_pump2Tcp["PORT"]) )
        self.TCP_PUMP2_num_tio_conn.setValue    ( int(self.DEF_pump2Tcp["C_TOUT"]) )
        self.TCP_PUMP2_num_bytesToRead.setValue ( int(self.DEF_pump2Tcp["R_BL"]) )
        self.TCP_PUMP2_num_tio_rw.setValue      ( int(self.DEF_pump2Tcp["RW_TOUT"]) )



    def setOutput(self):
        self.SET_robTcp     = {}
        self.SET_pump1Tcp   = {}
        self.SET_pump2Tcp   = {}

        self.SET_connDef1 = self.TCP_PUMP1_connDef.isChecked()
        self.SET_connDef2 = self.TCP_PUMP2_connDef.isChecked() 

        self.SET_robTcp["IP"]       = self.TCP_ROB_entry_ip.text()
        self.SET_robTcp["PORT"]     = self.TCP_ROB_entry_port.text()
        self.SET_robTcp["C_TOUT"]   = self.TCP_ROB_num_tio_conn.value()     / 1000
        self.SET_robTcp["R_BL"]     = self.TCP_ROB_num_bytesToRead.value()
        self.SET_robTcp["RW_TOUT"]  = self.TCP_ROB_num_tio_rw.value()       / 1000
        self.SET_robTcp["W_BL"]     = self.DEF_robTcp["W_BL"]

        self.SET_pump1Tcp["IP"]     = self.TCP_PUMP1_entry_ip.text()
        self.SET_pump1Tcp["PORT"]   = self.TCP_PUMP1_entry_port.text()
        self.SET_pump1Tcp["C_TOUT"] = self.TCP_PUMP1_num_tio_conn.value()   / 1000
        self.SET_pump1Tcp["R_BL"]   = self.TCP_PUMP1_num_bytesToRead.value()
        self.SET_pump1Tcp["RW_TOUT"]= self.TCP_PUMP1_num_tio_rw.value()     / 1000
        self.SET_pump1Tcp["W_BL"]   = self.DEF_pump2Tcp["W_BL"] 

        self.SET_pump2Tcp["IP"]     = self.TCP_PUMP2_entry_ip.text()
        self.SET_pump2Tcp["PORT"]   = self.TCP_PUMP2_entry_port.text()
        self.SET_pump2Tcp["C_TOUT"] = self.TCP_PUMP2_num_tio_conn.value()   / 1000
        self.SET_pump2Tcp["R_BL"]   = self.TCP_PUMP2_num_bytesToRead.value()
        self.SET_pump2Tcp["RW_TOUT"]= self.TCP_PUMP2_num_tio_rw.value()     / 1000
        self.SET_pump2Tcp["W_BL"]   = self.DEF_pump2Tcp["W_BL"]




#######################################   STRD DIALOG    #####################################################

def strdDialog(usrText='you forgot to set the text, dumbass', usrTitle='default window', standalone=False):
    """ shows a dialog window, text and title can be set, returns the users choice """

    if standalone:
        # leave that here so app doesnt include the remnant of a previous QApplication instance
        strd_dialog_app = 0       
        strd_dialog_app = QApplication(sys.argv)

    strd_dialog_win = StandardDialog(text=usrText, title=usrTitle)

    if standalone:
        strd_dialog_win.show()
        strd_dialog_app.exec()
        # sys.exit(app.exec())

        return strd_dialog_win.result()
    
    return strd_dialog_win



def fileDialog(usrTitle='default window', standalone=False):
    """ shows a dialog window, text and title can be set, returns the users choice """

    if standalone:
        # leave that here so app doesnt include the remnant of a previous QApplication instance
        file_dialog_app = 0       
        file_dialog_app = QApplication(sys.argv)

    file_dialog_win = FileDialog(title=usrTitle)

    if standalone:
        file_dialog_win.show()
        file_dialog_app.exec()
        # sys.exit(app.exec())

        return file_dialog_win.selectedFiles()
    
    return file_dialog_win



def connDialog(rob_tcp_default, pump1_tcp_default, pump2_tcp_default, usrTitle='default window', standalone=False):
    """ shows a dialog window, text and title can be set, returns the users choice """

    if standalone:
        # leave that here so app doesnt include the remnant of a previous QApplication instance
        conn_dialog_app = 0       
        conn_dialog_app = QApplication(sys.argv)

    conn_dialog_win = ConnDialog( title     = usrTitle
                                 ,rob_DEF   = rob_tcp_default
                                 ,pump1_DEF = pump1_tcp_default
                                 ,pump2_DEF = pump2_tcp_default)

    if standalone:
        conn_dialog_win.show()
        conn_dialog_app.exec()
        # sys.exit(app.exec())

        return  conn_dialog_win.result() \
                ,conn_dialog_win.SET_robTcp \
                ,conn_dialog_win.SET_pump1Tcp \
                ,conn_dialog_win.SET_pump2Tcp \
                ,conn_dialog_win.SET_connDef1 \
                ,conn_dialog_win.SET_connDef2
    
    return conn_dialog_win