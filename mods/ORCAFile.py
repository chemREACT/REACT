from mods.Atoms import Atom
from mods.MoleculeFile import Geometries
from mods.PropertiesFile import Properties


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


class ORCAInputFile(Properties):
    def __init__(self, filepath, new_file=False):
        geometries, charge, multiplicity = self.get_molecules_charge_multiplicity(
            filepath
        )

        super().__init__(filetype="ORCA", filepath=filepath, geometries=geometries)

        self.charge = charge
        self.multiplicity = multiplicity
        self.filename = filepath.split("/")[-1].split(".")[0] + ".inp"

    def get_molecules_charge_multiplicity(self, filepath):
        """
        Extract xyz from an ORCA input file and creates Atom objects
        ORCA format: * xyz charge multiplicity
                     atom x y z
                     atom x y z
                     *

        :return: [atoms] = [[Atom1, ....]], charge, multiplicity
        """
        atoms = list()
        index = 1
        charge = None
        multiplicity = None

        with open(filepath, "r") as orca_inp:
            get_coordinates = False
            for line in orca_inp:
                line_stripped = line.strip()

                # Check for xyz block start: * xyz charge multiplicity
                if line_stripped.startswith("* xyz") or line_stripped.startswith(
                    "*xyz"
                ):
                    parts = line_stripped.split()
                    if len(parts) >= 4:
                        charge = parts[2]
                        multiplicity = parts[3]
                        get_coordinates = True
                        continue

                # Check for xyzfile: *xyzfile charge multiplicity filename
                if line_stripped.startswith("* xyzfile") or line_stripped.startswith(
                    "*xyzfile"
                ):
                    parts = line_stripped.split()
                    if len(parts) >= 4:
                        charge = parts[2]
                        multiplicity = parts[3]
                        # TODO: Handle external xyz file reference
                        # For now, just note that coordinates are in external file
                    continue

                if get_coordinates:
                    # End of coordinate block
                    if line_stripped == "*":
                        break
                    # Skip empty lines
                    if not line_stripped:
                        continue
                    # Parse coordinate line: element x y z
                    atom_info = line_stripped.split()
                    if len(atom_info) >= 4:
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

        return [atoms], charge, multiplicity


