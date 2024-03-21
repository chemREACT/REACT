# REACT  <img src="/resources/platform_icons/mac/128.png" height="128" align="right" />
Development of a GUI for setting up and analysing DFT reaction (free) energies.

We recomend that you set up your python environment with homebrew. If you do not have homebrew, you can install this with 
<code>/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"</code>

**Quick install:**
* `./install.sh`

Install python environment from requirements.txt. 

<strong>General dependencies</strong>
<ul>
  <li>Python3.9 (<code>brew install python@3.9 </code>)
    <ul>
    <li> Want to use a different python3 version? See ** at the end of this file</li>
  </ul> </li>
  <li>PyQt5 (<code>python -m pip install pyqt5 </code>) </li>
  <li>Matplotlib (<code>python -m pip install matplotlib </code>)</li>
  <li>Numpy (<code>python -m pip install numpy </code>)</li>
  <li>OpenGL (<code>python -m pip install pyOpenGL </code>)</li>
  
</ul>

<strong> Making bundle App (mac) / exe binary (win) / unix binary (linux) with pyinstaller 4.2 </strong>
Install pyinstaller (<code>python -m pip install pyinstaller</code>).
The pyinstaller spec files for REACT and Open Source Pymol are already created, so all we now have to do is to run then,

Make Open Source Pymol bundle:
<ol>
  <li>Go to /OpenSourcePymol and run <code> pyinstaller OpenSourcePymol.spec </code></li>
  <li>Verify that the bundle runs. On MAC: <code> open OpenSourcePymol/dist/OpenSourcePymol.app (mac) </code>.</li>
Now, create the REACT bundle, which now includes the Open Source Pymol binary:
  <li>Go to root (where REACT.py is) and run <code>pyinstaller REACT.spec</code></li>
  <li>Verify that the bundle runs. On Mac: <code> open dist/REACT.app</code> </li>
</ol>


<strong>** Running python3 version different than 3.9.</strong>
If you will not be using the included Open Source Pymol, REACT can most likely be run from source and compiled with any python3 version compatible with PyQt5. If you already have a local pymol version, you can point to this in the REACT settings and set it as your pymol for REACT.

If you would like to use Open Source Pymol, you will need to compile it with your python version (version != 3.9). To do this, follow the instructions given at the official <a href="https://github.com/schrodinger/pymol-open-source">Open Source Pymol Github repository</a> to compile it. Go to the path where you installed Open Source Pymol and cd into "site-packages" (where you see the directories pymol, pymol2, pmg_qt etc.). Do <code>cp -r * path_to_REACT/OpenSourcePymol/</code> to replace our python3.9 version of Open Source Pymol with yours. Now you can follow the steps above to make the REACT/OpenSourcePymol binary/bundle/app. Good luck :) 



Now you can take the included pyinstaller OpenSourcePymol.spec and run it.

## Known bugs:
- Stuctures missing in PyMOL window. Closing and re-opening PyMOL window will correctly import all strucutres in the REACT workspace.

