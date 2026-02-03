from PyQt5 import QtWidgets
from UIs.SettingsWindow import Ui_SettingsWindow
import os
import copy
import json
import copy
import mods.common_functions as cf


class Settings:
    def __init__(self, parent=None, settingspath=None):
        self.react = parent

        if not settingspath:
            self.settingspath = ".custom_settings.json"
        else:
            self.settingspath = settingspath

        self._workdir = None
        self._pymolpath = None
        self._pymol_at_launch = None
        self._UI_mode = None
        self._software = None  # Gaussian or ORCA

        # Separate DFT settings for Gaussian and ORCA
        self._gaussian_settings = None
        self._orca_settings = None

        try:
            with open(self.settingspath, "r") as f:
                custom_data = json.load(f, object_hook=cf.json_hook_int_bool_converter)
                self.load_custom_settings(custom_data)
        except:
            self.set_default_settings()

    @property
    def workdir(self):
        return self._workdir

    @property
    def pymolpath(self):
        return self._pymolpath

    @property
    def pymol_at_launch(self):
        return self._pymol_at_launch

    @property
    def UI_mode(self):
        return self._UI_mode

    @property
    def software(self):
        return self._software

    @property
    def gaussian_settings(self):
        return self._gaussian_settings

    @property
    def orca_settings(self):
        return self._orca_settings

    @property
    def basis(self):
        if self.software == "ORCA":
            return self._orca_settings.get("basis", "6-31G")
        return self._gaussian_settings.get("basis", "6-31G")

    @property
    def basis_diff(self):
        if self.software == "ORCA":
            return self._orca_settings.get("basis_diff")
        return self._gaussian_settings.get("basis_diff")

    @property
    def basis_pol1(self):
        if self.software == "ORCA":
            return self._orca_settings.get("basis_pol1", "d")
        return self._gaussian_settings.get("basis_pol1", "d")

    @property
    def basis_pol2(self):
        if self.software == "ORCA":
            return self._orca_settings.get("basis_pol2", "p")
        return self._gaussian_settings.get("basis_pol2", "p")

    @property
    def functional(self):
        if self.software == "ORCA":
            return self._orca_settings.get("functional", "B3LYP")
        return self._gaussian_settings.get("functional", "B3LYP")

    @property
    def job_type(self):
        if self.software == "ORCA":
            return self._orca_settings.get("job_type", "Opt")
        return self._gaussian_settings.get("job_type", "Opt")

    @property
    def job_mem(self):
        # Gaussian only
        return self._gaussian_settings.get("job_mem", 6)

    @property
    def chk(self):
        # Gaussian only
        return self._gaussian_settings.get("chk", True)

    @property
    def additional_keys(self):
        if self.software == "ORCA":
            return self._orca_settings.get("additional_keys", [])
        return self._gaussian_settings.get("additional_keys", [])

    @property
    def job_options(self):
        if self.software == "ORCA":
            return self._orca_settings.get("job_options", {})
        return self._gaussian_settings.get("job_options", {})

    @property
    def basis_options(self):
        if self.software == "ORCA":
            return self._orca_settings.get("basis_options", {})
        return self._gaussian_settings.get("basis_options", {})

    @property
    def link0_options(self):
        # Gaussian only
        return self._gaussian_settings.get("link0_options", [])

    @property
    def orca_nprocs(self):
        # ORCA only
        return self._orca_settings.get("nprocs", 4)

    @property
    def orca_maxcore(self):
        # ORCA only
        return self._orca_settings.get("maxcore", 2000)

    @workdir.setter
    def workdir(self, value):
        self._workdir = value

    @pymolpath.setter
    def pymolpath(self, value):
        self._pymolpath = value

    @pymol_at_launch.setter
    def pymol_at_launch(self, value):
        self._pymol_at_launch = value

    @UI_mode.setter
    def UI_mode(self, value):
        self._UI_mode = value

    @software.setter
    def software(self, value):
        if value in ["Gaussian", "ORCA"]:
            self._software = value
        else:
            self._software = "Gaussian"  # Default to Gaussian

    @gaussian_settings.setter
    def gaussian_settings(self, value):
        self._gaussian_settings = value

    @orca_settings.setter
    def orca_settings(self, value):
        self._orca_settings = value

    @functional.setter
    def functional(self, value):
        if self.software == "ORCA":
            self._orca_settings["functional"] = value
        else:
            self._gaussian_settings["functional"] = value

    @job_type.setter
    def job_type(self, value):
        if self.software == "ORCA":
            self._orca_settings["job_type"] = value
        else:
            self._gaussian_settings["job_type"] = value

    @basis.setter
    def basis(self, value):
        if self.software == "ORCA":
            self._orca_settings["basis"] = value
        else:
            self._gaussian_settings["basis"] = value

    @basis_diff.setter
    def basis_diff(self, value):
        if self.software == "ORCA":
            self._orca_settings["basis_diff"] = value
        else:
            self._gaussian_settings["basis_diff"] = value

    @basis_pol1.setter
    def basis_pol1(self, value):
        if self.software == "ORCA":
            self._orca_settings["basis_pol1"] = value
        else:
            self._gaussian_settings["basis_pol1"] = value

    @basis_pol2.setter
    def basis_pol2(self, value):
        if self.software == "ORCA":
            self._orca_settings["basis_pol2"] = value
        else:
            self._gaussian_settings["basis_pol2"] = value

    @job_mem.setter
    def job_mem(self, value):
        if type(value) == int:
            self._gaussian_settings["job_mem"] = value

    @chk.setter
    def chk(self, value):
        self._gaussian_settings["chk"] = value

    @additional_keys.setter
    def additional_keys(self, value):
        if self.software == "ORCA":
            self._orca_settings["additional_keys"] = value
        else:
            self._gaussian_settings["additional_keys"] = value

    @job_options.setter
    def job_options(self, value):
        if self.software == "ORCA":
            self._orca_settings["job_options"] = value
        else:
            self._gaussian_settings["job_options"] = value

    @basis_options.setter
    def basis_options(self, value):
        if self.software == "ORCA":
            self._orca_settings["basis_options"] = value
        else:
            self._gaussian_settings["basis_options"] = value

    @link0_options.setter
    def link0_options(self, value):
        self._gaussian_settings["link0_options"] = value

    @orca_nprocs.setter
    def orca_nprocs(self, value):
        if type(value) == int:
            self._orca_settings["nprocs"] = value

    @orca_maxcore.setter
    def orca_maxcore(self, value):
        if type(value) == int:
            self._orca_settings["maxcore"] = value

    @property
    def default_settings(self):
        return {
            "software": "Gaussian",
            "gaussian_settings": {
                "functional": "B3LYP",
                "basis": "6-31G",
                "basis_diff": None,
                "basis_pol1": "d",
                "basis_pol2": "p",
                "job_type": "Opt",
                "additional_keys": ["empiricaldispersion=gd3"],
                "job_mem": 6,
                "chk": True,
                "job_options": {
                    "Opt": ["noeigentest", "calcfc"],
                    "Opt (TS)": ["noeigentest", "calcfc"],
                    "Freq": [],
                    "IRC": [],
                    "IRCMax": [],
                    "Single point": [],
                },
                "link0_options": ["chk", "mem=6GB"],
                "basis_options": {
                    "3-21G": {"pol1": [""], "pol2": [""], "diff": ["", "+"]},
                    "6-21G": {"pol1": ["", "d"], "pol2": ["", "p"], "diff": [""]},
                    "4-31G": {"pol1": ["", "d"], "pol2": ["", "p"], "diff": [""]},
                    "6-31G": {
                        "pol1": ["", "d", "2d", "3d", "df", "2df", "3df", "3d2f"],
                        "pol2": ["", "p", "2p", "3p", "pd", "2pd", "3pd", "3p2d"],
                        "diff": ["", "+", "++"],
                    },
                    "6-311G": {
                        "pol1": ["", "d", "2d", "3d", "df", "2df", "3df", "3d2f"],
                        "pol2": ["", "p", "2p", "3p", "pd", "2pd", "3pd", "3p2d"],
                        "diff": ["", "+", "++"],
                    },
                    "D95": {
                        "pol1": ["", "d", "2d", "3d", "df", "2df", "3df", "3d2f"],
                        "pol2": ["", "p", "2p", "3p", "pd", "2pd", "3pd", "3p2d"],
                        "diff": ["", "+", "++"],
                    },
                },
                "functional_options": ["B3LYP", "rB3LYP", "M062X"],
            },
            "orca_settings": {
                "functional": "B3LYP",
                "basis": "def2-SVP",
                "basis_diff": None,
                "basis_pol1": None,
                "basis_pol2": None,
                "job_type": "Opt",
                "additional_keys": [],
                "job_options": {
                    "Opt": ["TightOPT"],
                    "Opt (TS)": ["TightOPT"],
                    "Freq": [],
                    "IRC": [],
                    "IRCMax": [],
                    "Single point": [],
                },
                "blocks": {},
                "basis_options": {
                    # def2 basis sets (no separate polarization/diffuse - built into name)
                    "def2-SVP": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "def2-SV(P)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "def2-TZVP": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "def2-TZVP(-f)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "def2-TZVPP": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "def2-QZVP": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "def2-QZVPP": {"pol1": [""], "pol2": [""], "diff": [""]},
                    # Minimally augmented def2
                    "ma-def2-SVP": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "ma-def2-TZVP": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "ma-def2-TZVPP": {"pol1": [""], "pol2": [""], "diff": [""]},
                    # Diffuse def2
                    "def2-SVPD": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "def2-TZVPD": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "def2-TZVPPD": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "def2-QZVPD": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "def2-QZVPPD": {"pol1": [""], "pol2": [""], "diff": [""]},
                    # Correlation-consistent
                    "cc-pVDZ": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "cc-pVTZ": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "cc-pVQZ": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "cc-pV5Z": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "aug-cc-pVDZ": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "aug-cc-pVTZ": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "aug-cc-pVQZ": {"pol1": [""], "pol2": [""], "diff": [""]},
                    # Pople basis sets (support polarization and diffuse like Gaussian)
                    "STO-3G": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "3-21G": {"pol1": [""], "pol2": [""], "diff": ["", "+"]},
                    "6-31G": {
                        "pol1": ["", "d", "2d", "2df", "3df"],
                        "pol2": ["", "p", "2p", "2df", "3pd"],
                        "diff": ["", "+", "++"],
                    },
                    "6-311G": {
                        "pol1": ["", "d", "2d", "2df", "3df"],
                        "pol2": ["", "p", "2p", "2df", "3pd"],
                        "diff": ["", "+", "++"],
                    },
                },
                "functional_options": [
                    "B3LYP",
                    "PBE0",
                    "M06-2X",
                    "wB97X-D3",
                    "B97-D3",
                    "TPSS",
                ],
            },
        }

    def set_default_settings(self):
        # self.workdir = os.getcwd()
        self.workdir = os.path.expanduser("~")
        self.pymolpath = None
        self.pymol_at_launch = True
        self.UI_mode = True
        self.software = "Gaussian"

        # Gaussian DFT settings
        self._gaussian_settings = copy.deepcopy(
            self.default_settings["gaussian_settings"]
        )

        # ORCA DFT settings
        self._orca_settings = copy.deepcopy(self.default_settings["orca_settings"])

    def load_custom_settings(self, settings):
        for key in [
            "workdir",
            "pymolpath",
            "pymol_at_launch",
            "UI_mode",
            "software",
            "gaussian_settings",
            "orca_settings",
        ]:
            self._load_custom_settings(settings, key)

    def _load_custom_settings(self, settings, key):
        try:
            item = settings.pop(key)

            if key == "workdir":
                self.workdir = item
            elif key == "pymolpath":
                self.pymolpath = item
            elif key == "pymol_at_launch":
                self.pymol_at_launch = item
            elif key == "UI_mode":
                self.UI_mode = item
            elif key == "software":
                self.software = item
            elif key == "gaussian_settings":
                self._gaussian_settings = item
            elif key == "orca_settings":
                self._orca_settings = item
        except KeyError:
            # Key doesn't exist in settings file, use defaults
            if key == "gaussian_settings":
                self._gaussian_settings = copy.deepcopy(
                    self.default_settings["gaussian_settings"]
                )
            elif key == "orca_settings":
                self._orca_settings = copy.deepcopy(
                    self.default_settings["orca_settings"]
                )
        except Exception as e:
            if self.react:
                self.react.append_text(
                    f'Failed to load "{key}" from custom settings: {e}'
                )

    def save_custom_settings(self):
        settings = {}

        settings["workdir"] = self.workdir
        settings["pymolpath"] = self.pymolpath
        settings["pymol_at_launch"] = self.pymol_at_launch
        settings["UI_mode"] = self.UI_mode
        settings["software"] = self.software
        settings["gaussian_settings"] = self._gaussian_settings
        settings["orca_settings"] = self._orca_settings

        with open(self.settingspath, "w+") as f:
            json.dump(settings, f, indent=2)


