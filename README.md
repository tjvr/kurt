# kurt

Kurt's a Python library for working with Scratch project files.

It supports both Scratch 1.4 and Scratch 2.0 with a single Pythonic interface, and it's extensible to support new file formats (for Scratch derivatives such as [Snap!](http://snap.berkeley.edu/)).

Example uses:

* converting Scratch 2.0 projects back to 1.4
* importing midi files as play note blocks
* importing font files as costumes
* analysing projects

It also includes a parser for [Block Plugin](http://wiki.scratch.mit.edu/wiki/Block_Plugin) syntax code.

*[Scratch](http://scratch.mit.edu/) is created by the Lifelong Kindergarten Group at the MIT Media Lab.*


## Installation

*This is the dev branch for Kurt 2.0 -- just clone the Git repo for now*

With a proper python environment (one which has [pip](http://www.pip-installer.org/en/latest/installing.html) available), simply run:

    pip install kurt

Or using `easy_install`:

    easy_install kurt

Or [download the compressed archive from PyPI](http://pypi.python.org/pypi/kurt), extract it, and inside it run:

    python setup.py install


## Requirements

Requires at least Python 2.6. Doesn't support Python 3.

The installation methods above will automatically install kurt and its dependencies. To do a manual install instead, you need:

* **[Construct](http://github.com/construct/construct/tree/2.06)** version 2.0.6

* **[Pillow](http://python-imaging.github.io/)**

* **[PLY](http://www.dabeaz.com/ply/)**


## Documentation

Kurt's documentation is hosted [on Read the Docs](http://kurt.readthedocs.org/).


## Credits

* Thanks to [bboe](http://github.com/bboe) for the setup script and `default_colormap`.


## Licence

Kurt is released under the [LGPL](http://www.gnu.org/licenses/lgpl) Version 3 (or any later version).

