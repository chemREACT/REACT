from mods.Atoms import GaussianAtom, Atom
from mods.MoleculeFile import GaussianMolecule
import re
import copy


def strtobool(val):
    """
    Convert a string representation of truth to boolean.
    Replacement for deprecated distutils.util.strtobool (removed in Python 3.12).

    True values: 'y', 'yes', 't', 'true', 'on', '1'
    False values: 'n', 'no', 'f', 'false', 'off', '0'
    Raises ValueError for any other input.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    elif val in ("n", "no", "f", "false", "off", "0"):
        return 0
    else:
        raise ValueError(f"invalid truth value {val!r}")


class GaussianFile:
    def __init__(self, file_path=None):
        if file_path:
            self.file_path = file_path

        # TODO Put in some defaults here for now:
        self.job_details = {
            "route": None,
            "job type": None,
            "DFT functional": None,
            "basis set": None,
            "scrf": None,
            "empiricaldispersion": None,
        }

        # self.set_default_settings()

        # For each job details item, there is a list of known option (ex for basis sets there are b3lyp, m062x, etc)
        # These options are saved as regular expression objects, which makes it easier to search for them in textfiles.

        # TODO how to handle multiple job type? ex: opt freq ?
        # TODO for now, all optimization-related keywords (TS, modreduant..) are saved as part of 'job-type'. (could be a bad idea? ex: omit modredundant if no atoms are freezed?)
        # TODO deal with geom=connectivity, or ignore it?
        # TODO %chk, %mem, etc. retrive from output file, or just assign from default settings?

        self.job_details_regEx = {
            "route": [re.compile(p, re.IGNORECASE) for p in ["#p", "#n#"]],
            "job type": [
                re.compile(p, re.IGNORECASE) for p in ["opt[^\s]*", "freq[^\s]*"]
            ],
            "DFT functional": [
                re.compile(p, re.IGNORECASE) for p in [" b3lyp", "rb3lyp", "m062x"]
            ],
            "basis set": [re.compile(p, re.IGNORECASE) for p in ["6-31g\(d,p\)"]],
            "scrf": [re.compile(p, re.IGNORECASE) for p in ["scrf[^\s]*"]],
            "empiricaldispersion": [re.compile(p, re.IGNORECASE) for p in ["gd3"]],
        }
        self.modredudant_text = ""

        self.charge_multiplicity = None

    def set_default_settings(self):
        """
        TODO get settings from global settings (should be stored in a file, and read from there probably)
        :return:
        """
        self.job_details["basis set"] = "6-31g(d,p)"
        self.job_details["DFT functional"] = "b3lyp"
        # self.job_details["modredundant"] = True
        self.job_details["empiricaldispersion"] = "gd3"

    @property
    def get_job_details(self):
        """
        :return: job details
        NB should this propery be moved to parent class? problem: uses the read_gaussian_out fuction.
        """
        return self.job_details

    @property
    def get_charge_multiplicity(self):
        """
        :return: tuple -> (charge, multiplicity)
        """
        return self.charge_multiplicity

    @property
    def get_routecard(self):
        """
        :return: route card as one string.
        TODO: some warning if essential details are missing. (#, functional and basisset?)
        """

        essential_jobdetails = ["route", "job type", "DFT functional", "basis set"]
        routecard = ""

        for job_detail in self.job_details.items():
            if job_detail[0] in essential_jobdetails and job_detail[1]:
                routecard += " " + job_detail[1]
                essential_jobdetails.remove(job_detail[0])

            elif job_detail[1]:
                routecard += " " + job_detail[0] + "=" + job_detail[1]

        try:
            essential_jobdetails.remove("job type")
        except:
            pass

        if essential_jobdetails:
            print(f"missing job details: {essential_jobdetails}")

        # first character in string is a whitespace, thus we remove it
        return routecard[1:]

    @property
    def get_basis(self):
        return self.job_details["basis set"]

    @property
    def get_dft_functional(self):
        return self.job_details["DFT functional"]

    @property
    def get_filepath(self):
        """
        Return: filepath for gaussianfile
        """
        return self.file_path

    def update_fileobject(self):
        """
        TODO Called after file has been edited in text editor, should update object accordingly to changes in file.
        """
        pass

    def _regEx_job_detail_search(self, string, job_detail_key):
        """
        Private function used in read_gaussian_out() and read_gaussian_inp().
        """
        if not self.job_details[job_detail_key]:
            for regEx in self.job_details_regEx[job_detail_key]:
                if regEx.search(string) and re.search("^ %", string) == None:
                    self.job_details[job_detail_key] = regEx.search(string).group()


class InputFile(GaussianFile):
    def __init__(self, file_path):
        super().__init__(file_path)

        # Initialize dictionaries TODO:
        # Job Types: Energy, Optimization, Frequency, Opt+Freq, IRC, Scan
        # optimize to: Minimum, TS
        # Use tight convergence criteria: False (True: opt=tight)
        # Force Constants: default, Calculate at First point (opt=calcf), Calculate at all points (opt=calcall)
        # Method: Ground state ... there are other, but stick with this for now
        # Method type: DFT (include HF, MP2, MP4?)
        # Method functional: B3LYP
        # Spin type: Default Spin, Restricted, Undrestricted, Restricted-Open
        # multiplicity = 2S+1 (S=1/2*n; where n is number of unpaired electrons). For molecules and ions, S=0!
        # Spin multiplicity: Singlet, Triplet
        # Charge: 0 #Todo write method to find charge of molecule?
        # Basis set: 6-31G+(d,p)
        # Additional keywords: # Todo make this more elegant than GaussView opt=noeigentest, empiricaldispersion=gd3 ..
        # Job title: my job
        # memory: 16GB
        # Shared processors: None (None = do not include in input file)
        # Checkpoint file: None
        # Old checkpoint file: None
        # Quadratic convergent SCF: False (True = scf=qc)
        # Use modified redundant coordinates: False (opt=modredundant)
        # Compute polarizabilities: False (True = polar)
        # Additional print: True (# at beginning of inputfile line)
        # Solvation model: None, CPCM, IEFPCM, SMD
        # solvent: default, Water, DMSO, Methanol, Ethanol ....
        # Eps: None (default for solvent), number (include read at top and eps=number at end of input file)
        job_options = {"Job type": "Energy"}

        # regEx pattern to reconize charge-multiplicity line. -?\d+ any digit any length, [13] = digit 1 or 3, \s*$ = any num of trailing whitespace
        self.charge_multiplicity_regEx = re.compile("-?\d+ [13]\s*$")

        self.read_gaussian_inp()

        # TODO, I have commented the below out, because it does not do anything...
        # self.get_coordinates

    def read_gaussian_inp(self):
        """
        Reads through Gaussian input file, assigns values to self.job_details and self.charge_multiplicity
        """
        DFT_inp = self.file_path

        with open(DFT_inp) as f:
            for line in f:
                if self.charge_multiplicity_regEx.search(line):
                    temp = self.charge_multiplicity_regEx.search(line).group().split()
                    self.charge_multiplicity = (temp[0], temp[1])
                    # after charge/multiplicity line, all job details have been read -> break loop
                    break

                # for every job detail item, check line to see if any regEx are present. If found, assign it to job_details{}
                for job_detail_key in self.job_details.keys():
                    self._regEx_job_detail_search(line, job_detail_key)

    @property
    def get_coordinates(self):
        """
        Extract xyz from a gaussian input file and creates GaussianAtom objects

        :return: atoms = [GaussianAtom1, ....]

        """
        atoms = list()
        index = 1
        with open(self.file_path, "r") as ginp:
            get_coordinates = False
            for line in ginp:
                if get_coordinates:
                    if line.isspace():
                        break
                    else:
                        atom_info = line.split()
                        atoms.append(
                            Atom(
                                atom_info[0],
                                atom_info[1],
                                atom_info[2],
                                atom_info[3],
                                index,
                            )
                        )
                        index += 1
                if self.charge_multiplicity_regEx.search(line):
                    get_coordinates = True

        return [atoms]


class OutputFile(GaussianFile):
    def __init__(self, filepath=None):
        super().__init__(filepath)

        self.file_path = filepath

        # Job converged or not?
        self.converged = {
            "Maximum Force": bool,
            "RMS     Force": bool,
            "Maximum Displacement": bool,
            "RMS     Displacement": bool,
        }

        # Where to get gaussian output value from line.split(int)
        # first key = Line to look for in output file
        # second key(s) are key names for assignment in self.g_outdata with tuple value giving index [0] and
        # type expected in line [1]
        self.g_reader = {
            "Solvent": {"Solvent": (2, str), "Eps": (4, float)},
            "SCF Done": {"SCF Done": (4, float)},
            "Zero-point correction=": {"Zero-point correction": (2, float)},
            "Thermal correction to Energy= ": {
                "Thermal correction to Energy": (4, float)
            },
            "Thermal correction to Enthalpy": {
                "Thermal correction to Enthalpy": (4, float)
            },
            "Thermal correction to Gibbs Free Energy": {
                "Thermal correction to Gibbs Free Energy": (6, float)
            },
            "Maximum Force": {
                "Maximum Force Value": (2, float),
                "Maximum Force Threshold": (3, float),
                "Maximum Force Converged?": (4, bool),
            },
            "RMS     Force": {
                "RMS Force Value": (2, float),
                "RMS Force Threshold": (3, float),
                "RMS Force Converged?": (4, bool),
            },
            "Maximum Displacement": {
                "Maximum Displacement Value": (2, float),
                "Maximum Displacement Threshold": (3, float),
                "Maximum Displacement Converged?": (4, bool),
            },
            "RMS     Displacement": {
                "RMS Displacement Value": (2, float),
                "RMS Displacement Threshold": (3, float),
                "RMS Displacement Converged?": (4, bool),
            },
        }

        self.charge_multiplicity_regEx = re.compile(
            "Charge = -?\d+ Multiplicity = [13]"
        )
        # This will store data from output file given by self.g_reader
        self.g_outdata = dict()

        # Read output on init to get key job details
        self.read_gaussian_out()

    def read_gaussian_out(self):
        """
        Reads through Gaussian output file and assigns values to self.g_outdata using self.g_reader, and assigns values to self.job_details
        """
        DFT_out = self.file_path

        found_all_jobdetails = False

        with open(DFT_out) as f:
            for line in f:
                # Check if line contains any self.g_reader keys:
                if any(g_key in line for g_key in self.g_reader.keys()):
                    g_key = [term for term in self.g_reader.keys() if term in line][0]
                    for out_name in self.g_reader[g_key].keys():
                        split_int, type_ = self.g_reader[g_key][out_name][0:2]
                        if type_ is bool:
                            line_value = bool(strtobool(line.split()[split_int]))
                        else:
                            line_value = type_(line.split()[split_int])

                        self.g_outdata[out_name] = line_value

                if not found_all_jobdetails:
                    if " Cycle   1" in line:
                        found_all_jobdetails = True

                    # for every job detail item, check line to see if any regEx are present. If found, assign it to job_details{}
                    for job_detail_key in self.job_details.keys():
                        self._regEx_job_detail_search(line, job_detail_key)

                    if (
                        "The following ModRedundant input section has been read:"
                        in line
                    ):
                        while True:
                            temp = next(f)
                            if temp.isspace():
                                break
                            else:
                                self.modredudant_text += temp

                    if not self.charge_multiplicity:
                        if self.charge_multiplicity_regEx.search(line):
                            temp = (
                                self.charge_multiplicity_regEx.search(line)
                                .group()
                                .split()
                            )
                            self.charge_multiplicity = (temp[2], temp[5])

    @property
    def is_converged(self):
        """
        Returns True if all 4 SCF convergence criterias are met - else False
        :return: None (not geometry optimization), False (not converged) or True (converged)
        """
        converged = None

        converge_terms = list()
        for entry in self.g_outdata.keys():
            if "Converged?" in entry:
                converge_terms.append(self.g_outdata[entry])

        if len(converge_terms) > 3:
            if sum(converged_ is True for converged_ in converge_terms) == 4:
                converged = True
            else:
                converged = False

        return converged

    @property
    def get_energy(self):
        """
        :return: final SCF Done energy stored in self.g_outdata
        """
        return self.g_outdata["SCF Done"]

    @property
    def get_scf_convergence(self):
        """
        Reads output file and returns all SCF Done energies
        :return: energies, MaximumForce, RMS Force, Maximum Displacement, RMS Displacement
        """
        # SCF Done 4
        scf = list()

        # "Maximum Force" 2
        max_force = list()

        # "RMS     Force" 2
        rms_force = list()

        # "Maximum Displacement" 2
        max_displacement = list()

        # "RMS     Displacement" 2
        rms_displacement = list()
        scf_data = {
            "SCF Done": list(),
            "Maximum Force": list(),
            "RMS     Force": list(),
            "Maximum Displacement": list(),
            "RMS     Displacement": list(),
        }

        with open(self.file_path) as out:
            for line in out:
                if any(g_key in line for g_key in scf_data.keys()):
                    g_key = [term for term in scf_data.keys() if term in line][0]
                    split_int = 2
                    if g_key == "SCF Done":
                        split_int = 4
                    scf_data[g_key].append(float(line.split()[split_int]))

        return scf_data

    @property
    def get_coordinates(self):
        """
        Extract xyz from a gaussian output file and creates GaussianAtom objects

        :return: iter_atoms = [ [iteration 1], [iteration 2], .... ] where [iteration 1] = [GaussianAtom1, ....]
        """
        # list with GaussianAtom objects per geometry optimization --> iter_atoms[-1] is the final atom coordinates
        iter_atoms = list()

        atoms = list()
        with open(self.file_path, "r") as gout:
            standard_orientation = False
            get_coordinates = False
            for line in gout:
                if standard_orientation and line.split()[0].isdigit():
                    get_coordinates = True

                if get_coordinates:
                    if not line.split()[0].isdigit():
                        standard_orientation = False
                        get_coordinates = False

                        iter_atoms.append(atoms)
                    else:
                        atoms.append(GaussianAtom(line))

                if "Standard orientation" in line:
                    standard_orientation = True
                    atoms = list()

        return iter_atoms

    @property
    def get_final_molecule(self):
        """
        :return: GaussianMolecule
        """
        atoms = self.get_coordinates[-1]
        return GaussianMolecule(g_atoms=atoms)

    @property
    def has_solvent(self):
        """
        :return: solvent = True/False
        """
        solvent = False
        if "Solvent" in self.g_outdata.keys():
            solvent = True
        return solvent

    @property
    def has_frequencies(self):
        freq = False
        if "Zero-point correction" in self.g_outdata.keys():
            freq = True
        return freq

    @property
    def get_formatted_xyz(self):
        atoms = self.get_coordinates[-1]
        gmolecule = GaussianMolecule(g_atoms=atoms)
        return gmolecule.get_formatted_xyz


class FrequenciesOut(OutputFile):
    def __init__(self, filepath=None):
        super().__init__(filepath)

        self.file_path = filepath

        # frequency : IR Intensity
        self.freq_inten = dict()

        # frequency : {atom nr: name, x:float, y: float, z:float}
        self.freq_displacement = dict()

        self.read_frequencies()

    def read_frequencies(self):
        """
        Read Gaussian outpufile and store frequencies to self.freq[freq] = IR intensity (KM/Mole)
        :return:
        """
        # start = time.time()
        found_freq = False

        with open(self.file_path, "r") as frq:
            for line in frq:
                if "Frequencies" in line:
                    found_freq = True
                    freq = [float(i) for i in line.split()[2:5]]

                if found_freq:
                    if "IR Inten" in line:
                        intensities = [float(i) for i in line.split()[3:6]]
                        self.freq_inten.update(zip(freq, intensities))
                        found_freq = False
        # print("READ FREQ Time executed:", time.time() - start, "s")

    def get_displacement(self, frequency):
        """
        Make GaussianMolecule with displacements for X,Y,Z for all atoms as "coordinates"
        :param frequency: selected frequency to extract displacements from
        :return: TODO
        """
        # Skip reading of output file if already read and stored:
        if frequency in self.freq_displacement.keys():
            return self.freq_displacement[frequency]

        found_frequency = False
        found_displacement = False
        g_atoms = list()

        index_range = {0: (2, 5), 1: (5, 8), 2: (8, 11)}

        with open(self.file_path, "r") as frq:
            for line in frq:
                if "Frequencies" in line:
                    current_frqs = line.split()[2:5]
                    if frequency in current_frqs:
                        frq_index = current_frqs.index(frequency)
                        found_frequency = True

                if found_displacement:
                    if len(line.split()) > 5:
                        coord_start, coord_end = index_range[frq_index][:]
                        g_line = "%s 0 %s" % (
                            " ".join((line.split()[0:2])),
                            " ".join(line.split()[coord_start:coord_end]),
                        )
                        g_atoms.append(GaussianAtom(g_line))
                    else:
                        self.freq_displacement[frequency] = GaussianMolecule(
                            g_atoms=g_atoms
                        )
                        return self.freq_displacement[frequency]

                if found_frequency and "Atom  AN      X      Y      Z" in line:
                    found_displacement = True

    def create_displacement_animation(self, freq, scale=1, steps=10):
        """
        :param scale: scale displacment
        :param steps: number of structures to create
        :return: list of gaussian molecules, where the first is the original optimised molecules.
        """
        molecule = self.get_final_molecule.get_molecule
        displacement = self.get_displacement(freq).get_molecule

        molecules = list()
        molecules.append(molecule)

        # Forward direction (N steps)
        for i in range(steps):
            mol_disp = copy.deepcopy(molecule)
            for atom in mol_disp.keys():
                mol_disp[atom].x += float(displacement[atom].x) * scale * (i / steps)
                mol_disp[atom].y += float(displacement[atom].y) * scale * (i / steps)
                mol_disp[atom].z += float(displacement[atom].z) * scale * (i / steps)

            molecules.append(mol_disp)
        # Reversed direction
        for i in range(len(molecules) - 1, 0, -1):
            molecules.append(molecules[i])

        return molecules

    @property
    def get_img_frq(self):
        """
        :return: dictionary only with imaginary frequencies
        """
        return {k: v for k, v in self.freq_inten if k < 0}

    @property
    def get_frequencies(self):
        """
        :return:
        """
        return self.freq_inten

    @property
    def get_freq_displacement(self):
        """
        :return:
        """
        return self.freq_displacement

    @property
    def get_img_displacement(self):
        """
        :return:
        """
        return {k: v for k, v in self.freq_displacement if k < 0}

    @property
    def get_thermal_dg(self):
        if self.has_frequencies:
            return self.g_outdata["Thermal correction to Gibbs Free Energy"]
        else:
            return None

    @property
    def get_thermal_de(self):
        if self.has_frequencies:
            return self.g_outdata["Thermal correction to Energy"]
        else:
            return None

    @property
    def get_thermal_dh(self):
        if self.has_frequencies:
            return self.g_outdata["Thermal correction to Enthalpy"]
        else:
            return None

    @property
    def get_zpe(self):
        if self.has_frequencies:
            return self.g_outdata["Zero-point correction"]

    # Animate frequencies

    # set movie_fps, 5 (higher = slower)
    # load mol1.xyz, load mol2.xyx etc...
    # join_states moviename, mol*, 0 (the 0 assumes identical input objects so bonds can vary)
