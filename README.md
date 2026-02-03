# REACT  <img src="/resources/platform_icons/mac/128.png" height="128" align="right" />
Development of a GUI for setting up and analysing DFT reaction (free) energies.

We recomend that you set up your python environment with homebrew. If you do not have homebrew, you can install this with 
<code>/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"</code>

**Quick Install:**
```bash
./install.sh
source venv/bin/activate
python3 REACT.py
```

This will create a Python virtual environment and install all dependencies from `requirements.txt`.

<strong>System Requirements</strong>
<ul>
  <li>Python 3.10+
  <li>PyMOL 
</ul>


## PyMOL Setup



This software require PyMOL installed on your computer. When first using REACT, you need to set the path to your installation:

1. Open REACT Settings (Settings button in main window)
2. Enable "Use external PyMOL"
3. Set path to PyMOL executable (e.g., `/usr/local/bin/pymol` or typically `/Applications/PyMOL.app/Contents/MacOS/PyMOL` on mac, or try `which pymol` for source builds)

REACT also work with the free open-source version of PyMOL: https://github.com/schrodinger/pymol-open-source

