# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\strdDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(566, 392)
        Dialog.setStyleSheet("border-radius: 5px;\n"
"font-family: \"Bahnschrift\";\n"
"font-size: 14pt;\n"
"padding: 2px;\n"
"padding-left: 5px;\n"
"background-color: #4c4a48;\n"
"color: #f2f4f3;")
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(210, 331, 341, 51))
        font = QtGui.QFont()
        font.setFamily("Bahnschrift")
        font.setPointSize(14)
        self.buttonBox.setFont(font)
        self.buttonBox.setStyleSheet("QPushButton {\n"
"    background-color: #FFBA00;\n"
"    color: #000000;\n"
"    border-radius: 5px;\n"
"    border: None;\n"
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
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(20, 20, 521, 291))
        self.label.setStyleSheet("border-radius: 5px;\n"
"font-family: \"Bahnschrift\";\n"
"font-size: 14pt;\n"
"padding: 2px;\n"
"padding-left: 5px;\n"
"background-color: #4c4a48;\n"
"color: #f2f4f3;")
        self.label.setWordWrap(True)
        self.label.setObjectName("label")

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept) # type: ignore
        self.buttonBox.rejected.connect(Dialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "STARTING PRINT APP..."))