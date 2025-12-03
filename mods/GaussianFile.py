from mods.Atoms import GaussianAtom, Atom
from mods.MoleculeFile import Geometries
from mods.PropertiesFile import Properties
import re


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


class InputFile(Properties):
    def __init__(self, filepath, new_file=False):
        # regEx pattern to reconize charge-multiplicity line. -?\d+ any digit any length, [13] = digit 1 or 3, \s*$ = any num of trailing whitespace
        self.charge_multiplicity_regEx = re.compile("^\s*-?\d+\s*[13]\s*$")

        geometries, charge, multiplicity = self.get_molecules_charge_multiplicity(
            filepath
        )

        super().__init__(filetype="Gaussian", filepath=filepath, geometries=geometries)

        self.charge = charge
        self.multiplicity = multiplicity
        self.filename = filepath.split("/")[-1].split(".")[0] + ".com"

    # TODO InputFile must know how to read a Gaussian input file and extract all available info from that file

    def get_molecules_charge_multiplicity(self, filepath):
        """
        Extract xyz from a gaussian input file and creates GaussianAtom objects

        :return: [atoms] = [[GaussianAtom1, ....]]

        """

        atoms = list()
        index = 1
        charge = None
        multiplicity = None
        with open(filepath, "r") as ginp:
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
                    line_dict = line.split(" ")
                    found_charge = False
                    for i in line_dict:
                        if i != "":
                            if found_charge == False:
                                charge = i
                                found_charge = True
                            else:
                                multiplicity = i
                    get_coordinates = True

        return [atoms], charge, multiplicity

    def create_filecontent(self):
        """
        Create contant for inputfile TODO
        """
        pass

        # essential_jobdetails = ["route", "job type", "DFT functional", "basis set"]
        # routecard = ''

        # for job_detail in self.job_details.items():
        #     if job_detail[0] in essential_jobdetails and job_detail[1]:
        #         routecard += ' ' + job_detail[1]
        #         essential_jobdetails.remove(job_detail[0])

        #     elif job_detail[1]:
        #         routecard += ' ' + job_detail[0]+'='+job_detail[1]

        # try:
        #     essential_jobdetails.remove('job type')
        # except:
        #     pass

        # if essential_jobdetails:
        #     print(f'missing job details: {essential_jobdetails}')

        # #first character in string is a whitespace, thus we remove it
        # return routecard[1:]


