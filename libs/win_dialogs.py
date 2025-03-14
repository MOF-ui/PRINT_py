#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

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
from ui.UI_connDialog import Ui_CONN
from ui.UI_strdDialog import Ui_Dialog

# import my own libs
import libs.data_utilities as du



########################     DIALOG CLASSES      ############################

class StandardDialog(QDialog, Ui_Dialog):
    """default dialog class for PRINT_py with OK and ABBRECHEN buttons
    and setable text
    """

    def __init__(self, text='', title='default window', parent=None) -> None:

        super().__init__(parent)
        self.setupUi(self)
        self.label.setText(text)
        self.setWindowTitle(title)



class FileDialog(QFileDialog):
    """file dialog for print file loading"""

    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(1000, 620)


    def __init__(self, title='default window', parent=None) -> None:

        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(title)
        self.setFileMode(1)  # enum for 'ExistingFile'
        self.setDirectory(r"C:\Users\Max\Downloads")
        self.setNameFilters({'GCode files (*.gcode)', 'RAPID files (*.mod)'})
        self.selectNameFilter('GCode files (*.gcode)')

        # uncomment here if you want a custom sidebar
        # self.setOption(QFileDialog.DontUseNativeDialog,on = True)
        # self.setSidebarUrls([
        #     QUrl.fromLocalFile('/Users/Max/Desktop/MultiCarb3D/CAD2RAPID'),
        #     QUrl.fromLocalFile(QStandardPaths.writableLocation(
        #         QStandardPaths.DesktopLocation
        #     )),
        #     QUrl.fromLocalFile(QStandardPaths.writableLocation(
        #         QStandardPaths.RuntimeLocation
        #     ))
        # ])
        #
        # self.setStyleSheet("QWidget {font-family: \"Bahnschrift\"; font-size: 10pt; background-color: #f2f4f3;} \
        #                     QPushButton {background-color: #FFBA00; border-radius: 5px; font-size: 14pt; min-width: 100px;} \
        #                     QPushButton::hover {background-color: #FFC300;} \
        #                     QPushButton::pressed {background-color: #88AB75;} \
        #                     ")



class ConnDialog(QDialog, Ui_CONN):
    """default dialog class to costumize connection settings"""

    rob_set = {}
    p_com = None
    prh_url = None
    db_url = None
    dev_available = False

    def __init__(
        self,
        title='Connection Dialog',
        parent=None,
    ) -> None:

        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(title)

        self.set_default()
        self.CONN_btt_default.pressed.connect(self.set_default)
        self.CONN_bttbox.accepted.connect(self.safe_settings)

    def set_default(self) -> None:
        # ROBOT
        self.ROB_entry_ip.setText(du.DEF_ROB_TCP['ip'])
        self.ROB_entry_port.setText(str(du.DEF_ROB_TCP['port']))
        self.ROB_num_connTo.setValue(du.DEF_ROB_TCP['c_tout'])
        self.ROB_num_rwTo.setValue(du.DEF_ROB_TCP['rw_tout'])
        # PMPs
        self.P1_entry_port.setText(du.DEF_PUMP_SERIAL['port'])
        self.P2_entry_port.setText(du.DEF_PUMP_SERIAL['port'])
        # PRH
        ip, port = du.PRH_url.split(':')
        self.PRH_entry_ip.setText(ip)
        self.PRH_entry_port.setText(port)
        # DB
        ip, port = du.DB_url.split(':')
        self.DB_entry_ip.setText(ip)
        self.DB_entry_port.setText(port)

    def safe_settings(self) -> None:
        # availablity
        rob = self.ROB_chk_available.isChecked()
        p1 = self.P1_chk_available.isChecked()
        p2 = self.P2_chk_available.isChecked()
        prh = self.PRH_chk_available.isChecked()
        db = self.DB_chk_available.isChecked()
        self.dev_available = rob<<4 | p1 <<3 | p2 <<2 | prh<<1 | db
        # ROBOT
        self.rob_set['ip'] = self.ROB_entry_ip.text()
        self.rob_set['port'] = self.ROB_entry_port.text()
        self.rob_set['c_tout'] = self.ROB_num_connTo.value() / 1000
        self.rob_set['rw_tout'] = self.ROB_num_rwTo.value() / 1000
        self.rob_set['r_bl'] = du.DEF_ROB_TCP['r_bl']
        self.rob_set['w_bl'] = du.DEF_ROB_TCP['w_bl']
        # PMPs
        p_port = self.P1_entry_port.text()
        if p_port != self.P2_entry_port.text():
            raise ValueError('Please connect both P20 to the same port')
        else:
            self.p_com = p_port
        # PRINTHEAD
        self.prh_url = (
            f"http://{self.PRH_entry_ip.text()}:{self.PRH_entry_port.text()}"
        )
        # PRINTHEAD
        self.db_url = (
            f"http://{self.DB_entry_ip.text()}:{self.DB_entry_port.text()}"
        )
        




#######################################   STRD DIALOG    #####################################################

def strd_dialog(
        usr_text='you forgot to set a text, dummy',
        usr_title='default dialog',
        standalone=False,
) -> StandardDialog | int:
    """shows a dialog window, text and title can be set, returns the 
    users choice or the dialog object, depending on 'standalone'
    """

    if standalone:
        strd_dialog_app = 0
        strd_dialog_app = QApplication(sys.argv)
    strd_dialog_win = StandardDialog(text=usr_text, title=usr_title)
    if standalone:
        strd_dialog_win.show()
        strd_dialog_app.exec()
        # sys.exit(app.exec())
        return strd_dialog_win.result()

    return strd_dialog_win


def file_dialog(
        usr_title='default window',
        standalone=False
) -> FileDialog | list[str]:
    """creates FileDialog and either shows it directly and then returns the
    users choice or returns the dialog object, depending on 'standalone'
    """

    if standalone:
        file_dialog_app = 0
        file_dialog_app = QApplication(sys.argv)
    file_dialog_win = FileDialog(title=usr_title)
    if standalone:
        file_dialog_win.show()
        file_dialog_app.exec()
        # sys.exit(app.exec())
        return file_dialog_win.selectedFiles()

    return file_dialog_win


def conn_dialog(
        title='default window',
        standalone=False
) -> ConnDialog | list:
    """shows a dialog with robots and pumps connection setting, IPs, ports,
    etc. can be set, user can choose if to connect the pumps right away,
    returns the users settings
    """

    if standalone:
        conn_dialog_app = 0
        conn_dialog_app = QApplication(sys.argv)
    conn_dialog_win = ConnDialog(title=title)
    if standalone:
        conn_dialog_win.show()
        conn_dialog_app.exec()
        # sys.exit(app.exec())
        return [
            conn_dialog_win.result(),
            conn_dialog_win.dev_available,
            conn_dialog_win.rob_set,
            conn_dialog_win.p_com,
            conn_dialog_win.prh_url,
            conn_dialog_win.db_url,
        ]

    return conn_dialog_win
