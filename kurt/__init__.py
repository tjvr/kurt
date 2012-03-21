#coding=utf8
"""
kurt
Python library for parsing Scratch format project (.sb) and sprite files.

DEPENDENCIES:
    construct - for defining the format. See: http://construct.wikispaces.com/
                ["construct" in the Python package index]

USAGE:
    You'll probably just want to use the provided ScratchProjectFile and 
    ScratchSpriteFile classes. Pass them the path to the file and use their 
    provided .save() methods. Access them using:
        from kurt.files import *
    
    Most of the objects you're interested in inherit from UserObject. You can 
    use .fields to see the available fields on an object.
    
    Works with Scratch 1.4; not tested with earlier versions.
    Scratch is created by the Lifelong Kindergarten Group at the MIT Media Lab. 
    See their website: http://scratch.mit.edu/

"""
# TODO:
#   - Fill out all the _fields lists in user_objects.
#   - Implement some nice Pythonic classes for manipulating scripts.

from kurt.objtable import *
from kurt.files import *
