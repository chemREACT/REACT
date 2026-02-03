from PyQt5 import QtWidgets
import os
import time
import sys
import mods.common_functions as cf
from mods.ReactPlot import PlotEnergyDiagram
from mods.Plotter import Plotter
from mods.GlobalSettings import GlobalSettings
from mods.AnalyseCalc import AnalyseCalc
from mods.DialogsAndExceptions import DialogMessage, DialogSaveProject
from mods.FileEditor import FileEditor
from mods.PDBModel import ModelPDB


class PrintPlotOpen:
    """
    Defines the print/plot/open methods developed to be used by the MainWindow
    class. Will most likely throw errors left and right if called by any other
    classes than MainWindow!
    """

    def import_files(
        self, title_="Import files", filter_type="Any files (*.*)", path=os.getcwd()
    ):
        """
        Opens file dialog where multiple files can be selected.
        Return: files_ --> list of files (absolute path)
        Return: files_type --> string with the chosen filter_type
        """
        #  DontUseNativeDialog is required on Linux to avoid crashes
        if sys.platform == "linux":
            files_, files_type = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                title_,
                path,
                filter_type,
                options=QtWidgets.QFileDialog.DontUseNativeDialog,
            )
        else:
            files_, files_type = QtWidgets.QFileDialog.getOpenFileNames(
                self, title_, path, filter_type
            )

        return files_, files_type

    def append_text(self, text=str(), date_time=False):
        """
        :param text: text to be printed in ain window textBrowser
        :return:
        """
        if date_time:
            text = "\n%s\n%s" % (time.asctime(time.localtime(time.time())), text)
        self.textBrowser.appendPlainText(text)
        self.textBrowser.verticalScrollBar().setValue(
            self.textBrowser.verticalScrollBar().maximum()
        )

    def print_energy(self):
        """
        Takes the selected file and prints the final ENERGY (SCF Done) in hartree and kcal/mol.
        :return:
        """
        filepath = self.tabWidget.currentWidget().currentItem().text()
        filename = filepath.split("/")[-1]

        if filename.split(".")[-1] not in ["out", "log"]:
            self.append_text(
                "%s does not seem to be a Gaussian output file." % filename
            )
            return

        # this file --> State
        state_energy = self.states[self.tabWidget.currentIndex()].get_energy(filepath)
        # energy_kcal = superfile.connvert_to_kcal(energy_au) TODO ?

        energy_kcal = cf.hartree_to_kcal(state_energy)

        self.append_text("\nFinal energy of %s:" % filename)
        self.append_text("%f a.u" % state_energy)
        self.append_text("%.4f kcal/mol" % energy_kcal)

    def get_relative_energies(self):
        """
        :return: energies dict[state] = "dE": float, "file":path
        """
        energies = list()
        d_energies = dict()

        for tab_index in range(self.tabWidget.count()):
            if self.tabWidget.widget(tab_index).currentItem():
                file_path = self.tabWidget.widget(tab_index).currentItem().text()
                if file_path.split(".")[-1] in ["out", "log"]:
                    energies.append(self.states[tab_index].get_energy(file_path))
                    d_energies[tab_index + 1] = {
                        "dE": energies[tab_index] - energies[0],
                        "file": file_path,
                    }

                else:
                    self.append_text(
                        "%s does not seem to be Gaussian output" % file_path
                    )
            else:
                self.append_text("No files selected for state %d" % (tab_index + 1))

        return d_energies

    def print_relative_energy(self):
        """
        calculates the relative energy (to state 1) for all states and prints it in the log window
        :return:
        """
        self.append_text("Relative energies", date_time=True)

        d_energies = self.get_relative_energies()

        for state in sorted(d_energies.keys()):
            self.append_text(
                "%sE(%d): %.4f kcal/mol (%s)"
                % (
                    cf.unicode_symbols["Delta"],
                    state,
                    cf.hartree_to_kcal(d_energies[state]["dE"]),
                    d_energies[state]["file"].split("/")[-1],
                )
            )

    def plot_energy_diagram(self):
        """
        :return:
        """
        d_ene = self.get_relative_energies()

        # Convert d_ene dict to list of energies in kcal/mol
        d_ene = [cf.hartree_to_kcal(d_ene[x]["dE"]) for x in sorted(d_ene.keys())]

        plot = PlotEnergyDiagram(
            d_ene, x_title="State", y_title="Relative energy", plot_legend=False
        )

    def open_settings(self):
        if self.settings_window:
            self.append_text(
                "\nSettings window is already running.\nPerhaps the window is hidden?"
            )
            self.settings_window.raise_()
        else:
            self.settings_window = GlobalSettings(self)
            self.settings_window.show()

    def open_analyse(self):
        """

        :return:
        """
        if self.analyse_window:
            self.append_text(
                "\nAnalyse Calculation is already running. \nPerhaps the window is hidden?"
            )
            self.analyse_window.raise_()
            return

        if not self.tabWidget.currentWidget().currentItem() and not self.included_files:
            self.append_text("\n Nothing to analyse here ...")
            return
        self.analyse_window = AnalyseCalc(self)
        self.analyse_window.show()

    def create_cluster(self):
        """ """
        # dialog = DialogMessage(self, "Create Cluster not yet available:(")
        # dialog.exec_()
        if self.cluster_window:
            self.cluster_window.raise_()
        else:
            self.cluster_window = ModelPDB(self)
            self.cluster_window.show()

    def open_plotter(self):
        """

        :return:
        """

        self.plotter = Plotter(self)
        self.plotter.show()

    def open_editfile(self):
        """

        :return:
        """
        if not self.tabWidget.currentWidget().currentItem():
            self.append_text("\n No file selected for editing!")
            return

        filepath = self.tabWidget.currentWidget().currentItem().text()

        editor = FileEditor(self, filepath)
        editor.show()
