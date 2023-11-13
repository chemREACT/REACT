from mods.Atoms import XYZAtom, PDBAtom


class Molecule:
    """
    Takes a list of Atom objects at init and creates molecule (dict)
    molecule[i] = Atom
    """
    def __init__(self, atoms=None, filepath=None):
        self._molecule = dict()
        if atoms:
            if isinstance(atoms, dict):
                self._molecule = atoms
                self._atoms = atoms.values()
            else:
                self._atoms = atoms
                self.make_molecule()

        self._filepath = filepath

        # Properties
        self._charge = None
        self._multiplicity = None

    def make_molecule(self):
        for i in range(len(self.atoms)):
            self._molecule[i+1] = self.atoms[i]

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, value):
        self._filepath = value

    @property
    def filename(self):
        return self.filepath.split("/")[-1]

    @property
    def file_extension(self):
        return self.filename.split(".")[-1]

    @property
    def molecule_name(self):
        return self.filename.split(".")[0]

    @property
    def charge(self):
        return self._charge

    @charge.setter
    def charge(self, value):
        self._charge = value

    @property
    def multiplicity(self):
        return self._multiplicity

    @multiplicity.setter
    def multiplicity(self, value):
        self._multiplicity = value

    @property
    def atoms(self):
        return self._atoms

    @property
    def molecule(self):
        return self._molecule

    @property
    def molecules(self):
        """
        Duplicate/special property of the molecules class created since this is called in BSB recent code... probably
        would self.atoms be better...?
        """
        return [self.atoms]

    @property
    def formatted_xyz(self):
        molecule_xyz = list()

        for i in sorted(self.molecule.keys()):
            molecule_xyz.append(self.molecule[i].formatted_xyz_line)

        return molecule_xyz

    @property
    def formatted_pdb(self):
        pdb_list = list()
        for i in sorted(self.molecule.keys()):
            pdb_list.append(self.molecule[i].formatted_pdb_line)
        return pdb_list

    @property
    def atom_count(self):
        return len(self.atoms)

    @molecule.setter
    def molecule(self, value):
        self._molecule = value

    @atoms.setter
    def atoms(self, value):
        self._atoms = value


class Geometries(Molecule):
    """
    Takes a list of molecules [[Atoms], [Atoms],... iterations SCF] typically from geometry optimisations.
    """
    def __init__(self, molecules=None, filepath=None):

        # [[Atoms], [Atoms],... iterations SCF]
        self._molecules = molecules
        self._iteration = -1
        self.faulty = False

        # Init with final molecule / geometry optimization
        super().__init__(atoms=molecules[-1], filepath=filepath)

    @property
    def molecules(self):
        return self._molecules

    @molecules.setter
    def molecules(self, value):
        self._molecules = value


    @property
    def count_molecules(self):
        return len(self._molecules)

    @property
    def iteration(self):
        return self._iteration

    @iteration.setter
    def iteration(self, value):
        if abs(value) > self.count_molecules:
            return
        self._iteration = value

        self.atoms = self._molecules[value]
        self.make_molecule()

    @property
    def all_geometries_formatted(self):
        geoms = list()
        for i in range(self.count_molecules):
            self.iteration = i
            geoms.append(self.formatted_xyz)
        return geoms


class XYZFile(Geometries):
    def __init__(self, atoms=None, filepath=None):
        # Atoms = list(Atom)
        if atoms:
            # List of Atom objects
            self._atoms = atoms

        if not atoms and filepath:
            self._filepath = filepath
            self._atoms = self.read_xyz()

        super(XYZFile, self).__init__(molecules=[self._atoms], filepath=filepath)

    def read_xyz(self):
        """
        :param filepath: path to xyz file
        :return: dict with atoms - {atom_index: {name: C, x:value, y: value, z: value}}
        """
        index = 0
        atoms = list()
        with open(self._filepath, "r") as xyz:
            for line in xyz:
                if len(line.split()) > 3:
                    index += 1
                    try:
                        atoms.append(XYZAtom(line, index))
                    except ValueError:
                        continue
        return atoms


class PDBFile(Geometries):
    def __init__(self, pdb_atoms=None, filepath=None):
        if filepath:
            self._atoms = self.read_pdb(filepath)
        elif pdb_atoms:
            self._atoms = pdb_atoms

        super().__init__(molecules=[self._atoms], filepath=filepath)

    def read_pdb(self, filepath):
        atoms = list()
        with open(filepath, "r") as pdb:
            for line in pdb:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    atoms.append(PDBAtom(line))
        return atoms






