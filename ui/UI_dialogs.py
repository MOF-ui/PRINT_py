#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as  
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


#######################################     IMPORTS      #####################################################

from PyQt5 import QtCore, QtGui, QtWidgets



#######################################     CLASSES      #####################################################

class Ui_Dialog(object):
    # Form implementation generated from reading ui file 'ui/PwrUp.ui'
    #
    # Created by: PyQt5 UI code generator 5.15.9
    
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(566, 392)
        Dialog.setStyleSheet("background-color: #5d707f;")
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(210, 350, 341, 32))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift")
        font.setPointSize(14)
        self.buttonBox.setFont(font)
        self.buttonBox.setStyleSheet(   "QPushButton {\n"
                                        "    background-color: #FFBA00;\n"
                                        "    border-radius: 5px;\n"
                                        "    font-size: 14pt;\n"
                                        "    width: 5em;\n"
                                        "}\n"
                                        "\n"
                                        "QPushButton:hover {\n"
                                        "    background-color: #FFC300;\n"
                                        "}\n"
                                        "\n"
                                        "QPushButton:pressed {\n"
                                        "    background-color: #88AB75;\n"
                                        "}")
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(20, 20, 521, 311))
        self.label.setStyleSheet(   "border: 2px solid #5d707f;\n"
                                    "border-radius: 5px;\n"
                                    "font-family: \"Bahnschrift\";\n"
                                    "font-size: 14pt;\n"
                                    "padding: 2px;\n"
                                    "padding-left: 5px;\n"
                                    "background-color: #5d707f;\n"
                                    "color: #f2f4f3;")
        self.label.setObjectName("label")
        self.label.setWordWrap(True)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "PRINT welcome dialog"))
        self.label.setText(_translate("Dialog", "STARTING PRINT APP..."))







class Ui_FileDialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(1000,620)







