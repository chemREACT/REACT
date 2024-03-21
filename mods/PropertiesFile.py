from mods.MoleculeFile import Geometries, Molecule
import copy


class Properties(Geometries):
    """
    General class for REACT to store DFT/QM properties. All classes are meant to read their respective files and init
    this class.
    """

    def __init__(self, filetype=None, filepath=None, geometries=None):
        self._filepath = filepath
        # This class should know what filetype it has... Gaussian, PDB, XYZ... and other future softwares like ADF..
        self._filetype = filetype

        # Multiple geometries:
        if geometries:
            super().__init__(molecules=geometries, filepath=filepath)

        self._filename = filepath.split("/")[-1]
        self._file_extension = self.filename.split(".")[-1]

        # DFT/QM JOB settings
        self._job_type = None
        self._functional = None
        self._basis = None
        self._basis_diff = None
        self._basis_pol1 = None
        self._basis_pol2 = None
        self._empiricaldispersion = None
        self._job_mem = None
        self._chk = None
        self._job_options = []
        self._link0_options = []

        # From Output classes
        self._converged = None
        self._solvent = False
        self._frequencies = False
        self._energy = None
        self._scf_convergence = None

        # From Frq class:
        self._thermal_dg = None
        self._thermal_dh = None
        self._thermal_de = None
        self._zpe = None
        # frequency : IR Intensity
        self.freq_inten = dict()
        # frequency : {atom nr: name, x:float, y: float, z:float}
        self.freq_displacement = dict()

    @property
    def thermal_dg(self):
        return self._thermal_dg

    @thermal_dg.setter
    def thermal_dg(self, value):
        self._thermal_dg = value

    @property
    def thermal_de(self):
        return self._thermal_de

    @thermal_de.setter
    def thermal_de(self, value):
        self._thermal_de = value

    @property
    def thermal_dh(self):
        return self._thermal_dh

    @thermal_dh.setter
    def thermal_dh(self, value):
        self._thermal_dh = value

    @property
    def zpe(self):
        return self._zpe

    @zpe.setter
    def zpe(self, value):
        self._zpe = value

    @property
    def scf_convergence(self):
        return self._scf_convergence

    @scf_convergence.setter
    def scf_convergence(self, value):
        """
        Format:
        scf_data = {"SCF Done": list(),
                    "Maximum Force": list(),
                    "RMS     Force": list(),
                    "Maximum Displacement": list(),
                    "RMS     Displacement": list()}
        """
        if isinstance(value, dict):
            self._scf_convergence = value

    @property
    def converged(self):
        return self._converged

    @converged.setter
    def converged(self, value):
        if isinstance(value, bool):
            self._converged = value
        else:
            print(f"Properties: Tried to set self.converged to non-bool. I will not allow that!")

    @property
    def solvent(self):
        return self._solvent

    @solvent.setter
    def solvent(self, value):
        if isinstance(value, bool):
            self._solvent = value
        else:
            print(f"Properties: Tried to set self.solvent to non-bool. I will not allow that!")

    @property
    def frequencies(self):
        return self._frequencies

    @frequencies.setter
    def frequencies(self, value):
        if isinstance(value, bool):
            self._frequencies = value
        else:
            print(f"Properties: Tried to set self.frequencies to non-bool. I will not allow that!")

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, value):
        self._energy = value

    @property
    def filetype(self):
        return self._filetype

    @filetype.setter
    def filetype(self, value):
        self._filetype = value

    @property
    def filename(self):
        return self._filename

    @property
    def filepath(self):
        return self._filepath

    @property
    def file_extension(self):
        return self._file_extension

    @file_extension.setter
    def file_extension(self, value):
        self._file_extension = value

    @property
    def job_type(self):
        return self._job_type

    @property
    def basis(self):
        return self._basis

    @property
    def basis_diff(self):
        return self._basis_diff

    @property
    def basis_pol1(self):
        return self._basis_pol1

    @property
    def basis_pol2(self):
        return self._basis_pol2

    @property
    def functional(self):
        return self._functional

    @property
    def job_mem(self):
        return self._job_mem

    @property
    def chk(self):
        return self._chk

    @property
    def empiricaldispersion(self):
        return self._empiricaldispersion

    @property
    def job_options(self):
        return self._job_options

    @property
    def link0_options(self):
        return self._link0_options

    @filename.setter
    def filename(self, value):
        self._filename = value

    @filepath.setter
    def filepath(self, value):
        self._filepath = value

    @job_type.setter
    def job_type(self, value):
        self._job_type = value

    @functional.setter
    def functional(self, value):
        self._functional = value

    @basis.setter
    def basis(self, value):
        self._basis = value

    @basis_diff.setter
    def basis_diff(self, value):
        self._basis_diff = value

    @basis_pol1.setter
    def basis_pol1(self, value):
        self._basis_pol1 = value

    @basis_pol2.setter
    def basis_pol2(self, value):
        self._basis_pol2 = value

    @job_mem.setter
    def job_mem(self, value):
        if type(value) == int:
            self._job_mem = value

    @chk.setter
    def chk(self, value):
        self._chk = value

    @empiricaldispersion.setter
    def empiricaldispersion(self, value):
        self._empiricaldispersion = value

    @job_options.setter
    def job_options(self, value):
        self._job_options = value

    @link0_options.setter
    def link0_options(self, value):
        self._link0_options = value

    def displacement_animation(self, freq, scale=1, steps=10):
        """
        Creates a list of Molecule objects with coordinates corresponding to displacement caused by frequency.
        :param scale: scale displacment
        :param steps: number of structures to create
        :return: list of gaussian molecules, where the first is the original optimised molecules.
        """
        molecule = self.molecule
        try:
            displacement = self.get_displacement(freq).molecule
        except AttributeError:
            self.react.append_text("No molecule found...")
            return False
        molecules = list()
        molecules.append(Molecule(atoms=molecule))

        # Forward direction (N steps)
        for i in range(steps):
            mol_disp = copy.deepcopy(molecule)
            for atom in mol_disp.keys():
                mol_disp[atom].x += float(displacement[atom].x) * scale * (i / steps)
                mol_disp[atom].y += float(displacement[atom].y) * scale * (i / steps)
                mol_disp[atom].z += float(displacement[atom].z) * scale * (i / steps)

            molecules.append(Molecule(atoms=mol_disp))
        # Reversed direction
        for i in range(len(molecules) - 1, 0, -1):
            molecules.append(molecules[i])

        return molecules

    def get_displacement(self, frequency):
        """
        Make Geometries object with displacements for X,Y,Z for all atoms as "coordinates"
        :param frequency: selected frequency to extract displacements from
        :return: self.freq_displacement[frequency9
        """
        # Skip reading of output file if already read and stored:
        if frequency in self.freq_displacement.keys():
            return self.freq_displacement[frequency]

        # else --> read from Software output file.
        # [put this function in software child class]
