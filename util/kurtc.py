#!/usr/bin/python
#coding=utf8

# Copyright © 2012 Tim Radvan
# 
# This file is part of Kurt.
# 
# Kurt is free software: you can redistribute it and/or modify it under the 
# terms of the GNU Lesser General Public License as published by the Free 
# Software Foundation, either version 3 of the License, or (at your option) any 
# later version.
# 
# Kurt is distributed in the hope that it will be useful, but WITHOUT ANY 
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR 
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more 
# details.
# 
# You should have received a copy of the GNU Lesser General Public License along 
# with Kurt. If not, see <http://www.gnu.org/licenses/>.

"""Scratch project  <--->  folder structure of scripts and images

Usage: kurt.py decompile "path/to/file.sb"
       kurt.py compile "path/to/project files/"

decompile: scratch project  -> folders containing its contents
compile:   folder structure -> scratch project.

Folder structure:
    00 Stage/                 [each sprite has its own directory]
        backgrounds/
        ...
    01 Sprite 1/
        costumes/             [export to PNG or JPG format files, 
            01 costume1.png    import from most formats]
            02 costume2.jpg
            ...
        costumes.txt          [costume details: rotation centers]
        lists/                [.txt files, item per line]
        scripts/              [.txt files: block plugin (scratchblocks) syntax]
            01 when green flag clicked.txt
            ...
        variables.txt         [variable = value, one per line]
"""

import os
import sys

try:
    import kurt
except ImportError: # try and find kurt directory
    path_to_file = os.path.join(os.getcwd(), __file__)
    path_to_lib = os.path.split(os.path.split(path_to_file)[0])[0]
    sys.path.append(path_to_lib)

from kurt.compiler import cmd_compile
from kurt.decompiler import cmd_decompile



if __name__ == '__main__':
    command = None
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        path = None
        if len(sys.argv) > 2:
            path = sys.argv[2]
    
    if not command:
        print __doc__
    
    else:
        if command == "decompile":
            cmd_f = cmd_decompile
        elif command == "compile":
            cmd_f = cmd_compile
        else:
            print __doc__
            cmd_f = None
        
        if cmd_f:
            if path:
                project = cmd_f(path)
            else:
                print cmd_f.__doc__
