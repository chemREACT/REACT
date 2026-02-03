from PyQt5 import QtWidgets
import os
from UIs.FileEditorWindow import Ui_FileEditorWindow


class FileEditor(QtWidgets.QMainWindow):
    def __init__(self, parent, filepath, readonly=False):
        super().__init__(parent)

        self.react = parent
        self.ui = Ui_FileEditorWindow()
        self.ui.setupUi(self)
        self.filepath = filepath
        self.filename = self.filepath.split("/")[-1]

        if not os.path.isfile(filepath):
            self.react.append_text(
                "File not found. Please check and see if\
                                   file has been moved or deleted."
            )
            self.close

        self.mol_obj = self.react.states[self.react.state_index].get_molecule_object(
            self.filepath
        )

        self.setWindowTitle(self.filename)

        self.ui.comboBox.currentIndexChanged.connect(self.on_combobox_changed)
        self.ui.save_button.clicked.connect(self.save_file_)
        self.ui.cancel_button.clicked.connect(self.close)
        self.orig_text = ""
        self.read_file()

    def read_file(self):
        """
        Reads file and filetype. comboBox is updated with filetypes in which
        the file can be converted into.
        """

        self.filetype = self.filename.split(".")[-1]

        self.ui.comboBox.blockSignals(True)

        if self.filetype in ["xyz"]:
            self.ui.comboBox.addItems(["com", "inp", "xyz"])
        elif self.filetype == "pdb":
            self.ui.comboBox.addItems(["com", "inp", "xyz", "pdb"])
        elif self.filetype in ["out", "log"]:
            self.ui.comboBox.addItems(["out", "com", "inp", "xyz"])
        elif self.filetype in ["com", "inp"]:
            self.ui.comboBox.addItems(["com", "inp", "xyz"])
        else:
            self.ui.comboBox.addItem(self.filetype)

        # TODO We should utilize objects of Atom and Molecule here instead of reading a file
        with open(self.filepath, "r") as f:
            text = f.read()

        self.orig_text = text
        self.ui.comboBox.setCurrentText(self.filetype)
        self.ui.textwindow.setPlainText(self.orig_text)

        self.ui.comboBox.blockSignals(False)

    def on_combobox_changed(self):
        """
        When combobox is changed, file is converted into the filetype of choice
        """

        new_filetype = self.ui.comboBox.currentText()

        if self.filetype in new_filetype:
            self.ui.textwindow.setPlainText(self.orig_text)
            self.setWindowTitle(self.filename)
            return

        elif new_filetype in ["com", "inp"]:
            try:
                text = self.make_input_content()
                new_filename = self.filename.rsplit(".", 1)[0] + "." + new_filetype
            except:
                self.react.append_text("Failed to convert file to input format")
                return

        elif new_filetype == "xyz":
            try:
                text = self.react.create_xyz_filecontent(self.filepath)
                new_filename = self.filename.split(".")[0] + "_new.xyz"
            except:
                self.react.append_text("Failed to convert file to xyz format")
                return

        self.setWindowTitle(new_filename)
        self.ui.textwindow.setPlainText(text)

    def make_input_content(self):
        """
        Make content (not file) for one Gaussian inputfile.
        :return: str
        The code is divided into the following parts: link0, route, molecule and restraint.
        Each part prepares it's respective part as a string. named for ex. link0_str.
        Finally, all sub-strings are jointed into one string, containing the whole file content
        """

        s = self.react.settings

        ### This part creates prepares all link0 keyword by adding them first to the 'link0_list' ###

        link0_list = []
        for item in s.link0_options:
            if item.lower().strip() == "chk":
                filename_stripped = self.filename.rsplit(".", 1)[0]
                link0_list.append("chk=" + filename_stripped)
            else:
                link0_list.append(item)

        link0_str = "\n".join(link0_list)

        ### This part prepares all part of the route comment ###

        job_options = s.job_options[s.job_type]

        if s.job_type == "Opt (TS)":
            job_options.append("TS")
            options = ", ".join(s.job_options[s.job_type])
            job = f"Opt=({options}) "
        else:
            if job_options:
                options = ", ".join(s.job_options[s.job_type])
                job = f"{s.job_type}=({options}) "
            else:
                job = f"{s.job_type} "

        if s.basis_diff and not s.basis_diff.isspace():
            tmp = list(s.basis)
            if tmp[-1] == "G":
                tmp[-1] = s.basis_diff
                tmp.append("G")
            else:
                tmp.append(s.basis_diff)
            basis = "".join(tmp)
        else:
            basis = s.basis

        if (
            s.basis_pol1
            and not s.basis_pol1.isspace
            and s.basis_pol2
            and not s.basis_pol2.isspace()
        ):
            basis_pol = f"({s.basis_pol1},{s.basis_pol2})"
        elif s.basis_pol1 and not s.basis_pol1.isspace():
            basis_pol = f"({s.basis_pol1})"
        elif s.basis_pol2 and not s.basis_pol2.isspace():
            basis_pol = f"({s.basis_pol2})"
        else:
            basis_pol = False

        if basis_pol:
            basis = f"{basis}{basis_pol}"
        else:
            basis = f"{basis}"

        route_str = f"#p {job}{s.functional}/{basis} " + " ".join(s.additional_keys)

        molecule_str = (
            f"{self.mol_obj.charge} {self.mol_obj.multiplicity}\n"
            + "\n".join(self.mol_obj.formatted_xyz)
        )

        return f"{link0_str}\n{route_str}\n\n{molecule_str}\n\n"

    def save_file_(self):
        """
        Save the content of the texteditor as a new file.
        """

        new_filename = self.windowTitle()

        new_filepath = self.filepath.replace(self.filename, new_filename)

        self.filepath, filter_ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save file", new_filepath
        )

        if self.filepath == "":
            return

        with open(self.filepath, "w") as f:
            f.write(self.ui.textwindow.toPlainText())

        self.react.add_files([self.filepath])
        self.close()
