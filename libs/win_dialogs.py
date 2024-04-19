#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


#######################################     IMPORTS      #####################################################

# python standard libraries
import os
import sys

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# PyQt stuff
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog

# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from ui.UI_dialogs import Ui_Dialog, Ui_FileDialog, Ui_ConnDialog



#######################################   DIALOG CLASS   #####################################################

class StandardDialog(QDialog, Ui_Dialog):
    """default dialog class for PRINT_py with OK and ABBRECHEN buttons and setable text"""

    def __init__(self, text="", title="default window", parent=None):

        super().__init__(parent)

        self.setupUi(self)
        self.label.setText(text)
        self.setWindowTitle(title)



class FileDialog(QFileDialog, Ui_FileDialog):
    """default dialog class for PRINT_py with OK and ABBRECHEN buttons and setable text"""

    def __init__(self, title="default window", parent=None):

        super().__init__(parent)

        self.setupUi(self)
        self.setWindowTitle(title)
        self.setFileMode(1)  # enum for "ExistingFile"
        self.setDirectory(r"C:\Users\Max\Desktop\MultiCarb3D\CAD2RAPID")
        self.setNameFilters({"GCode files (*.gcode)", "RAPID files (*.mod)"})

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



class ConnDialog(QDialog, Ui_ConnDialog):
    """default dialog class to costumize connection settings"""

    def_rob_tcp = None
    def_pump1_tcp = None
    def_pump2_tcp = None

    set_rob_tcp = None
    set_pump1_tcp = None
    set_pump2_tcp = None
    set_conn_def1 = None
    set_conn_def2 = None

    def __init__(
        self,
        title="default window",
        rob_def=None,
        pump1_def=None,
        pump2_def=None,
        parent=None,
    ):

        super().__init__(parent)

        self.setupUi(self)
        self.setWindowTitle(title)

        if rob_def is None or pump1_def is None or pump2_def is None:
            self.close()

        else:
            self.def_rob_tcp = rob_def
            self.def_pump1_tcp = pump1_def
            self.def_pump2_tcp = pump2_def
            self.set_default()
            self.TCP_btt_default.pressed.connect(self.set_default)
            self.buttonBox.accepted.connect(self.set_output)

    def set_default(self):
        self.TCP_ROB_entry_ip.setText(str(self.def_rob_tcp["IP"]))
        self.TCP_ROB_entry_port.setText(str(self.def_rob_tcp["PORT"]))
        self.TCP_ROB_num_tio_conn.setValue(int(self.def_rob_tcp["C_TOUT"]))
        self.TCP_ROB_num_bytesToRead.setValue(int(self.def_rob_tcp["R_BL"]))
        self.TCP_ROB_num_tio_rw.setValue(int(self.def_rob_tcp["RW_TOUT"]))

        self.TCP_PUMP1_entry_ip.setText(str(self.def_pump1_tcp["IP"]))
        self.TCP_PUMP1_entry_port.setText(str(self.def_pump1_tcp["PORT"]))
        self.TCP_PUMP1_num_tio_conn.setValue(int(self.def_pump1_tcp["C_TOUT"]))
        self.TCP_PUMP1_num_bytesToRead.setValue(int(self.def_pump1_tcp["R_BL"]))
        self.TCP_PUMP1_num_tio_rw.setValue(int(self.def_pump1_tcp["RW_TOUT"]))

        self.TCP_PUMP2_entry_ip.setText(str(self.def_pump2_tcp["IP"]))
        self.TCP_PUMP2_entry_port.setText(str(self.def_pump2_tcp["PORT"]))
        self.TCP_PUMP2_num_tio_conn.setValue(int(self.def_pump2_tcp["C_TOUT"]))
        self.TCP_PUMP2_num_bytesToRead.setValue(int(self.def_pump2_tcp["R_BL"]))
        self.TCP_PUMP2_num_tio_rw.setValue(int(self.def_pump2_tcp["RW_TOUT"]))

    def set_output(self):
        self.set_rob_tcp = {}
        self.set_pump1_tcp = {}
        self.set_pump2_tcp = {}

        self.set_conn_def1 = self.TCP_PUMP1_connDef.isChecked()
        self.set_conn_def2 = self.TCP_PUMP2_connDef.isChecked()

        self.set_rob_tcp["IP"] = self.TCP_ROB_entry_ip.text()
        self.set_rob_tcp["PORT"] = self.TCP_ROB_entry_port.text()
        self.set_rob_tcp["C_TOUT"] = self.TCP_ROB_num_tio_conn.value() / 1000
        self.set_rob_tcp["R_BL"] = self.TCP_ROB_num_bytesToRead.value()
        self.set_rob_tcp["RW_TOUT"] = self.TCP_ROB_num_tio_rw.value() / 1000
        self.set_rob_tcp["W_BL"] = self.def_rob_tcp["W_BL"]

        self.set_pump1_tcp["IP"] = self.TCP_PUMP1_entry_ip.text()
        self.set_pump1_tcp["PORT"] = self.TCP_PUMP1_entry_port.text()
        self.set_pump1_tcp["C_TOUT"] = self.TCP_PUMP1_num_tio_conn.value() / 1000
        self.set_pump1_tcp["R_BL"] = self.TCP_PUMP1_num_bytesToRead.value()
        self.set_pump1_tcp["RW_TOUT"] = self.TCP_PUMP1_num_tio_rw.value() / 1000
        self.set_pump1_tcp["W_BL"] = self.def_pump2_tcp["W_BL"]

        self.set_pump2_tcp["IP"] = self.TCP_PUMP2_entry_ip.text()
        self.set_pump2_tcp["PORT"] = self.TCP_PUMP2_entry_port.text()
        self.set_pump2_tcp["C_TOUT"] = self.TCP_PUMP2_num_tio_conn.value() / 1000
        self.set_pump2_tcp["R_BL"] = self.TCP_PUMP2_num_bytesToRead.value()
        self.set_pump2_tcp["RW_TOUT"] = self.TCP_PUMP2_num_tio_rw.value() / 1000
        self.set_pump2_tcp["W_BL"] = self.def_pump2_tcp["W_BL"]