class ORCAOutputFile(Properties):
    def __init__(self, filepath):
        self._filepath = filepath
        self._charge = None
        self._multiplicity = None

        molecules = self.get_coordinates()

        if not molecules:
            self.faulty = True
            molecules = None

        super().__init__(filetype="ORCA", filepath=filepath, geometries=molecules)

        # Dictionary to map ORCA output patterns to data extraction
        # Format: "search_string": {"property_name": (split_index, type)}
        self.orca_reader = {
            "FINAL SINGLE POINT ENERGY": {"SCF Done": (4, float)},
            "Total Energy       :": {"SCF Done": (3, float)},
            "CPCM Solvation Model": {"Solvent": (0, str)},  # Will need special handling
            "Zero point energy": {"Zero-point correction": (4, float)},
            "Total thermal energy": {"Thermal correction to Energy": (4, float)},
            "Total Enthalpy": {"Thermal correction to Enthalpy": (3, float)},
            "Final Gibbs free energy": {
                "Thermal correction to Gibbs Free Energy": (5, float)
            },
        }

        # Convergence criteria for geometry optimization
        self.convergence_keys = {
            "Energy change": "Energy Change Converged?",
            "MAX gradient": "Maximum Gradient Converged?",
            "RMS gradient": "RMS Gradient Converged?",
            "MAX step": "Maximum Step Converged?",
            "RMS step": "RMS Step Converged?",
        }

        # This will store data from output file
        self.orca_outdata = dict()

        # Read output on init to get key job details
        self.read_orcafile()

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

    def read_orcafile(self):
        """
        Reads through ORCA output file and assigns values to self.orca_outdata
        """
        with open(self._filepath) as f:
            for line in f:
                # Extract charge and multiplicity
                if "Total Charge" in line:
                    parts = line.split()
                    try:
                        charge_idx = parts.index("Charge") + 1
                        if charge_idx < len(parts):
                            # Handle case where Multiplicity is on same line
                            self._charge = parts[charge_idx]
                            if "Multiplicity" in line:
                                mult_idx = parts.index("Multiplicity") + 1
                                if mult_idx < len(parts):
                                    self._multiplicity = parts[mult_idx]
                    except (ValueError, IndexError):
                        pass

                # Check for multiplicity on separate line
                if line.strip().startswith("Multiplicity"):
                    parts = line.split()
                    if len(parts) >= 2:
                        self._multiplicity = parts[1]

                # Check if line contains any orca_reader keys
                for orca_key in self.orca_reader.keys():
                    if orca_key in line:
                        for out_name in self.orca_reader[orca_key].keys():
                            split_int, type_ = self.orca_reader[orca_key][out_name][0:2]
                            try:
                                if type_ is bool:
                                    line_value = bool(
                                        strtobool(line.split()[split_int])
                                    )
                                else:
                                    line_value = type_(line.split()[split_int])
                                self.orca_outdata[out_name] = line_value
                            except (ValueError, IndexError):
                                pass

                # Check for convergence flags (YES/NO in ORCA optimization output)
                for conv_key, conv_name in self.convergence_keys.items():
                    if conv_key in line:
                        # ORCA prints "YES" or "NO" for convergence
                        if "YES" in line:
                            self.orca_outdata[conv_name] = True
                        elif "NO" in line:
                            self.orca_outdata[conv_name] = False

                # Special handling for solvent
                if "Solvent:" in line or "SMDsolvent" in line:
                    parts = line.split()
                    try:
                        solvent_idx = parts.index("Solvent:") + 1
                        if solvent_idx < len(parts):
                            self.orca_outdata["Solvent"] = parts[solvent_idx].strip('"')
                    except (ValueError, IndexError):
                        pass

    def is_converged(self):
        """
        Set self.converged True if geometry optimization convergence criteria are met
        ORCA typically checks: Energy change, MAX gradient, RMS gradient, MAX step, RMS step
        """
        converged = None

        converge_terms = list()
        for entry in self.orca_outdata.keys():
            if "Converged?" in entry:
                converge_terms.append(self.orca_outdata[entry])

        # ORCA optimization is converged if all criteria are met
        if len(converge_terms) > 0:
            if all(converged_ is True for converged_ in converge_terms):
                converged = True
            else:
                converged = False

        return converged

    def get_energy(self):
        """
        :return: final SCF energy stored in self.orca_outdata
        """
        if "SCF Done" in self.orca_outdata:
            return self.orca_outdata["SCF Done"]
        return None

    def get_scf_convergence(self):
        """
        Reads output file and returns all SCF energies and convergence info
        :return: dict with SCF Done energies and convergence criteria
        """
        scf_data = {
            "SCF Done": list(),
            "Energy change": list(),
            "MAX gradient": list(),
            "RMS gradient": list(),
            "MAX step": list(),
            "RMS step": list(),
        }

        with open(self.filepath) as out:
            for line in out:
                # Extract SCF energies
                if "FINAL SINGLE POINT ENERGY" in line:
                    try:
                        scf_data["SCF Done"].append(float(line.split()[4]))
                    except (ValueError, IndexError):
                        pass
                elif "Total Energy       :" in line:
                    try:
                        scf_data["SCF Done"].append(float(line.split()[3]))
                    except (ValueError, IndexError):
                        pass

                # Extract convergence criteria values
                for criterion in [
                    "Energy change",
                    "MAX gradient",
                    "RMS gradient",
                    "MAX step",
                    "RMS step",
                ]:
                    if criterion in line:
                        try:
                            # ORCA format: "criterion  ...  value  ...  threshold  ...  YES/NO"
                            parts = line.split()
                            # Find the numeric value (typically after the criterion name)
                            for i, part in enumerate(parts):
                                try:
                                    value = float(part)
                                    scf_data[criterion].append(value)
                                    break
                                except ValueError:
                                    continue
                        except (ValueError, IndexError):
                            pass

        return scf_data

    def get_coordinates(self):
        """
        Extract xyz from an ORCA output file and creates GaussianAtom objects
        ORCA prints coordinates in "CARTESIAN COORDINATES (ANGSTROEM)" or "CARTESIAN COORDINATES (A.U.)"

        :return: iter_atoms = [ [iteration 1], [iteration 2], .... ] where [iteration 1] = [Atom1, ....]
        """
        iter_atoms = list()
        atoms = list()

        with open(self.filepath, "r") as orca_out:
            get_coordinates = False
            coordinate_section_started = False

            for line in orca_out:
                # Look for coordinate blocks
                if "CARTESIAN COORDINATES (ANGSTROEM)" in line:
                    coordinate_section_started = True
                    atoms = list()
                    get_coordinates = False
                    continue

                if coordinate_section_started:
                    # Skip the separator line
                    if "---" in line:
                        get_coordinates = True
                        continue

                    if get_coordinates:
                        # End of coordinate block (empty line or next section)
                        if (
                            not line.strip()
                            or line.startswith("---")
                            or "CARTESIAN COORDINATES (A.U.)" in line
                        ):
                            if atoms:
                                iter_atoms.append(atoms)
                            coordinate_section_started = False
                            get_coordinates = False
                            continue

                        # Parse coordinate line: element  x  y  z
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                # Ensure we can parse coordinates as floats
                                x, y, z = (
                                    float(parts[1]),
                                    float(parts[2]),
                                    float(parts[3]),
                                )
                                atoms.append(
                                    Atom(
                                        parts[0],  # element
                                        parts[1],  # x
                                        parts[2],  # y
                                        parts[3],  # z
                                        len(atoms) + 1,  # index
                                    )
                                )
                            except (ValueError, IndexError):
                                pass

        return iter_atoms

    def has_solvent(self):
        """
        :return: solvent = True/False
        """
        solvent = False
        if "Solvent" in self.orca_outdata.keys():
            solvent = True
        return solvent

    def has_frequencies(self):
        """
        Check if output contains frequency calculation
        """
        freq = False
        if "Zero-point correction" in self.orca_outdata.keys():
            freq = True
        return freq


