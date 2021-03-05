from PyQt5 import QtWidgets
from UIs.SettingsWindow import Ui_SettingsWindow
import copy

class GlobalSettings(QtWidgets.QMainWindow):
    """
    User window to interact with global settings (REACT attributes
    workdir, DFT_settings and Ui_stylemode)
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.react = parent
        self.ui = Ui_SettingsWindow()
        self.ui.setupUi(self)
        
        self.DFT_options = {'functional': ['B3LYP', 'rB3LYP', 'M062X'],
                            'basis': {'3-21G': {'pol1': [''], 'pol2': [''], 'diff': [' ', '+']},
                                          '6-21G': {'pol1': ['', 'd'], 'pol2': ['', 'p'], 'diff': ['']},
                                          '4-31G': {'pol1': ['', 'd'], 'pol2': ['', 'p'], 'diff': ['']},
                                          '6-31G': {'pol1': ['', 'd', '2d', '3d', 'df', '2df', '3df', '3d2f'],
                                                    'pol2': ['', 'p', '2p', '3p', 'pd', '2pd', '3pd', '3p2d'],
                                                    'diff': ['', '+', '++']},
                                          '6-311G': {'pol1': ['', 'd', '2d', '3d', 'df', '2df', '3df', '3d2f'],
                                                     'pol2': ['', 'p', '2p', '3p', 'pd', '2pd', '3pd', '3p2d'],
                                                     'diff': ['', '+', '++']},
                                          'D95': {'pol1': ['', 'd', '2d', '3d', 'df', '2df', '3df', '3d2f'],
                                                  'pol2': ['', 'p', '2p', '3p', 'pd', '2pd', '3pd', '3p2d'],
                                                  'diff': ['', '+', '++']}
                                           }
                            }

        # Copy current setings from REACT. This variable will be modified
        # when the user makes changes to settings. On save, this variable
        # will replace the original settings variable beloning to REACT.
        # Some of the values in this variable may be None or False, else, 
        # It should look like this:
        #
        # self.settings = {"workdir": os.getcwd(),
        #                  "DFT": {"functional": "B3LYP",
        #                  "basis": ("6-31G", {"pol1": "d", "pol2": 'p', "diff": None}),
        #                  "additional keys": ["empiricaldispersion=gd3"],
        #                  "link 0"        : [],
        #                  "job keys"      : {"Opt (minimum)": ["noeigentest", "calcfc"], "Opt (TS)": [], "Freq": [], "IRC": [], "IRCMax": [], "SP": []},
        #                  "user"    : {"functional": [], "basis": {}}}, 
        #                  "pymolpath": None,
        #                  "REACT pymol" : True,
        #                  "pymol at launch": True,
        #                  "Ui": 1
        #                  }
        self.settings = copy.deepcopy(parent.settings)

        # fill functional and basis set comboboxes
        self.ui.comboBox_funct.addItems(self.DFT_options['functional'])
        self.ui.comboBox_funct.addItems(self.settings["DFT"]["user"]["functional"])
        self.ui.basis1_comboBox_3.addItems([x for x in self.DFT_options['basis']])
        self.ui.basis1_comboBox_3.addItems([x for x in self.settings["DFT"]["user"]["basis"] if x not in self.DFT_options['basis']])
        self.ui.job_type_comboBox.addItems(["Opt (minimum)", "Opt (TS)", "Freq", "IRC", "IRCMax", "SP"])

        # Read current settings, set window accordingly
        for item in self.settings.items():
            if item[0] == "DFT":
                self.ui.comboBox_funct.setCurrentText(item[1]["functional"])
                self.ui.basis1_comboBox_3.setCurrentText(item[1]["basis"][0])

                # update polarization and diffuse boxes, based on current basis
                self.update_basis_options(item[1]["basis"][0])

                #set current pol and diff functions
                self.ui.basis2_comboBox_4.setCurrentText(item[1]["basis"][1]["diff"])
                self.ui.basis3_comboBox_6.setCurrentText(item[1]["basis"][1]["pol1"])
                self.ui.basis4_comboBox_5.setCurrentText(item[1]["basis"][1]["pol2"])

                # Add all additional keys to appropriate QlistWidget
                self.ui.add_DFT_list_1.addItems(self.settings["DFT"]["additional keys"])
                self.ui.add_DFT_list_2.addItems(self.settings["DFT"]["link 0"])
                self.ui.add_DFT_list_3.addItems(self.settings["DFT"]["job keys"]["Opt (minimum)"])

            if item[0] == 'workdir':
                self.ui.cwd_lineEdit.setText(item[1])
            if item[0] == 'pymolpath':
                self.ui.pymol_lineEdit_2.setText(item[1])
            if item[0] == 'REACT pymol':
                if item[1]:
                    self.ui.checkBox.setChecked(True)
            if item[0] == 'pymol at launch':
                if item[1]:
                    self.ui.open_pymol_checkBox.setChecked(True)
            if item[0] == 'Ui':
                if item[1] == 1:
                    self.ui.dark_button.setChecked(True)
                else:
                    self.ui.light_button.setChecked(True)

        self.ui.label_2.hide()
        self.ui.dark_button.hide()
        self.ui.light_button.hide()

        self.ui.add_DFT_button_1.clicked.connect(lambda: self.add_item_to_list(self.ui.additionalKeys_1, self.ui.add_DFT_list_1, "additional keys"))
        self.ui.del_DFT_button_1.clicked.connect(lambda: self.del_item_from_list(self.ui.add_DFT_list_1, "additional keys"))
        self.ui.add_DFT_button_2.clicked.connect(lambda: self.add_item_to_list(self.ui.additionalKeys_2, self.ui.add_DFT_list_2, "link 0"))
        self.ui.del_DFT_button_2.clicked.connect(lambda: self.del_item_from_list(self.ui.add_DFT_list_2, "link 0"))
        self.ui.add_DFT_button_4.clicked.connect(lambda: self.add_item_to_list(self.ui.additionalKeys_3, self.ui.add_DFT_list_3, "job keys"))
        self.ui.del_DFT_button_4.clicked.connect(lambda: self.del_item_from_list(self.ui.add_DFT_list_3, "job keys"))
        self.ui.save_button.clicked.connect(self.save_settings)
        self.ui.cancel_button.clicked.connect(self.close)
        self.ui.comboBox_funct.textActivated.connect(lambda: self.combobox_update(self.ui.comboBox_funct, "functional"))
        self.ui.basis1_comboBox_3.textActivated.connect(lambda: self.combobox_update(self.ui.basis1_comboBox_3, "basis"))
        self.ui.basis2_comboBox_4.textActivated.connect(lambda: self.combobox_update(self.ui.basis2_comboBox_4, "diff"))
        self.ui.basis3_comboBox_6.textActivated.connect(lambda: self.combobox_update(self.ui.basis3_comboBox_6, "pol1"))
        self.ui.basis4_comboBox_5.textActivated.connect(lambda: self.combobox_update(self.ui.basis4_comboBox_5, "pol2"))
        self.ui.job_type_comboBox.textActivated.connect(lambda: self.combobox_update(self.ui.job_type_comboBox, "job type"))
        self.ui.change_cwd_button.clicked.connect(lambda: self.new_path_from_dialog(self.ui.cwd_lineEdit, "Select working directory"))
        self.ui.change_pymol_button.clicked.connect(lambda: self.new_path_from_dialog(self.ui.pymol_lineEdit_2,"select PyMOL path"))
        self.ui.checkBox.stateChanged.connect(lambda: self.check_box_update(self.ui.checkBox, "REACT pymol"))
        self.ui.open_pymol_checkBox.stateChanged.connect(lambda: self.check_box_update(self.ui.open_pymol_checkBox, "pymol at launch"))

    def new_path_from_dialog(self, textwidget, title_):
        """
        Changes text in work directory field using file dialog.
        No change saved in self.settings, this is handeled in save_settings. 
        """

        new_dir = QtWidgets.QFileDialog.getExistingDirectory(self, title_, self.settings["workdir"], options=QtWidgets.QFileDialog.DontUseNativeDialog)
        
        # use this instead for native QfileDialog
        # files_, files_type = QtWidgets.QFileDialog.getOpenFileName(self, title_, self.settings["workdir"], "PyMOL app (*.app)",options=QtWidgets.QFileDialog.DontUseNativeDialog)
                                                                
        if new_dir:
            textwidget.setText(new_dir)

    def check_box_update(self, checkbox, key):

        if checkbox.isChecked():
            self.settings[key] = True
        else:
            self.settings[key] = False

    def combobox_update(self, widget, key):
        """
        :param combobox: QComboBox
        :param DFT_key: str: key to access correct variable in self.settings
        Updates self.settings according to update on combobox
        Will add user input to self.settings if the input is unknown to REACT,
        """
        text = widget.currentText()

        if key == "job type":
            self.ui.add_DFT_list_3.clear()
            self.ui.add_DFT_list_3.addItems(self.settings["DFT"]["job keys"][text])

        if key in ["diff", "pol1", "pol2"]:

            basis = self.ui.basis1_comboBox_3.currentText()
            new_entry = True

            if basis in self.DFT_options["basis"]:
                if text in self.DFT_options["basis"][basis][key]:
                    new_entry = False
            if basis in self.settings["DFT"]["user"]["basis"]:
                if text in self.settings["DFT"]["user"]["basis"][basis][key]:
                    new_entry = False
            if new_entry:
                try:
                    self.settings["DFT"]["user"]["basis"][basis][key].append(text)
                except KeyError:
                    self.settings["DFT"]["user"]["basis"][basis] = {"pol1": [], "pol2": [], "diff": []}
                    self.settings["DFT"]["user"]["basis"][basis][key].append(text)
            self.settings["DFT"]["basis"][1][key] = text

        elif key in ["functional", "basis"]:

            if text not in self.DFT_options[key] and \
               text not in self.settings["DFT"]["user"][key]:
               # if basis or functional is unknown to REACT
                if key == "functional":
                    self.settings["DFT"]["user"]["functional"].append(text)
                elif key == "basis":
                    self.settings["DFT"]["user"]["basis"][text] = {"pol1": [], "pol2": [], "diff": []}

            if key == "functional":
                self.settings["DFT"]["functional"] = text
            else:
                self.settings["DFT"]["basis"] = (text, {"pol1": None, "pol2": None, "diff": None})
                self.update_basis_options(text)

    def add_item_to_list(self, Qtextinput, Qlist, DFT_key):
        """
        :param Qtextinput: QLineEdit
        :param Qlist: QListWidget
        :param DFT_key: str: key to access correct variable in self.settings
        Adds the text input from user (past to Qtextinput) to correct
        QlistWidget and updates self.settings accordingly.
        """

        user_input = Qtextinput.text()

        if Qlist == self.ui.add_DFT_list_3:
            job_type = self.ui.job_type_comboBox.currentText()
            item_list = self.settings["DFT"]["job keys"][job_type]
        else:
            item_list = self.settings["DFT"][DFT_key]

        if user_input and user_input not in item_list:
            item_list.append(user_input)
            Qlist.addItem(user_input)

    def del_item_from_list(self, Qlist, DFT_key):
        """
        :param Qlist: QListWidget
        :param DFT_key: str: key to access correct variable in self.settings
        Removes item in QlistWdiget and updates self.settings accordingly.
        """
        item_text = Qlist.currentItem().text()

        if Qlist == self.ui.add_DFT_list_3:
            job_type = self.ui.job_type_comboBox.currentText()
            item_list = self.settings["DFT"]["job keys"][job_type]
        else:
            item_list = self.settings["DFT"][DFT_key]  

        if item_text in item_list:
            item_list.remove(item_text)
        Qlist.takeItem(Qlist.currentRow())


    def update_basis_options(self, basis):
        """
        :param basis: str: name current basis
        Updates polarization and diffuse functions avail for basis set
        """

        self.block_all_combo_signals(True)

        self.ui.basis2_comboBox_4.clear()
        self.ui.basis3_comboBox_6.clear()
        self.ui.basis4_comboBox_5.clear()

        if basis in self.settings["DFT"]["user"]["basis"] and\
           basis in self.DFT_options["basis"]:
            # in case basis is in both, merge diff and pol options
            basis_options = {"diff": [], "pol1": [], "pol2": []}

            for key in ["diff", "pol1", "pol2"]:

                temp = self.DFT_options['basis'][basis][key]
                basis_options[key].extend(temp)

                temp = self.settings["DFT"]["user"]["basis"][basis][key]
                basis_options[key].extend(temp)

                # removes any duplicates in list
                basis_options[key] = list(set(basis_options[key]))

        elif basis in self.DFT_options['basis']:
            basis_options = self.DFT_options['basis'][basis]
        elif basis in self.settings["DFT"]["user"]["basis"]:
            basis_options = self.settings["DFT"]["user"]["basis"][basis]
        else:
            self.react.append_text('Basis set is unknown to REACT. Add polarization and diffuse functions as needed.')
            return

        for item in basis_options.items():
            if item[0] == "diff":
                if item[1]:
                    self.ui.basis2_comboBox_4.addItems(item[1])
            if item[0] == "pol1":
                if item[1]:
                    self.ui.basis3_comboBox_6.addItems(item[1])
            if item[0] == "pol2":
                if item[1]:
                    self.ui.basis4_comboBox_5.addItems(item[1])

        self.block_all_combo_signals(False)

    def block_all_combo_signals(self, bool_):
        self.ui.comboBox_funct.blockSignals(bool_)
        self.ui.basis1_comboBox_3.blockSignals(bool_)
        self.ui.job_type_comboBox.blockSignals(bool_)
        self.ui.basis2_comboBox_4.blockSignals(bool_)
        self.ui.basis3_comboBox_6.blockSignals(bool_)
        self.ui.basis4_comboBox_5.blockSignals(bool_) 

    def save_settings(self):
        self.settings["workdir"] = self.ui.cwd_lineEdit.text()
        self.settings["pymolpath"] = self.ui.pymol_lineEdit_2.text()
        
        self.react.settings = copy.deepcopy(self.settings)
        self.close()

    
    def switch_Ui_colormode(self, color):
        """
        Switch Ui colormode. Darkmode: color = 1, lightmode: color = 0 
        """
        pass


    def closeEvent(self, event):
        """
        When closing window, set to settings_window to None.
        :param event:
        """
        self.react.settings_window = None

