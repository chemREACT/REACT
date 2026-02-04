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
    def functional_options(self):
        if self.software == "ORCA":
            return self._orca_settings.get("functional_options", [])
        return self._gaussian_settings.get("functional_options", [])

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
                    "Opt": [],
                    "OptTS": [],
                    "NEB-TS": [],
                    "Freq": [],
                    "NumFreq": [],
                    "IRC": [],
                    "Single point": [],
                },
                "blocks": {},
                "blocks_available": {
                    "autoci": None,
                    "basis": None,
                    "casresp": None,
                    "casscf": None,
                    "cipsi": None,
                    "cim": None,
                    "cis": None,
                    "coords": None,
                    "compound": None,
                    "cosmors": None,
                    "cpcm": None,
                    "elprop": None,
                    "eprnmr": None,
                    "esd": None,
                    "freq": None,
                    "geom": None,
                    "irc": None,
                    "loc": None,
                    "mcrpa": None,
                    "md": None,
                    "mdci": None,
                    "method": None,
                    "mp2": None,
                    "mrcc": None,
                    "mrci": None,
                    "neb": None,
                    "numgrad": None,
                    "nbo": None,
                    "output": None,
                    "pal": None,
                    "paras": None,
                    "plots": None,
                    "rel": None,
                    "rocis": None,
                    "rr": None,
                    "scf": None,
                    "symmetry": None,
                },
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
                    # Pople basis sets (each combination as separate basis set)
                    "STO-3G": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "3-21G": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "3-21+G": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-31G": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-31G(d)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-31G(d,p)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-31+G": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-31+G(d)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-31+G(d,p)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-31++G": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-31++G(d)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-31++G(d,p)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-311G": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-311G(d)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-311G(d,p)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-311+G": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-311+G(d)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-311+G(d,p)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-311++G": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-311++G(d)": {"pol1": [""], "pol2": [""], "diff": [""]},
                    "6-311++G(d,p)": {"pol1": [""], "pol2": [""], "diff": [""]},
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
    User window to interact with instance of Settings with separate ORCA and Gaussian tabs
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.react = parent
        self.settings = parent.settings
        self.ui = Ui_SettingsWindow()
        self.ui.setupUi(self)

        # Separate settings for Gaussian and ORCA
        self.gaussian_job_options = copy.deepcopy(
            self.settings._gaussian_settings["job_options"]
        )
        self.gaussian_basis_options = copy.deepcopy(
            self.settings._gaussian_settings["basis_options"]
        )
        self.gaussian_functional_options = copy.deepcopy(
            self.settings._gaussian_settings["functional_options"]
        )

        self.orca_job_options = copy.deepcopy(
            self.settings._orca_settings["job_options"]
        )
        self.orca_basis_options = copy.deepcopy(
            self.settings._orca_settings["basis_options"]
        )
        self.orca_functional_options = copy.deepcopy(
            self.settings._orca_settings["functional_options"]
        )

        # Fill comboboxes
        try:
            self.add_items_to_window()
        except Exception as e:
            print(f"Error adding items to window: {e}")
            self.settings.set_default_settings()
            self.add_items_to_window()

        # General tab
        self.ui.cwd_lineEdit.setText(self.settings.workdir)

        if self.settings.pymolpath and self.settings.pymolpath != bool:
            self.ui.pymol_lineEdit.setText(self.settings.pymolpath)

        if self.settings.pymol_at_launch:
            self.ui.open_pymol_checkBox.setChecked(True)

        # Set software radio buttons
        if self.settings.software == "ORCA":
            self.ui.radioButton_ORCA.setChecked(True)
        else:
            self.ui.radioButton_Gaussian.setChecked(True)

        # Connect signals - General tab
        self.ui.save_button_0.clicked.connect(self.save_settings)
        self.ui.cancel_button_0.clicked.connect(self.close)
        self.ui.change_cwd_button.clicked.connect(
            lambda: self.new_path_from_dialog(
                self.ui.cwd_lineEdit, "Select working directory"
            )
        )
        self.ui.change_pymol_button.clicked.connect(
            lambda: self.new_path_from_dialog(
                self.ui.pymol_lineEdit, "select PyMOL path"
            )
        )
        self.ui.radioButton_ORCA.toggled.connect(self.on_software_changed)
        self.ui.radioButton_Gaussian.toggled.connect(self.on_software_changed)

        # Connect signals - ORCA tab
        self.ui.save_button_1.clicked.connect(self.save_settings)
        self.ui.cancel_button_1.clicked.connect(self.close)
        self.ui.pushButton.clicked.connect(
            lambda: self.add_item_to_list(
                self.ui.jobspec_keywords_orca,
                self.ui.add_jobspec_orca_list,
                "job keys",
                "orca",
            )
        )
        self.ui.pushButton_2.clicked.connect(
            lambda: self.del_item_from_list(
                self.ui.add_jobspec_orca_list, "job keys", "orca"
            )
        )

        self.ui.pushButton_3.clicked.connect(
            lambda: self.add_item_to_list(
                self.ui.additionalblock_orca,
                self.ui.add_list2_orca,
                "input blocks",
                "orca",
            )
        )

        self.ui.pushButton_4.clicked.connect(
            lambda: self.del_item_from_list(
                self.ui.add_list2_orca, "input blocks", "orca"
            )
        )

        self.ui.comboBox_funct_orca.textActivated.connect(
            lambda: self.combobox_update(
                self.ui.comboBox_funct_orca, "functional", "orca"
            )
        )
        self.ui.basis1_comboBox_orca.textActivated.connect(
            lambda: self.combobox_update(self.ui.basis1_comboBox_orca, "basis", "orca")
        )
        self.ui.job_type_comboBox_orca.textActivated.connect(
            lambda: self.combobox_update(
                self.ui.job_type_comboBox_orca, "job type", "orca"
            )
        )

        # Connect signals - Gaussian tab
        self.ui.save_button_2.clicked.connect(self.save_settings)
        self.ui.cancel_button_3.clicked.connect(self.close)
        self.ui.add_1_gauss.clicked.connect(
            lambda: self.add_item_to_list(
                self.ui.additionalKeys1_gauss,
                self.ui.add_DFT_list1_gauss,
                "additional keys",
                "gaussian",
            )
        )
        self.ui.del_1_gauss.clicked.connect(
            lambda: self.del_item_from_list(
                self.ui.add_DFT_list1_gauss, "additional keys", "gaussian"
            )
        )
        self.ui.add_2_gauss.clicked.connect(
            lambda: self.add_item_to_list(
                self.ui.additionalKeys2_gauss,
                self.ui.add_DFT_list2_gauss,
                "link 0",
                "gaussian",
            )
        )
        self.ui.del_2_gauss.clicked.connect(
            lambda: self.del_item_from_list(
                self.ui.add_DFT_list2_gauss, "link 0", "gaussian"
            )
        )
        self.ui.add_3_gauss.clicked.connect(
            lambda: self.add_item_to_list(
                self.ui.additionalKeys3_gauss,
                self.ui.add_DFT_list3_gauss,
                "job keys",
                "gaussian",
            )
        )
        self.ui.del_3_gauss.clicked.connect(
            lambda: self.del_item_from_list(
                self.ui.add_DFT_list3_gauss, "job keys", "gaussian"
            )
        )
        self.ui.comboBox_funct_gauss.textActivated.connect(
            lambda: self.combobox_update(
                self.ui.comboBox_funct_gauss, "functional", "gaussian"
            )
        )
        self.ui.basis1_comboBox_gauss.textActivated.connect(
            lambda: self.combobox_update(
                self.ui.basis1_comboBox_gauss, "basis", "gaussian"
            )
        )
        self.ui.basis2_comboBox_gauss.textActivated.connect(
            lambda: self.combobox_update(
                self.ui.basis2_comboBox_gauss, "diff", "gaussian"
            )
        )
        self.ui.basis3_comboBox_gauss.textActivated.connect(
            lambda: self.combobox_update(
                self.ui.basis3_comboBox_gauss, "pol1", "gaussian"
            )
        )
        self.ui.basis4_comboBox_gauss.textActivated.connect(
            lambda: self.combobox_update(
                self.ui.basis4_comboBox_gauss, "pol2", "gaussian"
            )
        )
        self.ui.job_type_comboBox_gauss.textActivated.connect(
            lambda: self.combobox_update(
                self.ui.job_type_comboBox_gauss, "job type", "gaussian"
            )
        )

    def on_software_changed(self):
        """Update software setting when radio button changes"""
        if self.ui.radioButton_ORCA.isChecked():
            self.settings.software = "ORCA"
        else:
            self.settings.software = "Gaussian"

    def add_items_to_window(self):
        """Fill all comboboxes and lists with current settings"""
        # ORCA tab
        self.ui.comboBox_funct_orca.addItems(self.orca_functional_options)
        self.ui.basis1_comboBox_orca.addItems([x for x in self.orca_basis_options])
        self.ui.job_type_comboBox_orca.addItems(
            ["Opt", "OptTS", "NEB-TS", "Freq", "NumFreq", "IRC", "Single point"]
        )
        self.ui.job_type_comboBox_orca.setCurrentText(
            self.settings._orca_settings["job_type"]
        )
        self.ui.comboBox_funct_orca.setCurrentText(
            self.settings._orca_settings["functional"]
        )
        self.ui.basis1_comboBox_orca.setCurrentText(
            self.settings._orca_settings["basis"]
        )
        self.ui.add_jobspec_orca_list.addItems(
            self.orca_job_options[self.ui.job_type_comboBox_orca.currentText()]
        )

        self.ui.inputblock_orca.addItems(
            self.settings._orca_settings["blocks_available"].keys()
        )
        self.ui.add_list2_orca.addItems(
            [
                f"%{k}\n   {v}\nEND\n"
                for k, v in self.settings._orca_settings["blocks"].items()
            ]
        )

        # Gaussian tab
        self.ui.comboBox_funct_gauss.addItems(self.gaussian_functional_options)
        self.ui.basis1_comboBox_gauss.addItems([x for x in self.gaussian_basis_options])
        self.ui.job_type_comboBox_gauss.addItems(
            ["Opt", "Opt (TS)", "Freq", "IRC", "IRCMax", "Single point"]
        )
        self.ui.job_type_comboBox_gauss.setCurrentText(
            self.settings._gaussian_settings["job_type"]
        )
        self.ui.comboBox_funct_gauss.setCurrentText(
            self.settings._gaussian_settings["functional"]
        )
        self.ui.basis1_comboBox_gauss.setCurrentText(
            self.settings._gaussian_settings["basis"]
        )

        # Update basis options for Gaussian
        self.update_basis_options(self.settings._gaussian_settings["basis"], "gaussian")

        self.ui.basis2_comboBox_gauss.setCurrentText(
            self.settings._gaussian_settings["basis_diff"]
        )
        self.ui.basis3_comboBox_gauss.setCurrentText(
            self.settings._gaussian_settings["basis_pol1"]
        )
        self.ui.basis4_comboBox_gauss.setCurrentText(
            self.settings._gaussian_settings["basis_pol2"]
        )

        self.ui.add_DFT_list1_gauss.addItems(
            self.settings._gaussian_settings["additional_keys"]
        )
        self.ui.add_DFT_list2_gauss.addItems(
            self.settings._gaussian_settings["link0_options"]
        )
        self.ui.add_DFT_list3_gauss.addItems(
            self.gaussian_job_options[self.ui.job_type_comboBox_gauss.currentText()]
        )

    def new_path_from_dialog(self, textwidget, title_):
        """Changes text in work directory field using file dialog"""
        if textwidget == self.ui.pymol_lineEdit:
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

    def combobox_update(self, widget, key, software):
        """Update window after a combobox is changed"""
        text = widget.currentText()

        # Select the right dictionaries based on software
        if software == "orca":
            job_options = self.orca_job_options
            basis_options = self.orca_basis_options
            functional_options = self.orca_functional_options
            job_list = self.ui.add_jobspec_orca_list
            job_type_combo = self.ui.job_type_comboBox_orca
        else:
            job_options = self.gaussian_job_options
            basis_options = self.gaussian_basis_options
            functional_options = self.gaussian_functional_options
            job_list = self.ui.add_DFT_list3_gauss
            job_type_combo = self.ui.job_type_comboBox_gauss

        if key == "job type":
            job_list.clear()
            job_list.addItems(job_options[text])

        elif key == "functional":
            if text not in functional_options:
                functional_options.append(text)

        elif key == "basis":
            if text not in basis_options:
                basis_options[text] = {"pol1": [""], "pol2": [""], "diff": [""]}
            if software == "gaussian":
                self.update_basis_options(text, software)

        elif key in ["diff", "pol1", "pol2"] and software == "gaussian":
            basis = self.ui.basis1_comboBox_gauss.currentText()
            try:
                if text and text not in basis_options[basis][key]:
                    basis_options[basis][key].append(text)
            except KeyError:
                self.react.append_text(
                    f"ERROR: cannot add custom options before basis {basis} has been properly added to REACT"
                )

    def add_item_to_list(self, Qtextinput, Qlist, DFT_key, software):
        """Adds text input to list widget"""
        user_input = Qtextinput.text()
        if not user_input:
            return

        if DFT_key == "input blocks" and software == "orca":
            block_type = self.ui.inputblock_orca.currentText()

            self.settings._orca_settings["blocks"][block_type] = user_input

            user_input = f"%{block_type}\n    {user_input}\nEND\n"

        all_values_in_list = [Qlist.item(i).text() for i in range(Qlist.count())]

        if user_input not in all_values_in_list:
            Qlist.addItem(user_input)

        if DFT_key == "job keys":
            if software == "orca":
                job_type = self.ui.job_type_comboBox_orca.currentText()
                self.orca_job_options[job_type].append(user_input)
            else:
                job_type = self.ui.job_type_comboBox_gauss.currentText()
                self.gaussian_job_options[job_type].append(user_input)

    def del_item_from_list(self, Qlist, DFT_key, software):
        """Removes item from list widget"""
        try:
            item = Qlist.currentItem().text()
            Qlist.takeItem(Qlist.currentRow())
        except:
            return

        if DFT_key == "job keys":
            if software == "orca":
                job_type = self.ui.job_type_comboBox_orca.currentText()
                try:
                    self.orca_job_options[job_type].remove(item)
                except ValueError:
                    pass
            else:
                job_type = self.ui.job_type_comboBox_gauss.currentText()
                try:
                    self.gaussian_job_options[job_type].remove(item)
                except ValueError:
                    pass

    def update_basis_options(self, basis, software):
        """Updates polarization and diffuse functions available for basis set"""
        if software != "gaussian":
            return

        self.block_gaussian_combo_signals(True)

        self.ui.basis2_comboBox_gauss.clear()
        self.ui.basis3_comboBox_gauss.clear()
        self.ui.basis4_comboBox_gauss.clear()

        try:
            self.ui.basis2_comboBox_gauss.addItems(
                self.gaussian_basis_options[basis]["diff"]
            )
            self.ui.basis3_comboBox_gauss.addItems(
                self.gaussian_basis_options[basis]["pol1"]
            )
            self.ui.basis4_comboBox_gauss.addItems(
                self.gaussian_basis_options[basis]["pol2"]
            )
        except KeyError:
            pass

        self.block_gaussian_combo_signals(False)

    def block_gaussian_combo_signals(self, bool_):
        """Block/unblock signals for Gaussian comboboxes"""
        self.ui.comboBox_funct_gauss.blockSignals(bool_)
        self.ui.basis1_comboBox_gauss.blockSignals(bool_)
        self.ui.job_type_comboBox_gauss.blockSignals(bool_)
        self.ui.basis2_comboBox_gauss.blockSignals(bool_)
        self.ui.basis3_comboBox_gauss.blockSignals(bool_)
        self.ui.basis4_comboBox_gauss.blockSignals(bool_)

    def save_settings(self):
        """Save all settings to custom_settings.json"""
        # Save software selection
        if self.ui.radioButton_ORCA.isChecked():
            self.settings.software = "ORCA"
        else:
            self.settings.software = "Gaussian"

        # Save general settings
        if os.path.exists(self.ui.cwd_lineEdit.text()):
            self.settings.workdir = self.ui.cwd_lineEdit.text()

        pymol_path = self.ui.pymol_lineEdit.text()
        if pymol_path and os.path.exists(pymol_path):
            self.settings.pymolpath = pymol_path

        self.settings.pymol_at_launch = self.ui.open_pymol_checkBox.isChecked()

        # Save Gaussian settings
        gaussian_functional = self.ui.comboBox_funct_gauss.currentText()
        gaussian_basis = self.ui.basis1_comboBox_gauss.currentText()

        if (
            gaussian_functional
            and gaussian_functional not in self.gaussian_functional_options
        ):
            self.gaussian_functional_options.append(gaussian_functional)

        if gaussian_basis and gaussian_basis not in self.gaussian_basis_options:
            self.gaussian_basis_options[gaussian_basis] = {
                "pol1": ["", "d", "2d", "3d"],
                "pol2": ["", "p", "2p", "3p"],
                "diff": ["", "+", "++"],
            }

        # Update Gaussian basis polarization/diffuse if custom values
        gaussian_diff = self.ui.basis2_comboBox_gauss.currentText()
        gaussian_pol1 = self.ui.basis3_comboBox_gauss.currentText()
        gaussian_pol2 = self.ui.basis4_comboBox_gauss.currentText()

        if gaussian_basis in self.gaussian_basis_options:
            if (
                gaussian_diff
                and gaussian_diff
                not in self.gaussian_basis_options[gaussian_basis]["diff"]
            ):
                self.gaussian_basis_options[gaussian_basis]["diff"].append(
                    gaussian_diff
                )
            if (
                gaussian_pol1
                and gaussian_pol1
                not in self.gaussian_basis_options[gaussian_basis]["pol1"]
            ):
                self.gaussian_basis_options[gaussian_basis]["pol1"].append(
                    gaussian_pol1
                )
            if (
                gaussian_pol2
                and gaussian_pol2
                not in self.gaussian_basis_options[gaussian_basis]["pol2"]
            ):
                self.gaussian_basis_options[gaussian_basis]["pol2"].append(
                    gaussian_pol2
                )

        self.settings._gaussian_settings["functional"] = gaussian_functional
        self.settings._gaussian_settings["basis"] = gaussian_basis
        self.settings._gaussian_settings["basis_diff"] = gaussian_diff
        self.settings._gaussian_settings["basis_pol1"] = gaussian_pol1
        self.settings._gaussian_settings["basis_pol2"] = gaussian_pol2
        self.settings._gaussian_settings["job_type"] = (
            self.ui.job_type_comboBox_gauss.currentText()
        )
        self.settings._gaussian_settings["additional_keys"] = [
            self.ui.add_DFT_list1_gauss.item(x).text()
            for x in range(self.ui.add_DFT_list1_gauss.count())
        ]
        self.settings._gaussian_settings["link0_options"] = [
            self.ui.add_DFT_list2_gauss.item(x).text()
            for x in range(self.ui.add_DFT_list2_gauss.count())
        ]
        self.settings._gaussian_settings["job_options"] = copy.deepcopy(
            self.gaussian_job_options
        )
        self.settings._gaussian_settings["basis_options"] = copy.deepcopy(
            self.gaussian_basis_options
        )
        self.settings._gaussian_settings["functional_options"] = copy.deepcopy(
            self.gaussian_functional_options
        )

        # Save ORCA settings
        orca_functional = self.ui.comboBox_funct_orca.currentText()
        orca_basis = self.ui.basis1_comboBox_orca.currentText()

        if orca_functional and orca_functional not in self.orca_functional_options:
            self.orca_functional_options.append(orca_functional)

        if orca_basis and orca_basis not in self.orca_basis_options:
            self.orca_basis_options[orca_basis] = {
                "pol1": [""],
                "pol2": [""],
                "diff": [""],
            }

        self.settings._orca_settings["functional"] = orca_functional
        self.settings._orca_settings["basis"] = orca_basis
        self.settings._orca_settings["job_type"] = (
            self.ui.job_type_comboBox_orca.currentText()
        )
        self.settings._orca_settings["job_options"] = copy.deepcopy(
            self.orca_job_options
        )
        self.settings._orca_settings["basis_options"] = copy.deepcopy(
            self.orca_basis_options
        )
        self.settings._orca_settings["functional_options"] = copy.deepcopy(
            self.orca_functional_options
        )
        self.settings._orca_settings["blocks"] = self.settings._orca_settings.get(
            "blocks", {}
        )

        # Save to file
        self.settings.save_custom_settings()
        self.close()

    def closeEvent(self, event):
        """When closing window, set to settings_window to None"""
        self.react.settings_window = None
