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

"""A Kurt plugin for Scratch 2.0."""

import zipfile
import json
import time
import os
import hashlib
import struct

import kurt
from kurt.plugin import Kurt, KurtPlugin

from kurt.scratch20.blocks import make_block_types



class ZipReader(object):
    def __init__(self, path):
        self.zip_file = zipfile.ZipFile(path)

        project_dict = json.load(self.zip_file.open("project.json"))

        kurt_project = kurt.Project()
        self.kurt_project = kurt_project

        kurt_project.stage = self.load_scriptable(project_dict, is_sprite=False)

        children = sorted(project_dict['children'],
                key=lambda c: c['indexInLibrary'])
        for sprite_dict in children:
            kurt_project.sprites.append(self.load_scriptable(sprite_dict))

        self.project_dict = project_dict

    def finish(self):
        self.zip_file.close()

    def load_scriptable(self, scriptable_dict, is_sprite=True):
        if is_sprite:
            kurt_scriptable = kurt.Sprite(self.kurt_project,
                    scriptable_dict["objName"])
        else:
            kurt_scriptable = kurt.Stage(self.kurt_project)

        #for costume_dict in scriptable_dict["costumes"]:
        #    kurt_scriptable.costumes.append(self.load_costume(costume_dict))

        for script_array in scriptable_dict.get("scripts", []):
            kurt_scriptable.scripts.append(self.load_script(script_array))


        if is_sprite:
            pass

        return kurt_scriptable

    def load_block(self, block_array):
        command = block_array.pop(0)
        block_type = kurt.BlockType.get(command)

        inserts = list(block_type.inserts)
        args = []
        for arg in block_array:
            insert = inserts.pop(0) if inserts else None
            if isinstance(arg, list):
                if isinstance(arg[0], list): # 'stack'-shaped Insert
                    arg = map(self.load_block, arg)
                else: # Block
                    arg = self.load_block(arg)
            elif insert:
                if insert.kind == 'spriteOrStage' and arg == '_stage_':
                    arg = 'Stage'
                elif insert.shape == 'color':
                    arg = self.load_color(arg)
            args.append(arg)

        return kurt.Block(block_type, *args)

    def load_script(self, script_array):
        (x, y, blocks) = script_array
        blocks = map(self.load_block, blocks)
        return kurt.Script(blocks, pos=(x, y))

    def load_color(value):
        # convert signed to unsigned 32-bit int
        value = struct.unpack('=I', struct.pack('=i', value))[0]
        # throw away leading ff, if any
        value &= 0x00ffffff
        # extract RGB values
        return kurt.Color(
            (value & 0xff0000) >> 16,
            (value & 0x00ff00) >> 8,
            (value & 0x0000ff),
        )

    def load_costume(self, costume_dict):
        return None #kurt.Costume()


class ZipWriter(object):
    def __init__(self, path, kurt_project):
        self.zip_file = zipfile.ZipFile(path, "w")

        project_dict = {
            "penLayerMD5": "279467d0d49e152706ed66539b577c00.png",
            "info": {},
            "tempoBPM": kurt_project.tempo,
            "children": [],

            "info": {
                "flashVersion": "MAC 11,7,700,203",
                "projectID": "10442014",
                "scriptCount": 0,
                "spriteCount": 0,
                "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.20 Safari/537.36",
                "videoOn": False,
                "hasCloudData": False, # todo
            },
            "videoAlpha": 0.5,
        }

        self.image_dicts = {}
        self.highest_image_id = 0

        stage_dict = self.save_scriptable(kurt_project.stage)
        project_dict.update(stage_dict)

        for (i, kurt_sprite) in enumerate(kurt_project.sprites):
            sprite_dict = self.save_scriptable(kurt_sprite, i)
            project_dict["children"].append(sprite_dict)

        self.write_file("project.json", json.dumps(project_dict))

        self.project_dict = project_dict

    def finish(self):
        self.zip_file.close()

    def write_file(self, name, contents):
        """Write file contents string into archive."""
        # TODO: find a way to make ZipFile accept a file object.
        zi = zipfile.ZipInfo(name)
        zi.date_time = time.localtime(time.time())[:6]
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0777 << 16L
        self.zip_file.writestr(zi, contents)

    def write_image(self, image):
        if image in self.image_dicts:
            image_dict = self.image_dicts[image]
        else:
            image_id = self.highest_image_id
            self.highest_image_id += 1

            image = image.convert("SVG", "JPEG", "PNG")
            filename = str(image_id) + (image.extension or ".png")
            self.write_file(filename, image.contents)

            image_dict = {
                "baseLayerID": image_id, #-1 for download
                "bitmapResolution": 1,
                "baseLayerMD5": hashlib.md5(image.contents).hexdigest(),
            }
            self.image_dicts[image] = image_dict
        return image_dict


    def save_scriptable(self, kurt_scriptable, i=None):
        is_sprite = isinstance(kurt_scriptable, kurt.Sprite)

        scriptable_dict = {
            "objName": kurt_scriptable.name,
            "currentCostumeIndex": kurt_scriptable.costume_index or 0,
            "scripts": [],
            "costumes": [],
            "sounds": [],
        }

        for kurt_script in kurt_scriptable.scripts:
            script_array = self.save_script(kurt_script)
            scriptable_dict["scripts"].append(script_array)

        for kurt_costume in kurt_scriptable.costumes:
            costume_dict = self.save_costume(kurt_costume)
            scriptable_dict["costumes"].append(costume_dict)

        if is_sprite:
            scriptable_dict.update({
                "scratchX": 0,
                "scratchY": 0,
                "scale": 1,
                "direction": 90,
                "indexInLibrary": i,
                "isDraggable": False,
                "rotationStyle": "normal",
                "spriteInfo": {},
                "visible": True,
            })

        return scriptable_dict

    def save_block(self, block):
        command = block.type.translate("scratch20").command
        args = []
        for arg in block.args:
            if isinstance(arg, kurt.Block):
                arg = self.save_block(arg)
            elif isinstance(arg, list):
                arg = map(self.save_block, arg)
            elif isinstance(arg, kurt.Color):
                arg = self.save_color(arg)
            args.append(arg)
        return [command] + args

    def save_script(self, script):
        (x, y) = script.pos or (10, 10)
        return [x, y, map(self.save_block, script.blocks)]

    def save_costume(self, kurt_costume):
        costume_dict = self.write_image(kurt_costume.image)
        (rx, ry) = kurt_costume.rotation_center
        costume_dict.update({
            "costumeName": kurt_costume.name,
            "rotationCenterX": rx,
            "rotationCenterY": ry,
        })
        return costume_dict

    def save_color(self, color):
        # build RGB values
        value = (color.r << 16) + (color.g << 8) + color.b
        # convert unsigned to signed 32-bit int
        value = struct.unpack('=i', struct.pack('=I', value))[0]
        return value


class Scratch20Plugin(KurtPlugin):
    name = "scratch20"
    display_name = "Scratch 2.0"
    extension = ".sb2"

    def make_blocks(self):
        return make_block_types()

    def load(self, path):
        zl = ZipReader(path)
        kurt_project = zl.kurt_project
        kurt_project._original = zl.project_dict
        zl.finish()
        return kurt_project

    def save(self, path, kurt_project):
        zw = ZipWriter(path, kurt_project)
        zw.finish()
        return zw.project_dict



Kurt.register(Scratch20Plugin())
