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

"""Classes for saving/loading Scratch files.
Construct them by passing them a path.

    ScratchProjectFile - .sb
    ScratchSpriteFile - .sprite
"""

from construct import Container, Struct, Bytes, Rename
from construct.text import Literal
from objtable import ObjTable, InfoTable
from fixed_objects import Form
from user_objects import Stage, Image

import os.path



class BinaryFile(object):
    """File(path)
    Implements a basic file with save() function.
    Subclasses override _load() and _save()."""

    EXTENSION = None

    def __init__(self, path=None, load=True):
        """Loads a file.
        @param path: the path passed to open().
        """
        self.path = None
        if path:
            if not path.lower().endswith("."+self.EXTENSION.lower()):
                path += "."+self.EXTENSION
            self.path = path

            if load:
                self.load()

    @property
    def name(self):
        (folder, name) = os.path.split(self.path)
        trimmed_name = ''.join(name.split('.')[:-1]) # Trim extension
        if trimmed_name:
            name = trimmed_name
        return name

    def load(self):
        """Reload the file from disk, replacing any changes in memory.
        """
        if not self.path:
            raise ValueError, "filepath not set."

        f = open(self.path, "rb")
        bytes = f.read()
        f.close()
        self._load(bytes)

    def _load(self, bytes):
        """Subclasses must override this method.
        Set the attributes of this file from the given contents.
        @param bytes: str containing the file contents read from disk.
        """
        raise NotImplementedError()

    def save(self, path):
        """Save the file to disk."""
        bytes = self._save()
        if not bytes:
            print "Can't write zero bytes to file, aborting"
            return

        f = open(path, 'wb')
        f.write(bytes)
        f.flush()
        f.close()

    def _save(self):
        """Subclasses must override this method.
        @return: str containing the bytes to be saved to disk.
        """
        raise NotImplementedError()



class ScratchProjectFile(BinaryFile):
    """Using this interface directly is DEPRECATED -- use kurt.Project instead,
    which provides conversion between multiple formats.

    Attributes:
        info - a Dictionary containing project info (author, notes, thumbnail)
        stage - the stage. Contains contents, including sprites and media.
    """

    _construct = Struct("scratch_file",
        Literal("ScratchV02"),
        Rename("info", InfoTable),
        Rename("stage", ObjTable),
    )

    def __init__(self):
        self.info = {
            "comment": "",
            "scratch-version": '1.4 of 30-Jun-09',
            "language": "en",
            "author": u"",
            "isHosting": False,
            "platform": "",
            "os-version": "",
            "thumbnail": None,
            "history": "",
            "name": "",
        }
        self.stage = Stage()

    def _load(self, bytes):
        project = self._construct.parse(bytes)
        self.info.update(project.info)

        if self.info["thumbnail"] and isinstance(self.info["thumbnail"], Form):
            self.info["thumbnail"] = Image(
                name = "thumbnail",
                form = self.info["thumbnail"],
            )
        self.stage = project.stage

    def _save(self):
        info = self.info.copy()
        if info["thumbnail"]:
            info["thumbnail"] = info["thumbnail"].form
        info["comment"] = info["comment"].replace("\n", "\r")

        self.stage.normalize()

        project = Container(
            info = info,
            stage = self.stage,
        )
        return self._construct.build(project)

    def get_sprite(self, name):
        for sprite in self.stage.sprites:
            if sprite.name == name:
                return sprite



class ScratchSpriteFile(BinaryFile):
    """A Scratch sprite file.
    @param path: path to .sprite file.

    Attributes:
        stage - the root object of the file (Sprite files actually contain a
                serialised Stage)
    """

    EXTENSION = "sprite"

    def _load(self, bytes):
        self.stage = ObjTable.parse(bytes)

    def _save(self):
        return ObjTable.build(self.stage)

