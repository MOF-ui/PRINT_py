import sys
import os

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from ui.UI_mainframe_v6 import Ui_MainWindow

# PyQt stuff
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer, QMutex, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QShortcut
import libs.threads as workers

class test(QMainWindow, Ui_MainWindow):

    Thread = None

    def __init__(self, parent=None):
        super().__init__(parent)

        if not isinstance(self.Thread, QThread):
            self.Thread = QThread()
            print('Thread initialized..')
        self.Worker = workers.TestWorker()
        self.Worker.moveToThread(self.Thread)
        self.Thread.started.connect(self.Worker.run)
        self.Thread.finished.connect(self.Worker.stop)
        self.Thread.finished.connect(self.Worker.deleteLater)

        print(f"thread before start: {self.Thread.isRunning()}")
        print(f"worker before start: {type(self.Worker)}")
        self.Thread.start()
        print(f"thread after start: {self.Thread.isRunning()}")
        print(f"worker after start: {type(self.Worker)}")
        self.Thread.quit()
        self.Thread.wait()
        print(f"thread after quit/wait: {self.Thread.isRunning()}")
        print(f"worker after quit/wait: {type(self.Worker)}")

        if not isinstance(self.Thread, QThread):
            self.Thread = QThread()
            print('Thread initialized..')
        self.Worker = workers.TestWorker()
        self.Worker.moveToThread(self.Thread)
        self.Thread.started.connect(self.Worker.run)
        self.Thread.finished.connect(self.Worker.stop)
        self.Thread.finished.connect(self.Worker.deleteLater)
        self.Thread.start()

        print(f"thread after restart: {self.Thread.isRunning()}")
        print(f"worker after restart: {type(self.Worker)}")
        self.Thread.quit()
        self.Thread.wait()
        print(f"thread after requit/wait: {self.Thread.isRunning()}")
        print(f"worker after requit/wait: {type(self.Worker)}")
        QTimer.singleShot(0,self.close)
        



app = 0  # leave that here so app doesnt include the remnant of a previous QApplication instance
win = 0
app = QApplication(sys.argv)
win = test()
win.show()

# start application (uses sys for CMD)
app.exec()