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

"""A Kurt plugin for Scratch 1.4."""

import kurt
from kurt.plugin import Kurt, KurtPlugin

from kurt.scratch14.objtable import *
from kurt.scratch14.files import *
from kurt.scratch14.scripts import *

try:
    from kurt.scratchblocks import parse_block_plugin
except ImportError:
    pass



# The main classes used by this package are ScratchProjectFile and
# ScratchSpriteFile classes.
#
# Most of the objects, like Stage and Sprite, inherit from :class:`UserObject`.
# You can use ``.fields.keys()`` to see the available fields on one of these
# objects.
#
# :class:`FixedObjects` have a ``.value`` property to access their value. Inline
# objects, such as int and bool, are converted to their Pythonic counterparts.
# Array and Dictionary are converted to list and dict.



# kurt_* -- objects from kurt 2.0 api from kurt/__init__.py
# v14_*  -- objects from this module, kurt.scratch14

def _load_image(v14_image):
    if not v14_image:
        return
    name = v14_image.name

    if v14_image.jpegBytes: # raw JPEG
        kurt_image = kurt.CostumeFromFile(v14_image.jpegBytes,
                "JPEG")
        kurt_image.size = v14_image.size
        kurt_image.rotation_center = v14_image.rotationCenter
        return (name, kurt_image)

    # TODO: subclass Costume for lazy image parsing

    else: # use PIL
        return (name, kurt.CostumeFromPIL(v14_image.get_image()))

def _save_image((name, kurt_image)):
    if not kurt_image:
        return

    if isinstance(kurt_image, kurt.CostumeFromFile):
        if kurt_image.format == "JPEG": # raw JPEG
            v14_image = Image(
                name = name,
                jpegBytes = ByteArray(kurt_image.read()),
            )
            v14_image.size = kurt_image.size
            v14_image.rotationCenter = kurt_image.rotation_center
            return v14_image

    # use PIL
    return Image.from_image(name, kurt_image.pil_image)

def _load_sound(v14_sound):
    pass

def _save_sound(kurt_sound):
    pass

def _load_block(v14_block):
    args = []
    for arg in v14_block.args:
        if isinstance(arg, Block):
            arg = _load_block(arg)
        elif isinstance(arg, list):
            arg = map(_load_block, arg)
        elif isinstance(arg, Symbol): # TODO: translate these
            arg = arg.value
        args.append(arg)
    return kurt.Block(v14_block.command, *args)

def _load_script(v14_script):
    return kurt.Script(
        map(_load_block, v14_script.blocks),
        pos = v14_script.pos,
    )

def _save_block(kurt_block):
    args = []
    for arg in kurt_block.args:
        if isinstance(arg, kurt.Block):
            arg = _save_block(arg)
        elif isinstance(arg, list):
            arg = map(_save_block, arg)
        args.append(arg)

    cmd = kurt_block.type.scratch14_command
    if cmd == "changeVariable":
        args[1] = Symbol(args[1])

    return Block(cmd, *args)

def _save_script(kurt_script):
    return Script(
        kurt_script.pos,
        map(_save_block, kurt_script.blocks),
    )

def _load_variable((name, value)):
    return (name, kurt.Variable(name, value))

def _save_variable((name, kurt_variable)):
    return (name, kurt_variable.value)

def _load_lists(v14_lists, kurt_project):
    kurt_lists = {}
    for v14_list in v14_lists.values():
        kurt_list = kurt.List(map(unicode, v14_list.items))

        kurt_watcher = kurt.Watcher(kurt_list)
        kurt_watcher.visible = bool(v14_list.owner)

        (x, y, w, h) = v14_list.bounds.value
        if not kurt_watcher.visible:
            x -= 534
            y -= 71
        kurt_watcher.pos = (x, y)
        kurt_project.actors.append(kurt_watcher)

        kurt_lists[v14_list.name] = kurt_list

    return kurt_lists

