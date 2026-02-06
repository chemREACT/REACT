#
# Copyright (C) 2022 Geir Villy Isaksen and Bente Sirin Barge
#
# This file is part of chemREACT.
#
# chemREACT is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
# chemREACT is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with chemREACT. If not, see <https://www.gnu.org/licenses/>.
#

import os
from os import path, mkdir, remove
import glob
import shutil
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QTimer
from UIs.SetupWindowOrca import Ui_SetupWindow
from mods.ScanBond import AtomBond
from mods.common_functions import atom_distance, random_color, write_file
import copy


class CalcSetupWindowORCA(QtWidgets.QMainWindow, Ui_SetupWindow):
    def __init__(self, parent, filepath):
        super(CalcSetupWindowORCA, self).__init__(parent)
        self.react = parent
        self.filepath = filepath
        self.settings = self.react.settings

        # Ensure we're using ORCA settings
        if self.settings.software != "ORCA":
            self.settings.software = "ORCA"

        # TODO this is temporary solution -> self.mol_obj should have a property state?
        self.state = self.react.get_current_state

        self.pymol = False
        self.pymol_animation = False
        if self.react.pymol:
            self.pymol = self.react.pymol
            self.pymol.pymol_cmd("set mouse_selection_mode, 0")
            self.pymol.pymol_cmd("hide cartoon")

            # Monitor clicks in pymol stdout_handler
            self.pymol.monitor_clicks()
            # Connect signals from pymol:
            self.pymol.atomsSelectedSignal.connect(self.pymol_atom_clicked)

            # Connect signal, update charge variable with the signal emitted
            self.pymol_charge = None
            self.pymol.overallChargeSignal.connect(self.handle_overall_charge)
            self.pymol.set_overall_charge()

        self.ui = Ui_SetupWindow()
        self.ui.setupUi(self)
        # TODO auto freeze function not working, hiding button for now
        self.ui.button_auto_freeze.hide()

        # TODO optimize this?:
        screen_size = self.screen().availableGeometry()
        window_size = self.geometry()
        self.move(int(((screen_size.width() - window_size.width()) / 2)) - 250, 100)

        self.setWindowTitle("REACT - Calculation setup")

        self.mol_obj = self.react.states[self.react.state_index].get_molecule_object(
            self.filepath
        )

        if self.mol_obj.charge:
            self.charge = self.mol_obj.charge
        else:
            self.charge = None

        if self.mol_obj.multiplicity:
            self.multiplicity = self.mol_obj.multiplicity
        else:
            self.multiplicity = "1"
        self.filename = self.mol_obj.filename.split(".")[0]

        # we need to make a local copy of all info job-related stuff,
        # So that we dont change the attributes in Settings object
        self.functional = copy.deepcopy(self.settings.functional)
        self.basis = copy.deepcopy(self.settings.basis)
        self.job_type = self.settings.job_type
        self.opt_freq_combi = False
        self.job_options = copy.deepcopy(self.settings.job_options)
        self.blocks = copy.deepcopy(self.settings._orca_settings.get("blocks", {}))
        self.blocks_available = copy.deepcopy(
            self.settings._orca_settings.get("blocks_available", {})
        )
        self.solvents = ["CPM", "SMD"]

        self.opt_freq_details = {"checked": False, "keywords": []}
        self.num_files = 1
        self.scan_bond_files = {}
        self.IRC_files = {}
        self.atom_bonds = {}
        self.Qbutton_scan_group = QtWidgets.QButtonGroup(self)
        self.Qbutton_scan_group.addButton(self.ui.radioButton_plus)
        self.Qbutton_scan_group.addButton(self.ui.radioButton_minus)
        self.Qbutton_scan_group.addButton(self.ui.radioButton_both)

        self.insert_model_atoms()
        self.fill_main_tab()

        self.ui.Button_add_job.clicked.connect(
            lambda: self.add_item_to_list(
                self.ui.LineEdit_add_job,
                self.ui.List_add_job,
                self.blocks,
                self.ui.comboBox.currentText(),
            )
        )
        self.ui.Button_del_job.clicked.connect(
            lambda: self.del_item_from_list(
                self.ui.List_add_job, self.job_options[self.job_type]
            )
        )

        self.ui.Button_add_job_2.clicked.connect(
            lambda: self.add_item_to_list(
                self.ui.LineEdit_add_job_2,
                self.ui.List_add_job_2,
                self.job_options[self.job_type],
            )
        )
        self.ui.Button_del_job_2.clicked.connect(
            lambda: self.del_item_from_list(self.ui.List_add_job_2, self.job_options)
        )
        self.ui.comboBox_basis1.currentIndexChanged.connect(self.update_basis1)
        self.ui.comboBox_funct.currentTextChanged.connect(self.update_functional)
        self.ui.comboBox_job_type.currentTextChanged.connect(self.update_job_details)
        self.ui.ComboBox_files.currentTextChanged.connect(self.update_preview_combobox)
        self.ui.button_close.clicked.connect(self.on_close)
        self.ui.button_write.clicked.connect(self.on_write)
        self.ui.button_add_freeze.clicked.connect(self.add_freeze_atoms)
        self.ui.button_delete_freeze.clicked.connect(self.remove_freeze_atoms)
        self.ui.button_auto_freeze.clicked.connect(self.auto_freeze_atoms)
        self.ui.button_add_scan.clicked.connect(self.add_scan_atoms)
        self.ui.button_delete_scan.clicked.connect(self.remove_scan_atoms)
        self.ui.lineEdit_filename.textChanged.connect(self.filename_update)
        self.ui.lineEdit_charge.textChanged.connect(self.update_charge)
        self.ui.lineEdit_multiplicity.textChanged.connect(self.update_multiplicity)
        self.ui.tabWidget.currentChanged.connect(self.update_preview)
        self.Qbutton_scan_group.buttonClicked.connect(self.on_scan_mode_changed)
        self.ui.spinbox_scan_pm.valueChanged.connect(
            lambda: self.on_spinbox_changed(self.ui.spinbox_scan_pm)
        )
        self.ui.spinbox_scan_increment.valueChanged.connect(
            lambda: self.on_spinbox_changed(self.ui.spinbox_scan_increment)
        )
        self.ui.button_invert.clicked.connect(self.on_invert_atoms)
        self.ui.checkBox_moveboth.clicked.connect(self.on_move_both_changed)

        self.ui.pushButton_create_mv.clicked.connect(self.add_move_atoms)
        self.ui.checkBox_moveboth_mv.clicked.connect(self.on_move_both_changed_mv)
        self.ui.spinbox_mv_bonds.valueChanged.connect(
            lambda: self.on_spinbox_changed(self.ui.spinbox_mv_bonds)
        )
        self.move_bond = False
        self.atoms_mv = list()
        self.ui.Button_save_new_geometry.clicked.connect(self.save_geometry_to_file)

        self.ui.list_model.itemSelectionChanged.connect(
            lambda: self.model_atom_clicked(self.ui.list_model)
        )
        self.ui.list_model.setSelectionMode(1)

        self.ui.list_model_mv.itemSelectionChanged.connect(
            lambda: self.model_atom_clicked(self.ui.list_model_mv)
        )
        self.ui.list_model_mv.setSelectionMode(2)

        self.ui.list_freeze_atoms.itemSelectionChanged.connect(self.freeze_list_clicked)

        self.atoms_to_select = 2
        self.ui.comboBox_freezetype.currentTextChanged.connect(
            self.change_selection_mode
        )

        self.ui.checkbox_eps.stateChanged.connect(self.update_eps)

        # Keep track of atoms selected (for multiple selection options)
        self.selected_indexes = list()

        # Pymol returns ordered atom id list, so we need to keep track of click order
        self.selected_ids = list()

        # key to get scan bond from list of bonds
        self.scan_bond_key = False

    @property
    def scan_bond(self):
        """
        Return AtomBond obj representing the bond selected from the scan list
        """
        try:
            return self.atom_bonds[self.scan_bond_key]
        except KeyError:
            pass

    def on_invert_atoms(self):
        if self.ui.list_model.count() < 1:
            return

        self.scan_bond.invert_atoms()
        self.ui.lineEdit_freeze.setText(str(self.scan_bond.atom1_idx))
        self.ui.lineEdit_move.setText(str(self.scan_bond.atom2_idx))
        self.update_scan()

    def on_move_both_changed(self):
        if self.ui.list_model.count() < 1:
            return

        if self.ui.checkBox_moveboth.isChecked():
            self.scan_bond.move_both = True
            disable = True
        else:
            self.scan_bond.move_both = False
            disable = False

        self.ui.button_invert.setDisabled(disable)
        self.ui.lineEdit_freeze.setDisabled(disable)
        self.ui.lineEdit_move.setDisabled(disable)
        self.update_scan()

    def on_move_both_changed_mv(self):
        if self.move_bond == False:
            return

        if self.ui.checkBox_moveboth_mv.isChecked():
            self.move_bond.move_both = True
        else:
            self.move_bond.move_both = False

        self.add_move_atoms()

    def update_eps(self):
        if self.ui.checkbox_eps.isChecked():
            self.ui.lineEdit_eps.setEnabled(True)
        else:
            self.ui.lineEdit_eps.setEnabled(False)

    def change_selection_mode(self):
        if self.ui.comboBox_freezetype.currentText() == "Atoms":
            self.ui.list_model.setSelectionMode(1)
        else:
            self.ui.list_model.setSelectionMode(2)

        select = {"Atom": 1, "Bond": 2, "Angle": 3, "Dihedral": 4}
        self.atoms_to_select = select[self.ui.comboBox_freezetype.currentText()]

    def enable_scan(self, enable=True):
        self.ui.button_add_scan.setEnabled(enable)
        self.ui.button_delete_scan.setEnabled(enable)
        self.ui.spinbox_radius.setEnabled(enable)
        self.ui.spinbox_scan_pm.setEnabled(enable)
        self.ui.spinbox_scan_increment.setEnabled(enable)

    @pyqtSlot(list)
    def pymol_atom_clicked(self, ids):
        """
        Get atoms selected in pymol and select deselect in model atom listwidget
        """
        if not ids or None in ids:
            return

        if self.ui.tabWidget.currentIndex() == 1:
            atom_list = self.ui.list_model_mv
        if self.ui.tabWidget.currentIndex() == 2:
            atom_list = self.ui.list_model

        ids = [int(x) - 1 for x in ids]

        # Effective when len(ids) > len(self.selected_ids)
        unsele = list(set(self.selected_ids) - set(ids))
        try:
            for id in unsele:
                if atom_list is None:
                    continue
                atom_list.item(id).setSelected(False)
                self.selected_ids.pop(self.selected_ids.index(id))
        except UnboundLocalError:
            pass

        # Effective when len(ids) < len(self.selected_ids)
        new_select = list(set(ids) - set(self.selected_ids))
        for id in new_select:
            self.selected_ids.append(id)
            if len(self.selected_ids) > self.atoms_to_select:
                self.selected_ids.pop(0)
            try:
                atom_list.item(id).setSelected(True)
            except:
                pass

    def model_atom_clicked(self, atom_list):
        """
        When selection i atom list is changed, update, and communicate with pymol
        """
        if self.pymol_animation:
            self.stop_pymol_animation()

        sele = atom_list.selectedIndexes()
        while len(sele) > self.atoms_to_select:
            if len(self.selected_indexes) > 0:
                atom_list.item(self.selected_indexes.pop(0).row()).setSelected(False)
            else:
                atom_list.item(sele.pop(0).row()).setSelected(False)
            sele = atom_list.selectedIndexes()

        self.selected_indexes = sele

        atoms = list()
        coordinates = list()
        for i in self.selected_indexes:
            atoms.append(self.mol_obj.molecule[i.row() + 1].atom_index)
            coordinates.append(self.mol_obj.molecule[i.row() + 1].coordinate)

        if len(atoms) == 2:
            # self.enable_scan(enable=True)
            r = atom_distance(coordinates[0], coordinates[1])
            self.ui.spinbox_radius.setValue(r)
            self.ui.spinbox_curr_mv.setValue(r)
        # else:
        #    self.enable_scan(enable=False)

        if self.pymol:
            self.update_pymol_selection(atoms=atoms)

    def freeze_list_clicked(self):
        """
        When entry in "Atoms to freeze" is clicked, update to selected in "Atoms in model" list and pymol
        """
        if self.pymol_animation:
            self.stop_pymol_animation()

        try:
            indexes = [
                int(x) - 1
                for x in self.ui.list_freeze_atoms.currentItem().text().split()[1:-1]
            ]
        except AttributeError:
            return
        freeze_type = {1: "Atom", 2: "Bond", 3: "Angle", 4: "Dihedral"}
        self.ui.comboBox_freezetype.setCurrentText(freeze_type[len(indexes)])

        self.selected_indexes = indexes
        self.ui.list_model.clearSelection()

        for index in indexes:
            self.ui.list_model.item(index).setSelected(True)

    def update_pymol_selection(self, atoms):
        filetype = self.mol_obj.filepath.split(".")[-1]
        object_name = self.mol_obj.molecule_name + "_" + filetype
        group = "state_%d" % self.react.get_current_state
        self.pymol.set_selection(
            atoms=atoms, sele_name="sele", object_name=object_name, group=group
        )

    def add_freeze_atoms(self):
        """
        Adds selected atoms to freeze section - append F to end of str for freeze
        """
        if len(self.selected_indexes) < 1:
            return
        type = "C"
        g_cmd = {"Atom": "C", "Bond": "B", "Angle": "A", "Dihedral": "D"}
        atoms = []
        for i in self.selected_indexes:
            atomnr = self.mol_obj.molecule[i.row() + 1].atom_index
            if self.pymol:
                self.pymol_spheres(atomnr)
            atoms.append(f"{atomnr} (ORCA idx {atomnr - 1})")

        atoms_str = ", ".join(atoms)

        self.ui.list_freeze_atoms.insertItem(
            0, f"{self.ui.comboBox_freezetype.currentText()}: {atoms_str}"
        )

    def remove_freeze_atoms(self):
        """
        Removes selected freeze atoms/bonds/angles/torsions
        """
        # Get rows for selected to delete:
        to_del = [
            self.ui.list_freeze_atoms.row(x)
            for x in self.ui.list_freeze_atoms.selectedItems()
        ]
        for row in to_del:
            if self.pymol:
                for i in self.ui.list_freeze_atoms.item(row).text().split()[1:-1]:
                    self.pymol_spheres(atom_nr=i, hide=True)

            self.ui.list_freeze_atoms.takeItem(row)

    def on_spinbox_changed(self, spinbox):
        try:
            if spinbox.value() == 0:
                return
            if spinbox == self.ui.spinbox_scan_pm:
                self.scan_bond.scan_dist = spinbox.value()
            elif spinbox == self.ui.spinbox_scan_increment:
                self.scan_bond.step_size = spinbox.value()
            elif spinbox == self.ui.spinbox_mv_bonds:
                self.move_bond.scan_dist = spinbox.value()
        except AttributeError:
            return

        self.update_scan()

    def add_scan_atoms(self):
        """
        First, gather information from the UI. Then, pass all information
        to a new instance of AtomBond object.
        """

        if len(self.selected_indexes) != 2:
            self.react.append_text("Scan only works when only 2 atoms are selected...")
            return

        if self.scan_bond_key:
            try:
                del self.atom_bonds[self.scan_bond_key]
            except:
                pass

        freeze = ""
        atoms = list()
        bond_size = self.ui.spinbox_radius.value()
        scan_size = self.ui.spinbox_scan_pm.value()
        scan_increment = self.ui.spinbox_scan_increment.value()

        for i in self.selected_indexes:
            atoms.append(self.mol_obj.molecule[i.row() + 1].atom_index)
            freeze += f"{self.mol_obj.molecule[i.row() + 1].atom_name} ({self.mol_obj.molecule[i.row() + 1].atom_index})    "

        if self.ui.radioButton_plus.isChecked():
            scan_mode = "+"
        elif self.ui.radioButton_minus.isChecked():
            scan_mode = "-"
        else:
            scan_mode = "+/-"

        self.atom_bonds[freeze] = AtomBond(
            self.mol_obj.formatted_xyz,
            atoms[0],
            atoms[1],
            bond_size,
            scan_size,
            scan_increment,
            self.ui.checkBox_moveboth.isChecked(),
            scan_mode,
        )

        self.scan_bond_key = freeze

        # list_item = QtWidgets.QListWidgetItem(freeze)
        # self.ui.list_scan_bonds.addItem(list_item)
        # self.ui.list_scan_bonds.setCurrentItem(list_item)
        self.ui.lineEdit_freeze.setText(str(atoms[0]))
        self.ui.lineEdit_move.setText(str(atoms[1]))

        self.update_scan()

    def add_move_atoms(self):
        """
        First, gather information from the UI. Then, pass all information
        to a new instance of AtomBond object.
        """

        bond_size = self.ui.spinbox_curr_mv.value()
        scan_size = self.ui.spinbox_mv_bonds.value()
        scan_increment = self.ui.spinbox_scan_increment.value()

        self.atoms_mv.clear()

        for i in self.selected_indexes:
            self.atoms_mv.append(self.mol_obj.molecule[i.row() + 1].atom_index)

        if self.ui.radioButton_plus_mv.isChecked():
            scan_mode = "+"
        else:
            scan_mode = "-"

        try:
            self.move_bond = AtomBond(
                self.mol_obj.formatted_xyz,
                self.atoms_mv[0],
                self.atoms_mv[1],
                bond_size,
                scan_size,
                scan_increment,
                self.ui.checkBox_moveboth_mv.isChecked(),
                scan_mode,
            )
        except:
            pass

        all_xyz = self.move_bond.scan_new_coordinates
        last_xyz = all_xyz.popitem()

        content = str(len(last_xyz[1])) + "\n" + last_xyz[0] + "\n"
        for line in last_xyz[1]:
            content += line + "\n"

        filepath = self.settings.workdir + "/.move_tmp.xyz"
        try:
            remove(filepath)
        except:
            pass

        with open(filepath, "w+") as f:
            f.write(content)

        self.react.pymol.load_structure(filepath, delete_after=True)
        self.react.pymol.pymol_cmd(
            "group state_%d, %s" % (1, filepath.split("/")[-1].split(".")[0])
        )

        self.react.pymol.set_default_rep()
        self.react.pymol.pymol_cmd(
            "enable state_%d and %s" % (1, filepath.split("/")[-1].split(".")[0])
        )
        # self.react.file_to_pymol(self.settings.workdir + '/.move_tmp.xyz', state=1, set_defaults=True)

        # if self.pymol:
        #    self.react.add_file(self.settings.workdir + '/.move_tmp.xyz')

    def save_geometry_to_file(self):
        bond_size = self.ui.spinbox_curr_mv.value()
        scan_size = self.ui.spinbox_mv_bonds.value()
        scan_increment = self.ui.spinbox_scan_increment.value()

        for i in self.selected_indexes:
            self.atoms_mv.append(self.mol_obj.molecule[i.row() + 1].atom_index)

        if self.ui.radioButton_plus_mv.isChecked():
            scan_mode = "+"
        else:
            scan_mode = "-"

        try:
            self.move_bond = AtomBond(
                self.mol_obj.formatted_xyz,
                self.atoms_mv[0],
                self.atoms_mv[1],
                bond_size,
                scan_size,
                scan_increment,
                self.ui.checkBox_moveboth_mv.isChecked(),
                scan_mode,
            )
        except IndentationError:
            pass

        all_xyz = self.move_bond.scan_new_coordinates
        last_xyz = all_xyz.popitem()

        content = str(len(last_xyz[1])) + "\n" + last_xyz[0] + "\n"
        for line in last_xyz[1]:
            content += line + "\n"

        filepath = self.settings.workdir + f"/{last_xyz[0]}.xyz"

        with open(filepath, "w+") as f:
            f.write(content)

        self.react.add_file(filepath)

    def update_scan(self):
        """
        Remove all old files before making new ones
        """
        if not path.isdir(f"{self.settings.workdir}/.scan_temp"):
            mkdir(f"{self.settings.workdir}/.scan_temp")
        else:
            tempfiles = glob.glob(f"{self.settings.workdir}/.scan_temp/*")
            for f in tempfiles:
                remove(f)

        try:
            self.scan_bond.write_xyzfiles(self.settings.workdir + "/.scan_temp/")
            if self.pymol:
                # read files to pymol obj
                self.anmiate_bond_pymol()
        except AttributeError:
            pass

    def update_move(self):
        """
        Remove all old files before making new ones
        """
        # if path.isfile(f"{self.settings.workdir}/.move_temp"):
        #    self.react.remove_file(f"{self.settings.workdir}/.move_temp")
        #    remove(f"{self.settings.workdir}/.move_temp")
        #    self.ui.list_model_mv.clearSelection()

        self.add_move_atoms()

    def anmiate_bond_pymol(self):
        # It is not possible to delete states, so we actually need to delete the mol_obj and load it again :/
        # name_split = self.mol_obj.filepath.split("/")[-1].split(".")
        # name = name_split[0] + "_" + name_split[-1]
        # self.pymol.pymol_cmd(f"delete {name} and state_{self.state}")
        # self.react.file_to_pymol(filepath=self.mol_obj.filepath, state=1, set_defaults=True)
        state = 1
        self.pymol.pymol_cmd(f"delete scan")
        for f in sorted(os.listdir(f"{self.settings.workdir}/.scan_temp")):
            state += 1
            _mol = f"{self.settings.workdir}/.scan_temp/{f}"
            self.pymol.pymol_cmd(f"load {_mol},  scan, {state}")
        self.pymol.set_default_rep()
        self.pymol.pymol_cmd("set movie_fps, 10")
        self.pymol_animation = True
        self.pymol.pymol_cmd("mplay")

    def stop_pymol_animation(self):
        self.pymol.pymol_cmd("mstop")
        self.pymol.pymol_cmd(f"delete scan")
        # self.react.file_to_pymol(filepath=self.mol_obj.filepath, state=1, set_defaults=True)
        self.pymol_animation = False

    def remove_scan_atoms(self):
        try:
            del self.atom_bonds[self.scan_bond_key]
            self.ui.lineEdit_move.clear()
            self.ui.lineEdit_freeze.clear()
            self.ui.spinbox_radius.clear()
        except:
            pass
        # self.update_scan()

    # def scan_list_clicked(self):
    #     if not hasattr(self, "scan_bond"):
    #         return
    #     self.ui.list_model_scan.clearSelection()

    #     self.ui.lineEdit_freeze.setText(str(self.scan_bond.atom1_idx))
    #     self.ui.lineEdit_move.setText(str(self.scan_bond.atom2_idx))

    #     self.ui.checkBox_moveboth.setChecked(self.scan_bond.move_both)
    #     self.ui.spinbox_radius.setValue(self.scan_bond.bond_dist)
    #     self.ui.spinbox_scan_pm.setValue(self.scan_bond.scan_dist)
    #     self.ui.spinbox_scan_increment.setValue(self.scan_bond.step_size)
    #     if self.scan_bond.scan_mode == '+':
    #         self.ui.radioButton_plus.setChecked(True)
    #     elif self.scan_bond.scan_mode == '-':
    #         self.ui.radioButton_plus.setChecked(True)
    #     else:
    #         self.ui.radioButton_both.setChecked(True)

    #     for i in [self.scan_bond.atom1_idx - 1, self.scan_bond.atom2_idx - 1]:
    #         self.ui.list_model_scan.item(i).setSelected(True)

    #     #self.scan_bond.write_xyzfiles()

    def pymol_spheres(self, atom_nr, hide=False):
        """
        Indicate withe spheres atoms to be frozen / modredundant
        """
        group = "state_%d" % self.react.get_current_state
        _cmd = "show"
        mol_obj_name = (
            self.mol_obj.filename.split(".")[0]
            + "_"
            + self.mol_obj.filepath.split(".")[-1]
        )
        if hide:
            _cmd = "hide"
        self.pymol.pymol_cmd(
            f"{_cmd} spheres, id {atom_nr} and {group} and {mol_obj_name}"
        )
        if not hide:
            self.pymol.pymol_cmd(
                f"set sphere_scale, 0.3, id {atom_nr} and {group} and {mol_obj_name}"
            )

    def update_job_details(self):
        """
        Activated when job option combobox is updated. Will fill Qlist,
        Enable multiple files in case IRC is chosen, and hide Opt+freq
        buttons whenever job != opt.
        :return:
        """
        self.IRC_files.clear()
        self.ui.ComboBox_files.blockSignals(True)
        self.ui.ComboBox_files.clear()
        self.ui.ComboBox_files.blockSignals(False)

        self.job_type = self.ui.comboBox_job_type.currentText()

        if self.job_type in ["Freq"]:
            self.ui.checkbox_freq.setHidden(True)
        else:
            self.ui.checkbox_freq.setHidden(False)

        self.ui.List_add_job.clear()
        self.ui.List_add_job_2.clear()

        self.ui.List_add_job_2.addItems(self.job_options[self.job_type])
        self.ui.List_add_job.addItems(
            [
                f"%{block_name}\n    {block_content}\nEND\n"
                for block_name, block_content in self.blocks.items()
            ]
        )

    def update_functional(self):
        self.functional = self.ui.comboBox_funct.currentText()

    def fill_main_tab(self):
        """
        Fill all widgets in main tab.
        ORCA doesn't use basis set modifiers - they're built into the basis name.
        :return:
        """
        self.ui.lineEdit_filename.setText(self.filename)

        # Get software-specific options
        functional_options = self.settings.functional_options
        basis_options = self.settings.basis_options

        self.ui.comboBox_funct.addItems(functional_options)
        self.ui.comboBox_basis1.addItems(basis_options)

        self.ui.comboBox_job_type.addItems(self.job_options)
        self.ui.List_add_job.addItems(
            [
                f"%{block_name}\n  {block_content}\nEND\n"
                for block_name, block_content in self.blocks.items()
            ]
        )
        self.ui.ComboBox_files.addItem(self.filename)

        self.ui.comboBox.addItems([x for x in self.blocks_available.keys()])

        self.ui.comboBox_job_type.setCurrentText(self.settings.job_type)
        self.ui.comboBox_funct.setCurrentText(self.functional)
        self.ui.comboBox_basis1.setCurrentText(self.basis)

        self.ui.lineEdit_charge.setText(self.charge)
        self.ui.lineEdit_multiplicity.setText(self.multiplicity)

        self.ui.comboBox_SCRF.addItems(self.solvents)
        self.ui.checkbox_eps.setChecked(False)
        self.ui.lineEdit_eps.setEnabled(False)

        self.update_job_details()

    def on_scan_mode_changed(self):
        if not hasattr(self, "scan_bond"):
            return
        scan_mode_map = {-2: "+", -3: "-", -4: "+/-"}
        key = self.Qbutton_scan_group.checkedId()
        self.scan_bond.scan_mode = scan_mode_map[key]
        self.update_scan()

    def update_preview(self):
        """
        Update preview tab. Combobox is cleared and loaded again everytime.
        In case of multiple files, add correct num of items to combobox,
        but make only file content for the last file in combobox, and load
        this to text preview box.
        """

        if self.ui.tabWidget.currentIndex() == 1:
            self.atoms_to_select = 2

        # check if preview tab is selected. if not, return
        if not self.ui.tabWidget.currentIndex() == 3:
            return

        self.ui.ComboBox_files.blockSignals(True)
        self.ui.ComboBox_files.clear()
        self.ui.ComboBox_files.blockSignals(False)

        if self.atom_bonds:
            for bond, bond_obj in self.atom_bonds.items():
                for filename, xyz in bond_obj.scan_new_coordinates.items():
                    self.ui.ComboBox_files.addItem(filename)

                self.ui.ComboBox_files.setCurrentText(filename)
                file_content = self.make_input_content(
                    filename=filename, xyz=xyz, bond_obj=bond_obj
                )
        elif self.IRC_files:
            for filename, keywords in self.IRC_files.items():
                self.ui.ComboBox_files.addItem(filename)

            self.ui.ComboBox_files.setCurrentText(filename)
            file_content = self.make_input_content(
                filename=filename, extra_job_keywords=keywords
            )
        else:
            file_content = self.make_input_content(filename=self.filename)
            self.ui.ComboBox_files.addItem(self.filename)

        self.ui.text_preview.setPlainText(file_content)

    def update_preview_combobox(self):
        """
        This function is called everytime any change to combobox is made.
        Program crashes if runs with only one file in comobox, thus the
        if statement is neccesarry!
        """
        if self.ui.ComboBox_files.count() > 1:
            filename = self.ui.ComboBox_files.currentText()
            try:
                file_content = self.make_input_content(
                    filename=filename, extra_job_keywords=self.IRC_files[filename]
                )
                self.ui.text_preview.setPlainText(file_content)
                return
            except KeyError:
                pass

            for bond, bond_obj in self.atom_bonds.items():
                for filename_scan, xyz in bond_obj.scan_new_coordinates.items():
                    if filename_scan == filename:
                        file_content = self.make_input_content(
                            filename=filename, xyz=xyz, bond_obj=bond_obj
                        )
                        self.ui.text_preview.setPlainText(file_content)

    def update_charge(self):
        self.charge = self.ui.lineEdit_charge.text()

    def update_multiplicity(self):
        self.multiplicity = self.ui.lineEdit_multiplicity.text()

    def make_files(self):
        """
        Writes one or multiple inputfiles (found in self.multiplefiles)
        New files are loaded into react again using the exsisting add_files()
        function in REACT.py
        """
        files = []
        if self.IRC_files:
            for filename, keywords in self.IRC_files.items():
                content = self.make_input_content(
                    filename=filename, extra_job_keywords=keywords
                )
                filepath = self._make_file(filename, content)
                files.append(filepath)
        elif self.atom_bonds:
            for bond, bond_obj in self.atom_bonds.items():
                for filename_scan, xyz in bond_obj.scan_new_coordinates.items():
                    content = self.make_input_content(
                        filename=filename_scan, xyz=xyz, bond_obj=bond_obj
                    )
                    filepath = self._make_file(filename_scan, content)
                    files.append(filepath)
        else:
            content = self.make_input_content(filename=self.filename)
            filepath = self._make_file(self.filename, content)
            files.append(filepath)

        # Add files separate to avoid issues relating to multithreading prosess in REACT.py
        for filepath in files:
            if filepath == None:
                # Something happend (maybe user changed their mind and closed QfileDialog)
                return
            self.react.append_text(f"{filepath.split('/')[-1]} saved to: {filepath}")
            if self.ui.checkBox_cp_to_reactmain.isChecked():
                self.react.add_file(filepath)

    def make_orca_input_content(
        self, filename, extra_job_keywords=False, xyz=False, bond_obj=False
    ):
        """
        Make content (not file) for one ORCA inputfile.
        :return: str
        ORCA simple input format:
        ! functional basis job_keywords
        %blocks
        * xyz charge multiplicity
        coordinates
        *
        """
        # Simple input line
        job_keywords = []
        blocks_str = ""

        job_type = self.job_type
        if self.ui.checkbox_freq.isChecked():
            job_keywords.append("Freq")

        if extra_job_keywords:
            job_keywords.extend(extra_job_keywords)

        # Add job type specific keywords
        if self.job_type in self.job_options:
            job_keywords.extend(self.job_options[self.job_type])

        if self.ui.checkbox_SCRF.isChecked():
            scrf_method = self.ui.comboBox_SCRF.currentText()
            solvent = self.ui.lineEdit_solvent.text()

            if self.ui.checkbox_eps.isChecked():
                blocks_str += f"\n%cpcm\n  epsilon {self.ui.lineEdit_eps.text()}\nEND\n"
                solvent = None

            if solvent:
                job_keywords.append(f"{scrf_method}({solvent})")
            else:
                job_keywords.append(f"{scrf_method}")

        # Build simple input line
        simple_input = (
            f"! {self.functional} {self.basis} {job_type} {' '.join(job_keywords)}"
        )

        if self.blocks:
            blocks_str += "\n" + ("\n").join(
                [
                    f"%{block_name}\n  {block_content}\nEND\n"
                    for block_name, block_content in self.blocks.items()
                ]
            )

        # Molecule specification
        if not self.charge:
            self.react.append_text(
                "WARNING: No charge is given to the system. Will set it to 0.."
            )
            self.charge = "0"

        if xyz:
            coords_str = "\n".join(xyz)
        else:
            coords_str = "\n".join(self.mol_obj.formatted_xyz)

        molecule_str = f"* xyz {self.charge} {self.multiplicity}\n{coords_str}\n*"

        # Geometry constraints (modredundant equivalent)
        constraints_str = ""
        if self.ui.list_freeze_atoms.count() > 0:
            constraints_str = "\n%geom\n"
            constraints_str += "  Constraints\n"
            for i in range(self.ui.list_freeze_atoms.count()):
                item = self.ui.list_freeze_atoms.item(i).text()
                # Parse format: "Constraint_type: 1 (ORCA idx 0), 2 (ORCA idx 1)"
                if ":" in item:
                    constraint_type_map = {
                        "Atom": "C",
                        "Bond": "B",
                        "Angle": "A",
                        "Dihedral": "D",
                    }
                    constraint_name, atoms_part = item.split(":", 1)
                    constraint_type = constraint_type_map.get(
                        constraint_name.strip(), "C"
                    )

                    # Extract atom numbers before parentheses
                    atom_indices = []
                    for atom_str in atoms_part.split(","):
                        atom_str = atom_str.strip()
                        if "(" in atom_str:
                            # Extract number before parenthesis and convert to 0-based
                            atom_num = atom_str.split("(")[0].strip()
                            atom_indices.append(str(int(atom_num) - 1))

                    if atom_indices:
                        constraints_str += (
                            f"    {{ {constraint_type} {' '.join(atom_indices)} C }}\n"
                        )
            constraints_str += "  END\nEND\n"

        return f"{simple_input}\n{blocks_str}\n{molecule_str}\n{constraints_str}\n"

    def _make_file(self, filename, file_content):
        """
        Private function. Makes sure that no files are overwritten, and
        makes an unique filepath by adding _1, _2, _3 etc until an unique
        filepath is found.
        """
        i = 0
        # ORCA uses .inp extension
        ext = ".inp"
        new_filepath = self.react.settings.workdir + "/" + filename + ext

        if path.isfile(new_filepath) == True:
            new_filepath, filter_ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Filename already exists, please select a different filename",
                self.react.settings.workdir,
                "input files (*.com *.inp)",
            )
        if new_filepath == "":
            return
        with open(new_filepath, "w+") as f:
            f.write(file_content)
            f.write("\n")

        return new_filepath

    def make_input_content(
        self, filename, extra_job_keywords=False, xyz=False, bond_obj=False
    ):
        """
        Make content (not file) for one inputfile (Gaussian or ORCA).
        Routes to appropriate method based on software selection.
        :return: str
        """
        return self.make_orca_input_content(filename, extra_job_keywords, xyz, bond_obj)

    def remove_extra_newline(self, input_string):
        """
        To remedy some strange bug in make_input_content..
        """

        # Split the string into lines
        lines = input_string.split("\n")

        # Remove any empty lines
        lines = [line for line in lines if line]

        # Join the lines back together with newline characters
        output_string = "\n".join(lines)

        return output_string

    def route_checkboxes_update(self, checkbox, lineEdit):
        if checkbox.isChecked():
            lineEdit.setEnabled(True)
        else:
            lineEdit.setEnabled(False)

    def update_basis1(self):
        """
        Updates self.basis according to basis selected by user.
        ORCA doesn't use basis set modifiers (diff, pol1, pol2).
        """
        self.basis = self.ui.comboBox_basis1.currentText()

    def filename_update(self):
        self.filename = self.ui.lineEdit_filename.text()

        self.ui.lineEdit_chk.setText(self.filename + ".chk")
        self.ui.lineEdit_oldchk.setText(self.filename + "_old.chk")

    def insert_model_atoms(self):
        """
        :return:
        """

        if "pdb" in self.filepath.split(".")[-1]:
            atoms = self.mol_obj.formatted_pdb
        else:
            self.ui.button_auto_freeze.setEnabled(False)
            atoms = self.mol_obj.formatted_xyz

        for atom_list in [self.ui.list_model, self.ui.list_model_mv]:
            for i in range(len(atoms)):
                atom_list.insertItem(i, atoms[i])

    def auto_freeze_atoms(self):
        """
        Goes through PDB atoms and tries to figure out base on pdb atom names and distances what atoms
        are terminal/chopped region atoms that should be frozen.
        """
        expected = ["CA", "C", "H", "N", "O"]
        atoms = self.mol_obj.atoms
        for atom in atoms:
            pdb_name = atom.get_pdb_atom_name
            if pdb_name in ["C", "N"]:
                atoms.pop(0)
                for next_atom in atoms:
                    radius = atom_distance(
                        atom.get_coordinate, next_atom.get_coordinate
                    )
                    if radius < 1.7:
                        if next_atom.get_pdb_atom_name not in expected:
                            atom_nr = next_atom.get_atom_index
                            self.ui.list_freeze_atoms.insertItem(0, f"X {atom_nr} F")
                            if self.pymol:
                                self.pymol_spheres(atom_nr)

    def add_item_to_list(self, Qtextinput, Qlist, job_list, block=False):
        """
        :param Qtextinput: QLineEdit
        :param Qlist: QListWidget
        :param job_list: list or dict to store item (dict for blocks, list for others)
        :param block: block name if adding a block, False otherwise
        Adds the text input from user (past to Qtextinput) to correct
        QlistWidget and append item to list.
        """
        user_input = Qtextinput.text()

        if not user_input:
            return

        if block:
            # For blocks: store raw content in dict, display formatted version in UI
            if block not in self.blocks or self.blocks[block] != user_input:
                self.blocks[block] = user_input
                display_text = f"%{block}\n    {user_input}\nEND\n"

                # Check if this block is already in the list, if so update it
                for i in range(Qlist.count()):
                    item_text = Qlist.item(i).text()
                    if item_text.startswith(f"%{block}\n"):
                        Qlist.takeItem(i)
                        break

                Qlist.addItem(display_text)
        else:
            # For regular lists (not blocks)
            if user_input not in job_list:
                job_list.append(user_input)
                Qlist.addItem(user_input)

        Qtextinput.clear()

    def del_item_from_list(self, Qlist, job_list):
        """
        :param Qlist: QListWidget
        :param job_list: list to delete from
        Removes item in QlistWdiget and updates self.settings accordingly.
        """
        try:
            item_text = Qlist.currentItem().text()

            # For blocks list (List_add_job), extract block name and delete from self.blocks
            if Qlist == self.ui.List_add_job:
                # Extract block name from formatted string like "%blockname\n    content\nEND\n"
                block_name = item_text.split("\n")[0][1:]  # Remove '%' prefix
                if block_name in self.blocks:
                    del self.blocks[block_name]
            # For job options list (List_add_job_2), delete from job_options for current job type
            elif Qlist == self.ui.List_add_job_2:
                if (
                    self.job_type in self.job_options
                    and item_text in self.job_options[self.job_type]
                ):
                    self.job_options[self.job_type].remove(item_text)
            # For other lists, delete from the passed job_list
            elif item_text in job_list:
                job_list.remove(item_text)

            Qlist.takeItem(Qlist.currentRow())
        except (AttributeError, IndexError):
            pass

    def del_tempfiles(self):
        try:
            shutil.rmtree(self.react.react_path + "/.scan_temp")
        except OSError as e:
            pass

    def on_close(self):
        self.del_tempfiles()
        self.close()

    def on_write(self):
        """
        Write all data to Inputfile object.
        # TODO how to return this object to react after closing the window?
        # TODO reply --> just open the .com file in the current state (tab) of REACT after write?
        # TODO on_write should probably just write whatever is in the preview window to a file.
        """
        # self.mol_obj.filename = self.ui.lineEdit_filename.text()
        # self.mol_obj.job_type = self.ui.comboBox_job_type.currentText()
        # self.mol_obj.basis = self.ui.comboBox_basis1.currentText()
        # self.mol_obj.basis_diff = self.ui.comboBox_basis2.currentText()
        # self.mol_obj.basis_pol1 = self.ui.comboBox_basis3.currentText()
        # self.mol_obj.basis_pol2 = self.ui.comboBox_basis4.currentText()
        # self.react.states[self.react.state_index].add_instance(self.mol_obj)

        self.make_files()
        self.del_tempfiles()
        # self.close()

    def closeEvent(self, event):
        if self.pymol:
            self.pymol.pymol_cmd("set mouse_selection_mode, 1")
            self.pymol.pymol_cmd("hide spheres,")
            self.pymol.unmonitor_clicks()
        if path.isdir(f"{self.settings.workdir}/.scan_temp"):
            shutil.rmtree(f"{self.settings.workdir}/.scan_temp")
        if self.pymol_animation:
            self.stop_pymol_animation()

        self.react.setup_window = None

    def handle_overall_charge(self, charge):
        if self.charge:
            return

        if charge:
            self.charge = charge
            self.ui.lineEdit_charge.setText(self.charge)
