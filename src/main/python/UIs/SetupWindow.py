# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'SetupWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SetupWindow(object):
    def setupUi(self, SetupWindow):
        SetupWindow.setObjectName("SetupWindow")
        SetupWindow.resize(572, 495)
        self.centralwidget = QtWidgets.QWidget(SetupWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_main = QtWidgets.QWidget()
        self.tab_main.setObjectName("tab_main")
        self.tabWidget.addTab(self.tab_main, "")
        self.tab_freeze = QtWidgets.QWidget()
        self.tab_freeze.setObjectName("tab_freeze")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tab_freeze)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout_6 = QtWidgets.QGridLayout()
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.comboBox_freezetype = QtWidgets.QComboBox(self.tab_freeze)
        self.comboBox_freezetype.setObjectName("comboBox_freezetype")
        self.comboBox_freezetype.addItem("")
        self.comboBox_freezetype.addItem("")
        self.gridLayout_6.addWidget(self.comboBox_freezetype, 0, 0, 1, 1)
        self.button_auto_freeze = QtWidgets.QPushButton(self.tab_freeze)
        self.button_auto_freeze.setObjectName("button_auto_freeze")
        self.gridLayout_6.addWidget(self.button_auto_freeze, 0, 1, 1, 1)
        self.button_auto_freeze_2 = QtWidgets.QPushButton(self.tab_freeze)
        self.button_auto_freeze_2.setObjectName("button_auto_freeze_2")
        self.gridLayout_6.addWidget(self.button_auto_freeze_2, 0, 2, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout_6)
        self.gridLayout_5 = QtWidgets.QGridLayout()
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label = QtWidgets.QLabel(self.tab_freeze)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.list_model = QtWidgets.QListWidget(self.tab_freeze)
        self.list_model.setMinimumSize(QtCore.QSize(300, 0))
        self.list_model.setObjectName("list_model")
        self.gridLayout_2.addWidget(self.list_model, 1, 0, 1, 1)
        self.gridLayout_5.addLayout(self.gridLayout_2, 0, 0, 3, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_5.addItem(spacerItem, 0, 1, 1, 1)
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_2 = QtWidgets.QLabel(self.tab_freeze)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.gridLayout_3.addWidget(self.label_2, 0, 0, 1, 1)
        self.list_freeze_atoms = QtWidgets.QListWidget(self.tab_freeze)
        self.list_freeze_atoms.setMinimumSize(QtCore.QSize(150, 0))
        self.list_freeze_atoms.setMaximumSize(QtCore.QSize(150, 16777215))
        self.list_freeze_atoms.setObjectName("list_freeze_atoms")
        self.gridLayout_3.addWidget(self.list_freeze_atoms, 1, 0, 1, 1)
        self.gridLayout_5.addLayout(self.gridLayout_3, 0, 2, 3, 1)
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.button_add_state = QtWidgets.QPushButton(self.tab_freeze)
        self.button_add_state.setMinimumSize(QtCore.QSize(24, 24))
        self.button_add_state.setMaximumSize(QtCore.QSize(24, 24))
        self.button_add_state.setStyleSheet("QPushButton {\n"
"    background-color: rgb(143, 23, 119);\n"
"      color: white;\n"
"\n"
"}\n"
"\n"
"QPushButton:hover\n"
"{\n"
"       background-color:rgb(143, 23, 119);\n"
"\n"
"    border-style: outset;\n"
"    border-width: 0px;\n"
"    border-radius:10px;\n"
"\n"
"    \n"
"    /*border-color: rgb(12, 103, 213);*/\n"
"}\n"
"QPushButton:pressed\n"
"{\n"
"       /*background-color:rgb(17, 145, 255);\n"
"    color: black*/\n"
"    background-color: rgb(42, 42, 42);\n"
"}")
        self.button_add_state.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/24x24/resources/icons/arrow-plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.button_add_state.setIcon(icon)
        self.button_add_state.setIconSize(QtCore.QSize(24, 24))
        self.button_add_state.setFlat(True)
        self.button_add_state.setObjectName("button_add_state")
        self.gridLayout_4.addWidget(self.button_add_state, 0, 0, 1, 1)
        self.button_delete_state = QtWidgets.QPushButton(self.tab_freeze)
        self.button_delete_state.setMinimumSize(QtCore.QSize(24, 24))
        self.button_delete_state.setMaximumSize(QtCore.QSize(24, 24))
        self.button_delete_state.setStyleSheet("QPushButton {\n"
"    background-color: rgb(143, 23, 119);\n"
"      color: white;\n"
"\n"
"}\n"
"\n"
"QPushButton:hover\n"
"{\n"
"       background-color:rgb(143, 23, 119);\n"
"\n"
"    border-style: outset;\n"
"    border-width: 0px;\n"
"    border-radius:10px;\n"
"\n"
"    \n"
"    /*border-color: rgb(12, 103, 213);*/\n"
"}\n"
"QPushButton:pressed\n"
"{\n"
"       /*background-color:rgb(17, 145, 255);\n"
"    color: black*/\n"
"    background-color: rgb(42, 42, 42);\n"
"}")
        self.button_delete_state.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/24x24/resources/icons/arrow-minus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.button_delete_state.setIcon(icon1)
        self.button_delete_state.setIconSize(QtCore.QSize(24, 24))
        self.button_delete_state.setFlat(True)
        self.button_delete_state.setObjectName("button_delete_state")
        self.gridLayout_4.addWidget(self.button_delete_state, 1, 0, 1, 1)
        self.gridLayout_5.addLayout(self.gridLayout_4, 1, 1, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_5.addItem(spacerItem1, 2, 1, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout_5)
        self.tabWidget.addTab(self.tab_freeze, "")
        self.tab_scan = QtWidgets.QWidget()
        self.tab_scan.setObjectName("tab_scan")
        self.tabWidget.addTab(self.tab_scan, "")
        self.tab_view = QtWidgets.QWidget()
        self.tab_view.setObjectName("tab_view")
        self.tabWidget.addTab(self.tab_view, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.frame_2 = QtWidgets.QFrame(self.centralwidget)
        self.frame_2.setMinimumSize(QtCore.QSize(0, 40))
        self.frame_2.setMaximumSize(QtCore.QSize(16777215, 100))
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.button_cancel = QtWidgets.QPushButton(self.frame_2)
        self.button_cancel.setObjectName("button_cancel")
        self.gridLayout.addWidget(self.button_cancel, 0, 0, 1, 1)
        self.button_write = QtWidgets.QPushButton(self.frame_2)
        self.button_write.setObjectName("button_write")
        self.gridLayout.addWidget(self.button_write, 0, 1, 1, 1)
        self.horizontalLayout_2.addLayout(self.gridLayout)
        self.verticalLayout.addWidget(self.frame_2)
        SetupWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(SetupWindow)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(SetupWindow)

    def retranslateUi(self, SetupWindow):
        _translate = QtCore.QCoreApplication.translate
        SetupWindow.setWindowTitle(_translate("SetupWindow", "MainWindow"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_main), _translate("SetupWindow", "Main"))
        self.comboBox_freezetype.setItemText(0, _translate("SetupWindow", "Atom"))
        self.comboBox_freezetype.setItemText(1, _translate("SetupWindow", "Bond"))
        self.button_auto_freeze.setText(_translate("SetupWindow", "Auto-freeze"))
        self.button_auto_freeze_2.setText(_translate("SetupWindow", "Add Pymol selected"))
        self.label.setText(_translate("SetupWindow", "Atoms in model"))
        self.label_2.setText(_translate("SetupWindow", "Atoms to freeze"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_freeze), _translate("SetupWindow", "Freeze"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_scan), _translate("SetupWindow", "Scan"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_view), _translate("SetupWindow", "Preview"))
        self.button_cancel.setText(_translate("SetupWindow", "Cancel"))
        self.button_write.setText(_translate("SetupWindow", "Write"))
#import icons_rc
