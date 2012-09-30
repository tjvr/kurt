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

"""Decompiles a Scratch project to folders containing its contents.
Exports images to PNG or JPG format files.
Exports scripts to .txt files with block plugin (scratchblocks) syntax.

    Usage: decompile.py "path/to/file.sb" """

import time
import os, sys

import codecs
def open(file, mode="r"):
    return codecs.open(file, mode, "utf-8")


try:
    import kurt
except ImportError: # try and find kurt directory
    path_to_file = os.path.join(os.getcwd(), __file__)
    path_to_lib = os.path.split(os.path.split(path_to_file)[0])[0]
    sys.path.append(path_to_lib)

from kurt.files import ScratchProjectFile, ScratchSpriteFile
from kurt import Stage

#from compiler import read_script_file ### DEBUG
import cStringIO


class InvalidProject(Exception):
    pass

class FolderExistsException(Exception):
    pass

class FileNotFoundException(Exception):
    pass


def log(msg, newline=True):
    if newline:
        print msg
    else:
        print msg, 


def write_file(path, contents, line_endings):
    if line_endings != "\n":
        contents = contents.replace("\n", line_endings)                
    
    f = open(path, "w")
    f.write(contents)
    f.flush()
    f.close()


def escape_filename(name):
    """Return name stripped of non-filename-friendly characters"""
    name = name.replace("/", "")
    return name


def export_sprite(parent_dir, sprite, number, line_endings, debug):
    log("* "+sprite.name, False)
    start_time = time.time()
    
    name = escape_filename(sprite.name)
    num_text = str(number)
    if len(num_text) == 1: num_text = "0"+num_text
    name = num_text + " " + name
    sprite_dir = os.path.join(parent_dir, name)
    os.mkdir(sprite_dir)

    # Scripts
    scripts_dir = os.path.join(sprite_dir, "scripts")
    os.mkdir(scripts_dir)
    
    scripts = sorted(sprite.scripts, key=lambda script: script.pos.y)
    
    count = 1
    for script in scripts:
        (x, y) = script.pos
        contents = "Position: %s, %s \n" % (x, y)
        contents += "\n"
        contents += script.to_block_plugin()

        count_text = str(count)
        if len(count_text) == 1: count_text = "0"+count_text
        name = count_text + " "
        name += escape_filename(script.blocks[0].to_block_plugin().split('\n')[0])
        
        script_path = os.path.join(scripts_dir, name+".txt")
        write_file(script_path, contents, line_endings)
        
        count += 1
        
        ### DEBUG
        #test = read_script_file(sprite, script_path)
        if 0 and test != script: ### DEBUG
            def compare(script_a, script_b, stack='script'):
                i = 0
                for (block_a, block_b) in zip(script_a, script_b):
                    if block_a != block_b:
                        print stack + '[%i]' % i
                        print block_a.type
                        print block_b.type
                        
                        done_args = False
                        j = 0
                        
                        if len(block_a.args) != len(block_b.args):
                            # weird.
                            if len(filter(None, block_a.args)) == len(filter(None, block_b.args)):
                                print "SECRETLY THE SAME"
                                continue
                        
                        for (arg_a, arg_b) in zip(block_a.args, block_b.args):
                            if arg_a != arg_b:
                                if isinstance(arg_a, list):
                                    assert isinstance(arg_b, list)
                                    compare(arg_a, arg_b, stack + '[%i]' % i + '.args[%i]' % j)
                                    done_args = True
                                else:
                                    print ' ', arg_a, arg_b
                            j += 1
                        
                        if not done_args:
                            print block_a
                            print block_b
                    i += 1
            
            print
            compare(script, test)
    
    
    # Costumes/Backgrounds
    if isinstance(sprite, Stage):
        costumes_dir = os.path.join(sprite_dir, "backgrounds")
    else:
        costumes_dir = os.path.join(sprite_dir, "costumes")
    
    os.mkdir(costumes_dir)
    
    count = 1
    costumes_list = ""
    for costume in sprite.images:
        count_text = str(count)
        if len(count_text) == 1: count_text = "0"+count_text
        name = count_text + " " + escape_filename(costume.name)
        costume_path = os.path.join(costumes_dir, name)
        
        filename = costume.save(costume_path)
        
        (rx, ry) = costume.rotationCenter
        costumes_list += "%s\n" % filename
        costumes_list += "rotationCenter: %i, %i\n" % (rx, ry)
        if costume == sprite.costume:
            costumes_list += "selected\n"
        
        if debug == True: # DEBUG
            if costume.form:
                costumes_list += "# depth: %i\n" % costume.form.depth
        
        costumes_list += "\n"
        count += 1
    
    costume_list_path = costumes_dir+".txt"
    write_file(costume_list_path, costumes_list, line_endings)
    
    
    # Variables
    var_list = ""
    var_names = sorted(sprite.variables.keys())
    for var_name in var_names:
        value = sprite.variables[var_name]
        if " = " in var_name:
            raise InvalidProject("Invalid variable name %s" % var_name)
        var_list += var_name + " = " + unicode(value)
        var_list += "\n"
    
    var_list_path = os.path.join(sprite_dir, "variables.txt")
    write_file(var_list_path, var_list, line_endings)
    
    
    # Lists
    lists_dir = os.path.join(sprite_dir, "lists")
    os.mkdir(lists_dir)
    for slist in sprite.lists.values():
        list_path = os.path.join(lists_dir, slist.name+".txt")
        contents = "\n".join(slist.items)
        write_file(list_path, contents, line_endings)
    
    
    sprite_save_time = time.time() - start_time
    log(sprite_save_time)



