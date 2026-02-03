class Atom:
    """
    Class to store information for atoms.
    Coordinates, mass, name, pdb name, type etc.
    """

    def __init__(self, atom, x, y, z, index=None):
        # Atom number to atom dictionary - only most common elements. Maybe complete at some point later ... maybe not.
        self.atomnr_atom = {
            1: "H",
            2: "He",
            3: "Li",
            4: "Be",
            5: "B",
            6: "C",
            7: "N",
            8: "O",
            9: "F",
            10: "Ne",
            11: "Na",
            12: "Mg",
            13: "Al",
            14: "Si",
            15: "P",
            16: "S",
            17: "Cl",
            18: "Ar",
            19: "K",
            20: "Ca",
            24: "Cr",
            25: "Mn",
            26: "Fe",
            27: "Co",
            28: "Ni",
            29: "Cu",
            30: "Zn",
            34: "Se",
            35: "Br",
            36: "Kr",
            53: "I",
        }

        # Atom name to atom number dictionary
        self.atom_atomnr = {atom: atomnr for atomnr, atom in self.atomnr_atom.items()}

        # atom can be passed to Atom class either as atomic number or atomic name:
        if atom.isdigit():
            self._atom_nr = int(atom)
            self._atom_name = self.atomnr_atom[self.atom_nr]
        else:
            try:
                self._atom_nr = self.atom_atomnr[atom]
            except KeyError:
                self._atom_nr = None

            self._atom_name = atom

        self._x = float(x)
        self._y = float(y)
        self._z = float(z)

        self._pdb_atom_nr = None
        if index:
            self.center_number = index
            self._pdb_atom_nr = index

        self._pdb_atom_name = self.atom_name
        self._residue_name = "UNK"
        self._residue_nr = 1
        self._formatted_pdb_line = self.make_pdb_line()

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, value):
        self._z = value

    @property
    def coordinate(self):
        return self.x, self.y, self.z

    @property
    def formatted_xyz_line(self):
        return " %15s%14.8f%14.8f%14.8f" % (
            self.atom_name.ljust(15),
            self.x,
            self.y,
            self.z,
        )

    @property
    def formatted_pdb_line(self):
        return self._formatted_pdb_line

    @formatted_pdb_line.setter
    def formatted_pdb_line(self, value):
        self._formatted_pdb_line = value

    @property
    def atom_name(self):
        return self._atom_name

    @property
    def atom_nr(self):
        return self._atom_nr

    @property
    def atom_index(self):
        return int(self.center_number)

    @property
    def pdb_atom_nr(self):
        return self._pdb_atom_nr

    @pdb_atom_nr.setter
    def pdb_atom_nr(self, value):
        self._pdb_atom_nr = value

    @property
    def pdb_atom_name(self):
        return self._pdb_atom_name

    @pdb_atom_name.setter
    def pdb_atom_name(self, value):
        self._pdb_atom_name = value

    @property
    def residue_name(self):
        return self._residue_name

    @residue_name.setter
    def residue_name(self, value):
        self._residue_name = value

    @property
    def residue_nr(self):
        return self._residue_nr

    @residue_nr.setter
    def residue_nr(self, value):
        self._residue_nr = value

    def make_pdb_line(self):
        occupancy_etc = " 0.00  0.00           "
        pdb_line = (
            f"ATOM {self.pdb_atom_nr:6d}  {self.pdb_atom_name:3s} {self.residue_name:4s}{self.residue_nr:5d}    "
            f"{self.x:8.3f}{self.y:8.3f}{self.z:8.3f} {occupancy_etc}{self.atom_name}"
        )
        return pdb_line


class XYZAtom(Atom):
    """
    Takes a line from a xyz file and creates an Atom object from it
    """

    def __init__(self, atom_line=None, index=None):
        if atom_line:
            atom = atom_line.split()[0]
            x = float(atom_line.split()[1])
            y = float(atom_line.split()[2])
            z = float(atom_line.split()[3])
            super(XYZAtom, self).__init__(atom, x, y, z, index)


class GaussianAtom(Atom):
    """
    Class to store information for atom coordinates extracted from Gaussian output files.
    takes line from gaussian file and converts it into GaussianAtom object, where atom_line:
    Center     Atomic      Atomic             Coordinates (Angstroms)
    Number     Number       Type             X           Y           Z
     1          6           0       -3.809685    3.412407   -1.222092
    """

    def __init__(self, atom_line=None):
        if atom_line:
            # Gaussian atom attributes:
            center_number = int(atom_line.split()[0])

            _atomic_type = int(atom_line.split()[2])

            # Atom class attributes:
            atom = atom_line.split()[1]
            x_coordinate = float(atom_line.split()[3])
            y_coordinate = float(atom_line.split()[4])
            z_coordinate = float(atom_line.split()[5])
            super(GaussianAtom, self).__init__(
                atom, x_coordinate, y_coordinate, z_coordinate, center_number
            )

        # atom = {index: int, name: C:str, X:float, Y:float, Z:float}


class PDBAtom(Atom):
    """
    Subclass of the Atom class with additional info required by the PDB file format TODO
    Takes a line from a pdb file at init
    """

    def __init__(self, atom_line=None):
        if atom_line:
            atom_index = int(atom_line[6:11])
            atom = atom_line[76:79].strip()
            atom = "".join([i for i in atom if not i.isdigit()])
            # PDB format: X is at columns 30-38, Y at 38-46, Z at 46-54
            try:
                x_coordinate = float(atom_line[30:38].strip())
                y_coordinate = float(atom_line[38:46].strip())
                z_coordinate = float(atom_line[46:54].strip())
            except (ValueError, IndexError):
                # Fallback for non-standard PDB files
                try:
                    coords = atom_line[26:].split()
                    x_coordinate = float(coords[0])
                    y_coordinate = float(coords[1])
                    z_coordinate = float(coords[2])
                except (ValueError, IndexError):
                    raise ValueError(
                        f"Could not parse coordinates from PDB line: {atom_line}"
                    )

            super(PDBAtom, self).__init__(
                atom, x_coordinate, y_coordinate, z_coordinate, atom_index
            )

            # setters pdb info:
            self.pdb_atom_nr = int(atom_line[6:11])
            self.pdb_atom_name = atom_line[12:17].strip()
            self.res_name = atom_line[16:21]
            self.res_nr = int("".join(i for i in atom_line[21:26] if i.isdigit()))
            self.pdb_line = atom_line.strip("\n")