#######################################   STRD DIALOG    #####################################################

def strd_dialog(
    usr_text="you forgot to set a text, dummy",
    usr_title="default window",
    standalone=False,
):
    """shows a dialog window, text and title can be set, returns the users choice"""

    if standalone:
        # leave that here so app doesnt include the remnant of a previous QApplication instance
        strd_dialog_app = 0
        strd_dialog_app = QApplication(sys.argv)

    strd_dialog_win = StandardDialog(text=usr_text, title=usr_title)

    if standalone:
        strd_dialog_win.show()
        strd_dialog_app.exec()
        # sys.exit(app.exec())

        return strd_dialog_win.result()

    return strd_dialog_win


def file_dialog(usr_title="default window", standalone=False):
    """shows a dialog window, text and title can be set, returns the users choice"""

    if standalone:
        # leave that here so app doesnt include the remnant of a previous QApplication instance
        file_dialog_app = 0
        file_dialog_app = QApplication(sys.argv)

    file_dialog_win = FileDialog(title=usr_title)

    if standalone:
        file_dialog_win.show()
        file_dialog_app.exec()
        # sys.exit(app.exec())

        return file_dialog_win.selectedFiles()

    return file_dialog_win


def conn_dialog(rob, p1, p2, title="default window", standalone=False):
    """shows a dialog window, text and title can be set, returns the users choice"""

    if standalone:
        # leave that here so app doesnt include the remnant of a previous QApplication instance
        conn_dialog_app = 0
        conn_dialog_app = QApplication(sys.argv)

    conn_dialog_win = ConnDialog(title=title, rob_def=rob, pump1_def=p1, pump2_def=p2)

    if standalone:
        conn_dialog_win.show()
        conn_dialog_app.exec()
        # sys.exit(app.exec())

        return (
            conn_dialog_win.result(),
            conn_dialog_win.set_rob_tcp,
            conn_dialog_win.set_pump1_tcp,
            conn_dialog_win.set_pump2_tcp,
            conn_dialog_win.set_conn_def1,
            conn_dialog_win.set_conn_def2,
        )

    return conn_dialog_win