class OutputFile(Properties):
    def __init__(self, filepath):
        self._filepath = filepath
        molecules = self.get_coordinates()

        if not molecules:
            self.faulty = True
            molecules = None

        super().__init__(filetype="Gaussian", filepath=filepath, geometries=molecules)

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

        # This will store data from output file given by self.g_reader
        self.g_outdata = dict()

        # Read output on init to get key job details
        self.read_gaussianfile()

        # Setters in Properties:
        if self.faulty:
            self.converged = False
            self.energy = False
            self.scf_convergence = False
        else:
            self.converged = self.is_converged()
            self.solvent = self.has_solvent()
            self.frequencies = self.has_frequencies()
            self.energy = self.get_energy()
            self.scf_convergence = self.get_scf_convergence()

    def read_gaussianfile(self):
        """
        Reads through Gaussian output file and assigns values to self.g_outdata using self.g_reader, and assigns values to self.job_details
        """
        DFT_out = self._filepath

        print(f"in read_gaussian, this is path={self._filepath}")

        # found_all_jobdetails = False

        with open(DFT_out) as f:
            for line in f:
                if "Multiplicity" in line:
                    tmp = line.split()
                    self.charge = tmp[2]
                    self._multiplicity = tmp[5]

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

    def is_converged(self):
        """
        Set self.converged True if 4 SCF convergence criterias are met - else False
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

    def get_energy(self):
        """
        :return: final SCF Done energy stored in self.g_outdata
        """
        return self.g_outdata["SCF Done"]

    def get_scf_convergence(self):
        """
        Reads output file and returns all SCF Done energies
        :return: energies, MaximumForce, RMS Force, Maximum Displacement, RMS Displacement
        """
        scf_data = {
            "SCF Done": list(),
            "Maximum Force": list(),
            "RMS     Force": list(),
            "Maximum Displacement": list(),
            "RMS     Displacement": list(),
        }

        with open(self.filepath) as out:
            for line in out:
                if any(g_key in line for g_key in scf_data.keys()):
                    g_key = [term for term in scf_data.keys() if term in line][0]
                    split_int = 2
                    if g_key == "SCF Done":
                        split_int = 4
                    scf_data[g_key].append(float(line.split()[split_int]))

        return scf_data

    def get_coordinates(self):
        """
        Extract xyz from a gaussian output file and creates GaussianAtom objects

        :return: iter_atoms = [ [iteration 1], [iteration 2], .... ] where [iteration 1] = [GaussianAtom1, ....]
        """
        # list with GaussianAtom objects per geometry optimization --> iter_atoms[-1] is the final atom coordinates
        iter_atoms = list()

        atoms = list()
        with open(self.filepath, "r") as gout:
            gaussian_v = False
            found_coordinates = False
            get_coordinates = False

            for line in gout:
                if not gaussian_v:
                    if "Gaussian(R) 16 program" in line:
                        gaussian_v = 16
                        continue
                    elif "Gaussian(R) 09 program" in line:
                        gaussian_v = 9
                        continue
                    else:
                        continue
                elif gaussian_v == 9:
                    if found_coordinates and line.split()[0].isdigit():
                        get_coordinates = True

                    if get_coordinates:
                        if not line.split()[0].isdigit():
                            found_coordinates = False
                            get_coordinates = False

                            iter_atoms.append(atoms)
                        else:
                            atoms.append(GaussianAtom(line))

                    if "Standard orientation" in line:
                        found_coordinates = True
                        atoms = list()
                elif gaussian_v == 16:
                    if found_coordinates and line.split()[0].isdigit():
                        get_coordinates = True

                    if get_coordinates:
                        if not line.split()[0].isdigit():
                            found_coordinates = False
                            get_coordinates = False

                            iter_atoms.append(atoms)
                        else:
                            atoms.append(GaussianAtom(line))

                    if "Input orientation:" in line or "Standard orientation" in line:
                        found_coordinates = True
                        atoms = list()
        return iter_atoms

    def has_solvent(self):
        """
        :return: solvent = True/False
        """
        solvent = False
        if "Solvent" in self.g_outdata.keys():
            solvent = True
        return solvent

    def has_frequencies(self):
        freq = False
        if "Zero-point correction" in self.g_outdata.keys():
            freq = True
        return freq


class FrequenciesOut(OutputFile):
    def __init__(self, filepath):
        super().__init__(filepath=filepath)

        # Read output file from Gaussian to get Properties self.freq_inte and self.freq_displacement dicts
        self.read_frequencies()

        # Properties setters:
        self.thermal_dg = self.get_thermal_dg
        self.thermal_dh = self.get_thermal_dh
        self.thermal_de = self.get_thermal_de
        self.zpe = self.get_zpe

    def read_frequencies(self):
        """
        Read Gaussian outpufile and store frequencies to self.freq[freq] = IR intensity (KM/Mole)
        self.freq_inten is dict in parent class Properties
        :return:
        """
        found_freq = False

        with open(self.filepath, "r") as frq:
            for line in frq:
                if "Frequencies" in line:
                    found_freq = True
                    freq = [float(i) for i in line.split()[2:5]]

                if found_freq:
                    if "IR Inten" in line:
                        intensities = [float(i) for i in line.split()[3:6]]
                        self.freq_inten.update(zip(freq, intensities))
                        found_freq = False

    def get_displacement(self, frequency):
        """
        Make Geometries object with displacements for X,Y,Z for all atoms as "coordinates"
        :param frequency: selected frequency to extract displacements from
        :return: self.freq_displacement[frequency9
        """
        # Skip reading of output file if already read and stored:
        if frequency in self.freq_displacement.keys():
            return self.freq_displacement[frequency]

        # Gaussian file specific extraction of frequency:

        found_frequency = False
        found_displacement = False
        g_atoms = list()

        index_range = {0: (2, 5), 1: (5, 8), 2: (8, 11)}

        with open(self.filepath, "r") as frq:
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
                        self.freq_displacement[frequency] = Geometries(
                            molecules=[g_atoms]
                        )
                        return self.freq_displacement[frequency]

                if found_frequency and "Atom  AN      X      Y      Z" in line:
                    found_displacement = True

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
        if self._frequencies:
            return self.g_outdata["Thermal correction to Gibbs Free Energy"]
        else:
            return None

    @property
    def get_thermal_de(self):
        if self._frequencies:
            return self.g_outdata["Thermal correction to Energy"]
        else:
            return None

    @property
    def get_thermal_dh(self):
        if self._frequencies:
            return self.g_outdata["Thermal correction to Enthalpy"]
        else:
            return None

    @property
    def get_zpe(self):
        if self._frequencies:
            return self.g_outdata["Zero-point correction"]

    # Animate frequencies

    # set movie_fps, 5 (higher = slower)
    # load mol1.xyz, load mol2.xyx etc...
    # join_states moviename, mol*, 0 (the 0 assumes identical input objects so bonds can vary)
