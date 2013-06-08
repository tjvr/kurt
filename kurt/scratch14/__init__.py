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
from kurt.scratch14.blocks import block_list



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

def load_image(v14_image):
    if v14_image:
        if v14_image.jpegBytes:
            image = kurt.Image(v14_image.jpegBytes.value, "JPEG")
            image._size = v14_image.size
        else:
            image = kurt.Image(v14_image.get_image())

        return kurt.Costume(v14_image.name, image, v14_image.rotationCenter)

def save_image(kurt_costume):
    if kurt_costume:
        image = kurt_costume.image.convert("JPEG", "bitmap")

        if image.format == "JPEG":
            v14_image = Image(
                name = kurt_costume.name,
                jpegBytes = ByteArray(kurt_costume.image.contents),
            )
            v14_image.size = kurt_costume.image.size
            v14_image.rotationCenter = Point(kurt_costume.rotation_center)
            return v14_image

        return Image.from_image(kurt_costume.name, kurt_costume.image.pil_image)

def load_sound(v14_sound):
    pass

def save_sound(kurt_sound):
    pass

def load_block(v14_block):
    # special-case blocks with weird arguments
    if v14_block.command == 'EventHatMorph':
        assert v14_block.args
        if v14_block.args[0] == 'Scratch-StartClicked':
            return kurt.Block('whenGreenFlag')
        else:
            return kurt.Block('whenIreceive', v14_block.args[0])
    elif v14_block.command == 'MouseClickEventHatMorph':
        return kurt.Block('whenClicked')
    elif v14_block.command == 'changeVariable':
        command = v14_block.args.pop(1).value
    else:
        command = v14_block.command

    args = []
    for arg in v14_block.args:
        if isinstance(arg, Block):
            arg = load_block(arg)
        elif isinstance(arg, list):
            arg = map(load_block, arg)
        elif isinstance(arg, Symbol):
            raise ValueError(arg) # TODO translate these
        args.append(arg)
    return kurt.Block(command, *args)

def load_script(v14_script):
    return kurt.Script(
        map(load_block, v14_script.blocks),
        pos = v14_script.pos,
    )

def save_block(kurt_block):
    command = kurt_block.type.translate('scratch14').command

    args = []
    for arg in kurt_block.args:
        if isinstance(arg, kurt.Block):
            arg = save_block(arg)
        elif isinstance(arg, list):
            arg = map(save_block, arg)
        args.append(arg)

    # special-case blocks with weird arguments
    if command == 'whenGreenFlag':
        return Block('EventHatMorph', 'Scratch-StartClicked')
    elif command == 'whenIReceive':
        return Block('EventHatMorph', args[0])
    elif command == 'whenClicked':
        return Block('MouseClickEventHatMorph', 'Scratch-MouseClickEvent')
    elif command in ('changeVar:by:', 'setVar:to:'):
        return Block('changeVariable', args[0],
                Symbol(command), args[1])

    return Block(command, *args)

def save_script(kurt_script):
    return Script(
        kurt_script.pos or (10, 10),
        map(save_block, kurt_script.blocks),
    )

def load_variable((name, value)):
    return (name, kurt.Variable(value))

def save_variable((name, kurt_variable)):
    return (name, kurt_variable.value)

def load_lists(v14_lists, kurt_project, kurt_owner):
    kurt_lists = {}
    for v14_list in v14_lists.values():
        kurt_list = kurt.List(map(unicode, v14_list.items))
        kurt_lists[v14_list.name] = kurt_list

        kurt_list_ref = kurt.ListReference(kurt_owner, v14_list.name)

        kurt_watcher = kurt.Watcher(kurt_list_ref)
        kurt_watcher.visible = bool(v14_list.owner)

        (x, y, w, h) = v14_list.bounds.value
        if not kurt_watcher.visible:
            x -= 534
            y -= 71
        kurt_watcher.pos = (x, y)
        kurt_project.actors.append(kurt_watcher)

    return kurt_lists

def save_lists(kurt_thing, kurt_project, v14_morph, v14_project):
    for (name, kurt_list) in kurt_thing.lists.items():
        v14_list = ScratchListMorph(
            name = name,
            items = kurt_list.items,
        )

        kurt_list_ref = kurt.ListReference(kurt_thing, name)

        for actor in kurt_project.actors:
            if isinstance(actor, kurt.Watcher):
                if actor.watching == kurt_list_ref:
                    kurt_watcher = actor
                    break
        else:
            kurt_watcher = kurt.Watcher(kurt_list_ref, visible=False)

        pos = kurt_watcher.pos
        if pos:
            (x, y) = pos
        else:
            (x, y) = (375, 10)
            # TODO: stack them properly

        if not kurt_watcher.visible:
            x += 534
            y += 71
        v14_list.bounds = Rectangle([x, y, x+95, y+115])

        v14_list.target = v14_morph
        if kurt_watcher.visible:
            v14_list.owner = v14_project.stage
            v14_project.stage.submorphs.append(v14_list)

        v14_morph.lists[v14_list.name] = v14_list

def load_scriptable(kurt_scriptable, v14_scriptable):
    kurt_scriptable.scripts = map(load_script, v14_scriptable.scripts)
    kurt_scriptable.variables = dict(map(load_variable,
            v14_scriptable.variables.items()))
    kurt_scriptable.costumes = map(load_image, v14_scriptable.images)
    # kurt_scriptable.sounds = dict(map(load_sound, v14_scriptable.sounds) # TODO

    costume_index = v14_scriptable.images.index(v14_scriptable.costume)
    kurt_scriptable.costume = kurt_scriptable.costumes[costume_index]

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

