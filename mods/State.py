from mods.GaussianFile import OutputFile, InputFile, FrequenciesOut
from mods.MoleculeFile import PDBFile, XYZFile, Geometries


class State:
    """
    Stores all file objects for one state in REACT.
    """
    def __init__(self, parent):
        self.parent = parent
        # File types --> sublass assignment
        # TODO we need (in time) a better way to figure out what filetype is loaded. "inp" fex could be other than gaussian
        self.file_types = {"com": InputFile,
                           "inp": InputFile,
                           "out": OutputFile,
                           "pdb": PDBFile,
                           "xyz": XYZFile}

        # filepath (key) : File object (value)
        self.files = {}

    def add_file(self, filepath):
        """
        Creates GaussianFile instance for each uploaded file-path.
        """
        # Check file type for correct GaussianFile subclass assignment:
        filename = filepath.split("/")[-1]
        filetype = filename.split(".")[-1]

        self.files[filepath] = self.file_types[filetype](filepath=filepath)

        # Check if OutFile has frequencies, and make it a FrequenciesOut object instead:
        if isinstance(self.files[filepath], OutputFile):

            if self.files[filepath].frequencies:
                self.files[filepath] = FrequenciesOut(filepath)

        return None

    def del_files(self, files_to_del):
        """
        Removes all files in files_to_del list from state.
        """

        for f in files_to_del:
            try:
                self.files.pop(f) 
            except KeyError:
                print(f"File \"{f}\" not found. Please check if the file has been moved or deleted.")

    @property
    def get_all_paths(self):
        """
        return: list of all gaussian filpaths associated with a given state.
        """
        return [x for x in self.files.keys()]

    def get_molecule_object(self, filepath):
        # print(f'this is states: {self.files}')
        try:
            return self.files[filepath]
        except KeyError:
            return False

    def get_energy(self, filepath):
        """
        :return: final SCF Done value
        """
        return self.files[filepath].energy

    def check_convergence(self, filepath):
        """
        :param filename:
        :return: None (not geometry optimization), False (not converged) or True (converged)
        """
        return self.files[filepath].converged

    def get_scf(self, filepath):
        """
        Get lists for SCF Done, and convergence values
        :param filename:
        :return:
        """
        return self.files[filepath].scf_convergence

    def update_fileobject(self, filepath):
        """
        Updates a GaussianFile object in the event a file has been edited.        
        """
        self.files[filepath].update_fileobject()

    def get_xyz_formatted(self, molecule):
        """
        :param molecule: = {1: {name: C, x:value, y: value, z: value}}
        :return: xyz_formatted (list)
        """
        return XYZFile(atoms=molecule).formatted_xyz

    def get_final_xyz(self, filepath):
        """
        :param filepath:
        :return: a list of formated XYZ lines for guassian input files
        """
        return self.files[filepath].formatted_xyz

    def has_solvent(self, filepath):
        """
        :param filepath:
        :return: bool
        """
        return self.files[filepath].solvent

    def has_frequencies(self, filepath):
        """
        :param filepath:
        :return: bool
        """
        return self.files[filepath].frequencies

    def get_thermal_dg(self, filepath):
        """
        :param filepath:
        :return:
        """
        if self.files[filepath].frequencies:
            return self.files[filepath].get_thermal_dg

    def get_thermal_dh(self, filepath):
        """
        :param filepath:
        :return:
        """
        if self.files[filepath].frequencies:
            return self.files[filepath].get_thermal_dh

    def get_thermal_de(self, filepath):
        """
        :param filepath:
        :return:
        """
        if self.files[filepath].frequencies:
            return self.files[filepath].get_thermal_de

    def get_zpe(self, filepath):
        """
        :param filepath:
        :return:
        """
        if self.files[filepath].frequencies:
            return self.files[filepath].get_thermal_zpe

    def get_frequencies(self, filepath):
        if self.files[filepath].frequencies:
            return self.files[filepath].get_frequencies

    def create_input_content(self, path):
        """
        Create inputfile content (not file), based on coordiantes from an outputfile or from *.xyz file,
        or from XYZfile object?
        TODO
        """
        pass
        
        # if coordinates argument is a file associated with this state. NB works for inp/out only, what if file is *.xyz?
        #content = ""
        #gaussian_filetypes = ["out", "inp", "com"]
        #if path.split(".")[-1] in gaussian_filetypes:
        #    routecard = self.files[path].get_routecard
        #    charge_multiplicity = self.files[path].get_charge_multiplicity
        #    xyz = self.get_final_xyz(path)
#
#
        #    #TODO doesn't work if any of these variables are of NoneType!
        #    content = routecard + '\n\n' + charge_multiplicity[0] + ' ' + charge_multiplicity[1] +  '\n'
#
        #    for line in xyz:
        #        content += line + '\n'
#
        #elif path.split(".")[-1] == "xyz":
        #    # content = self.files[path].get_formatted_xyz gives error?
        #    #TODO get global settings, get coordinates, make inputfile content
        #    content = "Empty since this hasn't been implemented yet..."
#
        #return content

    def create_xyz_filecontent(self, filepath):


        xyz = self.get_final_xyz(filepath)

        
        content = str(len(xyz)) + '\n' + str(filepath.split("/")[-1]) + '\n'
        for line in xyz:
            content += line + '\n'

        return content
