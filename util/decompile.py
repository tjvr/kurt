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

"""Decompiles a Scratch project to a folders for each sprite containing its contents.
Images are exported to PNG or JPG format files.
Scripts are converted to scratchblocks format txt files.

    Usage: python decompile.py [path/to/file.sb]
"""

import os, sys
from os.path import join as join_path
from os.path import split as split_path


try:
    import kurt
except ImportError: # try and find kurt directory
    path_to_file = join_path(os.getcwd(), __file__)
    path_to_lib = split_path(split_path(path_to_file)[0])[0]
    sys.path.append(path_to_lib)

from kurt.files import *



class FolderExistsException(Exception):
    pass



def decompile(project):
    line_endings = "\r\n"
    
    (project_dir, name) = split_path(project.path)
    project_dir = join_path(project_dir, "%s files" % project.name)
    if os.path.exists(project_dir):
        raise FolderExistsException(project_dir)
    os.mkdir(project_dir)
    
    project.load()
    
    for sprite in project.sprites:
        sprite_dir = join_path(project_dir, sprite.name)
        os.mkdir(sprite_dir)
        
        costumes_dir = join_path(sprite_dir, "costumes")
        os.mkdir(costumes_dir)
        
        costumes_list = ""
        for costume in sprite.costumes:
            costume_path = join_path(costumes_dir, costume.name)
            
            filename = costume.save(costume_path)
            
            costumes_list += "%s\n" % filename
            costumes_list += "# Original depth: %s\n" % costume.depth
            costumes_list += "\n"
        
        if line_endings != "\n":
            costumes_list = costumes_list.replace("\n", line_endings)                
        costume_list_path = join_path(sprite_dir, "costumes.txt")
        f = open(costume_list_path, "w")
        f.write(costumes_list)
        f.flush()
        f.close()
        
        scripts_dir = join_path(sprite_dir, "scripts")
        os.mkdir(scripts_dir)
        
        i = 1
        for script in sorted(sprite.scripts, key=lambda script: script.pos.y):
            (x, y) = script.pos
            contents = "# Position: %s, %s \n" % (x, y)
            contents += "\n"
            contents += script.to_block_plugin()
            
            if line_endings != "\n":
                contents = contents.replace("\n", line_endings)
            
            script_path = join_path(scripts_dir, "script%i.txt" % i)
            f = open(script_path, "w")
            f.write(contents)
            f.flush()
            f.close()
            
            i += 1



if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        print __doc__
        exit()
    
    project = ScratchProjectFile(path, load=False)
    
    try:
        decompile(project)
    except FolderExistsException, e:
        print "Folder exists: %r" % str(e)
        exit(1)