def _save_lists(kurt_lists, v14_morph, v14_project):
    for (name, kurt_list) in kurt_lists.items():
        v14_list = ScratchListMorph(
            name = name,
            items = kurt_list.items,
        )

        pos = kurt_list.watcher.pos
        if pos:
            (x, y) = pos
        else:
            (x, y) = (375, 10)
            # TODO: stack them prettily!

        if not kurt_list.watcher.visible:
            x += 534
            y += 71
        v14_list.bounds = Rectangle([x, y, x+95, y+115])

        v14_list.target = v14_morph
        if kurt_list.watcher.visible:
            v14_list.owner = v14_project.stage
            v14_project.stage.submorphs.append(v14_list)

        v14_morph.lists[v14_list.name] = v14_list

def _load_scriptable(kurt_scriptable, v14_scriptable):
    kurt_scriptable.scripts = map(_load_script, v14_scriptable.scripts)
    kurt_scriptable.variables = dict(map(_load_variable,
            v14_scriptable.variables.items()))
    kurt_scriptable.costumes = dict(map(_load_image, v14_scriptable.images))
    # kurt_scriptable.sounds = dict(map(_load_sound, v14_scriptable.sounds) # TODO

    costume_index = v14_scriptable.images.index(v14_scriptable.costume)
    kurt_scriptable.costume = kurt_scriptable.costumes.values()[costume_index]

    kurt_scriptable.volume = v14_scriptable.volume
    kurt_scriptable.tempo = v14_scriptable.tempoBPM

    # sprite
    if isinstance(kurt_scriptable, kurt.Sprite):
        kurt_scriptable.name = v14_scriptable.name
        kurt_scriptable.direction = v14_scriptable.rotationDegrees
        kurt_scriptable.rotation_style = v14_scriptable.rotationStyle.value
        kurt_scriptable.is_draggable = v14_scriptable.draggable

        # bounds
        (x, y, right, bottom) = v14_scriptable.bounds.value
        (rx, ry) = v14_scriptable.costume.rotationCenter
        x = x + rx - 240
        y = 180 - y - ry
        kurt_scriptable.position = (x, y)

def _save_scriptable(kurt_scriptable, v14_scriptable):
    v14_scriptable.scripts = user_objects.ScriptCollection(
            map(_save_script, kurt_scriptable.scripts))
    v14_scriptable.variables = dict(map(_save_variable,
        kurt_scriptable.variables.items()))
    v14_scriptable.images = map(_save_image, kurt_scriptable.costumes.items())
    #v14_scriptable.sounds = map(_save_sound, kurt_scriptable.sounds) # TODO

    if kurt_scriptable.costume:
        costume_index = kurt_scriptable.costumes.values().index(kurt_scriptable.costume)
        v14_scriptable.costume = v14_scriptable.images[costume_index]

    v14_scriptable.volume = kurt_scriptable.volume
    v14_scriptable.tempoBPM = kurt_scriptable.tempo

    # sprite
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
        v14_scriptable.bounds = Rectangle([x, y, x+w, y+h])



