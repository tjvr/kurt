
# kurt

Python library for parsing Scratch format project (.sb) and sprite files.


## Dependencies

You'll need the awesome [construct](http://construct.wikispaces.com/) library — used for defining the format. Available as "construct" in the Python package index.


## Usage

You'll probably just want to use the provided `ScratchProjectFile` and `ScratchSpriteFile` classes. Construct them by passing them the path to the file and use their provided `.save()` methods.

You can import just these classes them using:

    from kurt.files import *

Most of the objects you're interested in inherit from `UserObject`. You can 
use `.fields.keys()` to see the available fields on one of these objects.

Tested with Python 2.6.
Works with Scratch 1.4; not tested with earlier versions, but probably works.
[Scratch](http://scratch.mit.edu/) is created by the Lifelong Kindergarten Group at the MIT Media Lab.

kurt is currently very quick at parsing files; but pretty slow at writing them, particularly very large ones.

## TODO

- Fill out all the _fields lists in user_objects. (Need to look at the Squeak source to find the field names.)
- Implement some nice Pythonic classes for manipulating scripts.
- Optimise ObjectNetworkAdapter for building large files.
