from PyQt5.QtWidgets import QColorDialog
import random
import numpy as np
import json

unicode_symbols = {"delta": "\u03b4", "Delta": "\u0394"}


def random_color():
    """
    :return: Hex Color Code
    """
    return f"#{random.randrange(0x1000000):06x}"


def select_color(parent=None, return_hex=True):
    """
    Opens QColorDialog where user selects color.
    :return_hex: Return hex color code
    :return: Hex Color Code (hex=True), else RGB tuple will be returned (r,g,b)
    """
    color = QColorDialog.getColor(parent=parent)
    if return_hex:
        return color
    else:
        color = color.lstrip("#")
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def hartree_to_kcal(au):
    """
    :param au: Hartree /atomic units
    :return: kcal
    """
    return float(au) * 627.51


def hartree_to_kjoul(au):
    """
    :param au: Hartree /atomic units
    :return: kjoul
    """
    return float(au) * 2625.51


def is_number(s):
    """
    Check if string is a float value
    :param s: string or anything
    :return: True/False for s is float
    """
    try:
        float(s)
        return True
    except:
        return False


def json_hook_int_bool_converter(obj):
    """
    Used as object hook when calling json.load()
    Will convert a key-object of type str into type int, if possible
    """
    new_dict = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            new_dict_sub = {}
            for k_sub, v_sub in v.items():
                if v_sub == "false":
                    new_dict_sub[k_sub] = False
                elif v_sub == "true":
                    new_dict_sub[k_sub] = True

                else:
                    try:
                        new_k_sub = int(k_sub)
                        new_dict_sub[new_k_sub] = v[k_sub]
                    except ValueError:
                        new_dict_sub[k] = v[k_sub]

            new_dict[k] = new_dict_sub

        if v == "false":
            new_dict[k] = False
        elif v == "true":
            new_dict[k] = True
        else:
            try:
                new_k = int(k)
                new_dict[new_k] = obj[k]
            except ValueError:
                new_dict[k] = obj[k]

    return new_dict


def load_json(json_path, json_hook=False):
    with open(json_path, "r") as json_file:
        obj = json.load(json_file, object_hook=json_hook)

    return obj


def dump_json(json_path, obj):
    with open(json_path, "w") as json_file:
        json_file.dump(obj)


def write_file(list_stuff, path):
    """
    Takes a list of lines and writes file to path
    :param list_stuff: list()
    :param path: str()
    :return: path: str()
    """
    _file = open(path, "w")
    for line in list_stuff:
        _file.write(line + "\n")
    _file.close()


def find_ligands_pdbfile(pdbfile):
    """
    Reads through a PDB file and identifies residue_names that har not amino acids or similar. Used for highlighting
    ligands in pymol.
    :param pdbfile: path to pdb file.
    :return: resnames (list of non-protein residue names)
    """
    residues = list()

    res_ignore = [
        "GLY",
        "HIS",
        "HID",
        "HIP",
        "HIE",
        "ALA",
        "VAL",
        "ILE",
        "CYS",
        "MET",
        "TYR",
        "ASP",
        "GLU",
        "ARG",
        "LYS",
        "PHE",
        "TRP",
        "ASN",
        "GLN",
        "SER",
        "AR+",
        "LY+",
        "GL-",
        "AS-",
        "PRO",
        "LEU",
        "THR",
    ]
    # N-terminals (Q-style)
    res_ignore += ["N%s" % x for x in res_ignore]
    # C-terminals (Q-style)
    res_ignore += ["C%s" % x for x in res_ignore]
    # ions etc.
    res_ignore += ["CL-", "CLA", "HOH", "WAT", "Cl-", "SOD", "Na+", "NA+"]

    with open(pdbfile, "r") as pdb:
        for line in pdb:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                res = line[17:21].strip()
                if res not in res_ignore:
                    if res not in residues:
                        residues.append(res)

    return residues


def atom_distance(a1, a2):
    """
    :param a1: [x,y,z]
    :param a2: [x,y,z]
    :return: radois (float)
    """
    return np.sqrt(
        (float(a2[0]) - float(a1[0])) ** 2
        + (float(a2[1]) - float(a1[1])) ** 2
        + (float(a2[2]) - float(a1[2])) ** 2
    )


def detect_software_type(filepath):
    """
    Detects whether a computational chemistry file is from Gaussian or ORCA
    by examining the file content.

    :param filepath: path to input or output file
    :return: "Gaussian", "ORCA", or "Unknown"
    """
    gaussian_markers = [
        "Gaussian(R) 16",
        "Gaussian(R) 09",
        "Gaussian, Inc.",
        "%chk=",
        "%mem=",
        "%nproc=",
        " Entering Gaussian System",
        "Gaussian 09",
        "Gaussian 16",
        "Entering Link 1",
        "l1.exe",
        "l9.exe",
        "g16",
        "g09",
    ]

    # Gaussian route card indicators (only check at start of file)
    gaussian_route_markers = ["#p ", "#n ", "#t ", "# "]

    # ORCA simple input markers (only check at start of file)
    orca_simple_input_markers = ["! "]

    orca_markers = [
        "O   R   C   A",
        "* O R C A *",
        "An Ab Initio, DFT and Semiempirical electronic structure package",
        "%pal",
        "%maxcore",
        "* xyz",
        "*xyz",
        "*xyzfile",
        "* xyzfile",
        "%method",
        "%scf",
        "%basis",
        "ORCA TERMINATED NORMALLY",
        "Max Planck Institute fuer Kohlenforschung",
        "Department of theory and spectroscopy",
        "Directorship and core code : Frank Neese",
        "ORCA GEOMETRY:",
        "FINAL SINGLE POINT ENERGY",
        "---An Ab Initio",
    ]

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            # Read first 100 lines - should be enough to identify software
            lines_to_check = 100
            gaussian_score = 0
            orca_score = 0

            for i, line in enumerate(f):
                if i >= lines_to_check:
                    break

                line_lower = line.lower()
                line_stripped = line.strip()

                # Check for Gaussian markers
                for marker in gaussian_markers:
                    if marker.lower() in line_lower:
                        gaussian_score += 1
                        # Strong indicators get extra weight
                        if "gaussian" in marker.lower():
                            gaussian_score += 2
                        break  # Count each line only once

                # Check for ORCA simple input (! keyword) - only in first 20 lines
                if i < 20:
                    for orca_simple in orca_simple_input_markers:
                        if line_stripped.startswith(orca_simple.strip()):
                            orca_score += 3  # Very strong indicator
                            break

                # Check for Gaussian route cards only in first 10 lines
                # But skip if we already detected ORCA simple input
                if i < 10 and orca_score == 0:
                    for route_marker in gaussian_route_markers:
                        if line_stripped.startswith(route_marker.strip()):
                            gaussian_score += 2  # Strong indicator
                            break

                # Check for ORCA markers
                for marker in orca_markers:
                    if marker.lower() in line_lower:
                        orca_score += 1
                        # Strong indicators get extra weight
                        if "o   r   c   a" in line_lower or "* o r c a *" in line_lower:
                            orca_score += 3
                        break  # Count each line only once

            # Determine software based on scores
            if gaussian_score > orca_score and gaussian_score > 0:
                return "Gaussian"
            elif orca_score > gaussian_score and orca_score > 0:
                return "ORCA"
            else:
                return "Unknown"

    except (IOError, UnicodeDecodeError) as e:
        print(f"Error reading file {filepath}: {e}")
        return "Unknown"