class Ui_ConnDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(789, 643)
        Dialog.setStyleSheet(   "/* leave here to be overwritten by anything more specific */\n"
                                "QObject {\n"
                                "    background: #4c4a48;\n"
                                "}\n"
                                "\n"
                                "QWidget {\n"
                                "    font-family: \"Bahnschrift\";\n"
                                "}\n"
                                "\n"
                                "\n"
                                "\n"
                                "/* alphabetical from here */\n"
                                "\n"
                                "QCheckBox::indicator {\n"
                                "    top: -1 px;\n"
                                "    width: 13px;\n"
                                "    height: 13px;\n"
                                "    background-color: #f2f4f3;\n"
                                "    border-radius: 2px;\n"
                                "}\n"
                                "\n"
                                "QCheckBox::indicator:checked {\n"
                                "    background-color: #ffba00;\n"
                                "    image: url(:/images/right.png);\n"
                                "}\n"
                                "\n"
                                "\n"
                                "\n"
                                "\n"
                                "QComboBox {\n"
                                "    border-radius: 5px;\n"
                                "    padding-left: 10px;\n"
                                "    min-width: 6em;\n"
                                "    background: #F2F4F3;\n"
                                "    font-family: \"Bahnschrift\";\n"
                                "}\n"
                                "\n"
                                "QComboBox:on { /* shift the text when the popup opens */\n"
                                "    border: 2px sold #F2F4F3;\n"
                                "}\n"
                                "\n"
                                "QComboBox::drop-down {\n"
                                "    width: 25px;\n"
                                "    background-color: #FFBA00;\n"
                                "}\n"
                                "\n"
                                "QComboBox::down-arrow {\n"
                                "    border-image: url(:/images/down.png);\n"
                                "}\n"
                                "\n"
                                "QComboBox::drop-down::hover {\n"
                                "    background-color: #FFC300;\n"
                                "}\n"
                                "\n"
                                "QComboBox::drop-down::pressed {\n"
                                "    background-color: #88AB75;\n"
                                "}\n"
                                "\n"
                                "QComboBox QAbstractItemView {\n"
                                "    selection-background-color: #FFBA00;\n"
                                "}\n"
                                "\n"
                                "\n"
                                "\n"
                                "\n"
                                "QListView {\n"
                                "    padding: 2px;\n"
                                "    background: #F2F4F3;\n"
                                "    border-radius: 5px;\n"
                                "}\n"
                                "\n"
                                "\n"
                                "\n"
                                "\n"
                                "QLabel, QLineEdit {\n"
                                "    border: 2px solid #F2F4F3;\n"
                                "    border-radius: 5px;\n"
                                "    font-size: 14pt;\n"
                                "    padding: 2px;\n"
                                "    padding-left: 5px;\n"
                                "    background-color: #F2F4F3;\n"
                                "}\n"
                                "\n"
                                "\n"
                                "\n"
                                "\n"
                                "QTextEdit, QListWidget {\n"
                                "    border: 0px;\n"
                                "    border-radius: 5px;\n"
                                "    font-size: 12pt;\n"
                                "    padding: 2px;\n"
                                "    padding-left: 5px;\n"
                                "    background-color: #F2F4F3;\n"
                                "}\n"
                                "\n"
                                "\n"
                                "\n"
                                "QPushButton {\n"
                                "    background-color: #FFBA00;\n"
                                "    border-radius: 5px;\n"
                                "    font-size: 14pt;\n"
                                "}\n"
                                "\n"
                                "QPushButton:hover {\n"
                                "    background-color: #FFC300;\n"
                                "}\n"
                                "\n"
                                "QPushButton:pressed {\n"
                                "    background-color: #88AB75;\n"
                                "}\n"
                                "\n"
                                "\n"
                                "\n"
                                "QSlider {\n"
                                "    background: #5d707f;\n"
                                "}\n"
                                "\n"
                                "QSlider::handle:horizontal, QSlider::handle:vertical {\n"
                                "    background-color: #FFBA00;\n"
                                "}\n"
                                "\n"
                                "\n"
                                "\n"
                                "\n"
                                "QSpinBox, QDoubleSpinBox {\n"
                                "    border: 2px solid #F2F4F3;\n"
                                "    border-radius: 5px;\n"
                                "    border-width: 3px;\n"
                                "    border-top-right-radius: 0;\n"
                                "    border-bottom-right-radius: 0;\n"
                                "    font-size: 12pt;\n"
                                "    padding: 2px;\n"
                                "    padding-left: 5px;\n"
                                "    padding-right: 5px;\n"
                                "    background-color: #F2F4F3;\n"
                                "}\n"
                                "\n"
                                "QSpinBox::up-button, QDoubleSpinBox::up-button { \n"
                                "    subcontrol-origin: padding;\n"
                                "    subcontrol-position: top right; /* position at the top right corner */\n"
                                "    width: 30 px;\n"
                                "}\n"
                                "\n"
                                "QSpinBox::down-button, QDoubleSpinBox::down-button { \n"
                                "    subcontrol-origin: padding;\n"
                                "    subcontrol-position: bottom right; /* position at the top right corner */\n"
                                "    width: 30 px;\n"
                                "    top: 1px;\n"
                                "}\n"
                                "\n"
                                "QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {\n"
                                "    image: url(:/images/up.png);\n"
                                "}\n"
                                "\n"
                                "QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {\n"
                                "    image: url(:/images/down.png);;\n"
                                "}\n"
                                "\n"
                                "\n"
                                "\n"
                                "\n"
                                "QScrollBar:vertical {  \n"
                                "    border: None;\n"
                                "    background:#f2f4f3;\n"
                                "    width: 10px;\n"
                                "}\n"
                                "\n"
                                "QScrollBar::handle:vertical {\n"
                                "    background:#ffba00;\n"
                                "    border-radius: 4px;\n"
                                "    min-height: 20px;\n"
                                "}\n"
                                "\n"
                                "QScrollBar:horizontal {  \n"
                                "    background:#f2f4f3;\n"
                                "    height: 15px;\n"
                                "}\n"
                                "\n"
                                "QScrollBar::handle:horizontal {\n"
                                "    background:#ffba00;\n"
                                "    border-radius: 4px;\n"
                                "    min-width: 20px;\n"
                                "}\n"
                                "\n"
                                "\n"
                                "\n"
                                "QTextEdit {\n"
                                "    border: 2px solid #909cc2\n"
                                "}\n"
                                "\n"
                                "QTextEdit:selected {\n"
                                "    border-color: #aab9e6\n"
                                "}")
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(170, 560, 571, 51))
        self.buttonBox.setStyleSheet(   "QPushButton {\n"
                                        "    background-color: #FFBA00;\n"
                                        "    color: #000000;\n"
                                        "    border-radius: 5px;\n"
                                        "    font-size: 14pt;\n"
                                        "    width: 5em;\n"
                                        "    height: 35px;\n"
                                        "}\n"
                                        "\n"
                                        "QPushButton:hover {\n"
                                        "    background-color: #FFC300;\n"
                                        "}\n"
                                        "\n"
                                        "QPushButton:pressed {\n"
                                        "    background-color: #88AB75;\n"
                                        "}")
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Abort|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.TCP_ROB_lbl_tio_conn = QtWidgets.QLabel(Dialog)
        self.TCP_ROB_lbl_tio_conn.setGeometry(QtCore.QRect(80, 290, 131, 30))
        self.TCP_ROB_lbl_tio_conn.setStyleSheet("border: 0px;\n"
                                                "font-size: 12pt;\n"
                                                "background-color: #4c4a48;\n"
                                                "color: #E1E5EE;")
        self.TCP_ROB_lbl_tio_conn.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_ROB_lbl_tio_conn.setObjectName("TCP_ROB_lbl_tio_conn")
        self.TCP_ROB_lbl_bytesToRead = QtWidgets.QLabel(Dialog)
        self.TCP_ROB_lbl_bytesToRead.setGeometry(QtCore.QRect(80, 370, 131, 30))
        self.TCP_ROB_lbl_bytesToRead.setStyleSheet( "border: 0px;\n"
                                                    "font-size: 12pt;\n"
                                                    "background-color: #4c4a48;\n"
                                                    "color: #E1E5EE;")
        self.TCP_ROB_lbl_bytesToRead.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_ROB_lbl_bytesToRead.setObjectName("TCP_ROB_lbl_bytesToRead")
        self.TCP_ROB_lbl_port = QtWidgets.QLabel(Dialog)
        self.TCP_ROB_lbl_port.setGeometry(QtCore.QRect(80, 210, 131, 30))
        self.TCP_ROB_lbl_port.setStyleSheet("border: 0px;\n"
                                            "font-size: 12pt;\n"
                                            "background-color: #4c4a48;\n"
                                            "color: #E1E5EE;")
        self.TCP_ROB_lbl_port.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_ROB_lbl_port.setObjectName("TCP_ROB_lbl_port")
        self.TCP_ROB_lbl_tio_rw = QtWidgets.QLabel(Dialog)
        self.TCP_ROB_lbl_tio_rw.setGeometry(QtCore.QRect(80, 450, 131, 30))
        self.TCP_ROB_lbl_tio_rw.setStyleSheet(  "border: 0px;\n"
                                                "font-size: 12pt;\n"
                                                "background-color: #4c4a48;\n"
                                                "color: #E1E5EE;")
        self.TCP_ROB_lbl_tio_rw.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_ROB_lbl_tio_rw.setObjectName("TCP_ROB_lbl_tio_rw")
        self.TCP_ROB_lbl_ip = QtWidgets.QLabel(Dialog)
        self.TCP_ROB_lbl_ip.setGeometry(QtCore.QRect(80, 130, 131, 30))
        self.TCP_ROB_lbl_ip.setStyleSheet(  "border: 0px;\n"
                                            "font-size: 12pt;\n"
                                            "background-color: #4c4a48;\n"
                                            "color: #E1E5EE;")
        self.TCP_ROB_lbl_ip.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_ROB_lbl_ip.setObjectName("TCP_ROB_lbl_ip")
        self.TCP_ROB_lbl_0 = QtWidgets.QLabel(Dialog)
        self.TCP_ROB_lbl_0.setGeometry(QtCore.QRect(90, 40, 111, 41))
        self.TCP_ROB_lbl_0.setStyleSheet(   "background: #5d707f;\n"
                                            "color: #f2f4f3;")
        self.TCP_ROB_lbl_0.setAlignment(QtCore.Qt.AlignCenter)
        self.TCP_ROB_lbl_0.setObjectName("TCP_ROB_lbl_0")
        self.TCP_PUMP1_lbl_0 = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP1_lbl_0.setGeometry(QtCore.QRect(330, 40, 111, 41))
        self.TCP_PUMP1_lbl_0.setStyleSheet( "background: #5d707f;\n"
                                            "color: #f2f4f3;")
        self.TCP_PUMP1_lbl_0.setAlignment(QtCore.Qt.AlignCenter)
        self.TCP_PUMP1_lbl_0.setObjectName("TCP_PUMP1_lbl_0")
        self.TCP_PUMP2_lbl_0 = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP2_lbl_0.setGeometry(QtCore.QRect(560, 40, 111, 41))
        self.TCP_PUMP2_lbl_0.setStyleSheet( "background: #5d707f;\n"
                                            "color: #f2f4f3;")
        self.TCP_PUMP2_lbl_0.setAlignment(QtCore.Qt.AlignCenter)
        self.TCP_PUMP2_lbl_0.setObjectName("TCP_PUMP2_lbl_0")
        self.TCP_PUMP1_lbl_ip = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP1_lbl_ip.setGeometry(QtCore.QRect(320, 130, 131, 30))
        self.TCP_PUMP1_lbl_ip.setStyleSheet("border: 0px;\n"
                                            "font-size: 12pt;\n"
                                            "background-color: #4c4a48;\n"
                                            "color: #E1E5EE;")
        self.TCP_PUMP1_lbl_ip.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_PUMP1_lbl_ip.setObjectName("TCP_PUMP1_lbl_ip")
        self.TCP_PUMP1_lbl_tio_conn = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP1_lbl_tio_conn.setGeometry(QtCore.QRect(320, 290, 131, 30))
        self.TCP_PUMP1_lbl_tio_conn.setStyleSheet(  "border: 0px;\n"
                                                    "font-size: 12pt;\n"
                                                    "background-color: #4c4a48;\n"
                                                    "color: #E1E5EE;")
        self.TCP_PUMP1_lbl_tio_conn.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_PUMP1_lbl_tio_conn.setObjectName("TCP_PUMP1_lbl_tio_conn")
        self.TCP_PUMP1_lbl_bytesToRead = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP1_lbl_bytesToRead.setGeometry(QtCore.QRect(320, 370, 131, 30))
        self.TCP_PUMP1_lbl_bytesToRead.setStyleSheet(   "border: 0px;\n"
                                                        "font-size: 12pt;\n"
                                                        "background-color: #4c4a48;\n"
                                                        "color: #E1E5EE;")
        self.TCP_PUMP1_lbl_bytesToRead.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_PUMP1_lbl_bytesToRead.setObjectName("TCP_PUMP1_lbl_bytesToRead")
        self.TCP_PUMP1_lbl_port = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP1_lbl_port.setGeometry(QtCore.QRect(320, 210, 131, 30))
        self.TCP_PUMP1_lbl_port.setStyleSheet(  "border: 0px;\n"
                                                "font-size: 12pt;\n"
                                                "background-color: #4c4a48;\n"
                                                "color: #E1E5EE;")
        self.TCP_PUMP1_lbl_port.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_PUMP1_lbl_port.setObjectName("TCP_PUMP1_lbl_port")
        self.TCP_PUMP1_lbl_tio_rw = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP1_lbl_tio_rw.setGeometry(QtCore.QRect(320, 450, 131, 30))
        self.TCP_PUMP1_lbl_tio_rw.setStyleSheet("border: 0px;\n"
                                                "font-size: 12pt;\n"
                                                "background-color: #4c4a48;\n"
                                                "color: #E1E5EE;")
        self.TCP_PUMP1_lbl_tio_rw.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_PUMP1_lbl_tio_rw.setObjectName("TCP_PUMP1_lbl_tio_rw")
        self.TCP_PUMP2_lbl_tio_rw = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP2_lbl_tio_rw.setGeometry(QtCore.QRect(550, 450, 131, 30))
        self.TCP_PUMP2_lbl_tio_rw.setStyleSheet("border: 0px;\n"
                                                "font-size: 12pt;\n"
                                                "background-color: #4c4a48;\n"
                                                "color: #E1E5EE;")
        self.TCP_PUMP2_lbl_tio_rw.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_PUMP2_lbl_tio_rw.setObjectName("TCP_PUMP2_lbl_tio_rw")
        self.TCP_PUMP2_lbl_port = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP2_lbl_port.setGeometry(QtCore.QRect(550, 210, 131, 30))
        self.TCP_PUMP2_lbl_port.setStyleSheet(  "border: 0px;\n"
                                                "font-size: 12pt;\n"
                                                "background-color: #4c4a48;\n"
                                                "color: #E1E5EE;")
        self.TCP_PUMP2_lbl_port.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_PUMP2_lbl_port.setObjectName("TCP_PUMP2_lbl_port")
        self.TCP_PUMP2_lbl_bytesToRead = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP2_lbl_bytesToRead.setGeometry(QtCore.QRect(550, 370, 131, 30))
        self.TCP_PUMP2_lbl_bytesToRead.setStyleSheet(   "border: 0px;\n"
                                                        "font-size: 12pt;\n"
                                                        "background-color: #4c4a48;\n"
                                                        "color: #E1E5EE;")
        self.TCP_PUMP2_lbl_bytesToRead.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_PUMP2_lbl_bytesToRead.setObjectName("TCP_PUMP2_lbl_bytesToRead")
        self.TCP_PUMP2_lbl_ip = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP2_lbl_ip.setGeometry(QtCore.QRect(550, 130, 131, 30))
        self.TCP_PUMP2_lbl_ip.setStyleSheet("border: 0px;\n"
                                            "font-size: 12pt;\n"
                                            "background-color: #4c4a48;\n"
                                            "color: #E1E5EE;")
        self.TCP_PUMP2_lbl_ip.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_PUMP2_lbl_ip.setObjectName("TCP_PUMP2_lbl_ip")
        self.TCP_PUMP2_lbl_tio_conn = QtWidgets.QLabel(Dialog)
        self.TCP_PUMP2_lbl_tio_conn.setGeometry(QtCore.QRect(550, 290, 131, 30))
        self.TCP_PUMP2_lbl_tio_conn.setStyleSheet(  "border: 0px;\n"
                                                    "font-size: 12pt;\n"
                                                    "background-color: #4c4a48;\n"
                                                    "color: #E1E5EE;")
        self.TCP_PUMP2_lbl_tio_conn.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.TCP_PUMP2_lbl_tio_conn.setObjectName("TCP_PUMP2_lbl_tio_conn")
        self.TCP_ROB_entry_ip = QtWidgets.QLineEdit(Dialog)
        self.TCP_ROB_entry_ip.setGeometry(QtCore.QRect(80, 160, 131, 41))
        self.TCP_ROB_entry_ip.setObjectName("TCP_ROB_entry_ip")
        self.TCP_ROB_entry_port = QtWidgets.QLineEdit(Dialog)
        self.TCP_ROB_entry_port.setGeometry(QtCore.QRect(80, 240, 131, 41))
        self.TCP_ROB_entry_port.setObjectName("TCP_ROB_entry_port")
        self.TCP_PUMP1_entry_port = QtWidgets.QLineEdit(Dialog)
        self.TCP_PUMP1_entry_port.setGeometry(QtCore.QRect(320, 240, 131, 41))
        self.TCP_PUMP1_entry_port.setObjectName("TCP_PUMP1_entry_port")
        self.TCP_PUMP1_entry_ip = QtWidgets.QLineEdit(Dialog)
        self.TCP_PUMP1_entry_ip.setGeometry(QtCore.QRect(320, 160, 131, 41))
        self.TCP_PUMP1_entry_ip.setObjectName("TCP_PUMP1_entry_ip")
        self.TCP_PUMP2_entry_port = QtWidgets.QLineEdit(Dialog)
        self.TCP_PUMP2_entry_port.setGeometry(QtCore.QRect(550, 240, 131, 41))
        self.TCP_PUMP2_entry_port.setObjectName("TCP_PUMP2_entry_port")
        self.TCP_PUMP2_entry_ip = QtWidgets.QLineEdit(Dialog)
        self.TCP_PUMP2_entry_ip.setGeometry(QtCore.QRect(550, 160, 131, 41))
        self.TCP_PUMP2_entry_ip.setObjectName("TCP_PUMP2_entry_ip")
        self.TCP_ROB_num_tio_rw = QtWidgets.QSpinBox(Dialog)
        self.TCP_ROB_num_tio_rw.setGeometry(QtCore.QRect(80, 480, 131, 41))
        self.TCP_ROB_num_tio_rw.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.TCP_ROB_num_tio_rw.setMaximum(99999)
        self.TCP_ROB_num_tio_rw.setObjectName("TCP_ROB_num_tio_rw")
        self.TCP_ROB_num_bytesToRead = QtWidgets.QSpinBox(Dialog)
        self.TCP_ROB_num_bytesToRead.setGeometry(QtCore.QRect(80, 400, 131, 41))
        self.TCP_ROB_num_bytesToRead.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.TCP_ROB_num_bytesToRead.setMaximum(99999)
        self.TCP_ROB_num_bytesToRead.setObjectName("TCP_ROB_num_bytesToRead")
        self.TCP_ROB_num_tio_conn = QtWidgets.QSpinBox(Dialog)
        self.TCP_ROB_num_tio_conn.setGeometry(QtCore.QRect(80, 320, 131, 41))
        self.TCP_ROB_num_tio_conn.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.TCP_ROB_num_tio_conn.setMaximum(99999)
        self.TCP_ROB_num_tio_conn.setObjectName("TCP_ROB_num_tio_conn")
        self.TCP_PUMP1_num_tio_rw = QtWidgets.QSpinBox(Dialog)
        self.TCP_PUMP1_num_tio_rw.setGeometry(QtCore.QRect(320, 480, 131, 41))
        self.TCP_PUMP1_num_tio_rw.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.TCP_PUMP1_num_tio_rw.setMaximum(99999)
        self.TCP_PUMP1_num_tio_rw.setObjectName("TCP_PUMP1_num_tio_rw")
        self.TCP_PUMP1_num_bytesToRead = QtWidgets.QSpinBox(Dialog)
        self.TCP_PUMP1_num_bytesToRead.setGeometry(QtCore.QRect(320, 400, 131, 41))
        self.TCP_PUMP1_num_bytesToRead.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.TCP_PUMP1_num_bytesToRead.setMaximum(99999)
        self.TCP_PUMP1_num_bytesToRead.setObjectName("TCP_PUMP1_num_bytesToRead")
        self.TCP_PUMP1_num_tio_conn = QtWidgets.QSpinBox(Dialog)
        self.TCP_PUMP1_num_tio_conn.setGeometry(QtCore.QRect(320, 320, 131, 41))
        self.TCP_PUMP1_num_tio_conn.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.TCP_PUMP1_num_tio_conn.setMaximum(99999)
        self.TCP_PUMP1_num_tio_conn.setObjectName("TCP_PUMP1_num_tio_conn")
        self.TCP_PUMP2_num_tio_rw = QtWidgets.QSpinBox(Dialog)
        self.TCP_PUMP2_num_tio_rw.setGeometry(QtCore.QRect(550, 480, 131, 41))
        self.TCP_PUMP2_num_tio_rw.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.TCP_PUMP2_num_tio_rw.setMaximum(99999)
        self.TCP_PUMP2_num_tio_rw.setObjectName("TCP_PUMP2_num_tio_rw")
        self.TCP_PUMP2_num_tio_conn = QtWidgets.QSpinBox(Dialog)
        self.TCP_PUMP2_num_tio_conn.setGeometry(QtCore.QRect(550, 320, 131, 41))
        self.TCP_PUMP2_num_tio_conn.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.TCP_PUMP2_num_tio_conn.setMaximum(99999)
        self.TCP_PUMP2_num_tio_conn.setObjectName("TCP_PUMP2_num_tio_conn")
        self.TCP_PUMP2_num_bytesToRead = QtWidgets.QSpinBox(Dialog)
        self.TCP_PUMP2_num_bytesToRead.setGeometry(QtCore.QRect(550, 400, 131, 41))
        self.TCP_PUMP2_num_bytesToRead.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.TCP_PUMP2_num_bytesToRead.setMaximum(99999)
        self.TCP_PUMP2_num_bytesToRead.setObjectName("TCP_PUMP2_num_bytesToRead")
        self.TCP_PUMP1_connDef = QtWidgets.QCheckBox(Dialog)
        self.TCP_PUMP1_connDef.setGeometry(QtCore.QRect(327, 100, 131, 20))
        self.TCP_PUMP1_connDef.setStyleSheet(   "QCheckBox {\n"
                                                "    color: #f2f4f3;\n"
                                                "    font-size: 10pt;\n"
                                                "}\n"
                                                "")
        self.TCP_PUMP1_connDef.setObjectName("TCP_PUMP1_connDef")
        self.TCP_PUMP2_connDef = QtWidgets.QCheckBox(Dialog)
        self.TCP_PUMP2_connDef.setGeometry(QtCore.QRect(560, 100, 131, 20))
        self.TCP_PUMP2_connDef.setStyleSheet(   "QCheckBox {\n"
                                                "    color: #f2f4f3;\n"
                                                "    font-size: 10pt;\n"
                                                "}\n"
                                                "")
        self.TCP_PUMP2_connDef.setObjectName("TCP_PUMP2_connDef")
        self.TCP_btt_default = QtWidgets.QPushButton(Dialog)
        self.TCP_btt_default.setGeometry(QtCore.QRect(50, 568, 141, 35))
        self.TCP_btt_default.setObjectName("TCP_btt_default")

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.TCP_ROB_lbl_tio_conn.setText(_translate("Dialog", "conn timeout [ms]"))
        self.TCP_ROB_lbl_bytesToRead.setText(_translate("Dialog", "bytes to read"))
        self.TCP_ROB_lbl_port.setText(_translate("Dialog", "port"))
        self.TCP_ROB_lbl_tio_rw.setText(_translate("Dialog", "r/w timeout [ms]"))
        self.TCP_ROB_lbl_ip.setText(_translate("Dialog", "IP"))
        self.TCP_ROB_lbl_0.setText(_translate("Dialog", "ROBOT"))
        self.TCP_PUMP1_lbl_0.setText(_translate("Dialog", "PUMP 1"))
        self.TCP_PUMP2_lbl_0.setText(_translate("Dialog", "PUMP 2"))
        self.TCP_PUMP1_lbl_ip.setText(_translate("Dialog", "IP"))
        self.TCP_PUMP1_lbl_tio_conn.setText(_translate("Dialog", "conn timeout [ms]"))
        self.TCP_PUMP1_lbl_bytesToRead.setText(_translate("Dialog", "bytes to read"))
        self.TCP_PUMP1_lbl_port.setText(_translate("Dialog", "port"))
        self.TCP_PUMP1_lbl_tio_rw.setText(_translate("Dialog", "r/w timeout [ms]"))
        self.TCP_PUMP2_lbl_tio_rw.setText(_translate("Dialog", "r/w timeout [ms]"))
        self.TCP_PUMP2_lbl_port.setText(_translate("Dialog", "port"))
        self.TCP_PUMP2_lbl_bytesToRead.setText(_translate("Dialog", "bytes to read"))
        self.TCP_PUMP2_lbl_ip.setText(_translate("Dialog", "IP"))
        self.TCP_PUMP2_lbl_tio_conn.setText(_translate("Dialog", "conn timeout [ms]"))
        self.TCP_PUMP1_connDef.setText(_translate("Dialog", "connect on start"))
        self.TCP_PUMP2_connDef.setText(_translate("Dialog", "connect on start"))
        self.TCP_btt_default.setText(_translate("Dialog", "Voreinstellungen"))




import resources
