from mods.GaussianFile import OutputFile, InputFile
from mods.MoleculeFile import PDBFile, XYZFile


class State:

    def __init__(self, file_paths=None):

        # File types --> sublass assignment
        self.file_types = {"com": InputFile,
                           "inp": InputFile,
                           "out": OutputFile,
                           "pdb": PDBFile,
                           "xyz": XYZFile}

        # filename (key) : file_path (value)
        # TODO Bente - what happens if to filenames with the same name are added to the same state (different paths)
        self.gfiles = {}
        if file_paths:
            for filepath in file_paths:
                self.add_gfiles(filepath)

    def get_filenames(self):
        """
        Return: list with all filenames of current state.
        """
        # return [x for x in self.gfiles.keys()] --> to use when printing filename only in workspace, instead of the whole filepath
        return [x.get_filepath() for x in self.gfiles.values()]

    def add_gfiles(self, filepath):
        """
        Creates GaussianFile instance for each uploaded file-path.
        """

        # if len(files_path) > some number:
        #    do multiprocessing or threading instead? Each new GaussianFile object will undergo some processing (read file, check convergence, energies...)


        # Check file type for correct GaussianFile subclass assignment:
        filename = filepath.split("/")[-1]
        filetype = filename.split(".")[-1]

        self.gfiles[filename] = self.file_types[filetype](filepath)

    def del_gfiles(self, files_to_del):
        """
        Removes all files in files_to_del list from state.
        """

        for f in files_to_del:
            try:
                self.gfiles.pop(f.split("/")[-1])  # here f is the whole path, not only the filename.
            except KeyError:
                print(f"File \"{f}\" not found")

    def get_all_gpaths(self):
        """
        return: list of all gaussian filpaths associated with a given state.
        """
        return [x.get_filepath() for x in self.gfiles.values()]

    def get_energy(self, filename):
        """
        :return: final SCF Done value
        """
        return self.gfiles[filename].get_energy()

    def check_convergence(self, filename):
        """
        :param filename:
        :return: None (not geometry optimization), False (not converged) or True (converged)
        """
        return self.gfiles[filename].check_convergence()

    def get_scf(self, filename):
        """
        Get lists for SCF Done, and convergence values
        :param filename:
        :return:
        """
        return self.gfiles[filename].get_scf_convergence()

    def get_xyx(self, filename):
        pass
