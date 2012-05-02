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

import codecs
def open(file, mode):
    return codecs.open(file, mode, "utf-8")


try:
    import kurt
except ImportError: # try and find kurt directory
    path_to_file = join_path(os.getcwd(), __file__)
    path_to_lib = split_path(split_path(path_to_file)[0])[0]
    sys.path.append(path_to_lib)

from kurt.files import *



class InvalidProject(Exception):
    pass

class FolderExistsException(Exception):
    pass



def log(msg):
    print msg


def write_file(path, contents, line_endings):
    if line_endings != "\n":
        contents = contents.replace("\n", line_endings)                
    
    f = open(path, "w")
    f.write(contents)
    f.flush()
    f.close()


def export_sprite(parent_dir, sprite, line_endings):
    log("* "+sprite.name)
    
    sprite_dir = join_path(parent_dir, sprite.name)
    os.mkdir(sprite_dir)

    # Scripts
    scripts_dir = join_path(sprite_dir, "scripts")
    os.mkdir(scripts_dir)
    
    scripts = sorted(sprite.scripts, key=lambda script: script.pos.y)
    
    count = 1
    for script in scripts:
        (x, y) = script.pos
        contents = "# Position: %s, %s \n" % (x, y)
        contents += "\n"
        contents += script.to_block_plugin()
        
        script_path = join_path(scripts_dir, "script%i.txt" % count)
        write_file(script_path, contents, line_endings)
        
        count += 1
    
    # Costumes/Backgrounds
    costumes_dir = join_path(sprite_dir, "costumes")
    os.mkdir(costumes_dir)
    
    costumes_list = ""
    for costume in sprite.images:
        costume_path = join_path(costumes_dir, costume.name)
        
        filename = costume.save(costume_path)
        
        (rx, ry) = costume.rotationCenter
        costumes_list += "%s\n" % filename
        costumes_list += "rotationCenter: %i, %i\n" % (rx, ry)
        costumes_list += "\n"
        
    costume_list_path = join_path(sprite_dir, "costumes.txt")
    write_file(costume_list_path, costumes_list, line_endings)


def decompile(project):
    line_endings = "\r\n"
    
    (project_dir, name) = split_path(project.path)
    project_dir = join_path(project_dir, "%s files" % project.name)
    if os.path.exists(project_dir):
        raise FolderExistsException(project_dir)
    os.mkdir(project_dir)
    
    log("Loading project %s..." % project.path)
    project.load()
    
    log("Exporting sprites...")
    export_sprite(project_dir, project.stage, line_endings)
    
    for sprite in project.sprites:
        if sprite.name == "Stage": # disallow this!
            raise InvalidProject("Can't have sprite named 'Stage'")
        
        export_sprite(project_dir, sprite, line_endings)
    
    log("Done!")



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
    except InvalidProject, e:
        print "Invalid project: %r" % str(e)
        exit(2)