def save_scriptable(kurt_scriptable, v14_scriptable):
    v14_scriptable.scripts = user_objects.ScriptCollection(
            map(save_script, kurt_scriptable.scripts))
    v14_scriptable.variables = dict(map(save_variable,
        kurt_scriptable.variables.items()))
    v14_scriptable.images = map(save_image, kurt_scriptable.costumes)
    #v14_scriptable.sounds = map(save_sound, kurt_scriptable.sounds) # TODO

    if kurt_scriptable.costume:
        costume_index = kurt_scriptable.costumes.index(kurt_scriptable.costume)
        v14_scriptable.costume = v14_scriptable.images[costume_index]

    v14_scriptable.volume = kurt_scriptable.volume

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
        (w, h) = kurt_scriptable.costume.image.size
        v14_scriptable.bounds = Rectangle([x, y, x+w, y+h])



class Scratch14Plugin(KurtPlugin):
    name = "scratch14"
    display_name = "Scratch 1.4"
    extension = ".sb"

    def make_blocks(self):
        return block_list

    def load(self, path):
        v14_project = ScratchProjectFile(path)
        kurt_project = kurt.Project()

        # project info
        kurt_project.notes = v14_project.info['comment']
        kurt_project.author = v14_project.info['author']
        kurt_project.thumbnail = load_image(v14_project.info['thumbnail'])

        # stage
        load_scriptable(kurt_project.stage, v14_project.stage)
        kurt_project.lists = load_lists(v14_project.stage.lists, kurt_project,
                kurt_project)

        # global vars
        kurt_project.variables = kurt_project.stage.variables
        kurt_project.stage.variables = {}

        # sprites
        for v14_sprite in v14_project.sprites:
            kurt_sprite = kurt.Sprite(v14_sprite.name)
            load_scriptable(kurt_sprite, v14_sprite)
            kurt_sprite.lists = load_lists(v14_sprite.lists, kurt_project,
                    kurt_sprite)
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
                kurt_var_ref = kurt.VariableReference(kurt_thing, name)

                kurt_watcher = kurt.Watcher(kurt_var_ref)

                (x, y, right, bottom) = v14_watcher.bounds.value
                kurt_watcher.pos = (x, y)

                if v14_watcher.isLarge:
                    kurt_watcher.style = "large"
                elif v14_watcher.scratchSlider:
                    kurt_watcher.style = "slider"

                kurt_watcher.slider_min = v14_watcher.sliderMin
                kurt_watcher.slider_max = v14_watcher.sliderMax

                kurt_project.actors.append(kurt_watcher)

        # TODO: stacking order of actors.

        kurt_project._original = v14_project # DEBUG

        return kurt_project


    def save(self, path, kurt_project):
        v14_project = ScratchProjectFile.new()

        # project info
        v14_project.info['comment'] = kurt_project.notes
        v14_project.info['author'] = kurt_project.author
        v14_project.info['thumbnail'] = save_image(kurt_project.thumbnail)

        # stage
        save_scriptable(kurt_project.stage, v14_project.stage)
        save_lists(kurt_project, kurt_project, v14_project.stage, v14_project)
        v14_project.stage.variables = dict(map(save_variable,
            kurt_project.variables.items()))

        v14_project.stage.tempoBPM = kurt_project.tempo

        # sprites
        for kurt_sprite in kurt_project.sprites:
            v14_sprite = Sprite()
            save_scriptable(kurt_sprite, v14_sprite)
            save_lists(kurt_sprite, kurt_project, v14_sprite, v14_project)
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
                if isinstance(kurt_watcher.watching, kurt.ListReference):
                    continue

                if not kurt_watcher.visible:
                    continue

                v14_watcher = WatcherMorph()

                if kurt_watcher.pos:
                    (x, y) = kurt_watcher.pos
                else:
                    (x, y) = (10, 10)

                if isinstance(kurt_watcher.watching, kurt.VariableReference):
                    kurt_parent = kurt_watcher.watching.scriptable
                else:
                    kurt_parent = kurt_project
                if kurt_parent == kurt_project:
                    v14_morph = v14_project.stage
                    v14_watcher.isSpriteSpecfic = False
                else:
                    v14_morph = v14_project.sprites[kurt_parent.name]

                v14_watcher.readout.target = v14_morph
                v14_watcher.owner = v14_project.stage

                if isinstance(kurt_watcher.watching, kurt.VariableReference):
                    v14_watcher.readout.parameter = kurt_watcher.watching.name

                    v14_watcher.name = kurt_watcher.watching.name

                (w, h) = (63, 21)

                if kurt_watcher.style == "large":
                    v14_watcher.isLarge = True
                    v14_watcher.readout.font_with_size[1] = 14
                    (w, h) = (52, 26)

                elif kurt_watcher.style == "slider":
                    v14_watcher.make_slider(v14_project.stage)

                v14_watcher.sliderMin = kurt_watcher.slider_min
                v14_watcher.sliderMax = kurt_watcher.slider_max

                v14_watcher.bounds = Rectangle([x, y, x+w, x+h])

                v14_project.stage.submorphs.append(v14_watcher)

        v14_project.save(path)

        return v14_project



Kurt.register(Scratch14Plugin())
