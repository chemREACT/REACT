from UIs.SplashScreen import Ui_SplashScreen
from PyQt5 import QtWidgets, QtGui, QtCore

counter = 0


class SplashScreen(QtWidgets.QMainWindow, Ui_SplashScreen):
    def __init__(self, parent):
        QtWidgets.QMainWindow.__init__(self)
        self.parent = parent
        self.ui = Ui_SplashScreen()
        self.ui.setupUi(self)

        # Remove title bar:
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)

        # Drop shadow effect:
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QtGui.QColor(0, 0, 0, 60))
        self.ui.dropShadowFrame.setGraphicsEffect(self.shadow)

        # Start timer:
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.progress)
        countdown = 35
        # Timer in milliseconds:
        self.timer.start(countdown)

    def progress(self):
        """
        :return:
        """
        global counter

        # SET VALUE TO PROGRESS BAR
        self.ui.progressBar.setValue(counter)
        if counter == 10:
            self.ui.label_loading.setText("loading... source code")
        if counter == 30:
            self.ui.label_loading.setText("loading... User Interface & libraries")

        if counter == 45:
            # Launch open source pymol at login:
            if self.parent.settings.pymol_at_launch:
                # if self.parent.settings['REACT pymol']:
                self.parent.start_pymol()

        # CLOSE SPLASH SCREE AND OPEN APP
        if counter > 100:
            # STOP TIMER
            self.timer.stop()

            # SHOW MAIN WINDOW
            self.parent.window().show()
            self.parent.window().setWindowState(QtCore.Qt.WindowActive)
            self.parent.window().isActiveWindow()
            # CLOSE SPLASH SCREEN
            self.close()

        # INCREASE COUNTER
        counter += 1
