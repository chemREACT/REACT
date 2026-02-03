from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from UIs.AnalyseWindow import Ui_AnalyseWindow
import mods.common_functions as cf
from mods.ReactPlot import SpectrumIR, PlotEnergyDiagram
from mods.GaussianFile import OutputFile, FrequenciesOut
from mods.ORCAFile import ORCAOutputFile, ORCAFrequenciesOut


class AnalyseCalc(QtWidgets.QMainWindow, Ui_AnalyseWindow):
    def __init__(self, parent):
        super(AnalyseCalc, self).__init__(parent, Qt.WindowStaysOnTopHint)

        self.react = parent

        self.ui = Ui_AnalyseWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("REACT - Analyse")

        # Hartree / kcal/mol / kj/mol:
        self.unit = 1

        self.ui.button_set_file.clicked.connect(self.set_file_included)

        self.ui.button_set_file.clicked.connect(self.set_file_included)
        self.ui.button_remove_file.clicked.connect(self.remove_file_included)

        self.ui.button_plot_frq.clicked.connect(self.plot_frequency)

        self.ui.button_plot_energies.clicked.connect(self.plot_energies)

        self.ui.button_frq_pymol.clicked.connect(self.animate_frequency)

        self.ui.button_next_state.clicked.connect(lambda: self.change_state(i=1))
        self.ui.button_prev_state.clicked.connect(lambda: self.change_state(i=-1))

        self.ui.horizontalSlider_scale.valueChanged.connect(self.update_scale)

        # Track State viewed in MainWindow:
        self.react.tabWidget.tabBar().currentChanged.connect(
            self.update_state_included_files
        )
        self.react.tabWidget.currentWidget().itemClicked.connect(
            self.update_included_files
        )

        # Initialise dict of included files if it does not exist:
        self.energies = dict()

        # Pymol session:
        # TODO - get pymol_path from global settings
        self.pymol = self.react.pymol

        state = self.react.get_current_state
        self.init_included_files()
        self.update_state_included_files()
        # try:
        #     if not self.react.included_files or sum(len(x) for x in self.react.included_files[state].values()) < 4:
        #         self.init_included_files()
        #     self.update_state_included_files()
        # except KeyError:
        #     pass

        self.ui.calctype.setCurrentRow(0)

        # TODO get units from global settings (mainwindow) and set correct unit:
        self.ui.unit_hartree.setChecked(True)

        # Connect unit radiobuttons to self.unit
        self.ui.unit_hartree.toggled.connect(lambda: self.set_unit(1))
        self.ui.unit_kcal.toggled.connect(lambda: self.set_unit(627.51))
        self.ui.unit_kj.toggled.connect(lambda: self.set_unit(2625.51))

        self.react.tabWidget.tabBar().setMovable(False)

    def update_scale(self):
        """
        connect scalebar with LCD number displayed
        """
        self.ui.lcdNumber_scale.display(self.ui.horizontalSlider_scale.value())

    @property
    def get_selected_frequency(self):
        frq = self.ui.list_frequencies.selectedItems()
        if not frq:
            # TODO Bente, did you make some class for pop-up warnings? This could be nice here, I think.
            self.react.append_text("Select frequency to be displayed in pymol")
            return None
        else:
            return frq[0].text().split()[0]

    def animate_frequency(self):
        """
        Takes current output file, creates temporary xyz files - loads it to pymol and creates movie for
        selected frequency. Temporary xyz files, can be stored if selected by user under settings.
        :return:
        """
        view_pymol = False
        delete_files = True

        if self.ui.checkBox_view_pymol.isChecked():
            view_pymol = True

        if self.ui.checkBox_write_xyz.isChecked():
            delete_files = False

        # if not view in pymol or not write files - nothing to do - return
        if not view_pymol and delete_files:
            print("Well, no reason to get up and go to work with these settings... ")
            return

        # Get selected frequency:
        frq = self.get_selected_frequency
        if not frq:
            print("No frequencies found ")
            return
        print("Displaying Frequency %s" % frq)

        if view_pymol and not self.pymol:
            self.pymol = self.react.start_pymol(return_session=True)

        # path to output file with frequencies:
        g_file = self.get_freq_file
        # Current state:
        state = self.react.get_current_state
        mol_obj = self.react.states[state - 1].get_molecule_object(filepath=g_file)

        # Get vibration scaling:
        scale = self.ui.lcdNumber_scale.value() / 100.0

        # Get list with Molecule objects for vibrational displacement:
        mol_vibs = mol_obj.displacement_animation(freq=frq, steps=10, scale=scale)

        # Load files to pymol, and/or write xyz files.
        i = 0
        base_name = "%s/%s" % (
            self.react.settings.workdir,
            g_file.split("/")[-1].split(".")[0],
        )
        for mol in mol_vibs:
            xyz_path = "%s_tmp%03d.xyz" % (base_name, i)
            cf.write_file(mol.formatted_xyz, xyz_path)
            i += 1
            if view_pymol:
                self.pymol.load_structure(xyz_path, delete_after=delete_files)
                self.pymol.pymol_cmd("group state_%d, %s" % (state, xyz_path))

        if view_pymol:
            # Make animation
            # join_states moviename, mol*, 0 (the 0 assumes identical input objects so bonds can vary)
            self.pymol.pymol_cmd("delete w_%s" % frq)
            self.pymol.pymol_cmd(
                "join_states w_%s, %s*, 0" % (frq, base_name.split("/")[-1])
            )
            self.pymol.pymol_cmd("delete %s_tmp*" % base_name.split("/")[-1])
            self.pymol.pymol_cmd("group state_%d, w_%s" % (state, frq))
            self.pymol.highlight(name="w_%s" % frq, group="state_%d" % state)
            self.pymol.pymol_cmd("set movie_fps, 40")
            self.pymol.pymol_cmd("mplay")

            # Fix representation
            self.pymol.set_default_rep()

    def change_state(self, i=1):
        current_state = self.react.get_current_state
        self.react.set_state(current_state + i)

    def set_unit(self, value):
        self.unit = float(value)
        self.update_relative_values()
        self.update_absolute_values()

    def init_included_files(self):
        """
        initialise dictionary with included files per state
        :return:
        """
        self.react.included_files = dict()
        for tab_index in range(self.react.tabWidget.count()):
            state = tab_index + 1

            self.react.included_files[state] = {0: "", 1: "", 2: "", 3: ""}
            if self.react.tabWidget.widget(tab_index).currentItem():
                file_path = self.react.tabWidget.widget(tab_index).currentItem().text()
                if file_path.split(".")[-1] in ["out", "log"]:
                    self.react.included_files[state][0] = file_path

                    # Check output file for frequencies
                    if self.react.states[tab_index].has_frequencies(file_path):
                        self.react.included_files[state][1] = file_path

                    # Check output file for Solvent
                    if self.react.states[tab_index].has_solvent(file_path):
                        self.react.included_files[state][2] = file_path

    def update_included_files(self):
        insert_index = self.ui.calctype.currentRow()
        filepath = self.react.get_selected_filepath
        state = self.react.get_current_state

        # Check if file is an output file (Gaussian or ORCA)
        file_obj = self.react.states[state - 1].files.get(filepath)
        if not isinstance(file_obj, (OutputFile, ORCAOutputFile)):
            self.react.append_text(
                "File must be a computational chemistry output file (.out or .log)"
            )
            return

        self.react.included_files[state][insert_index] = filepath
        self.update_state_included_files()

    def update_state_included_files(self):
        """
        When tabs are changed (state displayed) in main window, update correct files in list in analyse window
        :return:
        """
        tab_index = self.react.tabWidget.currentIndex()
        self.ui.label_state.setText(str(tab_index + 1))

        # In case a new state has been added after initialising the analyse window:
        if tab_index + 1 not in self.react.included_files.keys():
            self.react.included_files[tab_index + 1] = {0: "", 1: "", 2: "", 3: ""}

        # Iterate through includes files and insert them into list:
        for index in sorted(self.react.included_files[tab_index + 1].keys()):
            # If items exist in list, these must be removed before inserting new item:
            if self.ui.calc_files.count() > 0:
                self.ui.calc_files.takeItem(index)
            # Insert the new item:
            self.ui.calc_files.insertItem(
                index, self.react.included_files[tab_index + 1][index]
            )

            # Check if freq or solv is included in the main file:
            if index > 0:
                if (
                    self.react.included_files[tab_index + 1][index]
                    == self.react.included_files[1][0]
                ):
                    self.ui.calc_files.item(index).setForeground(
                        QtGui.QColor(70, 70, 70)
                    )

        # Move horizontal scrollbar according to text
        self.ui.calc_files.repaint()
        scrollbar = self.ui.calc_files.horizontalScrollBar()
        scrollbar.setValue(self.ui.calc_files.horizontalScrollBar().maximum())

        self.update_energies()
        self.update_absolute_values()
        self.update_relative_values()
        self.update_checkboxes()

    def update_energies(self):
        """
        Add energies to states. If they do not exist, they are False.
        :return:
        """
        self.energies = dict()
        for state in self.react.included_files.keys():
            state = int(state)
            if state not in self.energies.keys():
                self.energies[state] = {0: None, 1: None, 2: None, 3: None}

            for term in self.react.included_files[state].keys():
                # Check if state term has file (file length for now)
                if len(self.react.included_files[state][term]) > 2:
                    filepath = self.react.included_files[state][term]
                    # state_object = self.react.states[state - 1]
                    mol_obj = self.react.states[state - 1].get_molecule_object(filepath)
                    # Include 3 corrections from frequency calculation
                    if term == 1:
                        self.energies[state][term] = dict()

                        self.energies[state][term]["dG"] = mol_obj.thermal_dg
                        self.energies[state][term]["dH"] = mol_obj.thermal_dh
                        self.energies[state][term]["dE"] = mol_obj.thermal_de

                    else:
                        # self.energies[state][term] = state_object.get_energy(filepath)
                        self.energies[state][term] = mol_obj.energy
                else:
                    self.energies[state][term] = None

    def get_relative_energies(self):
        """

        :return:
        """
        de = dict()
        self.update_energies()
        for state in sorted(self.energies.keys()):
            de[state] = dict()
            for term in self.energies[state].keys():
                # main or big basis:
                if self.energies[state][term] and self.energies[1][term]:
                    if term == 0:
                        de[state]["main"] = (
                            self.energies[state][term] - self.energies[1][term]
                        )
                    # Frequencies = compute gibbs, enthalpy, energy in addition ...
                    elif term == 1:
                        # Relative thermal corrections to Gibbs, Enthalpy and Energy:
                        de[state]["ddG"] = (
                            self.energies[state][term]["dG"]
                            - self.energies[1][term]["dG"]
                        )
                        de[state]["ddH"] = (
                            self.energies[state][term]["dH"]
                            - self.energies[1][term]["dH"]
                        )
                        de[state]["ddE"] = (
                            self.energies[state][term]["dE"]
                            - self.energies[1][term]["dE"]
                        )

                        # Gibbs, Enthalpy and Energy with thermal corrections:
                        de[state]["dG"] = de[state]["main"] + de[state]["ddG"]
                        de[state]["dH"] = de[state]["main"] + de[state]["ddH"]
                        de[state]["dE"] = de[state]["main"] + de[state]["ddE"]

                    # Solvation correction:
                    elif term == 2:
                        solv_1 = self.energies[1][2] - self.energies[1][0]
                        solv_state = self.energies[state][2] - self.energies[state][0]
                        de[state]["ddSolv"] = solv_state - solv_1
                        de[state]["dSolv"] = solv_state

                        # Update Gibbs, Enthalpy and Energy with solvation correction:
                        if "dG" in de[state].keys():
                            for delta in ["dG", "dH", "dE"]:
                                de[state][delta] += de[state]["ddSolv"]

                    # Big basis correction:
                    elif term == 3:
                        de[state]["big"] = (
                            self.energies[state][term] - self.energies[1][term]
                        )

                        # Update Gibbs, Enthalpy and Energy with using big basis:
                        if "dG" in de[state].keys():
                            for delta in ["dG", "dH", "dE"]:
                                de[state][delta] += de[state]["big"] - de[state]["main"]

        return de

    def update_absolute_values(self):
        """

        :return:
        """
        self.ui.text_state_values.clear()

        self.update_energies()
        D = cf.unicode_symbols["Delta"]
        d = cf.unicode_symbols["delta"]

        symb = {
            0: "E(elec)",
            1: {"dG": d + "G ", "dH": d + "H ", "dE": d + "E "},
            2: "E(solv)",
            3: "E(big)",
        }

        state = self.react.tabWidget.currentIndex() + 1
        energies = self.energies[state]
        for term in sorted(energies.keys()):
            if energies[term]:
                if term == 1:
                    # Get thermal corrections:
                    for subterm in sorted(energies[term].keys()):
                        ene = energies[term][subterm] * self.unit
                        self.ui.text_state_values.appendPlainText(
                            "%8s %16.6f" % (symb[term][subterm], ene)
                        )
                else:
                    ene = energies[term] * self.unit
                    self.ui.text_state_values.appendPlainText(
                        "%8s %16.6f" % (symb[term], ene)
                    )

                # Calculate solvation energy:
                if term == 2:
                    de_solv = (energies[2] - energies[0]) * self.unit
                    self.ui.text_state_values.appendPlainText(
                        "%8s %16.6f" % (D + "E(solv)", de_solv)
                    )

        # If frequencies, insert them to list_frequencies:
        self.insert_frequencies(state)

    def insert_frequencies(self, state):
        self.ui.list_frequencies.clear()
        if self.energies[state][1]:
            insert_index = 0
            frequencies = self.react.states[state - 1].get_frequencies(
                str(self.react.included_files[state][1])
            )
            self.ui.list_frequencies.insertItem(insert_index, " Frequency IR Intensity")
            for freq in sorted(frequencies.keys()):
                insert_index += 1
                self.ui.list_frequencies.insertItem(
                    insert_index, "%10.4f %10.4f" % (freq, frequencies[freq])
                )

            # select the first frequency:
            self.ui.list_frequencies.setCurrentRow(1)

    def update_relative_values(self):
        """

        :return:
        """
        self.ui.text_relative_values.clear()

        # If no files defined for state 1, there is nothing to calculate:
        if not self.energies[1][0]:
            self.ui.text_relative_values.appendPlainText(
                "Relative energies to state 1...\nAdd files to calculate."
            )
            return

        rel_ene = self.get_relative_energies()

        # Generate the relevant header:
        D = cf.unicode_symbols["Delta"]
        d = cf.unicode_symbols["delta"]
        Dd = D + d
        DD = D + D

        header = "State"

        big = False
        # Include big basis correction?
        if "big" in rel_ene[1].keys():
            big = True
            header += "  %1sE(big)" % D
        else:
            header += " %1sE(main)" % D

        # Include solvation correction?
        solvation = False
        if "ddSolv" in rel_ene[1].keys():
            solvation = True
            header += " %2sE(solv)" % Dd

        # Include frequencies?
        freq = False
        if "dG" in rel_ene[1].keys():
            freq = True
            # only printing out Gibbs, to simplify table
            # header += "%8s %8s %8s %8s %8s %8s" % (Dd + "G", Dd + "H", Dd + "E", D + "G", D + "H", D + "E")
            header += "%8s %8s" % (Dd + "G", D + "G")

        self.ui.text_relative_values.appendPlainText(header)

        # insert relative energies to UI with correct unit:
        for state in rel_ene.keys():
            energies = "%5d" % state

            # If big basis - put this first, so that everything connected to main comes after main.
            dbig = 0
            if big:
                if "big" in rel_ene[state].keys():
                    dbig = rel_ene[state]["big"] * self.unit
                energies += "%9.2f" % dbig
            # Electronic energies of main file:
            else:
                d_el = 0
                if "main" in rel_ene[state].keys():
                    d_el = rel_ene[state]["main"] * self.unit
                energies += "%9.2f" % d_el

            # Change in solvation energy:
            dd_solv = 0
            if solvation:
                if "ddSolv" in rel_ene[state].keys():
                    dd_solv = rel_ene[state]["ddSolv"] * self.unit
                energies += "%10.2f" % dd_solv

            # Insert corrections from frequency calculations and calculate ∆G, ∆H and ∆E:
            if freq:
                ddg = 0
                dde = 0
                ddh = 0
                de = 0
                dh = 0
                dg = 0
                if "dG" in rel_ene[state].keys():
                    ddg = rel_ene[state]["ddG"] * self.unit
                    dde = rel_ene[state]["ddE"] * self.unit
                    ddh = rel_ene[state]["ddH"] * self.unit

                    dg = rel_ene[state]["dG"] * self.unit
                    de = rel_ene[state]["dE"] * self.unit
                    dh = rel_ene[state]["dH"] * self.unit

                # energies += "%8.2f %8.2f %8.2f %8.2f %8.2f %8.2f" % (ddg, ddh, dde, dg, dh, de)
                energies += "%8.2f %8.2f" % (ddg, dg)

            self.ui.text_relative_values.appendPlainText(energies)

    def update_checkboxes(self):
        """
        :return:
        """
        boxes = {
            0: [self.ui.checkBox_main],
            1: [
                self.ui.checkBox_gibbs,
                self.ui.checkBox_energy,
                self.ui.checkBox_enthalpy,
            ],
            2: [self.ui.checkBox_solvation],
            3: [self.ui.checkBox_big],
        }

        checked = 0

        for term in sorted(boxes.keys()):
            if self.has_energy_terms(term).count(True) > 1 and self.energies[1][term]:
                for box in boxes[term]:
                    if box.isChecked():
                        checked += 1
                    if not box.isCheckable():
                        box.setCheckable(True)
            else:
                for box in boxes[term]:
                    if box.isCheckable():
                        box.setChecked(False)
                        box.setCheckable(False)
        # If no boxes are checked - check the main box, if possible:
        if self.ui.checkBox_main.isCheckable():
            self.ui.checkBox_main.setChecked(True)

    def plot_energies(self):
        """
        :return:
        """
        # What terms to include?
        boxes = {
            0: [self.ui.checkBox_main],
            1: [
                self.ui.checkBox_gibbs,
                self.ui.checkBox_energy,
                self.ui.checkBox_enthalpy,
            ],
            2: [self.ui.checkBox_solvation],
            3: [self.ui.checkBox_big],
        }

        box_labels = {
            self.ui.checkBox_main: "main",
            self.ui.checkBox_big: "big",
            self.ui.checkBox_solvation: "solv",
            self.ui.checkBox_gibbs: "%sG" % cf.unicode_symbols["Delta"],
            self.ui.checkBox_energy: "%sE" % cf.unicode_symbols["Delta"],
            self.ui.checkBox_enthalpy: "%sH" % cf.unicode_symbols["Delta"],
        }

        rel_keys = {
            self.ui.checkBox_main: "main",
            self.ui.checkBox_big: "big",
            self.ui.checkBox_solvation: "dSolv",
            self.ui.checkBox_gibbs: "dG",
            self.ui.checkBox_energy: "dE",
            self.ui.checkBox_enthalpy: "dH",
        }

        rel_ene = self.get_relative_energies()
        plots = list()
        legends = list()
        print(rel_ene)
        for i in sorted(boxes.keys()):
            for box in boxes[i]:
                if box.isChecked():
                    legends.append(box_labels[box])
                    energies = list()
                    term = rel_keys[box]
                    for state in rel_ene.keys():
                        ene = 0
                        if term in rel_ene[state].keys():
                            ene = rel_ene[state][term] * self.unit
                        energies.append(ene)
                    plots.append(energies)

        PlotEnergyDiagram(
            ene_array=plots,
            legends=legends,
            x_title="State",
            y_title="Relative Energy",
            plot_legend=True,
        )

    def has_energy_terms(self, term=0):
        """
        Check if all states have energy terms...
        0: main
        1: frequencies
        2: Solvent
        3: big basis
        :return: True/False list(states)
        """
        has_it = list()

        for state in sorted(self.energies.keys()):
            if not self.energies[state][term]:
                has_it.append(False)
            else:
                has_it.append(True)

        return has_it

    @property
    def has_main(self):
        """
        Check if all states have frequencies...
        :return: True/False
        """
        return self.has_energy_terms(0)

    @property
    def has_frequencies(self):
        """
        Check if all states have frequencies...
        :return: True/False
        """
        return self.has_energy_terms(1)

    @property
    def has_solvation(self):
        """
        Check if all states have solvation ....
        :return: True/False
        """
        return self.has_energy_terms(2)

    @property
    def has_big_basis(self):
        """
        Check if all states have big basis correction ....
        :return: True/False
        """
        return self.has_energy_terms(3)

    @property
    def get_freq_file(self):
        """
        :return: path to frequency file of currently active state
        """
        return str(self.react.included_files[self.react.get_current_state][1])

    def plot_frequency(self):
        """
        :return:
        """
        state = self.react.get_current_state
        if self.energies[state][1]:
            # TODO Bente, states should probably use the actual state number, not the tab index?
            frequencies = self.react.states[state - 1].get_frequencies(
                self.get_freq_file
            )
            freq = list()
            inten = list()
            for x in sorted(frequencies.keys()):
                freq.append(x)
                inten.append(frequencies[x])
            plot = SpectrumIR(freq, inten)

    def set_file_included(self):
        """
        Add file from main window to included_files and update list
        :return:
        """
        insert_index = self.ui.calctype.currentRow()
        filepath = self.react.get_selected_filepath
        state = self.react.get_current_state

        # Check if file is an output file (Gaussian or ORCA)
        file_obj = self.react.states[state - 1].files.get(filepath)
        if not isinstance(file_obj, (OutputFile, ORCAOutputFile)):
            self.react.append_text(
                "File must be a computational chemistry output file (.out or .log)"
            )
            return

        # Check if file is what it is supposed to be:
        if insert_index == 1:
            if not self.react.states[state - 1].has_frequencies(filepath):
                self.react.append_text("\nNo frequencies found in %s" % filepath)
                return
        elif insert_index == 2:
            if not self.react.states[state - 1].has_solvent(filepath):
                self.react.append_text("\nNo solvent found in %s" % filepath)
                return

        # If no main file is set, automatically set the added file also as main:
        if insert_index != 0 and self.react.included_files[state][0] == "":
            self.react.included_files[state][0] = filepath

        self.react.included_files[state][insert_index] = filepath
        self.update_state_included_files()

    def remove_file_included(self):
        """
        Remove file from included_files and update list
        :return:
        """
        remove_index = self.ui.calctype.currentRow()
        state = self.react.tabWidget.currentIndex() + 1
        self.react.included_files[state][remove_index] = ""

        self.update_state_included_files()

    def closeEvent(self, event):
        """
        When closing window, set to analyse_window to None, so that window can be reopened again later.
        :param event:
        """
        self.react.analyse_window = None
        self.react.tabWidget.tabBar().setMovable(True)
        self.react.tabWidget.tabBar().currentChanged.disconnect(
            self.update_state_included_files
        )
        if self.pymol:
            self.pymol.pymol_cmd("mstop")

            # TODO delete frequency animation.. a bit risky to do delete w_* ... figure out a safer delete.
            self.pymol.pymol_cmd("delete w_*")
