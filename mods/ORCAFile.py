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
        # Note: We don't use orca_reader for all values as some need special handling
        self.orca_reader = {}

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
        ORCA output format based on actual examples:
        - Charge: 'Total Charge           Charge          ....   -1' OR '*xyz 0 1' in input section
        - Multiplicity: 'Multiplicity           Mult            ....    1' OR '*xyz 0 1' in input section
        - SCF Energy: 'FINAL SINGLE POINT ENERGY         -123.00' (avoid QM/MM or MM variants)
        - Thermochemistry: 'Zero point energy', 'Total thermal energy', 'Total Enthalpy', 'Final Gibbs free energy'
        - Convergence: Table with 'Energy change', 'RMS gradient', etc. with YES/NO
        """
        with open(self._filepath) as f:
            for line in f:
                # Extract charge and multiplicity from input section: '*xyz 0 1'
                if line.strip().startswith("*xyz") or line.strip().startswith("* xyz"):
                    parts = line.strip().split()
                    try:
                        if len(parts) >= 3:
                            # Format: *xyz charge multiplicity
                            self._charge = int(parts[1])
                            self._multiplicity = int(parts[2])
                    except (ValueError, IndexError):
                        pass

                # Extract charge: 'Total Charge           Charge          ....   -1'
                if "Total Charge" in line and "Charge" in line:
                    parts = line.split()
                    try:
                        charge_idx = parts.index("Charge")
                        # Find the numeric value after '....'
                        for i in range(charge_idx + 1, len(parts)):
                            if parts[i] != "....":
                                try:
                                    self._charge = int(parts[i])
                                    break
                                except ValueError:
                                    pass
                    except (ValueError, IndexError):
                        pass

                # Extract multiplicity: 'Multiplicity           Mult            ....    1'
                if "Multiplicity" in line and "Mult" in line:
                    parts = line.split()
                    try:
                        mult_idx = parts.index("Mult")
                        # Find the numeric value after '....'
                        for i in range(mult_idx + 1, len(parts)):
                            if parts[i] != "....":
                                try:
                                    self._multiplicity = int(parts[i])
                                    break
                                except ValueError:
                                    pass
                    except (ValueError, IndexError):
                        pass

                # Extract SCF energy (only QM, not QM/MM or MM)
                # Format: 'FINAL SINGLE POINT ENERGY         -123.00'
                if (
                    "FINAL SINGLE POINT ENERGY" in line
                    and "(QM/MM)" not in line
                    and "(MM)" not in line
                ):
                    parts = line.split()
                    try:
                        # Last element should be the energy
                        energy = float(parts[-1])
                        self.orca_outdata["SCF Done"] = energy
                    except (ValueError, IndexError):
                        pass

                # Extract Zero point energy
                # Format: 'Zero point energy                ...      0.10746477 Eh'
                if "Zero point energy" in line and "..." in line:
                    parts = line.split()
                    try:
                        # Look for the numeric value before 'Eh'
                        if "Eh" in parts:
                            eh_idx = parts.index("Eh")
                            zpe = float(parts[eh_idx - 1])
                            self.orca_outdata["Zero-point correction"] = zpe
                    except (ValueError, IndexError):
                        pass

                # Extract Total thermal energy (this is E + thermal corrections)
                # Format: 'Total thermal energy                   -157.07337829 Eh'
                if "Total thermal energy" in line and "Eh" in line:
                    parts = line.split()
                    try:
                        if "Eh" in parts:
                            eh_idx = parts.index("Eh")
                            thermal_e = float(parts[eh_idx - 1])
                            # This is the total E with thermal correction
                            # We need to calculate the correction: thermal_e - SCF_energy
                            if "SCF Done" in self.orca_outdata:
                                self.orca_outdata["Thermal correction to Energy"] = (
                                    thermal_e - self.orca_outdata["SCF Done"]
                                )
                    except (ValueError, IndexError):
                        pass

                # Extract Total Enthalpy
                # Format: 'Total Enthalpy                    ...   -157.07243408 Eh'
                if (
                    "Total Enthalpy" in line
                    and "..." in line
                    and "Total entropy" not in line
                ):
                    parts = line.split()
                    try:
                        if "Eh" in parts:
                            eh_idx = parts.index("Eh")
                            enthalpy = float(parts[eh_idx - 1])
                            # Calculate correction: enthalpy - SCF_energy
                            if "SCF Done" in self.orca_outdata:
                                self.orca_outdata["Thermal correction to Enthalpy"] = (
                                    enthalpy - self.orca_outdata["SCF Done"]
                                )
                    except (ValueError, IndexError):
                        pass

                # Extract Final Gibbs free energy
                # Format: 'Final Gibbs free energy         ...   -157.10597083 Eh'
                if "Final Gibbs free energy" in line and "..." in line:
                    parts = line.split()
                    try:
                        if "Eh" in parts:
                            eh_idx = parts.index("Eh")
                            gibbs = float(parts[eh_idx - 1])
                            # Calculate correction: gibbs - SCF_energy
                            if "SCF Done" in self.orca_outdata:
                                self.orca_outdata[
                                    "Thermal correction to Gibbs Free Energy"
                                ] = gibbs - self.orca_outdata["SCF Done"]
                    except (ValueError, IndexError):
                        pass

                # Check for convergence criteria in geometry optimization table
                # Format: 'Energy change      -0.0000044470            0.0000010000      NO'
                for conv_key, conv_name in self.convergence_keys.items():
                    if conv_key in line:
                        parts = line.split()
                        # ORCA prints "YES" or "NO" as last element in convergence table
                        if "YES" in line:
                            self.orca_outdata[conv_name] = True
                            # Also store the value and threshold
                            try:
                                # Format: criterion value threshold YES/NO
                                if len(parts) >= 4:
                                    value_key = conv_key + " Value"
                                    threshold_key = conv_key + " Threshold"
                                    # Find numeric values
                                    numeric_vals = []
                                    for p in parts:
                                        try:
                                            numeric_vals.append(float(p))
                                        except ValueError:
                                            pass
                                    if len(numeric_vals) >= 2:
                                        self.orca_outdata[value_key] = numeric_vals[0]
                                        self.orca_outdata[threshold_key] = numeric_vals[
                                            1
                                        ]
                            except (ValueError, IndexError):
                                pass
                        elif "NO" in line:
                            self.orca_outdata[conv_name] = False
                            # Also store the value and threshold
                            try:
                                if len(parts) >= 4:
                                    value_key = conv_key + " Value"
                                    threshold_key = conv_key + " Threshold"
                                    numeric_vals = []
                                    for p in parts:
                                        try:
                                            numeric_vals.append(float(p))
                                        except ValueError:
                                            pass
                                    if len(numeric_vals) >= 2:
                                        self.orca_outdata[value_key] = numeric_vals[0]
                                        self.orca_outdata[threshold_key] = numeric_vals[
                                            1
                                        ]
                            except (ValueError, IndexError):
                                pass

                # Check for solvation models
                # SMD: 'Your calculation utilizes the SMD solvation module'
                # or: 'Total Energy after SMD CDS correction'
                if "SMD solvation" in line or "SMD CDS" in line:
                    self.orca_outdata["Solvent"] = "SMD"
                # CPCM check
                elif "CPCM" in line:
                    self.orca_outdata["Solvent"] = "CPCM"

    def is_converged(self):
        """
        Set self.converged True if geometry optimization convergence criteria are met
        ORCA typically checks: Energy change, MAX gradient, RMS gradient, MAX step, RMS step
        Returns False if no convergence data found (single point calculation)
        """
        converge_terms = list()
        for entry in self.orca_outdata.keys():
            if "Converged?" in entry:
                converge_terms.append(self.orca_outdata[entry])

        # ORCA optimization is converged if all criteria are met
        if len(converge_terms) > 0:
            if all(converged_ is True for converged_ in converge_terms):
                return True
            else:
                return False

        # No convergence data found - likely a single point calculation
        return False

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
                # Extract SCF energies (only QM, not QM/MM or MM)
                # Format: 'FINAL SINGLE POINT ENERGY         -123.00'
                if (
                    "FINAL SINGLE POINT ENERGY" in line
                    and "(QM/MM)" not in line
                    and "(MM)" not in line
                ):
                    try:
                        energy = float(line.split()[-1])
                        scf_data["SCF Done"].append(energy)
                    except (ValueError, IndexError):
                        pass

                # Extract convergence criteria values from geometry optimization table
                # Format: 'Energy change      -0.0000044470            0.0000010000      NO'
                for criterion in [
                    "Energy change",
                    "MAX gradient",
                    "RMS gradient",
                    "MAX step",
                    "RMS step",
                ]:
                    if criterion in line and ("YES" in line or "NO" in line):
                        try:
                            parts = line.split()
                            # Find the first numeric value (the actual value, not threshold)
                            numeric_vals = []
                            for p in parts:
                                try:
                                    numeric_vals.append(float(p))
                                except ValueError:
                                    pass
                            if numeric_vals:
                                scf_data[criterion].append(numeric_vals[0])
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
        VIBRATIONAL FREQUENCIES - lists all modes including translations/rotations
        IR SPECTRUM - contains actual IR intensities (km/mol) for vibrational modes only
        """
        # First pass: read all frequencies from VIBRATIONAL FREQUENCIES section
        freq_list = {}
        with open(self.filepath, "r") as frq:
            in_freq_section = False
            for line in frq:
                # Look for frequency section
                if "VIBRATIONAL FREQUENCIES" in line:
                    in_freq_section = True
                    continue

                if in_freq_section:
                    # Skip header and separator lines
                    if "Mode" in line or "Scaling factor" in line or "---" in line:
                        continue
                    # Skip lines that don't have the mode number format
                    if ":" not in line:
                        continue

                    # End of frequency section
                    if (
                        not line.strip()
                        or "NORMAL MODES" in line
                        or "IR SPECTRUM" in line
                    ):
                        in_freq_section = False
                        break

                    # Parse frequency line: "  0:      1234.56 cm**-1"
                    # Format: "   6:      1623.45 cm**-1   ***imaginary mode***"
                    parts = line.split()
                    try:
                        # First part should be mode number with colon
                        if not parts[0].endswith(":"):
                            continue

                        mode_num = int(parts[0].rstrip(":"))
                        freq = float(parts[1])

                        # ORCA marks imaginary frequencies with "***imaginary mode***" comment
                        if "imaginary" in line.lower():
                            freq = -abs(freq)  # Make negative for imaginary

                        # Store with default intensity 0.0
                        freq_list[mode_num] = freq
                        self.freq_inten[freq] = 0.0
                    except (ValueError, IndexError):
                        pass

        # Second pass: read IR intensities from IR SPECTRUM section
        with open(self.filepath, "r") as frq:
            in_ir_section = False
            for line in frq:
                # Look for IR SPECTRUM section
                if "IR SPECTRUM" in line:
                    in_ir_section = True
                    continue

                if in_ir_section:
                    # Skip header and separator lines
                    if "Mode" in line or "freq" in line or "---" in line or "*" in line:
                        continue

                    # End of IR section (empty line or next section)
                    if not line.strip() or "RAMAN" in line or "THERMOCHEMISTRY" in line:
                        in_ir_section = False
                        break

                    # Parse IR line: "  7:     14.03   0.000475    2.40  0.010558  ( 0.002172  0.012368  0.101983)"
                    # Format: mode: freq eps Int T**2 ...
                    parts = line.split()
                    try:
                        if not parts[0].endswith(":"):
                            continue

                        mode_num = int(parts[0].rstrip(":"))
                        freq = float(parts[1])
                        # IR intensity is in column 3 (index 3) in km/mol
                        if len(parts) >= 4:
                            intensity = float(parts[3])
                            # Update the intensity for this frequency
                            self.freq_inten[freq] = intensity
                    except (ValueError, IndexError):
                        pass

    def get_displacement(self, frequency):
        """
        Make Geometries object with displacements for X,Y,Z for all atoms as "coordinates"
        ORCA format: NORMAL MODES section has rows organized as:
        row 0 = atom 1 X, row 1 = atom 1 Y, row 2 = atom 1 Z
        row 3 = atom 2 X, row 4 = atom 2 Y, row 5 = atom 2 Z, etc.
        Columns represent different normal modes (0, 1, 2, ...)

        :param frequency: selected frequency to extract displacements from
        :return: self.freq_displacement[frequency]
        """
        # Skip reading of output file if already read and stored:
        if frequency in self.freq_displacement.keys():
            return self.freq_displacement[frequency]

        # First, find which mode number corresponds to this frequency
        freq_to_mode = {}
        with open(self.filepath, "r") as frq:
            in_freq_section = False
            for line in frq:
                if "VIBRATIONAL FREQUENCIES" in line:
                    in_freq_section = True
                    continue

                if in_freq_section:
                    if ":" not in line or not line.strip():
                        if "NORMAL MODES" in line:
                            break
                        continue

                    parts = line.split()
                    try:
                        if parts[0].endswith(":"):
                            mode_num = int(parts[0].rstrip(":"))
                            freq = float(parts[1])
                            if "imaginary" in line.lower():
                                freq = -abs(freq)
                            freq_to_mode[freq] = mode_num
                    except (ValueError, IndexError):
                        pass

        # Find the mode number for the requested frequency
        target_mode = None
        for freq, mode in freq_to_mode.items():
            if abs(abs(freq) - abs(float(frequency))) < 0.01:
                target_mode = mode
                break

        if target_mode is None:
            return None

        # Now extract displacement vectors from NORMAL MODES section
        with open(self.filepath, "r") as frq:
            in_normal_modes = False
            reading_data = False
            mode_columns = []  # Which columns in current block?
            target_column_idx = None
            displacement_rows = []

            for line in frq:
                if "NORMAL MODES" in line:
                    in_normal_modes = True
                    continue

                if not in_normal_modes:
                    continue

                # Skip description lines
                if "Cartesian" in line or "normalized" in line or "orthogonal" in line:
                    continue

                # End of normal modes section
                if "IR SPECTRUM" in line or "RAMAN" in line:
                    break

                # Check for column header line (mode numbers)
                if line.strip() and line.split()[0].isdigit() and ":" not in line:
                    # This is a header line with mode numbers
                    mode_columns = [int(x) for x in line.split()]
                    # Check if our target mode is in this block
                    if target_mode in mode_columns:
                        target_column_idx = mode_columns.index(target_mode)
                        reading_data = True
                        displacement_rows = []
                    else:
                        reading_data = False
                    continue

                if reading_data:
                    # Data line: row_num  value1  value2  ...
                    parts = line.split()
                    if len(parts) > 1 and parts[0].isdigit():
                        try:
                            row_num = int(parts[0])
                            # Get the displacement value for our target column
                            # +1 because first column is row number
                            if len(parts) > target_column_idx + 1:
                                disp_value = float(parts[target_column_idx + 1])
                                displacement_rows.append(disp_value)
                        except (ValueError, IndexError):
                            pass
                    elif not line.strip():
                        # Empty line might end this block
                        if displacement_rows:
                            # We have data, check if next line is new mode header
                            pass

        # Convert displacement rows to atoms
        # Format: row 0=atom1_X, row 1=atom1_Y, row 2=atom1_Z, row 3=atom2_X, ...
        if displacement_rows:
            atoms = []
            num_atoms = len(displacement_rows) // 3
            for i in range(num_atoms):
                x = displacement_rows[i * 3]
                y = displacement_rows[i * 3 + 1]
                z = displacement_rows[i * 3 + 2]
                atoms.append(
                    Atom(
                        "H",  # placeholder element
                        str(x),
                        str(y),
                        str(z),
                        i + 1,
                    )
                )

            if atoms:
                self.freq_displacement[frequency] = Geometries(molecules=[atoms])
                return self.freq_displacement[frequency]

        return None

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
