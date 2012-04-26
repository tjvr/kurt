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

"""Exports all the costumes present in a Scratch project file as PNG format.

    Usage: python export_images.py [path/to/file.sb]
"""

import os, sys

try:
    import kurt
except ImportError: # try and find kurt directory
    path_to_file = os.path.join(os.getcwd(), __file__)
    path_to_lib = os.path.split(os.path.split(path_to_file)[0])[0]
    sys.path.append(path_to_lib)

from kurt.files import *


class FolderExistsException(Exception):
    pass


def export_sprites(project):
    string = ""
    
    (project_dir, name) = os.path.split(project.path)
    project_dir = os.path.join(project_dir, "%s files" % project.name)
    
    if os.path.exists(project_dir):
        raise FolderExistsException(project_dir)
    
    os.mkdir(project_dir)
    
    for sprite in project.sprites:
        sprite_dir = os.path.join(project_dir, sprite.name)
        os.mkdir(sprite_dir)
        
        for costume in sprite.costumes:
            costume_path = os.path.join(sprite_dir, costume.name)
            costume.save(costume_path)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        print __doc__
        exit()
    
    project = ScratchProjectFile(path)
    export_sprites(project)

