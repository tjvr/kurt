
# kurt

Python library for parsing Scratch format project (.sb) and sprite files.


## Dependencies

* [construct](http://construct.wikispaces.com/) — for defining the format. Available as "construct" in the Python package index, so if you have pip you can simply do:
    
    sudo pip install construct


## Usage

You'll probably just want to use the provided ScratchProjectFile and 
ScratchSpriteFile classes. Pass them the path to the file and use their 
provided .save() methods. Access them using:

    from kurt.files import *

Most of the objects you're interested in inherit from UserObject. You can 
use .fields to see the available fields on an object.

Tested with Python 2.6.
Works with Scratch 1.4; not tested with earlier versions, but probably works.
Scratch is created by the Lifelong Kindergarten Group at the MIT Media Lab. 
See their website: http://scratch.mit.edu/

Currently very quick at parsing files; pretty slow at writing them, particularly very large ones.