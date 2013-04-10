# Copyright (C) 2012 Tim Radvan
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

"""A Kurt plugin for Scratch 1.4.


INTERNALS:

The main classes used by this package are ScratchProjectFile and
ScratchSpriteFile classes.

Most of the objects, like Stage and Sprite, inherit from :class:`UserObject`.
You can use ``.fields.keys()`` to see the available fields on one of these
objects.

:class:`FixedObjects` have a ``.value`` property to access their value. Inline
objects, such as int and bool, are converted to their Pythonic counterparts.
Array and Dictionary are converted to list and dict.

"""

import kurt
import kurt.plugin

from kurt.scratch14.objtable import *
from kurt.scratch14.files import *
from kurt.scratch14.scripts import *

try:
    from kurt.scratchblocks import parse_block_plugin
except ImportError:
    print "WARNING: parser not available, requires PLY"



# kurt_* -- objects from kurt 2.0 api from kurt/__init__.py
# v14_*  -- objects from this module, kurt.scratch14

def _load_image(v14_image):
    if not v14_image:
        return

    if v14_image.jpegBytes: # raw JPEG
        kurt_image = kurt.CostumeFromFile(v14_image.name, v14_image.jpegBytes,
                "JPEG")
        kurt_image.size = v14_image.size
        kurt_image.rotation_center = v14_image.rotationCenter
        return kurt_image

    # TODO: subclass Costume for lazy image parsing

    else: # use PIL
        return kurt.CostumeFromPIL(v14_image.name, v14_image.get_image())

def _save_image(kurt_image):
    if isinstance(kurt_image, kurt.CostumeFromFile):
        if kurt_image.format == "JPEG": # raw JPEG
            v14_image = Image(
                name = kurt_image.name,
                jpegBytes = ByteArray(kurt_image.read()),
            )
            v14_image.size = kurt_image.size
            v14_image.rotationCenter = kurt_image.rotation_center
            return v14_image

    # use PIL
    return Image.from_image(kurt_image.name, kurt_image.pil_image)

def _load_sound(v14_sound):
    pass

def _save_sound(kurt_sound):
    pass

def _load_script(v14_script):
    return kurt.Script()

def _save_script(kurt_script):
    return Script()


def _load_variable((name, value)):
    return kurt.Variable(name, value)

def _save_variable(kurt_variable):
    return (kurt_variable.name, kurt_variable.value)

def _load_lists(v14_lists): # dict
    return []

def _save_lists(kurt_lists): # MediaDict
    return {}

def _load_scriptable(kurt_scriptable, v14_scriptable):
    kurt_scriptable.scripts = map(_load_script, v14_scriptable.scripts)
    kurt_scriptable.variables = map(_load_variable,
            v14_scriptable.variables.items())
    kurt_scriptable.lists = _load_lists(v14_scriptable.lists)
    kurt_scriptable.costumes = map(_load_image, v14_scriptable.images)
    #kurt_scriptable.sounds = map(_load_sound, v14_scriptable.sounds) # TODO

    costume_index = v14_scriptable.images.index(v14_scriptable.costume)
    kurt_scriptable.costume = kurt_scriptable.costumes[costume_index]

    kurt_scriptable.volume = v14_scriptable.volume
    kurt_scriptable.tempo = v14_scriptable.tempoBPM

    if isinstance(kurt_scriptable, kurt.Sprite):
        kurt_scriptable.name = v14_scriptable.name
        kurt_scriptable.direction = v14_scriptable.rotationDegrees
        kurt_scriptable.rotation_style = v14_scriptable.rotationStyle.value
        kurt_scriptable.is_draggable = v14_scriptable.draggable

        # bounds
        (x, y, w, h) = v14_scriptable.bounds.value
        (rx, ry) = v14_scriptable.costume.rotationCenter
        x = x + rx - 240
        y = 180 - y - ry
        kurt_scriptable.position = (x, y)

def _save_scriptable(kurt_scriptable, v14_scriptable):
    v14_scriptable.scripts = map(_save_script, kurt_scriptable.scripts)
    v14_scriptable.variables = dict(map(_save_variable,
        kurt_scriptable.variables))
    v14_scriptable.lists = _save_lists(kurt_scriptable.lists)
    v14_scriptable.images = map(_save_image, kurt_scriptable.costumes)
    #v14_scriptable.sounds = map(_save_sound, kurt_scriptable.sounds) # TODO

    costume_index = kurt_scriptable.costumes.index(kurt_scriptable.costume)
    v14_scriptable.costume = v14_scriptable.images[costume_index]

    v14_scriptable.volume = kurt_scriptable.volume
    v14_scriptable.tempoBPM = kurt_scriptable.tempo

    if isinstance(kurt_scriptable, kurt.Sprite):
        v14_scriptable.name = kurt_scriptable.name
        v14_scriptable.rotationDegrees = kurt_scriptable.direction
        v14_scriptable.rotationStyle = Symbol(kurt_scriptable.rotation_style)
        v14_scriptable.draggable = kurt_scriptable.is_draggable

        # bounds
        (x, y) = kurt_scriptable.position
        (rx, ry) = kurt_scriptable.costume.rotation_center
        x = x + 240 - rx
        y = 180 - y - ry
        (w, h) = kurt_scriptable.costume.size
        v14_scriptable.bounds = Rectangle([x, y, w, h])



class Scratch14Plugin(kurt.plugin.KurtPlugin):
    def load(self, path):
        v14_project = ScratchProjectFile(path)
        kurt_project = kurt.Project()

        # project info
        kurt_project.comment = v14_project.info['comment']
        kurt_project.author = v14_project.info['author']
        kurt_project.thumbnail = _load_image(v14_project.info['thumbnail'])

        # stage
        _load_scriptable(kurt_project.stage, v14_project.stage)

        # sprites
        for v14_sprite in v14_project.sprites:
            kurt_sprite = kurt.Sprite(kurt_project)
            _load_scriptable(kurt_sprite, v14_sprite)
            kurt_project.sprites.add(kurt_sprite)

        # actors
        for v14_morph in v14_project.stage.submorphs:
            if v14_morph not in v14_project.sprites:
                pass # TODO watchers

        kurt_project.original = v14_project # DEBUG

        return kurt_project


    def save(self, path, kurt_project):
        v14_project = ScratchProjectFile.new()

        # project info
        v14_project.info['comment'] = kurt_project.comment
        v14_project.info['author'] = kurt_project.author
        v14_project.info['thumbnail'] = _save_image(kurt_project.thumbnail)

        # stage
        _save_scriptable(kurt_project.stage, v14_project.stage)

        # sprites
        for kurt_sprite in kurt_project.sprites:
            v14_sprite = Sprite()
            _save_scriptable(kurt_sprite, v14_sprite)
            v14_project.sprites.append(v14_sprite)

        # actors
        for kurt_actor in kurt_project.children:
            if kurt_actor not in kurt_project.sprites:
                pass # TODO watchers

        v14_project.save(path)

        return v14_project



kurt.plugin.Kurt.register(Scratch14Plugin())