class SettingsTheWindow(QtWidgets.QMainWindow):
    """
    User window to interact with instanse of Settings
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.react = parent
        self.settings = parent.settings
        self.ui = Ui_SettingsWindow()
        self.ui.setupUi(self)

        self.job_options = copy.deepcopy(self.settings.job_options)
        self.basis_options = copy.deepcopy(self.settings.basis_options)
        self.functional_options = copy.deepcopy(self.settings.functional_options)

        # fill functional and basis set comboboxes

        try:
            self.add_items_to_window()
        except:
            self.settings.set_default_settings()
            self.add_items_to_window()

        self.ui.cwd_lineEdit.setText(self.settings.workdir)

        if self.settings.pymolpath != bool:
            self.ui.pymol_lineEdit_2.setText(self.settings.pymolpath)

        if self.settings.pymol_at_launch:
            self.ui.open_pymol_checkBox.setChecked(True)

        if self.settings.UI_mode == 1:
            self.ui.dark_button.setChecked(True)
        else:
            self.ui.light_button.setChecked(True)

        self.ui.label_2.hide()
        self.ui.dark_button.hide()
        self.ui.light_button.hide()

        self.ui.add_DFT_button_1.clicked.connect(
            lambda: self.add_item_to_list(
                self.ui.additionalKeys_1, self.ui.add_DFT_list_1, "additional keys"
            )
        )
        self.ui.del_DFT_button_1.clicked.connect(
            lambda: self.del_item_from_list(self.ui.add_DFT_list_1, "additional keys")
        )
        self.ui.add_DFT_button_2.clicked.connect(
            lambda: self.add_item_to_list(
                self.ui.additionalKeys_2, self.ui.add_DFT_list_2, "link 0"
            )
        )
        self.ui.del_DFT_button_2.clicked.connect(
            lambda: self.del_item_from_list(self.ui.add_DFT_list_2, "link 0")
        )
        self.ui.add_DFT_button_4.clicked.connect(
            lambda: self.add_item_to_list(
                self.ui.additionalKeys_3, self.ui.add_DFT_list_3, "job keys"
            )
        )
        self.ui.del_DFT_button_4.clicked.connect(
            lambda: self.del_item_from_list(self.ui.add_DFT_list_3, "job keys")
        )
        self.ui.save_button.clicked.connect(self.save_settings)
        self.ui.cancel_button.clicked.connect(self.close)
        self.ui.comboBox_funct.textActivated.connect(
            lambda: self.combobox_update(self.ui.comboBox_funct, "functional")
        )
        self.ui.basis1_comboBox_3.textActivated.connect(
            lambda: self.combobox_update(self.ui.basis1_comboBox_3, "basis")
        )
        self.ui.basis2_comboBox_4.textActivated.connect(
            lambda: self.combobox_update(self.ui.basis2_comboBox_4, "diff")
        )
        self.ui.basis3_comboBox_6.textActivated.connect(
            lambda: self.combobox_update(self.ui.basis3_comboBox_6, "pol1")
        )
        self.ui.basis4_comboBox_5.textActivated.connect(
            lambda: self.combobox_update(self.ui.basis4_comboBox_5, "pol2")
        )
        self.ui.job_type_comboBox.textActivated.connect(
            lambda: self.combobox_update(self.ui.job_type_comboBox, "job type")
        )
        self.ui.change_cwd_button.clicked.connect(
            lambda: self.new_path_from_dialog(
                self.ui.cwd_lineEdit, "Select working directory"
            )
        )
        self.ui.change_pymol_button.clicked.connect(
            lambda: self.new_path_from_dialog(
                self.ui.pymol_lineEdit_2, "select PyMOL path"
            )
        )
        self.ui.reset_button.clicked.connect(self.reset_settings)

    def reset_settings(self):
        for DFT_list in [
            self.ui.add_DFT_list_1,
            self.ui.add_DFT_list_2,
            self.ui.add_DFT_list_3,
        ]:
            DFT_list.clear()

        self.job_options = copy.deepcopy(self.settings.default_settings["job_options"])
        self.basis_options = copy.deepcopy(
            self.settings.default_settings["basis_options"]
        )
        self.functional_options = copy.deepcopy(
            self.settings.default_settings["functional_options"]
        )

        self.ui.comboBox_funct.addItems(
            self.settings.default_settings["functional_options"]
        )
        self.ui.basis1_comboBox_3.addItems(
            [x for x in self.settings.default_settings["basis_options"]]
        )
        self.ui.job_type_comboBox.addItems(
            ["Opt", "Opt (TS)", "Freq", "IRC", "IRCMax", "Single point"]
        )
        self.ui.job_type_comboBox.setCurrentText(
            self.settings.default_settings["job_type"]
        )

        self.ui.comboBox_funct.setCurrentText(
            self.settings.default_settings["functional"]
        )
        self.ui.basis1_comboBox_3.setCurrentText(
            self.settings.default_settings["basis"]
        )
        self.update_basis_options(self.settings.default_settings["basis"])

        self.ui.basis2_comboBox_4.setCurrentText(
            self.settings.default_settings["basis_diff"]
        )
        self.ui.basis3_comboBox_6.setCurrentText(
            self.settings.default_settings["basis_pol1"]
        )
        self.ui.basis4_comboBox_5.setCurrentText(
            self.settings.default_settings["basis_pol2"]
        )

        self.ui.add_DFT_list_1.addItems(
            self.settings.default_settings["additional_keys"]
        )
        self.ui.add_DFT_list_2.addItems(self.settings.default_settings["link0_options"])
        self.ui.add_DFT_list_3.addItems(
            self.settings.default_settings["job_options"][
                self.ui.job_type_comboBox.currentText()
            ]
        )

    def add_items_to_window(self):
        self.ui.comboBox_funct.addItems(self.settings.functional_options)
        self.ui.basis1_comboBox_3.addItems([x for x in self.settings.basis_options])
        self.ui.job_type_comboBox.addItems(
            ["Opt", "Opt (TS)", "Freq", "IRC", "IRCMax", "Single point"]
        )
        self.ui.job_type_comboBox.setCurrentText(self.settings.job_type)

        self.ui.comboBox_funct.setCurrentText(self.settings.functional)
        self.ui.basis1_comboBox_3.setCurrentText(self.settings.basis)

        self.update_basis_options(self.settings.basis)

        self.ui.basis2_comboBox_4.setCurrentText(self.settings.basis_diff)
        self.ui.basis3_comboBox_6.setCurrentText(self.settings.basis_pol1)
        self.ui.basis4_comboBox_5.setCurrentText(self.settings.basis_pol2)

        self.ui.add_DFT_list_1.addItems(self.settings.additional_keys)
        self.ui.add_DFT_list_2.addItems(self.settings.link0_options)
        self.ui.add_DFT_list_3.addItems(
            self.settings.job_options[self.ui.job_type_comboBox.currentText()]
        )

    def new_path_from_dialog(self, textwidget, title_):
        """
        Changes text in work directory field using file dialog.
        No change saved in self.settings, this is handeled in save_settings.
        """
        if textwidget == self.ui.pymol_lineEdit_2:
            new_dir = QtWidgets.QFileDialog.getOpenFileName(
                parent=self,
                caption=title_,
                directory=self.settings.workdir,
                filter="Any (*)",
            )[0]
        else:
            new_dir = QtWidgets.QFileDialog.getExistingDirectory(
                self, title_, self.settings.workdir
            )

        if new_dir:
            textwidget.setText(new_dir)

    #    def check_box_update(self, checkbox, key):
    #
    #        if checkbox.isChecked():
    #            self.settings[key] = True
    #        else:
    #            self.settings[key] = False

    def combobox_update(self, widget, key):
        """
        :param combobox: QComboBox
        :param key: str: key to identifu what combobox is changed

        Update window after a combobox is changed.
        """
        text = widget.currentText()

        if key == "job type":
            self.settings.job_type = text
            self.ui.add_DFT_list_3.clear()
            self.ui.add_DFT_list_3.addItems(self.job_options[text])

        if key == "functional":
            if text not in self.functional_options:
                # new functional not listed in settings from before
                self.functional_options.append(text)

        if key == "basis":
            if text not in self.basis_options:
                # new basis not listed in settings from before

                self.basis_options[text] = {"pol1": [], "pol2": [], "diff": []}
            self.update_basis_options(text)

        elif key in ["diff", "pol1", "pol2"]:
            basis = self.ui.basis1_comboBox_3.currentText()

            try:
                if text not in self.basis_options[basis][key]:
                    # diff, pol1 or pol2 not listed for current basis
                    self.basis_options[basis][key].append(text)
            except KeyError:
                self.react.append_text(
                    f"ERROR: cannot add custom options before basis {basis} has been properly added to REACT. Select {basis}, then click on the add button."
                )

    def add_item_to_list(self, Qtextinput, Qlist, DFT_key):
        """
        :param Qtextinput: QLineEdit
        :param Qlist: QListWidget
        :param DFT_key: str: key to access correct variable in self.settings
        Adds the text input from user (past to Qtextinput) to correct
        QlistWidget and updates self.settings accordingly.
        """

        user_input = Qtextinput.text()

        all_values_in_list = []

        for i in range(Qlist.count()):
            item = Qlist.item(i).text()
            all_values_in_list.append(item)

        if user_input not in all_values_in_list:
            Qlist.addItem(user_input)

        if DFT_key == "job keys":
            job_type = self.ui.job_type_comboBox.currentText()
            self.job_options[job_type].append(user_input)

    def del_item_from_list(self, Qlist, DFT_key):
        """
        :param Qlist: QListWidget
        :param DFT_key: str: key to access correct variable in self.settings
        Removes item in QlistWdiget and updates self.settings accordingly.
        """

        try:
            item = Qlist.currentItem().text()
            Qlist.takeItem(Qlist.currentRow())
        except:
            # User tried to delete item from list before selecting
            # an item in the list, or some other stupid thing
            return

        if DFT_key == "job keys":
            job_type = self.ui.job_type_comboBox.currentText()
            try:
                self.job_options[job_type].remove(item)
            except ValueError:
                pass

    def update_basis_options(self, basis):
        """
        :param basis: str: name current basis
        Updates polarization and diffuse functions avail for basis set
        """

        self.block_all_combo_signals(True)

        self.ui.basis2_comboBox_4.clear()
        self.ui.basis3_comboBox_6.clear()
        self.ui.basis4_comboBox_5.clear()

        try:
            self.ui.basis2_comboBox_4.addItems(self.basis_options[basis]["diff"])
            self.ui.basis3_comboBox_6.addItems(self.basis_options[basis]["pol1"])
            self.ui.basis4_comboBox_5.addItems(self.basis_options[basis]["pol2"])
        except KeyError:
            # exception: when the basis set has been removed by user.
            # nothing to do when there is no basis!
            pass

        self.block_all_combo_signals(False)

    def block_all_combo_signals(self, bool_):
        self.ui.comboBox_funct.blockSignals(bool_)
        self.ui.basis1_comboBox_3.blockSignals(bool_)
        self.ui.job_type_comboBox.blockSignals(bool_)
        self.ui.basis2_comboBox_4.blockSignals(bool_)
        self.ui.basis3_comboBox_6.blockSignals(bool_)
        self.ui.basis4_comboBox_5.blockSignals(bool_)

    def save_settings(self):
        # Get current values from UI
        functional_name = self.ui.comboBox_funct.currentText()
        basis_name = self.ui.basis1_comboBox_3.currentText()
        basis_diff = self.ui.basis2_comboBox_4.currentText()
        basis_pol1 = self.ui.basis3_comboBox_6.currentText()
        basis_pol2 = self.ui.basis4_comboBox_5.currentText()

        # Add functional to list if it's new
        if functional_name and functional_name not in self.functional_options:
            self.functional_options.append(functional_name)

        # Ensure basis exists in basis_options with proper structure
        if basis_name and basis_name not in self.basis_options:
            # Create default structure for new basis set
            self.basis_options[basis_name] = {
                "pol1": ["", "d", "2d", "3d"],
                "pol2": ["", "p", "2p", "3p"],
                "diff": ["", "+", "++"],
            }

        # Add custom polarization/diffuse functions if they're new
        if basis_name and basis_name in self.basis_options:
            if basis_diff and basis_diff not in self.basis_options[basis_name]["diff"]:
                self.basis_options[basis_name]["diff"].append(basis_diff)
            if basis_pol1 and basis_pol1 not in self.basis_options[basis_name]["pol1"]:
                self.basis_options[basis_name]["pol1"].append(basis_pol1)
            if basis_pol2 and basis_pol2 not in self.basis_options[basis_name]["pol2"]:
                self.basis_options[basis_name]["pol2"].append(basis_pol2)

        # Save to settings
        self.settings.functional = functional_name
        self.settings.basis = basis_name
        self.settings.basis_diff = basis_diff
        self.settings.basis_pol1 = basis_pol1
        self.settings.basis_pol2 = basis_pol2
        self.settings.job_type = self.ui.job_type_comboBox.currentText()
        self.settings.additional_keys = [
            self.ui.add_DFT_list_1.item(x).text()
            for x in range(self.ui.add_DFT_list_1.count())
        ]
        self.settings.job_options = copy.deepcopy(self.job_options)
        self.settings.link0_options = [
            self.ui.add_DFT_list_2.item(x).text()
            for x in range(self.ui.add_DFT_list_2.count())
        ]
        self.settings.functional_options = copy.deepcopy(self.functional_options)
        self.settings.basis_options = copy.deepcopy(self.basis_options)

        if os.path.exists(self.ui.cwd_lineEdit.text()):
            self.settings.workdir = self.ui.cwd_lineEdit.text()
        else:
            # TODO promt errormessage on screen
            pass

        if os.path.exists(self.ui.pymol_lineEdit_2.text()):
            self.settings.pymolpath = self.ui.pymol_lineEdit_2.text()
        else:
            print("pymol path not found. Please add a path in Settings!")

        if self.ui.open_pymol_checkBox.isChecked():
            self.settings.pymol_at_launch = True
        else:
            self.settings.pymol_at_launch = False

        self.settings.save_custom_settings()

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
