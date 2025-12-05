from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSlot, QTimer
from UIs.PDB_clusterWindow import Ui_ClusterPDB
from mods.DialogsAndExceptions import DialogMessage
from mods.common_functions import find_ligands_pdbfile
import os


class ModelPDB(QtWidgets.QMainWindow):
    """
    User window to interact with global settings (REACT attributes
    workdir, DFT_settings and Ui_stylemode)
    """

    def __init__(self, parent):
        # super().__init__(parent, Qt.WindowStaysOnTopHint)
        super().__init__(parent)

        self.react = parent
        self.ui = Ui_ClusterPDB()

        self.ui.setupUi(self)

        # TODO optimize this:
        screen_size = self.screen().availableGeometry()
        window_size = self.geometry()
        self.move(int(((screen_size.width() - window_size.width()) / 2)) - 250, 100)
        ###

        self.setWindowTitle("REACT - PDB model generation")

        if not self.react.pymol:
            self.close()
            self.react.start_pymol()

        self.pymol = self.react.pymol

        self.selected_atoms = {"central": list(), "included": list()}
        self.fix_atoms = list()
        self.model_tmp = False
        self.model_final = False
        self.auto_added = False
        self.atom_count = dict()

        # Connect signals from pymol:
        self.pymol.atomsSelectedSignal.connect(self.update_selected_atoms)
        self.pymol.ntermResidues.connect(self.update_nterm)
        self.pymol.ctermResidues.connect(self.update_cterm)
        self.pymol.dihedralSignal.connect(self.update_dihedral)
        self.pymol.countAtomsSignal.connect(self.update_atom_count)

        # Connect UI widgets:
        self.ui.select_byres.clicked.connect(self.update_inclusion_size)
        self.ui.include_solvent.clicked.connect(self.update_inclusion_size)
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)

        self.ui.lineEdit_atoms_in_model.setText("0")

        self.ui.slider_inclusion_size.valueChanged.connect(self.update_inclusion_size)
        self.ui.slider_inclusion_size.setValue(1)
        self.ui.button_pdb_from_table.clicked.connect(self.import_pdb_project_table)
        self.ui.button_set_cluster_center.clicked.connect(self.set_central_atoms)
        self.ui.button_update_manual_selection.clicked.connect(
            lambda: self.pymol.get_selected_atoms("included")
        )
        self.ui.button_create_model.clicked.connect(self.create_model)
        self.ui.button_auto_nterm.clicked.connect(self.auto_add_terminals)
        self.ui.button_delete_selected.clicked.connect(self.delete_selected)
        self.ui.button_add_group.clicked.connect(self.build_fragment)
        self.ui.button_load_pdb.clicked.connect(self.load_pdb)
        self.ui.button_finalize.clicked.connect(self.copy_model)
        self.ui.button_export_model.clicked.connect(self.save_pdb_model)

    def load_pdb(self):
        file_, file_type = self.react.import_files(
            title_="Import PDB",
            filter_type="Protein data bank (*.pdb)",
            path=self.react.settings.workdir,
        )
        if not file_:
            return
        file_ = file_[0]
        self.pymol.load_structure(file_=file_, delete_after=False)
        self.add_new_pdb(file_)

    def import_pdb_project_table(self):
        """
        take selected PDB file from project table
        :return:
        """
        try:
            file_ = self.react.get_selected_filepath
        except AttributeError:
            return
        if not file_:
            return
        if not file_.split(".")[-1] == "pdb":
            warn = DialogMessage(self, "PDB file required")
            warn.show()
            self.react.append_text(
                "%s is not recognised as a pdb file." % (file_.split("/")[-1])
            )
            return
        self.add_new_pdb(file_)

    def add_new_pdb(self, file_):
        self.ui.list_model_summary.clear()
        for i in range(8):
            self.ui.list_model_summary.insertItem(i, "")
        self.ui.lineEdit_pdb_file.setText(file_)
        self.group_pdb_pymol(
            pdb_source=file_.split("/")[-1].split(".")[0], pdb_target="source"
        )
        self.guess_highlight_ligand(pdb_file=file_, pymol_name="source")
        self.pymol.pymol_cmd("count_atoms source")
        self.pymol.pymol_cmd("count_atoms source and not sol.")

        if self.ui.list_model_summary.count() > 0:
            self.ui.list_model_summary.takeItem(0)
        self.ui.list_model_summary.insertItem(0, "Source: %s" % file_)

    def tab_changed(self):
        """

        :return:
        """
        if self.model_tmp:
            self.pymol.pymol_cmd("count_atoms included")
            self.pymol.pymol_cmd("count_atoms included and not sol.")
        tab_index = self.ui.tabWidget.currentIndex()
        if tab_index == 0:
            if self.model_tmp:
                self.model_tmp = False
                self.pymol.pymol_cmd("delete model_tmp")
            if self.auto_added:
                self.auto_added = False
                self.pymol.pymol_cmd("delete auto_added")
            self.pymol.highlight(name="source", group="pdb_model")
            self.pymol.pymol_cmd("enable included or central")
            self.pymol.pymol_cmd("set mouse_selection_mode, 1")
            self.pymol.pymol_cmd("config_mouse three_button_viewing")
            self.update_inclusion_size()
        elif tab_index == 1:
            if not self.model_tmp:
                self.create_model()
            if self.model_tmp:
                self.pymol.highlight(name="model_tmp", group="pdb_model")
                self.pymol.pymol_cmd("set mouse_selection_mode, 0")
                self.pymol.pymol_cmd("config_mouse three_button_viewing")
        elif tab_index == 2:
            if not self.model_tmp:
                print("Please create a model first...")
                self.ui.tabWidget.setCurrentIndex(0)
                return
            self.pymol.pymol_cmd("count_atoms model_tmp")
            self.pymol.pymol_cmd("count_atoms model_tmp and not sol.")
            self.copy_model()
            self.pymol.pymol_cmd("config_mouse three_button_editing")

        if tab_index != 2:
            if self.model_final:
                self.pymol.pymol_cmd("delete model_final")
                self.model_final = False

        # else:
        #    self.pymol.pymol_cmd("config_mouse three_button_viewing")

    def guess_highlight_ligand(self, pdb_file, pymol_name):
        """
        Guess from pdb file what is the interesting region of the protein and highlight it in pymol
        :param pdb_file: path to pdb file
        :return:
        """
        residues = find_ligands_pdbfile(pdb_file)

        self.pymol.set_protein_ligand_rep(
            residues, pymol_name=pymol_name, group="pdb_model"
        )

    def group_pdb_pymol(self, pdb_source, pdb_target):
        """
        Make a group in pymol for setting up PDB model / cluster
        :param pdb_source: pdb name (pymol) to copy into pdb_model group
        :param pdb_target: pymol name of internal pdb to create
        :return:
        """
        self.pymol.pymol_cmd("create %s, %s" % (pdb_target, pdb_source))
        self.pymol.pymol_cmd("group pdb_model, %s" % pdb_target)
        self.pymol.highlight(name=pdb_target, group="pdb_model")

    def set_central_atoms(self):
        """
        :return:
        """
        # Reset central atoms
        self.selected_atoms["central"] = list()
        self.selected_atoms["included"] = list()
        self.pymol.get_selected_atoms()

    @pyqtSlot(list)
    def update_selected_atoms(self, atoms):
        """
        Signal from PymolProcess when atoms are selected. Updates global self.selected_atoms dictionary
        :param: atoms list of atom numbers (str)
        :return:
        """
        if len(atoms) == 0:
            print("No atoms selected")
            self.react.append_text("No atoms selected")
            return

        # Remove duplicates (maybe not necessary):
        atoms = list(dict.fromkeys(atoms))
        if self.model_tmp:
            self.fix_atoms = list()
            self.fix_atoms = atoms
            return

        if len(self.selected_atoms["central"]) < 1:
            self.selected_atoms["central"] = atoms
            self.pymol.set_selection(
                atoms=atoms,
                sele_name="central",
                object_name="source",
                group="pdb_model",
            )
            self.pymol.highlight_atoms(
                atoms=atoms, color="lightmagenta", name="source", group="pdb_model"
            )
            self.update_inclusion_size()
        else:
            self.selected_atoms["included"] = atoms
            self.pymol.set_selection(
                atoms=atoms,
                sele_name="included",
                object_name="source",
                group="pdb_model",
            )
        self.pymol.pymol_cmd("count_atoms included")
        self.pymol.pymol_cmd("count_atoms included not sol.")

    @pyqtSlot(list)
    def update_nterm(self, resi):
        self.get_terminal_dihedrals(term="nterm", residues=resi)

    @pyqtSlot(list)
    def update_cterm(self, resi):
        self.get_terminal_dihedrals(term="cterm", residues=resi)

    @pyqtSlot(list)
    def update_dihedral(self, dihedral):
        if "/N" in dihedral[2]:
            adding = self.ui.nterm_capping.currentText()
        elif "/C" in dihedral[2]:
            adding = self.ui.cterm_capping.currentText()
        else:
            print("I am not sure what you want to add or where... FIX ME!")
            return

        self.pymol.add_fragment(attach_to=dihedral[2], fragment=adding)
        self.pymol.set_dihedral(
            dihedral[0], dihedral[1], dihedral[2], dihedral[3], dihedral[4]
        )

    @pyqtSlot(dict)
    def update_atom_count(self, count):
        for k in count.keys():
            self.atom_count[k] = count[k]

        if "model_tmp" in self.atom_count.keys():
            self.ui.lineEdit_atoms_in_model.setText(self.atom_count["model_tmp"])
            self.ui.list_model_summary.takeItem(3)
            self.ui.list_model_summary.insertItem(
                3, "Model: %s atoms in total" % self.atom_count["model_tmp"]
            )

        if "source" in self.atom_count.keys():
            if self.ui.list_model_summary.count() > 1:
                self.ui.list_model_summary.takeItem(1)
            self.ui.list_model_summary.insertItem(
                1, "Source: %s atoms in total" % self.atom_count["source"]
            )

        if "source and not sol." in self.atom_count.keys():
            if self.ui.list_model_summary.count() > 2:
                self.ui.list_model_summary.takeItem(2)
            self.ui.list_model_summary.insertItem(
                2,
                "Source: %s atoms excluding solvent"
                % self.atom_count["source and not sol."],
            )

        if "model_tmp and not sol." in self.atom_count.keys():
            self.ui.list_model_summary.takeItem(4)
            self.ui.list_model_summary.insertItem(
                4,
                "Model: %s atoms excluding solvent"
                % self.atom_count["model_tmp and not sol."],
            )

        if "included" in self.atom_count.keys():
            if not self.model_tmp:
                self.ui.lineEdit_atoms_in_model.setText(self.atom_count["included"])
            self.ui.list_model_summary.takeItem(5)
            self.ui.list_model_summary.insertItem(
                5, "Model: %s atoms from source" % self.atom_count["included"]
            )
            self.ui.list_model_summary.takeItem(6)
            model_coverage = (
                float(self.atom_count["included"]) / float(self.atom_count["source"])
            ) * 100.0
            self.ui.list_model_summary.insertItem(
                6, "Model covering %.2f %% of source" % model_coverage
            )

        if "included and not sol." in self.atom_count.keys():
            self.ui.list_model_summary.takeItem(7)
            model_coverage2 = (
                float(self.atom_count["included and not sol."])
                / float(self.atom_count["source and not sol."])
            ) * 100.0
            self.ui.list_model_summary.insertItem(
                7,
                "Model covering %.2f %% of source excluding solvent" % model_coverage2,
            )

    def update_inclusion_size(self):
        """
        Sets radius of residues to include in lineEdit
        :return:
        """
        expand_radius = self.ui.slider_inclusion_size.value()
        self.ui.lineEdit_inclusion_radius.setText(str(expand_radius))

        if self.selected_atoms["central"]:
            self.selected_atoms["included"].clear()
            self.pymol.expand_sele(
                selection="central",
                sele_name="included",
                group="pdb_model",
                radius=expand_radius,
                by_res=self.ui.select_byres.isChecked(),
                include_solv=self.ui.include_solvent.isChecked(),
            )
            # Delay this in case user does rappid changes...
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.delayed_get_atoms)
            # Timer in milliseconds:
            self.timer.start(500)

    def delayed_get_atoms(self):
        self.timer.stop()
        self.pymol.get_selected_atoms(sele="included")

    def create_model(self):
        if len(self.selected_atoms["included"]) < 1:
            print("No atoms to generate model from. Please select central molecule")
            self.react.append_text(
                "No atoms to generate model from. Please select central molecule."
            )
            self.ui.tabWidget.setCurrentIndex(0)
            return

        self.pymol.copy_sele_to_object(
            sele="included", target_name="model_tmp", group="pdb_model"
        )
        self.pymol.pymol_cmd("disable source")
        self.pymol.pymol_cmd("hide cartoon, model_tmp")
        self.pymol.pymol_cmd("show nonbonded, model_tmp")

        # Update included selection to now refer to model_tmp instead of source:
        self.pymol.pymol_cmd("select included, model_tmp")
        self.pymol.pymol_cmd("count_atoms model_tmp")
        self.pymol.pymol_cmd("count_atoms model_tmp and not sol.")

        # Identify terminals that have been chopped
        [
            self.pymol.find_unbonded(pymol_name="model_tmp", type=x, group="pdb_model")
            for x in ["nterm", "cterm"]
        ]
        self.pymol.pymol_cmd("count_atoms nterm")
        self.pymol.pymol_cmd("count_atoms cterm")

        self.model_tmp = True
        self.ui.tabWidget.setCurrentIndex(1)

    def copy_model(self, source="model_tmp", target="model_final"):
        self.pymol.copy_sele_to_object(
            sele=source, target_name=target, group="pdb_model"
        )
        self.pymol.pymol_cmd("disable %s" % source)
        self.pymol.pymol_cmd("color lightmagenta, %s and name C*" % target)
        self.pymol.highlight(name="model_final", group="pdb_model")
        self.ui.tabWidget.setCurrentIndex(2)
        self.model_final = True

    def delete_selected(self):
        self.pymol.pymol_cmd("remove sele and model_tmp")
        self.pymol.pymol_cmd("count_atoms model_tmp")
        self.pymol.pymol_cmd("count_atoms model_tmp and not sol.")

    def build_fragment(self):
        fragment = self.ui.groups_to_add.currentText()
        self.pymol.add_fragment(attach_to="sele", fragment=fragment)
        self.pymol.pymol_cmd("count_atoms model_tmp")
        self.pymol.pymol_cmd("count_atoms model_tmp and not sol.")

    def auto_add_terminals(self):
        """
        :return:
        """
        if self.auto_added:
            return

        for selection in ["nterm", "cterm"]:
            self.pymol.get_selected_atoms(sele=selection, type="int(resi)")

        build_time = (
            int(self.atom_count["nterm"]) + int(self.atom_count["cterm"])
        ) * 300
        QtCore.QTimer.singleShot(
            build_time,
            lambda: self.pymol.pymol_cmd(
                "select auto_added, included extend 5 and not included"
            ),
        )
        QtCore.QTimer.singleShot(
            build_time + 25, lambda: self.pymol.pymol_cmd("group pdb_model, auto_added")
        )
        QtCore.QTimer.singleShot(
            build_time + 50,
            lambda: self.pymol.pymol_cmd("color gray, auto_added and name C*"),
        )
        QtCore.QTimer.singleShot(
            build_time + 75, lambda: self.pymol.pymol_cmd("count_atoms model_tmp")
        )
        self.auto_added = True

    def get_terminal_dihedrals(self, term="nterm", residues=None):
        """

        :param term:
        :param residues:
        :return:
        """
        if residues is None:
            residues = list()

        prot = "model_tmp"
        if term == "nterm":
            names = ["C", "CA", "N", "H"]
        else:
            names = ["N", "CA", "C", "O"]

        for i in residues:
            atoms = list()
            for atom in names:
                atoms.append("%s///%s/%s" % (prot, i, atom))
            self.pymol.get_dihedral(atoms[0], atoms[1], atoms[2], atoms[3])

    def save_pdb_model(self):
        """
        :return:
        """
        if not self.pymol:
            return

        temp_filepath = self.react.settings.workdir + "/"
        pdb_path, filter_ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save PDB model", temp_filepath, "PDB (*.pdb)"
        )

        if not pdb_path:  # User cancelled dialog
            return

        # Ensure model_final exists before saving
        if not self.model_final:
            self.react.append_text("Please finalize the model first (tab 3)")
            return

        # Delay save command to ensure PyMOL has processed model_final creation
        QTimer.singleShot(200, lambda: self._do_save_pdb(pdb_path))

    def _do_save_pdb(self, pdb_path):
        """Helper to execute the actual save command after delay"""
        self.pymol.pymol_cmd('save "%s", model_final' % pdb_path)
        self.react.append_text(f"\n{pdb_path} written.")

    def closeEvent(self, event):
        self.react.cluster_window = None

        if self.pymol:
            self.pymol.pymol_cmd("delete pdb_model")
            self.pymol.pymol_cmd("set mouse_selection_mode, 1")
            self.pymol.pymol_cmd("config_mouse three_button_viewing")