class ORCAFrequenciesOut(ORCAOutputFile):
    def __init__(self, filepath):
        super().__init__(filepath=filepath)

        # Read output file from ORCA to get Properties self.freq_inten and self.freq_displacement dicts
        self.read_frequencies()

        # Properties setters:
        self.thermal_dg = self.get_thermal_dg
        self.thermal_dh = self.get_thermal_dh
        self.thermal_de = self.get_thermal_de
        self.zpe = self.get_zpe

    def read_frequencies(self):
        """
        Read ORCA output file and store frequencies to self.freq_inten[freq] = IR intensity
        ORCA format:
        VIBRATIONAL FREQUENCIES
        Mode    freq (cm**-1)   IR-intensity
          0:         0.00           0.000000
          1:      1234.56           1.234567
        """
        with open(self.filepath, "r") as frq:
            in_freq_section = False
            for line in frq:
                # Look for frequency section
                if "VIBRATIONAL FREQUENCIES" in line:
                    in_freq_section = True
                    continue

                if in_freq_section:
                    # Skip header lines
                    if "Mode" in line and "freq" in line:
                        continue
                    if "---" in line:
                        continue

                    # End of frequency section
                    if not line.strip() or "NORMAL MODES" in line:
                        in_freq_section = False
                        continue

                    # Parse frequency line: "  0:      1234.56         1.234567"
                    parts = line.split()
                    if len(parts) >= 3 and ":" in parts[0]:
                        try:
                            freq = float(parts[1])
                            # ORCA marks imaginary frequencies with "***imaginary mode***" comment
                            if "imaginary" in line.lower():
                                freq = -abs(freq)  # Make negative for imaginary
                            intensity = float(parts[2]) if len(parts) > 2 else 0.0
                            self.freq_inten[freq] = intensity
                        except (ValueError, IndexError):
                            pass

    def get_displacement(self, frequency):
        """
        Make Geometries object with displacements for X,Y,Z for all atoms as "coordinates"
        :param frequency: selected frequency to extract displacements from
        :return: self.freq_displacement[frequency]
        """
        # Skip reading of output file if already read and stored:
        if frequency in self.freq_displacement.keys():
            return self.freq_displacement[frequency]

        # ORCA-specific extraction of frequency displacement vectors
        found_frequency = False
        found_displacement = False
        atoms = list()

        with open(self.filepath, "r") as frq:
            current_freqs = []
            freq_index = -1

            for line in frq:
                # Look for frequency values
                if "VIBRATIONAL FREQUENCIES" in line:
                    # Start of frequency section
                    continue

                # Look for normal modes section
                if "NORMAL MODES" in line:
                    found_displacement = True
                    continue

                if found_displacement and not found_frequency:
                    # ORCA prints frequencies in normal modes section
                    # Format: "  0:         0.00 cm**-1"
                    if ":" in line and "cm**-1" in line:
                        parts = line.split()
                        try:
                            freq = float(parts[1])
                            if abs(abs(freq) - abs(float(frequency))) < 0.01:
                                found_frequency = True
                                continue
                        except (ValueError, IndexError):
                            pass

                if found_frequency:
                    # Parse displacement vectors
                    # ORCA format shows atom displacements in columns
                    if line.strip() and not line.startswith("---"):
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                atom_num = int(parts[0])
                                x, y, z = (
                                    float(parts[1]),
                                    float(parts[2]),
                                    float(parts[3]),
                                )
                                # Create atom with displacement as coordinates
                                atoms.append(
                                    Atom(
                                        f"H",  # placeholder element
                                        str(x),
                                        str(y),
                                        str(z),
                                        atom_num,
                                    )
                                )
                            except (ValueError, IndexError):
                                pass
                    elif not line.strip() and atoms:
                        # End of this mode
                        self.freq_displacement[frequency] = Geometries(
                            molecules=[atoms]
                        )
                        return self.freq_displacement[frequency]

        if atoms:
            self.freq_displacement[frequency] = Geometries(molecules=[atoms])
        return self.freq_displacement.get(frequency, None)

    @property
    def get_img_frq(self):
        """
        :return: dictionary only with imaginary frequencies
        """
        return {k: v for k, v in self.freq_inten.items() if k < 0}

    @property
    def get_frequencies(self):
        """
        :return: all frequencies
        """
        return self.freq_inten

    @property
    def get_freq_displacement(self):
        """
        :return: all frequency displacements
        """
        return self.freq_displacement

    @property
    def get_img_displacement(self):
        """
        :return: displacement for imaginary frequencies only
        """
        return {k: v for k, v in self.freq_displacement.items() if k < 0}

    @property
    def get_thermal_dg(self):
        if self._frequencies:
            return self.orca_outdata.get(
                "Thermal correction to Gibbs Free Energy", None
            )
        else:
            return None

    @property
    def get_thermal_de(self):
        if self._frequencies:
            return self.orca_outdata.get("Thermal correction to Energy", None)
        else:
            return None

    @property
    def get_thermal_dh(self):
        if self._frequencies:
            return self.orca_outdata.get("Thermal correction to Enthalpy", None)
        else:
            return None

    @property
    def get_zpe(self):
        if self._frequencies:
            return self.orca_outdata.get("Zero-point correction", None)
        else:
            return None
