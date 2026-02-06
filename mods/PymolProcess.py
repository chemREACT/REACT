from PyQt5.QtCore import QProcess, Qt, pyqtSignal, pyqtSlot, QObject, QTimer
import os


class PymolSession(QObject):
    # Signal to be emitted when pymol returns stuff of interest to REACT
    atomsSelectedSignal = pyqtSignal(list)
    dihedralSignal = pyqtSignal(list)
    ntermResidues = pyqtSignal(list)
    ctermResidues = pyqtSignal(list)
    countAtomsSignal = pyqtSignal(dict)
    importSavedPDB = pyqtSignal(str)
    # atomClickedSignal = pyqtSignal(list)
    overallChargeSignal = pyqtSignal(str)
    # Signal for text messages to avoid cross-thread GUI calls
    textMessageSignal = pyqtSignal(str, bool)  # (message, date_time)
    # Signal to safely disconnect PyMOL from main thread
    disconnectSignal = pyqtSignal()
    # Signal when PyMOL process finishes
    pymolFinishedSignal = pyqtSignal()

    def __init__(self, parent=None, home=None, pymol_path=None):
        super(QObject, self).__init__(parent)
        self.parent = parent
        self.react = home
        self.pymol_path = pymol_path
        self.session = QProcess()
        self.session.setInputChannelMode(QProcess.ManagedInputChannel)
        self.session.setProcessChannelMode(QProcess.MergedChannels)

        # Connect Qprocess signals
        # Use QueuedConnection for frequently-emitting signals to avoid cross-thread issues on Linux
        # finished and stateChanged use AutoConnection since they emit infrequently and Qt handles threading
        self.session.finished.connect(self._on_process_finished)
        self.session.readyReadStandardOutput.connect(
            self.handle_stdout, Qt.QueuedConnection
        )
        self.session.stateChanged.connect(self._on_process_state_changed)

        # Delete file of loaded molecule after loading it:
        self.files_to_delete = list()

        # Handling standard output:
        self.atoms_selected = list()
        self.atom_count = dict()
        self.unbonded = 0
        self.neg_charge = None
        self.pos_charge = None

        self.stdout_handler = {
            "iterate sele, ID": {
                "collect": False,
                "process": self.collect_iterate,
                "return": "iterated",
                "signal": self.return_sel_atomnr,
            },
            "iterate included, ID": {
                "collect": False,
                "process": self.collect_iterate,
                "return": "iterated",
                "signal": self.return_sel_atomnr,
            },
            "iterate nterm": {
                "collect": False,
                "process": self.collect_iterate,
                "return": "iterated",
                "signal": self.return_nterm,
            },
            "iterate cterm": {
                "collect": False,
                "process": self.collect_iterate,
                "return": "iterated",
                "signal": self.return_cterm,
            },
            "get_dihedral ": {
                "collect": False,
                "process": self.collect_dihedral,
                "return": "cmd.get_dihedral:",
                "signal": self.return_dihedral,
            },
            "count_atoms ": {
                "collect": False,
                "process": self.return_atom_count,
                "return": "count_atoms:",
                "signal": None,
            },
            "Save: wrote ": {
                "collect": False,
                "process": self.pdb_written,
                "return": "Save: wrote",
                "signal": None,
            },
            "Selector": {
                "collect": False,
                "process": self.print_selector,
                "return": "Selector",
                "signal": None,
            },
        }

        self.start_pymol()
        # Wait for PyMOL to be ready before sending commands
        QTimer.singleShot(1000, self.set_pymol_settings)

    def monitor_clicks(self):
        self.stdout_handler["You clicked "] = {
            "collect": False,
            "process": self.iterate_sele,
            "return": "You clicked ",
            "signal": None,
        }
        print("Now monitoring all pymol atom clicks!")

    def iterate_sele(self, stdout):
        """
        Iterates over selected atoms and get ID
        """
        self.pymol_cmd("iterate sele, ID")

    def unmonitor_clicks(self):
        del self.stdout_handler["You clicked "]

    def load_structure(self, file_=None, delete_after=False):
        """
        Load file in pymol
        :param file_: path to file (xyz, pdb, mae)
        """
        print("Loading structure", file_)
        if delete_after:
            # filename as displayed in pymol : filepath
            self.files_to_delete.append(file_)

        if not file_:
            print("PymolProcess load_structure - No file given")
            return

        # Extract object name from filename (without extension)
        import os

        object_name = os.path.basename(file_).rsplit(".", 1)[0]

        # Verify file exists
        if not os.path.exists(file_):
            print(f"ERROR: File does not exist: {file_}")
            return

        # Quote the file path and specify object name explicitly
        self.pymol_cmd('load "%s", %s' % (file_, object_name))
        print(f'PyMOL command: load "{file_}", {object_name}')

    def start_pymol(self, external_gui=False):
        startup = ["-p"]
        if not external_gui:
            startup.append("-x")
        self.session.start(self.pymol_path, startup)
        print(self.session.waitForStarted())
        self.session.isWindowType()

    def pymol_cmd(self, cmd=""):
        """
        Write standard pymol commands to pymol
        :param cmd: pymol command
        :return:
        """
        if not self.session or self.session.state() != QProcess.Running:
            return

        cmd += "\n"
        try:
            self.session.write(cmd.encode())
            # Wait briefly for bytes to be written, but don't block too long
            # Use a short timeout to avoid deadlocks on Linux
            self.session.waitForBytesWritten(30)
        except Exception as e:
            # If write fails, don't crash - just log it
            pass

    def set_pymol_settings(self):
        """
        :return:
        """
        if not self.session:
            return
        settings = [
            "space cmyk\n",
            "set stick_radius, 0.17\n",
            "set spec_power, 250\n",
            "set spec_reflect, 2\n",
        ]
        for setting in settings:
            self.pymol_cmd(setting)

    def set_default_rep(self):
        """
        :return:
        """
        print("setting defaults")
        self.pymol_cmd("hide spheres")
        self.pymol_cmd("show sticks")
        self.pymol_cmd("color grey, name C*")

    def set_protein_ligand_rep(self, residues, pymol_name, group):
        """
        :param name: pymol pdb name (internal)
        :param group: pymol group where pdb is located
        :param residues: residue names to highlight
        :return:
        """
        # makes sure solvent is not represented by sticks
        self.pymol_cmd("hide sticks, %s and %s and sol." % (group, pymol_name))
        self.pymol_cmd("show lines, %s and %s" % (group, pymol_name))

        sel_str = "resname %s" % residues.pop(0)

        if len(residues) > 0:
            sel_str += " or resname ".join(residues)

        self.pymol_cmd(
            "hide sticks, %s and %s and not %s" % (group, pymol_name, sel_str)
        )
        self.pymol_cmd("color gray, %s and %s and name C*" % (group, pymol_name))
        self.pymol_cmd(
            "color chartreuse, %s and %s and %s and name C*"
            % (group, pymol_name, sel_str)
        )
        self.pymol_cmd("zoom %s and %s and %s, 10" % (group, pymol_name, sel_str))

    def highlight_atoms(self, atoms=list, color=str, name=str, group=None):
        """
        :param atoms:
        :param color:
        :param name:
        :param group:
        :return:
        """
        cmd = str()
        if group:
            cmd += "%s and " % group
        self.pymol_cmd("hide sticks, %s %s" % (cmd, name))
        self.pymol_cmd("color grey, %s %s and name C*" % (cmd, name))
        selection = "(id %s)" % (" or id ".join(atoms))
        self.pymol_cmd("show sticks, %s%s " % (cmd, selection))
        self.pymol_cmd("color %s, name C* and %s%s" % (color, cmd, selection))

    def highlight(self, name=None, group=None):
        """
        :param name: name of structure to be highlighted
        :param group: name of group, if used
        :return:
        """
        self.pymol_cmd("disable *")
        if group:
            self.pymol_cmd("group %s, toggle, open" % group)

        # Build enable command only if we have valid name or group
        if name and group:
            self.pymol_cmd("enable %s or %s" % (group, name))
            self.pymol_cmd("zoom %s and %s" % (group, name))
        elif name:
            self.pymol_cmd("enable %s" % name)
            self.pymol_cmd("zoom %s" % name)
        elif group:
            self.pymol_cmd("enable %s" % group)
            self.pymol_cmd("zoom %s" % group)

    def set_selection(self, atoms, sele_name, object_name, group):
        """
        :param atoms: list of atom numbers
        :param sele_name: what to call selection (rather than (sele))
        :param object_name: What object to select from in pymol
        :param group: what group object belongs to
        :return:
        """
        self.pymol_cmd("delete %s" % sele_name)
        sel_str = "id "
        sel_str += " or id ".join([str(x) for x in atoms])
        self.pymol_cmd(
            "select %s, %s and %s and (%s)" % (sele_name, group, object_name, sel_str)
        )
        self.pymol_cmd("group %s, %s" % (group, sele_name))

    def expand_sele(
        self,
        selection="sele",
        sele_name="new",
        group="",
        radius=5,
        by_res=True,
        include_solv=True,
    ):
        """
        :param selection:
        :param radius: radius around selection to select
        :return:
        """
        self.pymol_cmd("delete %s" % sele_name)
        cmd = "select %s, " % sele_name
        if by_res:
            cmd += "byres "
        cmd += "%s around %s " % (selection, str(radius))
        if not include_solv:
            cmd += "and not sol."

        self.pymol_cmd(cmd)
        self.pymol_cmd("group %s, %s" % (group, sele_name))

    def get_selected_atoms(self, sele="sele", type="ID"):
        """
        Get PDB atom numbers/residue numbers of selection
        :return:
        """
        self.pymol_cmd("iterate %s, %s" % (sele, type))

    def get_dihedral(self, a1, a2, a3, a4):
        self.look_for_dihedral = True
        self.pymol_cmd("get_dihedral %s, %s, %s, %s" % (a1, a2, a3, a4))

    def set_dihedral(self, a1, a2, a3, a4, dihedral):
        self.pymol_cmd("set_dihedral %s, %s, %s, %s, %s" % (a1, a2, a3, a4, dihedral))
        self.pymol_cmd("unpick")

    def set_overall_charge(self):
        self.pymol_cmd("select negative_charge, visible and formal_charge < 0")
        QTimer.singleShot(500, lambda: None)
        self.pymol_cmd("select positive_charge, visible and formal_charge > 0")
        QTimer.singleShot(500, lambda: None)

    def add_fragment(self, attach_to, fragment):
        """

        :param attach_to: atom to attach fragment to
        :param fragment: type of fragment
        :return:
        """
        if fragment == "H":
            cmd = "h_add %s" % attach_to
        elif fragment == "methyl":
            if attach_to != "pk1":
                self.pymol_cmd("select sele, first sele")
                self.pymol_cmd("edit %s" % attach_to)
            cmd = "editor.attach_fragment('pk1', 'methane', 1, 0)"
        elif fragment in ["ace", "nme"]:
            cmd = "editor.attach_amino_acid('%s', '%s')" % (attach_to, fragment)
        else:
            return

        self.pymol_cmd(cmd)
        self.pymol_cmd("unpick")

    def find_unbonded(self, pymol_name, type="nterm", group=None):
        """
        Special function to locate atoms that potentially are missing bonds.
        :param pymol_name: object name in pymol
        :param type:
        :param group:
        :return:
        """
        selector = {
            "nterm": "and (elem n and (neighbor name CA and not neighbor name C))",
            "cterm": "and (elem C and (neighbor name O and not neighbor name N))",
        }

        cmd = "select %s, %s " % (type, pymol_name)
        if group:
            cmd += "and %s " % group
        cmd += selector[type]
        self.pymol_cmd(cmd)
        if group:
            self.pymol_cmd("group %s, %s" % (group, type))

    def copy_sele_to_object(self, sele="sele", target_name="new_obj", group=None):
        """
        :param sele:
        :param target_name:
        :param group:
        :return:
        """
        self.pymol_cmd("delete %s" % target_name)
        self.pymol_cmd("create %s, %s" % (target_name, sele))
        if group:
            self.pymol_cmd("group %s, %s" % (group, target_name))

    def _on_process_finished(self, exitCode, exitStatus):
        """Wrapper for QProcess.finished signal - handles the exit status enum"""
        self.pymol_finished()

    def pymol_finished(self):
        # Emit signal instead of direct attribute access to avoid cross-thread issues
        self.pymolFinishedSignal.emit()
        # Disable print to prevent recursive repaint on Linux
        # print("Pymol session completed")

    def _on_process_state_changed(self, state):
        """Wrapper for QProcess.stateChanged signal"""
        self.handle_state(state)

    def delete_all_files(self):
        """
        Iterates through self.delete_file and removes from disk
        :return:
        """
        for filename in self.files_to_delete:
            os.remove(filename)
        self.files_to_delete = list()

    def handle_stdout(self):
        """
        Reads output from Qprocess - this will be used to auto-decide handling REACT <--> Pymol
        :return:
        """
        data = self.session.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")

        # Only print for debugging errors, not all output (prevents repaint issues)
        # Uncomment next line for full PyMOL output debugging:
        # print(stdout)

        # Check for errors and print those
        if "Error:" in stdout or "ExecutiveLoad-Error:" in stdout:
            # Disable print to prevent recursive repaint on Linux
            # print(f"PyMOL Error detected: {stdout}")
            pass

        if "CmdLoad:" in stdout:
            if len(self.files_to_delete) > 0:
                try:
                    os.remove(self.files_to_delete.pop(0))
                except FileNotFoundError:
                    pass

        for k in self.stdout_handler.keys():
            if k in stdout:
                self.atoms_selected.clear()
                self.stdout_handler[k]["collect"] = True

        for k in self.stdout_handler.keys():
            if self.stdout_handler[k]["collect"]:
                self.stdout_handler[k]["process"](stdout)

                if self.stdout_handler[k]["return"] in stdout:
                    if self.stdout_handler[k]["signal"]:
                        self.stdout_handler[k]["signal"]()
                    self.stdout_handler[k]["collect"] = False

    def collect_iterate(self, stdout):
        """
        Read standard output from Qprocess pymol in the case of "iterate sele, rank" and collects atom numbers to
        self.atoms_selected
        :param stdout:
        :return:
        """
        for junk in stdout.split():
            for atomnr in junk.split("\n"):
                if atomnr.isnumeric():
                    self.atoms_selected.append(atomnr)
                elif "atoms" in atomnr and len(self.atoms_selected) > 0:
                    del self.atoms_selected[-1]

    def collect_dihedral(self, stdout):
        if "get_dihedral " in stdout:
            self.atoms_selected.extend(stdout.replace(",", "").split()[1:5])
        elif "cmd.get_dihedral:" in stdout:
            self.atoms_selected.append(stdout.split()[1])

    @pyqtSlot()
    def return_sel_atomnr(self):
        self.atomsSelectedSignal.emit(self.atoms_selected)

    @pyqtSlot()
    def return_dihedral(self):
        self.dihedralSignal.emit(self.atoms_selected)

    @pyqtSlot()
    def return_nterm(self):
        self.ntermResidues.emit(self.atoms_selected)

    @pyqtSlot()
    def return_cterm(self):
        self.ctermResidues.emit(self.atoms_selected)

    @pyqtSlot()
    def return_atom_count(self, stdout):
        if "count_atoms " in stdout:
            self.atom_count[" ".join(stdout.split()[1:])] = None
        elif "count_atoms:" in stdout:
            for k in self.atom_count.keys():
                if not self.atom_count[k]:
                    self.atom_count[k] = stdout.split()[1]
            self.countAtomsSignal.emit(self.atom_count)

    @pyqtSlot()
    def pdb_written(self, stdout):
        pdb_path = ""
        if "Save: wrote" in stdout:
            pdb_path = stdout.split('"')[1]

        self.importSavedPDB.emit(pdb_path)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: "Exited",
            QProcess.Starting: "Starting",
            QProcess.Running: "Running",
        }
        state_name = states[state]
        # Disable print to prevent recursive repaint on Linux
        # print(f"Pymol: {state_name}")
        # Use signal instead of direct GUI call to avoid cross-thread issues
        self.textMessageSignal.emit(f"Pymol: {state_name}", True)
        if state == QProcess.NotRunning:
            self.disconnect_pymol()

    def handle_stderr(self):
        data = self.session.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        print(stderr)

    def close(self):
        """
        Disconnect for a cleaner kill
        :return:
        """
        try:
            self.pymol_cmd("quit")
            self.session.kill()
            self.disconnect_pymol()
        except:
            pass

    def disconnect_pymol(self):
        # Emit signal to handle GUI disconnection in main thread
        self.disconnectSignal.emit()
        self.delete_all_files()

    def _do_disconnect_pymol(self):
        """Actual GUI disconnection - must be called from main thread"""
        try:
            self.react.tabWidget.tabBar().currentChanged.disconnect(
                self.react.pymol_view_current_state
            )
        except:
            pass  # May already be disconnected
        try:
            self.react.connect_pymol_structures(connect=False)
        except:
            pass

    @pyqtSlot()
    def print_selector(self, stdout):
        # Parse negative_charge atom count from Selector output
        if "negative_charge" in stdout and "defined with" in stdout:
            for line in stdout.split("\n"):
                if "negative_charge" in line and "defined with" in line:
                    try:
                        # Extract number between 'defined with' and 'atoms'
                        parts = line.split("defined with ")
                        if len(parts) > 1:
                            count_str = parts[1].split(" atoms")[0].strip()
                            self.neg_charge = int(count_str)
                            # print("got neg charge: ", self.neg_charge)
                    except (ValueError, IndexError):
                        pass

        # Parse positive_charge atom count from Selector output
        if "positive_charge" in stdout and "defined with" in stdout:
            for line in stdout.split("\n"):
                if "positive_charge" in line and "defined with" in line:
                    try:
                        # Extract number between 'defined with' and 'atoms'
                        parts = line.split("defined with ")
                        if len(parts) > 1:
                            count_str = parts[1].split(" atoms")[0].strip()
                            self.pos_charge = int(count_str)
                            # print("got pos charge: ", self.pos_charge)
                    except (ValueError, IndexError):
                        pass

        # Calculate overall charge if both values have been parsed
        try:
            if self.neg_charge is not None and self.pos_charge is not None:
                overall_charge = self.pos_charge - self.neg_charge
                self.overallChargeSignal.emit(str(overall_charge))
                self.pymol_cmd("delete %s" % "negative_charge")
                self.pymol_cmd("delete %s" % "positive_charge")
                self.neg_charge = None
                self.pos_charge = None
        except:
            # Use signal instead of direct GUI call to avoid cross-thread issues
            self.textMessageSignal.emit(
                "Something went wrong while calculating charge of the system..", False
            )