class Scratch14Plugin(KurtPlugin):
    name = "scratch14"
    display_name = "Scratch 1.4"
    extension = ".sb"

    def load(self, path):
        v14_project = ScratchProjectFile(path)
        kurt_project = kurt.Project()

        # project info
        kurt_project.notes = v14_project.info['comment']
        kurt_project.author = v14_project.info['author']
        (_, kurt_project.thumbnail) = _load_image(v14_project.info['thumbnail'])

        # stage
        _load_scriptable(kurt_project.stage, v14_project.stage)
        kurt_project.lists = _load_lists(v14_project.stage.lists, kurt_project)
        
        # global vars
        kurt_project.variables = kurt_project.stage.variables
        kurt_project.stage.variables = {}

        # sprites
        for v14_sprite in v14_project.sprites:
            kurt_sprite = kurt.Sprite(v14_sprite.name)
            _load_scriptable(kurt_sprite, v14_sprite)
            kurt_sprite.lists = _load_lists(v14_sprite.lists, kurt_project)
            kurt_project.sprites.append(kurt_sprite)

        # variable watchers
        for v14_morph in v14_project.stage.submorphs:
            if v14_morph in v14_project.sprites:
                continue
            if isinstance(v14_morph, WatcherMorph):
                v14_watcher = v14_morph

                v14_sprite = v14_watcher.readout.target
                if v14_sprite == v14_project.stage:
                    kurt_thing = kurt_project
                else:
                    kurt_thing = kurt_project.get_sprite(v14_sprite.name)

                name = v14_watcher.readout.parameter
                kurt_var = kurt_thing.variables[name]

                kurt_watcher = kurt.Watcher(kurt_var)

                (x, y, right, bottom) = v14_watcher.bounds.value
                kurt_watcher.pos = (x, y)

                if v14_watcher.isLarge:
                    kurt_watcher.style = "large"
                elif v14_watcher.scratchSlider:
                    kurt_watcher.style = "slider"

                kurt_project.actors.append(kurt_watcher)
        
        # TODO: stacking order of actors.

        kurt_project.original = v14_project # DEBUG

        return kurt_project


    def save(self, path, kurt_project):
        v14_project = ScratchProjectFile.new()

        # project info
        v14_project.info['comment'] = kurt_project.notes
        v14_project.info['author'] = kurt_project.author
        v14_project.info['thumbnail'] = _save_image(("thumbnail", 
                kurt_project.thumbnail))

        # stage
        _save_scriptable(kurt_project.stage, v14_project.stage)
        _save_lists(kurt_project.lists, v14_project.stage, v14_project)
        v14_project.stage.variables = dict(map(_save_variable,
            kurt_project.variables))

        # sprites
        for kurt_sprite in kurt_project.sprites:
            v14_sprite = Sprite()
            _save_scriptable(kurt_sprite, v14_sprite)
            _save_lists(kurt_sprite.lists, v14_sprite, v14_project)
            v14_project.sprites.append(v14_sprite)

        # variable watchers
        for kurt_actor in kurt_project.actors:
            if kurt_actor in kurt_project.sprites:
                v14_project.stage.submorphs.append(
                    v14_project.sprites[kurt_actor.name]
                )
                continue

            if isinstance(kurt_actor, kurt.Watcher):
                kurt_watcher = kurt_actor
                if isinstance(kurt_watcher.value, kurt.List):
                    continue

                if not kurt_watcher.visible:
                    continue

                v14_watcher = WatcherMorph()

                if kurt_watcher.pos:
                    (x, y) = kurt_watcher.pos
                else:
                    (x, y) = (10, 10)

                kurt_parent = kurt_watcher.value.parent
                if kurt_parent == kurt_project:
                    v14_morph = v14_project.stage
                    v14_watcher.isSpriteSpecfic = False
                else:
                    v14_morph = v14_project.sprites[kurt_parent.name]

                v14_watcher.readout.target = v14_morph
                v14_watcher.owner = v14_project.stage

                if isinstance(kurt_watcher.value, kurt.Variable):
                    v14_watcher.readout.parameter = kurt_watcher.value.name

                    v14_watcher.name = kurt_watcher.value.name

                (w, h) = (63, 21)

                if kurt_watcher.style == "large":
                    v14_watcher.isLarge = True
                    v14_watcher.readout.font_with_size[1] = 14
                    (w, h) = (52, 26)

                elif kurt_watcher.style == "slider":
                    v14_watcher.scratchSlider = slider = WatcherSliderMorph(
                        arguments = [u'slider'],
                        borderColor = Symbol('inset'),
                        borderWidth = 0,
                        bounds = Rectangle([59, 273, 134, 283]),
                        color = Color(512, 512, 512),
                        descending = False,
                        flags = 0,
                        maxVal = 100,
                        minVal = 0,
                        model = None,
                        owner = v14_watcher,
                        properties = None,
                        setValueSelector = Symbol('setVar:to:'),
                                                sliderColor = None,
                        sliderShadow = None,
                        sliderThickness = 0,
                        target = v14_project.stage,
                        truncate = True,
                        value = 0.0,
                    )

                    slider.slider = ImageMorph(
                        bounds = Rectangle([59, 273, 69, 283]),
                        color = Color(0, 0, 1023),
                        flags = 0,
                        owner = slider,
                        properties = None,
                        submorphs = [],
                        transparency = 1.0,
                    )

                    slider.submorphs = [slider.slider]

                    v14_watcher.submorphs.append(v14_watcher.scratchSlider)

                v14_watcher.bounds = Rectangle([x, y, x+w, x+h])

                v14_project.stage.submorphs.append(v14_watcher)

        v14_project.save(path)
        #v14_project.path = path

        # TODO: stacking order

        return v14_project



Kurt.register(Scratch14Plugin())
