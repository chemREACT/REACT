import sys
import os
import json
import time
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThreadPool, QTimer, pyqtSlot
from mods.SplashScreen import SplashScreen
import UIs.icons_rc
import mods.common_functions as cf
from UIs.MainWindow import Ui_MainWindow
from mods.ReactWidgets import DragDropListWidget
from mods.State import State
from mods.DialogsAndExceptions import DialogSaveProject
from mods.CalcSetupWindow import CalcSetupWindow
from mods.ReactPlot import PlotEnergyDiagram
from mods.Plotter import Plotter
from mods.Settings import Settings, SettingsTheWindow
from mods.AnalyseCalc import AnalyseCalc
from mods.FileEditor import FileEditor
from mods.PDBModel import ModelPDB
from mods.ThreadWorkers import Worker
from threading import Lock
from mods.PymolProcess import PymolSession
from mods.ReactPlot import PlotGdata


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowTitle("REACT - Main")

        self.react_path = os.getcwd()
        # It is not a good idea to have the settings file inside the software itself
        # self.settings = Settings(parent=self, settingspath=f"{self.react_path}/.custom_settings.json")
        self.settings = Settings(
            parent=self, settingspath=f"{os.path.expanduser('~')}/.custom_settings.json"
        )
        self.states = []
        self.proj_name = "new_project"

        self.pymol = None

        # bool to keep track of unsaved changes to project.
        self.unsaved_proj = False

        # { state (int): main: path, frequency: path, solvation: path, big basis: path }
        self.included_files = None

        # Analyse window active or not:
        self.analyse_window = None

        # Create PDB cluster window active or not
        self.cluster_window = None

        # Bool allows only one instance of settings/calc setup window at the time.
        self.settings_window = None
        self.setup_window = None

        self.add_state()

        self.tabWidget.tabBar().tabMoved.connect(self.update_tab_names)
        self.tabWidget.currentWidget().itemClicked.connect(self.change_pymol_structure)

        # MainWindow Buttons with methods:
        self.button_add_state.clicked.connect(self.add_state)
        self.button_delete_state.clicked.connect(self.delete_state)
        self.button_add_file.clicked.connect(self.add_files)
        self.button_delete_file.clicked.connect(self.delete_file)
        self.button_edit_file.clicked.connect(self.open_editfile)
        self.button_analyse_calc.clicked.connect(self.open_analyse)
        self.button_settings.clicked.connect(self.open_settings)
        self.button_print_energy.clicked.connect(self.print_energy)
        self.button_print_scf.clicked.connect(self.plot_scf)
        self.button_print_relativeE.clicked.connect(self.print_relative_energy)
        self.button_plot_ene_diagram.clicked.connect(self.plot_energy_diagram)
        self.button_save_project.clicked.connect(self.save_project)
        self.button_open_project.clicked.connect(self.import_project)
        self.button_create_cluster.clicked.connect(self.create_cluster)
        self.button_plotter.clicked.connect(self.open_plotter)
        self.button_power_off.clicked.connect(self.power_off_on)
        self.button_pymol.clicked.connect(self.start_pymol)
        self.button_calc_setup.clicked.connect(self.open_calc_setup)

        self.power = True

        # Print welcome
        self.append_text("Welcome to REACT", True)

        # Set progressbar to full:
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progressbar)
        self.update_progressbar(100)

        # Threads for jobs take take time:
        self.threadpool = QThreadPool()

        # SPLASH
        self.splash = SplashScreen(self)
        self.splash.show()

        # PyQt5.QtCore.QRect(0, 0, 5120, 1440)
        screen_size = self.screen().availableGeometry()
        window_size = self.geometry()
        self.move(int(((screen_size.width() - window_size.width()) / 2)), 50)

        # TODO put this some place in the UI bottom ?
        self.append_text(
            "\nMultithreading with\nmaximum %d threads"
            % self.threadpool.maxThreadCount()
        )

    def _find_pymol_executable(self):
        """
        Find PyMOL executable from system PATH or known installation locations
        :return: path to pymol executable or None
        """
        import shutil

        # Try to find pymol in PATH
        pymol_exe = shutil.which("pymol")
        if pymol_exe:
            return pymol_exe

        # Platform-specific fallback locations
        if sys.platform == "darwin":  # macOS
            common_paths = [
                "/Applications/PyMOL.app/Contents/MacOS/pymol",
                os.path.expanduser("~/Applications/PyMOL.app/Contents/MacOS/pymol"),
                "/usr/local/bin/pymol",
            ]
        elif sys.platform == "linux":
            common_paths = [
                "/usr/bin/pymol",
                "/usr/local/bin/pymol",
            ]
        elif sys.platform == "win32":
            common_paths = [
                "C:\\Program Files\\PyMOL\\PyMOL.exe",
                "C:\\Program Files (x86)\\PyMOL\\PyMOL.exe",
            ]
        else:
            common_paths = []

        for path in common_paths:
            if os.path.isfile(path):
                return path

        return None

    def start_pymol(self, return_session=False):
        """
        Starts pymol sync to REACT
        :return_session: return the pymol session link
        :return: session (if return_session = True)
        """
        if self.pymol:
            self.pymol.close()
            return

        pymol_path = None

        # First, try user-configured PyMOL path from settings
        if self.settings.pymolpath:
            pymol_path = self.settings.pymolpath
            if not os.path.isfile(pymol_path) and not os.path.isfile(
                f"{pymol_path}/Contents/MacOS/pymol"
            ):
                self.append_text(f"Configured PyMOL not found at: {pymol_path}")
                pymol_path = None

        # If no user path, try to find PyMOL from environment/installation
        if not pymol_path:
            pymol_path = self._find_pymol_executable()

        if not pymol_path:
            self.append_text(
                "PyMOL not found. Please install pymol-open-source: pip install pymol-open-source"
            )
            self.append_text("Or configure PyMOL path in settings.")
            return

        self.pymol = PymolSession(parent=self, home=self, pymol_path=pymol_path)

        if return_session:
            return self.pymol

        self.tabWidget.tabBar().currentChanged.connect(self.pymol_view_current_state)
        self.connect_pymol_structures(connect=True)

        self.pymol.pymol_cmd("group state_%d" % 1)
        self.load_all_states_pymol()

        self.pymol.importSavedPDB.connect(self.pdb_from_pymol)

    def connect_pymol_structures(self, connect=True):
        """
        Connect clicks in QListWidget to structure displayed in pymol
        :param connect: bool
        :return:
        """
        # on_off = {True:}
        for state in range(self.count_states):
            if connect:
                self.tabWidget.widget(state).itemClicked.connect(
                    self.change_pymol_structure
                )
            else:
                self.tabWidget.widget(state).itemClicked.disconnect(
                    self.change_pymol_structure
                )

    def pymol_view_current_state(self):
        """
        :return:
        """
        if not self.pymol:
            return
        state = self.get_current_state
        name = None
        if self.get_selected_filepath:
            name_split = self.get_selected_filepath.split("/")[-1].split(".")
            name = name_split[0] + "_" + name_split[-1]

        self.pymol.pymol_cmd("group state_%d, toggle, open" % state)
        for i in range(1, self.count_states + 1):
            if i != state:
                self.pymol.pymol_cmd("group state_%d, toggle, close" % i)
                self.pymol.pymol_cmd("disable state_%d" % i)
        self.pymol.highlight(name=name, group="state_%d" % state)

    def file_to_pymol(self, filepath, state=1, set_defaults=True):
        """
        Takes any file and opens it in pymol
        :param filepath: path to file
        :param state: integer for state
        :param set_defaults: fix pymol representation
        :return:
        """

        try:
            mol_obj = self.states[state - 1].get_molecule_object(filepath)
        except AttributeError:
            self.append_text("Make sure you have selected a file to display in Pymol")

        try:
            if mol_obj.faulty or not mol_obj:
                return
        except AttributeError:
            return

        if not self.pymol:
            return

        delete_after = True
        if filepath.split(".")[-1] not in ["xyz", "pdb"]:
            xyz = self.states[state - 1].get_final_xyz(filepath)
            filename = filepath.split("/")[-1]
            new_filename = "_".join(filename.split("."))
            new_filepath = f"{self.settings.workdir}/{new_filename}.xyz"
            cf.write_file(xyz, new_filepath)
        else:
            old_filename = filepath.split("/")[-1]
            new_filename = "_".join(old_filename.split("."))
            new_filepath = (
                f"{self.settings.workdir}/{new_filename}.{old_filename.split('.')[-1]}"
            )
            os.popen(f"cp {filepath} {new_filepath}")

        self.pymol.load_structure(new_filepath, delete_after=delete_after)
        self.pymol.pymol_cmd(
            "group state_%d, %s" % (state, new_filepath.split("/")[-1].split(".")[0])
        )

        if set_defaults:
            self.pymol.set_default_rep()
            self.pymol.pymol_cmd(
                "enable state_%d and %s"
                % (state, new_filepath.split("/")[-1].split(".")[0])
            )

    def load_all_states_pymol(self):
        """
        Loads all files from project table to pymol
        :return:
        """
        if not self.pymol:
            return

        for i in range(len(self.states)):
            state = i + 1
            for filepath in self.states[i].get_all_paths:
                self.file_to_pymol(filepath, state, set_defaults=False)
            self.pymol.pymol_cmd(f"group state_{state}")

        self.pymol.set_default_rep()

        state = self.get_current_state
        self.pymol.pymol_cmd("group state_%d, toggle, open" % state)
        self.pymol.pymol_cmd("disable *")
        sel_file = self.get_selected_filepath
        if sel_file:
            self.pymol.pymol_cmd(
                "enable state_%d and %s"
                % (state, sel_file.split("/")[-1].split(".")[0])
            )

    def load_scf_geometries(self):
        """
        Creates pymol object with all scf geometries
        :return:
        """
        state = self.get_current_state
        # filepath = self.get_selected_filepath

        mol_obj = self.states[self.state_index].get_molecule_object(
            self.get_selected_filepath
        )

        delete_after = True
        xyz_list = mol_obj.all_geometries_formatted

        del xyz_list[-1]
        i = 0
        base_path = "%s/%s" % (self.settings.workdir, mol_obj.molecule_name)

        for xyz in xyz_list:
            xyz_path = "%s_scf%03d.xyz" % (base_path, i)
            cf.write_file(xyz, xyz_path)
            self.pymol.load_structure(xyz_path, delete_after=delete_after)
            i += 1

        self.pymol.pymol_cmd("delete %s_scf" % base_path.split("/")[-1].split(".")[0])
        self.pymol.pymol_cmd(
            "join_states %s_scf, %s_scf*, 0"
            % (base_path.split("/")[-1].split(".")[0], base_path.split("/")[-1])
        )
        self.pymol.pymol_cmd(
            "group state_%d, %s_scf" % (state, base_path.split("/")[-1].split(".")[0])
        )

        for j in range(0, i + 1):
            self.pymol.pymol_cmd("delete %s_scf%03d*" % (base_path.split("/")[-1], j))

        self.pymol.set_default_rep()
        self.pymol.pymol_cmd("disable *")
        self.pymol.pymol_cmd(
            "enable state_%d and %s_scf"
            % (state, base_path.split("/")[-1].split(".")[0])
        )

    def change_pymol_structure(self):
        """
        displayes clicked entry in pymol
        :return:
        """
        if not self.pymol:
            return
        group = "state_%d" % self.get_current_state
        name_split = self.get_selected_filepath.split("/")[-1].split(".")
        name = name_split[0] + "_" + name_split[-1]
        self.pymol.highlight(name=name, group=group)

    def plot_scf(self):
        """
        Takes the selected file and prints the 4 Convergence criterias.
        :return:
        """
        mol_obj = self.states[self.state_index].get_molecule_object(
            self.tabWidget.currentWidget().currentItem().text()
        )

        if mol_obj.faulty:
            self.append_text("ERROR: not possible for broken file!")
            return

        try:
            filepath = self.tabWidget.currentWidget().currentItem().text()
        except:
            return

        # Can not plot? :
        if filepath.split(".")[-1] not in ["out", "log"]:
            return

        # Sync with pymol
        if self.pymol:
            self.load_scf_geometries()

        filename = filepath.split("/")[-1]

        scf_data = self.states[self.tabWidget.currentIndex()].get_scf(filepath)

        # Check if this is geometry optimization or not (None if not):
        converged = self.states[self.tabWidget.currentIndex()].check_convergence(
            filepath
        )
        plot = PlotGdata(self, scf_data, filename)

        if converged is None:
            plot.plot_scf_done()
            self.append_text("%s seem to not be a geometry optimisation ..." % filename)
        else:
            plot.plot_scf_convergence()
            if converged is False:
                self.append_text("%s has not converged successfully." % filename)

    def add_file(self, filepath):
        """
        Adds only one file.
        """
        self.states[self.state_index].add_file(filepath)

        items_insert_index = self.tabWidget.currentWidget().count()
        self.tabWidget.currentWidget().insertItem(items_insert_index, filepath)
        self.check_convergence(
            filepath, items_insert_index, self.tabWidget.currentIndex()
        )

        if self.pymol:
            self.file_to_pymol(
                filepath=filepath, state=self.get_current_state, set_defaults=True
            )

    def add_files(self, paths=False):
        """
        Adds filenames via self.import_files (QFileDialog) to current QtabWidget tab QListWidget and selected state.
        TODO: need to check if files exist in list from before! If file exist,
        delete old and add again, since the user might have edited the file
        outside the app or using FileEditorWindow.
        """
        # Add state tab if not any exists...
        if self.tabWidget.currentIndex() < 0:
            self.append_text(
                "No states exist - files must be assigned to a state.", True
            )
            self.append_text("Auto-creating state 1 - files will be added there")
            self.add_state()

        # path = os.getcwd()  # wordkdir TODO set this as global at some point
        path = self.settings.workdir
        filter_type = (
            "Gaussian output files (*.out);; Gaussian input files (*.com *.inp);; "
            "Geometry files (*.pdb *.xyz)"
        )
        title_ = "Import File"

        if isinstance(paths, list):
            files_path = paths
        else:
            files_path, type_ = self.import_files(title_, filter_type, path)

        if len(files_path) < 1:
            return

        # Remove file types not accepted by REACT
        accepted_files = ["inp", "com", "out", "xyz", "pdb"]
        files_path = [x for x in files_path if x.split(".")[-1] in accepted_files]

        # Where to start inserting files in project list:
        items_insert_index = self.tabWidget.currentWidget().count()

        # Start thread first:
        worker = Worker(self.thread_add_files, files_path, items_insert_index)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)
        self.timer.start(10)

        # Insert files/filenames to project table:
        for file in files_path:
            self.tabWidget.currentWidget().insertItem(items_insert_index, file)
            self.tabWidget.currentWidget().item(items_insert_index).setForeground(
                QtGui.QColor(80, 80, 80)
            )
            items_insert_index += 1

        # Move horizontall scrollbar according to text
        self.tabWidget.currentWidget().repaint()
        scrollbar = self.tabWidget.currentWidget().horizontalScrollBar()
        scrollbar.setValue(
            self.tabWidget.currentWidget().horizontalScrollBar().maximum()
        )

    def thread_add_files(
        self, file_paths, item_index, progress_callback, results_callback
    ):
        """
        :param file_paths:
        :param item_index: index where to start insertion of files in list
        :param progress_callback:
        :return:
        """
        # set progressbar to 1:
        self.update_progressbar(1)
        pymol_defaults = False
        for n in range(len(file_paths)):
            file = file_paths[n]
            self.states[self.state_index].add_file(file)
            if n == len(file_paths) - 1:
                pymol_defaults = True
            progress_callback.emit(
                {
                    self.update_progressbar: ((int(n + 1) * 100 / len(file_paths)),),
                    self.check_convergence: (
                        file,
                        item_index,
                        self.tabWidget.currentIndex(),
                    ),
                    self.file_to_pymol: (file, self.get_current_state, pymol_defaults),
                }
            )
            item_index += 1

        return "Done"

    def progress_fn(self, progress_stuff):
        """
        :param progress_stuff: {function : arguments}
        :return:
        """
        for func in progress_stuff.keys():
            args = progress_stuff[func]
            func(*args)

    def update_progressbar(self, val=None, reverse=False):
        """
        :param val:
        :return:
        """
        with Lock():
            if not val:
                val = self.progressBar.value()
                if reverse:
                    val -= 1
                else:
                    val += 1
                if val > 80:
                    self.timer.setInterval(50)
                else:
                    self.timer.setInterval(10)

            if val < 100:
                self.progressBar.setTextVisible(True)

            if not reverse and val > 99:
                self.progressBar.setTextVisible(False)
                self.timer.stop()
            elif reverse and val < 1:
                self.timer2.stop()
                sys.exit()

            self.progressBar.setValue(int(val))

    def thread_complete(self):
        pass

        # if self.pymol:
        #    self.file_to_pymol(filepath=file, state=self.get_current_state, set_defaults=True)

    def check_convergence(self, file_path, item_index, tab_index=None):
        if tab_index is None:
            tab_index = self.tabWidget.currentIndex()
            tab_widget = self.tabWidget.currentWidget()
        else:
            tab_widget = self.tabWidget.widget(tab_index)

        mol_obj = self.states[tab_index].get_molecule_object(filepath=file_path)
        if mol_obj.faulty:
            tab_widget.item(item_index).setForeground(QtGui.QColor(195, 82, 52))
            self.append_text("\nERROR: %s seems to have faulty..." % mol_obj.filename)
            return

        if mol_obj.file_extension not in ["out", "log"]:
            tab_widget.item(item_index).setForeground(QtGui.QColor(98, 114, 164))
        else:
            converged = mol_obj.converged

            if isinstance(converged, bool) and not converged:
                tab_widget.item(item_index).setForeground(QtGui.QColor(195, 82, 52))
                self.append_text(
                    "\nWarning: %s seems to have not converged!" % mol_obj.filename
                )
            elif isinstance(converged, bool) and converged:
                tab_widget.item(item_index).setForeground(QtGui.QColor(117, 180, 104))
            elif not isinstance(converged, bool):
                tab_widget.item(item_index).setForeground(QtGui.QColor(117, 180, 104))

    def delete_file(self):
        """
        Deletes selected file(s) from QtabBarWidget-->Tab-->QListWdget-->item
        :return:
        """
        # Avoid crash when no tabs exist
        if self.tabWidget.currentIndex() < 0:
            return

        # avoid crash when no files exist in state:
        if self.tabWidget.currentWidget().count() < 1:
            return

        # Get the list displayed in the current tab (state)
        current_list = self.tabWidget.currentWidget()

        # Get the selected item(s) ---> returns a list of objects
        list_items = current_list.selectedItems()

        # delete files from state
        tab_index = self.tabWidget.currentIndex()
        self.states[tab_index].del_files([x.text() for x in list_items])

        # delete files from pymol
        if self.pymol:
            state = self.get_current_state
            [
                self.pymol.pymol_cmd(
                    "delete %s"
                    % (
                        x.text().split("/")[-1].split(".")[0]
                        + "_"
                        + x.text().split("/")[-1].split(".")[-1]
                    )
                )
                for x in list_items
            ]

        # Remove selected items from list:
        for item in list_items:
            current_list.takeItem(current_list.row(item))

            # Remove from included_files if existing:
            try:
                if self.included_files:
                    for type_ in self.included_files[tab_index + 1].keys():
                        if item.text() == self.included_files[tab_index + 1][type_]:
                            self.included_files[tab_index + 1][type_] = ""
                            # Update analyse window, if active:
                            if self.analyse_window:
                                self.analyse_window.update_state_included_files()
            except KeyError:
                pass

    def update_tab_names(self):
        """
        Changes the order of states in self.states according to the order of tabs in the tabBar widget.
        """

        try:
            new_states = []
            new_included_files = dict()

            for tab_index in range(len(self.states)):
                state = self.tabWidget.tabText(tab_index)
                new_states.append(self.states[int(state) - 1])
                if state != str(tab_index + 1):
                    self.tabWidget.setTabText(tab_index, str(tab_index + 1))
                    # swap values of state and tab_index+1
                    if self.included_files:
                        new_included_files[int(state)] = self.included_files[
                            tab_index + 1
                        ]

                else:
                    if self.included_files:
                        new_included_files[int(state)] = self.included_files[int(state)]

            self.states = new_states
            self.included_files = new_included_files

            if self.pymol:
                self.pymol.pymol_cmd("delete state_*")
                QTimer.singleShot(100, self.load_all_states_pymol)
        except KeyError:
            if self.analyse_window:
                self.analyse_window.init_included_files()

    def add_state(self):
        """
        Add state (new tab) to tabBar widget with a ListWidget child.
        """
        self.states.append(State(self))

        # new state:
        state = self.count_states + 1
        self.tabWidget.addTab(DragDropListWidget(self), f"{state}")
        self.tabWidget.setCurrentWidget(self.tabWidget.widget(state - 1))
        if self.pymol:
            self.pymol.pymol_cmd("group state_%d" % state)
            self.tabWidget.widget(state - 1).itemClicked.connect(
                self.change_pymol_structure
            )

    def set_state(self, state):
        """
        Set tab to be displayed
        :param state: integer
        :return:
        """
        if int(state) <= self.count_states:
            self.tabWidget.setCurrentWidget(self.tabWidget.widget(state - 1))

    def delete_state(self):
        """
        Deletes current state (tab) from tabBar widget together with QListWidget child.
        """
        tab_index = self.tabWidget.currentIndex()
        state = tab_index + 1

        # Avoid crash when there are not tabs
        if tab_index < 0:
            return

        # Delete from self.included_files
        if self.included_files:
            self.included_files[state] = {0: "", 1: "", 2: "", 3: ""}
            if self.analyse_window:
                self.analyse_window.update_state_included_files()

        self.tabWidget.widget(tab_index).deleteLater()
        self.states.pop(tab_index)

        # This is important here:
        QTimer.singleShot(100, self.update_tab_names)

        if self.pymol:
            self.pymol.pymol_cmd("delete state_%s" % str(state))

    def create_input_content(self, filepath):
        """
        :return: string -> content of new input file, based on outputfile given as argument
        """
        return self.states[self.tabWidget.currentIndex()].create_input_content(filepath)

    def create_xyz_filecontent(self, filepath):
        return self.states[self.tabWidget.currentIndex()].create_xyz_filecontent(
            filepath
        )

    def import_project(self):
        """
        Import project-file and creates new state instances accordingly.
        """
        proj_path, type_ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import project", self.settings.workdir, filter="Project (*.rxt)"
        )

        # To avoid error if dialogwindow is opened, but no file is selected
        if proj_path == "":
            return

        if self.unsaved_proj:
            # TODO set self.unsaved_proj = True when approriate
            # when Save is clicked: signal = 1, else signal = 0.
            # TODO save project when signal == 1, else: discard project
            dialog = DialogSaveProject(self)
            signal = dialog.exec_()

        # delete states currently in workspace
        self.states.clear()
        self.tabWidget.clear()
        self.textBrowser.clear()
        if self.pymol:
            self.pymol.pymol_cmd("delete *")

        self.proj_name = proj_path.split("/")[-1]
        self.label_projectname.setText(self.proj_name.replace(".rxt", ""))

        with open(proj_path, "r") as proj_file:
            proj = json.load(proj_file, object_hook=cf.json_hook_int_bool_converter)

        for key in ["states", "included files", "workdir", "log"]:
            self._import_project_pop_and_assign(proj, key)

    def _import_project_pop_and_assign(self, project, key):
        try:
            proj_item = project.pop(key)

            if key == "states":
                for state in proj_item.items():
                    self.add_state()
                    # self.add_files(state[1])

                    # each state has to be completely loaded before moving on to text,
                    # to ensure the multithreading assigns files to correct state.
                    # self.threadpool.waitForDone()
                    for file in state[1]:
                        self.add_file(file)

            if key == "included files":
                self.included_files = proj_item
            if key == "log":
                self.textBrowser.appendPlainText(proj_item)
            elif key == "workdir":
                self.settings.workdir = proj_item
        except:
            self.append_text(f'Failed to load "{key}" from "{self.proj_name}"')

    def save_project(self):
        """
        exports a *.rxt (identical to JSON) file containing:
        project = {'states'        : {1: [file1,file2,..],
                                      2: [file1,file2,..]
                                      },
                   'included files': self.included_files,
                   'workdir'      : self.settings.workdir
                   'log'           : self.textBrowser.toPlainText()
                   }
        """
        project = {}
        states = {}

        self.append_text(
            "\nREACT project last saved: %s\n"
            % (time.asctime(time.localtime(time.time())))
        )

        for index in range(len(self.states)):
            states[index + 1] = self.states[index].get_all_paths

        project["states"] = states
        project["included files"] = self.included_files
        project["workdir"] = self.settings.workdir
        project["log"] = self.textBrowser.toPlainText()

        temp_filepath = self.settings.workdir + "/" + self.proj_name

        proj_path, filter_ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save project", temp_filepath, "REACT project (*.rxt)"
        )

        if proj_path == "":
            return

        self.proj_name = proj_path.split("/")[-1]

        # change project name title in workspace
        new_proj_title = proj_path.split("/")[-1].replace(".rxt", "")
        self.label_projectname.setText(new_proj_title)

        with open(proj_path, "w") as f:
            json.dump(project, f)

    def import_files(
        self, title_="Import files", filter_type="Any files (*.*)", path=os.getcwd()
    ):
        """
        Opens file dialog where multiple files can be selected.
        Return: files_ --> list of files (absolute path)
        Return: files_type --> string with the chosen filter_type
        """
        #  DontUseNativeDialog was planned removed - but it is required on linux... will crash elsewise.

        files_, files_type = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            title_,
            path,
            filter_type,
            options=QtWidgets.QFileDialog.DontUseNativeDialog,
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
        try:
            filepath = self.tabWidget.currentWidget().currentItem().text()
        except AttributeError:
            return

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
                    try:
                        energies.append(self.states[tab_index].get_energy(file_path))
                        d_energies[tab_index + 1] = {
                            "dE": energies[tab_index] - energies[0],
                            "file": file_path,
                        }
                    except IndexError:
                        self.append_text("Something went wrong with tab indexes...")

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
            self.settings_window = SettingsTheWindow(self)
            self.settings_window.show()

    def open_analyse(self):
        """

        :return:
        """

        if not self.tabWidget.currentWidget().currentItem():
            self.append_text(
                "\n Nothing to analyse here ... Make sure you have selected a file to analyse."
            )
            return

        try:
            mol_obj = self.states[self.state_index].get_molecule_object(
                self.tabWidget.currentWidget().currentItem().text()
            )
        except AttributeError:
            self.append_text("ERROR: something is wrong")
            return
        try:
            if mol_obj.faulty:
                self.append_text("ERROR: Analyse not possible for broken file!")
                return
        except AttributeError:
            print(self.states)
            print(self.included_files)
            return

        if self.analyse_window:
            self.append_text(
                "\nAnalyse Calculation is already running. \nPerhaps the window is hidden?"
            )
            self.analyse_window.raise_()
            return

        self.analyse_window = AnalyseCalc(self)
        self.analyse_window.show()

    def create_cluster(self):
        """ """

        try:
            mol_obj = self.states[self.state_index].get_molecule_object(
                self.tabWidget.currentWidget().currentItem().text()
            )
        except AttributeError:
            self.append_text(
                "ERROR: please select the geometry file to create a cluster from."
            )
            return

        if isinstance(mol_obj, bool):
            return

        if mol_obj.faulty:
            self.append_text("ERROR: Create cluster not possible for broken file!")
            return

        if not self.pymol:
            self.append_text(
                "\nINFO:\nPlease launch Pymol to use the Create cluster app.\n"
            )
            return
        if self.cluster_window:
            self.cluster_window.raise_()
        else:
            self.cluster_window = ModelPDB(self)
            self.cluster_window.show()

    @pyqtSlot(str)
    def pdb_from_pymol(self, pdb_path):
        if not self.cluster_window:
            return
        if self.cluster_window.ui.copy_to_project.isChecked():
            self.add_file(pdb_path)

    def open_plotter(self):
        """
        :return:
        """

        try:
            mol_obj = self.states[self.state_index].get_molecule_object(
                self.tabWidget.currentWidget().currentItem().text()
            )
        except AttributeError:
            pass
        # if mol_obj.faulty:
        #     self.append_text("ERROR: Plotter not possible for broken file!")
        #     return

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

    def open_calc_setup(self):
        if not self.tabWidget.currentWidget().currentItem():
            self.append_text(
                "\n No file selected - select a file to prepare calculation on"
            )
            return

        mol_obj = self.states[self.state_index].get_molecule_object(
            self.tabWidget.currentWidget().currentItem().text()
        )

        if mol_obj.faulty:
            self.append_text("ERROR: Calculation setup not possible for broken file!")
            return

        if self.setup_window:
            self.append_text(
                "\nSettup window is already running.\nPerhaps the window is hidden?"
            )
            self.setup_window.raise_()
        else:
            self.setup_window = CalcSetupWindow(self, self.current_file)
            self.setup_window.show()

    def power_off_on(self):
        """
        power down when power button is clicked
        :return:
        """
        if self.power:
            self.button_power_off.setIcon(QtGui.QIcon("resources/icons/power_off.png"))
            self.append_text("Powering down...", date_time=True)
            if self.pymol:
                self.pymol.close()
            self.power = False
            self.timer2 = QTimer()
            self.timer2.timeout.connect(lambda: self.update_progressbar(reverse=True))
            self.timer2.start(5)

        else:
            self.button_power_off.setIcon(QtGui.QIcon("resources/icons/power_on.png"))
            self.append_text("Powering down cancelled.")
            self.power = True

            self.timer2.stop()
            self.timer.start(5)

    @property
    def get_selected_filepath(self):
        """
        :return: path to selected file, str
        """
        try:
            return self.tabWidget.currentWidget().currentItem().text()
        except:
            return None

    @property
    def get_current_state(self):
        """
        :return: integer (state)
        """
        return self.tabWidget.currentIndex() + 1

    @property
    def curr_state(self):
        return self.states[self.state_index]

    @property
    def state_index(self):
        return self.tabWidget.currentIndex()

    @property
    def count_states(self):
        """
        :return: integer (total number of states)
        """
        return self.tabWidget.count()

    @property
    def current_file(self):
        """
        :return: current file (filepath, in text)
        """
        return self.tabWidget.currentWidget().currentItem().text()

    @property
    def workdir(self):
        """
        :return: self.settings.workdir
        """
        return self.settings.workdir

    def closeEvent(self, event):
        if self.pymol:
            try:
                # TODO this only partly works... QProcess: Destroyed while process ("OpenSourcePymol/dist/OpenSourcePymol.app") is still running.
                self.pymol.close()
            except:
                pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    # TODO transparent frameless main window? Maybe not, but maybe all the others?
    # window.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    # window.setAttribute(QtCore.Qt.WA_TranslucentBackground)
    app.exec()