def decompile(project, debug=True): # DEBUG: set to false
    start_time = time.time()
    
    line_endings = "\r\n"
    
    if not os.path.exists(project.path):
        raise FileNotFoundException(project.path)
    
    (project_dir, name) = os.path.split(project.path)
    project_dir = os.path.join(project_dir, "%s files" % project.name)
    if os.path.exists(project_dir):
        raise FolderExistsException(project_dir)
    os.mkdir(project_dir)
    
    log("Loading project %s..." % project.path)
    project.load()
    
    # Thumbnail
    thumb = project.info["thumbnail"]
    if thumb:
        log("Exporting thumbnail...", False)
        thumb_path = os.path.join(project_dir, "thumbnail.png")
        thumb.save(thumb_path)
        log("Done.")
    
    # Notes
    notes = project.info["comment"]
    notes_path = os.path.join(project_dir, "notes.txt")
    f = open(notes_path, 'w')
    f.write(notes.replace('\n', line_endings))
    f.close()
        
    # Sprites
    decompile_start_time = time.time()
    
    log("Exporting sprites...")
    export_sprite(project_dir, project.stage, 0, line_endings, debug)
    
    number = 1
    for sprite in project.sprites:
        if sprite.name in ("Stage", "_Stage"): # disallow this!
            raise InvalidProject("Can't have sprite named 'Stage'")
        
        export_sprite(project_dir, sprite, number, line_endings, debug)
        number += 1
    
    decompile_time = time.time() - decompile_start_time
    log("Decompiled! %f" % decompile_time)
    
    log("")
    
    total_time = time.time() - start_time
    log("Total %f secs" % total_time)



def cmd_decompile(path):    
    """Usage: decompile.py "path/to/file.sb" 

    scratch project -> folder structure with project contents"""
    
    if path.endswith(".sb"):
        path = path[:-3]
    if path.endswith(" files"):
        path = path[:-6]
    
    project = ScratchProjectFile(path, load=False)
    
    try:
        decompile(project)
    except FolderExistsException, e:
        print "Folder exists: %s" % unicode(e)
    except FileNotFoundException, e:
        print "File missing: %s" % unicode(e)
    except InvalidProject, e:
        print "Invalid project: %s" % unicode(e)
    
    return project # useful for debugging



if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print __doc__
        exit()
        
    else:
        path = sys.argv[1]
        cmd_decompile(path)

