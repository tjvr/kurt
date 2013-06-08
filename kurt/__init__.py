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

"""
A Python module for reading and writing Scratch project files.

Scratch is created by the Lifelong Kindergarten Group at the MIT Media Lab.
See their website: http://scratch.mit.edu/


Classes
-------

The main interface:

* :class:`Project`

The following :class:`Actors <Actor>` may be found on the project stage:

* :class:`Stage`
* :class:`Sprite`
* :class:`Watcher`

The two :class:`Scriptables <Scriptable>` (:class:`Stage` and :class:`Sprite`)
have instances of the following contained in their attributes:

* :class:`Variable`
* :class:`List`

Scripts use the following classes:

* :class:`Block`
* :class:`Script`
* :class:`Comment`
* :class:`BlockType`

Media files use the following classes:

* :class:`Costume`
* :class:`Image`
* :class:`Sound`

File Formats
------------

Supported file formats:

    =============== =========== =========
    Format Name     Description Extension
    =============== =========== =========
    ``"scratch14"`` Scratch 1.4 ``.sb``
    ``"scratch20"`` Scratch 2.0 ``.sb2``
    =============== =========== =========

Pass "Format name" as the argument to :attr:`Project.convert`.

Kurt provides a superset of the information in each individual format, but will
only convert features between a subset of formats.

----

"""

__version__ = '2.0.0'

from collections import OrderedDict
import re
import os
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import PIL.Image



#-- Utils --#

def _clean_filename(name):
    """Strip non-alphanumeric characters to makes name safe to be used as
    filename."""
    return re.sub("[^\w ]", "", name)



#-- Project: main class --#

class Project(object):
    """The main kurt class. Stores the contents of a project file.

    Contents include global variables and lists, the :attr:`stage` and
    :attr:`sprites`, each with their own :attr:`scripts`, :attr:`costumes`,
    :attr:`sounds`, :attr:`variables` and :attr:`lists`.

    A Project can be loaded from or saved to disk in a format which can be read
    by a Scratch program or one of its derivatives.

    Loading a project::

        p = kurt.Project.load("tests/game.sb")

    Getting all the scripts::

        for scriptable in p.sprites + [p.stage]:
            for script in scriptable.scripts:
                print script

    Creating a new project::

        p = kurt.Project()

    Converting between formats::

        p = kurt.Project.load("tests/game.sb")
        p.convert("scratch20")
        p.save()
        # 'tests/game.sb2'

    """

    def __init__(self):
        self.name = u""
        """The name of the project.

        May be displayed to the user. Doesn't have to match the filename in
        :attr:`path`. May not be saved for some formats.

        """

        self.path = None
        """The path to the project file."""

        self._plugin = None
        """The file format plugin used to load this project.

        Get the current format using the :attr:`format` property. Use
        :attr:`convert()` to change between formats.

        """

        self.stage = Stage()
        """The :class:`Stage`."""

        self.sprites = []
        """List of :class:`Sprites <Sprite>`.

        Use :attr:`get_sprite` to get a sprite by name.

        """

        self.actors = []
        """List of each :class:`Actor` on the stage.

        Includes :class:`Watchers <Watcher>` as well as :class:`Sprites
        <Sprite>`.

        Sprites in :attr:`sprites` but not in actors will be added to actors on
        save.

        """

        self.variables = {}
        """:class:`dict` of global :class:`Variables <Variable>` by name."""

        self.lists = {}
        """:class:`dict` of global :class:`Lists <List>` by name."""

        self.tempo = 60
        """The tempo in BPM used for note blocks."""

        self.thumbnail = None
        """A screenshot of the project. May be displayed in project browser."""

        self.notes = "Made with Kurt\nhttp://github.com/blob8108/kurt"
        """Notes about the project, aka project comments.

        Displayed on the website next to the project.

        Line endings will be converted to ``\\n``.

        """

        self.author = u""
        """The username of the project's author, eg. ``'blob8108'``."""

        self._normalize()

    def __repr__(self):
        return "<%s.%s name=%r>" % (self.__class__.__module__,
                self.__class__.__name__, self.name)

    def get_sprite(self, name):
        """Get a sprite from :attr:`sprites` by name.

        Returns None if the sprite isn't found.

        """
        for sprite in self.sprites:
            if sprite.name == name:
                return sprite

    @property
    def format(self):
        """The file format of the project.

        :class:`Project` is mainly a universal representation, and so a project
        has no specfic format. This is the format the project was loaded with.
        To convert to a different format, use :attr:`save()`.

        """
        if self._plugin:
            return self._plugin.name

    @classmethod
    def load(cls, path, format=None):
        """Load project from file.

        Guesses the appropriate format from the extension.

        Use ``format`` to specify the file format to use.

        :param path:   Path or URL.
        :param format: :attr:`KurtFileFormat.name` eg. ``"scratch14"``.
                       Overrides the extension.

        :raises: :class:`UnknownFormat` if the extension is unrecognised.
        :raises: :py:class:`ValueError` if the format doesn't exist.

        """

        (folder, filename) = os.path.split(path)
        (name, extension) = os.path.splitext(filename)

        if format is None:
            plugin = kurt.plugin.Kurt.get_plugin(extension=extension)
            if not plugin:
                raise UnknownFormat(extension)
        else:
            plugin = kurt.plugin.Kurt.get_plugin(name=format)
            if not plugin:
                raise ValueError, "Unknown format %r" % format

        project = plugin.load(path)

        project.path = path
        project._plugin = plugin
        if not project.name:
            project.name = name # use filename

        project._normalize()

        return project

    def convert(self, format):
        """Convert the project in-place to a different file format.

        Returns self.

        :param format: :attr:`KurtFileFormat.name` eg. ``"scratch14"``.

        :raises: :class:`ValueError` if the format doesn't exist.

        """

        plugin = kurt.plugin.Kurt.get_plugin(name=format)

        self._normalize()

        # TODO

        self._plugin = plugin

        return self

    def save(self, path=None, debug=False):
        """Save project to file.

        :param path: Path or URL. If path is not given, the original path given
                     to :attr:`load()` is used.

                     The extension, if any, will be removed, and the extension
                     of the current file format added.

                     If the path ends in a folder instead of a file, the
                     filename is based on the project's :attr:`name`.

        :param debug: If true, return debugging information from the format
                      plugin instead of the path.

        :raises: :py:class:`ValueError` if there's no path or name, or you forgot
                 to :attr:`convert()` before saving.

        :returns: path to the saved file.

        """

        if path is None:
            path = self.path

            if path is None:
                raise ValueError, "path is required"

        if self._plugin is None:
            raise ValueError, "must convert project to a format before saving"

        (folder, filename) = os.path.split(path)
        (name, extension) = os.path.splitext(filename)

        extension = self._plugin.extension
        if not name:
            name = _clean_filename(self.name)
            if not name:
                raise ValueError, "name is required"

        filename = name + extension
        path = os.path.join(folder, filename)
        self.path = path

        self._normalize()
        result = self._plugin.save(path, self)

        if debug:
            return result
        else:
            return path

    def _normalize(self):
        """Convert the project to a standardised form.

        Called after loading & before saving.

        """

        unique_sprite_names = set(sprite.name for sprite in self.sprites)
        if len(unique_sprite_names) < len(self.sprites):
            raise ValueError, "Sprite names must be unique"

        # sync self.sprites and self.actors
        for sprite in self.sprites:
            if sprite not in self.actors:
                self.actors.append(sprite)
        for actor in self.actors:
            if isinstance(actor, Sprite):
                if actor not in self.sprites:
                    raise ValueError, \
                        "Can't have sprite on stage that isn't in sprites"

        # normalize actors
        self.stage._normalize()
        for actor in self.actors:
            actor._normalize()

        # notes - line endings
        self.notes = self.notes.replace("\r\n", "\n").replace("\r", "\n")

        # global variables & lists
        if self._plugin and not self._plugin.has_stage_specific_variables:
            self.variables.update(self.stage.variables)
            self.lists.update(self.stage.lists)
            self.stage.variables = {}
            self.stage.lists = {}



#-- Errors --#

class UnknownFormat(Exception):
    """The file extension is not recognised.

    Raised when :class:`Project` can't find a valid format plugin to handle the
    file extension.

    """
    pass



#-- Actors & Scriptables --#

class Actor(object):
    """An object that goes on the project stage.

    Subclasses include :class:`Watcher` or :class:`Sprite`.

    """


class Scriptable(object):
    """Superclass for all scriptable objects.

    Subclasses are :class:`Stage` and :class:`Sprite`.

    """

    def __init__(self):
        self.scripts = []
        """The contents of the scripting area.

        List containing :class:`Scripts <Script>` and :class:`Comments
        <Comment>`.

        Will be sorted by y position on load/save.

        """

        self.variables = {}
        """:class:`dict` of :class:`Variables <Variable>` by name."""

        self.lists = {}
        """:class:`dict` of :class:`Lists <List>` by name."""

        self.costumes = []
        """List of :class:`Costumes <Costume>`."""

        self.sounds = []
        """List of :class:`Sounds <Sound>`."""

        self.costume = None
        """The currently selected :class:`Costume`.

        Defaults to the first costume in :attr:`self.costumes` on save.

        """

        self.volume = 100

    def _normalize(self):
        if self.costume:
            # Make sure it's in costumes
            if self.costume not in self.costumes:
                self.costumes.append(self.costume)
        else:
            # No costume!
            if self.costumes:
                self.costume = self.costumes[0]
            else:
                raise ValueError, "%r doesn't have a costume" % self

    @property
    def costume_index(self):
        """The index of :attr:`costume` in :attr:`costumes`.

        None if no costume is selected.

        """
        if self.costume:
            return self.costumes.index(self.costume)

    @costume_index.setter
    def costume_index(self, index):
        if index is None:
            self.costume = None
        else:
            self.costume = self.costumes[index]


class Stage(Scriptable):
    """Represents the background of the project. The stage is similar to a
    :class:`Sprite`, but has a fixed position. The stage has a fixed size of
    ``480x360`` pixels.

    The stage does not require a costume. If none is given, it is assumed to be
    white (#FFF).

    Not all formats have stage-specific variables and lists. Global variables
    and lists are stored on the :class:`Project`.

    """

    name = "Stage"

    SIZE = (480, 360)
    COLOR = (255, 255, 255)

    def __init__(self):
        Scriptable.__init__(self)

    @property
    def backgrounds(self):
        """Alias for :attr:`costumes`."""
        return self.costumes

    def __repr__(self):
        return "<%s.%s()>" % (self.__class__.__module__, self.__class__.__name__)

    def _normalize(self):
        if not self.costume and not self.costumes:
            self.costume = Costume("blank", Image(PIL.Image.new("RGB",
                self.SIZE, self.COLOR)))
        Scriptable._normalize(self)


class Sprite(Scriptable, Actor):
    """A scriptable object displayed on the project stage. Can be moved and
    rotated, unlike the :class:`Stage`.

    Sprites require a :attr:`costume`, and will raise an error when saving
    without one.

    """

    def __init__(self, name):
        Scriptable.__init__(self)

        self.name = unicode(name)
        """The name of the sprite, as referred to from scripts and displayed in
        the Scratch interface.

        """

        self.position = (0, 0)
        """The ``(x, y)`` position to the right and above of the centre of the
        stage in pixels.

        """

        self.direction = 0.0
        """The angle in degrees the sprite is rotated to."""

        self.rotation_style = "normal"
        """How the sprite's costume rotates with the sprite. Valid values are:

        ``'normal'``
            Continuous rotation with :attr:`direction`. The default.

        ``'leftRight'``
            Don't rotate. Instead, flip the costume for directions with x
            component < 0. Useful for side-views.

        ``'none'``
            Don't rotate with direction.

        """

        self.is_draggable = False
        """True if the sprite can be dragged using the mouse in the
        player/presentation mode.

        """

    def _normalize(self):
        Scriptable._normalize(self)
        assert self.rotation_style in ("normal", "leftRight", "none")
        if not self.costume:
            raise ValueError, "%r doesn't have a costume" % self

    def __repr__(self):
        return "<%s.%s(%r)>" % (self.__class__.__module__,
                self.__class__.__name__, self.name)


class Watcher(Actor):
    """A monitor for displaying a data value on the stage.

    Some formats won't save hidden watchers, and so their position won't be
    remembered.

    """

    def __init__(self, watching, style="normal", visible=True, pos=None):
        Actor.__init__(self)

        self.watching = watching
        """The data the watcher displays.

        Can be a :class:`VariableReference`, a :class:`ListReference`, or a
        reporter :class:`Block`.

        """

        self.style = str(style)
        """How the watcher should appear. Valid values:

        ``'normal'``
            The name of the data is displayed next to its value. The only
            valid value for list watchers.

        ``'large'``
            The data is displayed in a larger font with no describing text.

        ``'slider'``
            Like the normal style, but displayed with a slider that can change
            the variable's value. Not valid for reporter block watchers.

        """

        self.pos = pos
        """``(x, y)`` position of the top-left of the watcher from the top-left
        of the stage in pixels. None if not specified.

        """

        self.visible = bool(visible)
        """Whether the watcher is displayed on the screen.

        Some formats won't save hidden watchers, and so their position won't be
        remembered.

        """

        self.slider_min = 0
        """Minimum value for slider. Only applies to ``"slider"`` style."""

        self.slider_max = 100
        """Maximum value for slider. Only applies to ``"slider"`` style."""

        self._normalize()

    def _normalize(self):
        assert self.style in ("normal", "large", "slider")
        if isinstance(self.watching, ListReference):
            assert self.style == "normal"
        elif isinstance(self.watching, Block):
            assert self.style != "slider"
        elif isinstance(self.watching, VariableReference):
            pass

    def __repr__(self):
        r = "%s.%s(%r, %r" % (self.__class__.__module__,
                self.__class__.__name__, self.watching, self.style)
        if not self.visible:
            r += ", visible=False"
        if self.pos:
            r += ", pos=%s" % repr(self.pos)
        r += ")"
        return r


class VariableReference(object):
    """A reference to a :class:`Variable` owned by a :class:`Scriptable`."""

    def __init__(self, scriptable, name):
        self.scriptable = scriptable
        """The :class:`Scriptable` or :class:`Project` instance the variable
        belongs to.

        """

        self.name = name
        """The name of the variable in :attr:`Scriptable.variables`."""

    @property
    def variable(self):
        """Return the :class:`Variable` instance the reference points to."""
        return self.scriptable.variables[self.name]

    def __eq__(self, other):
        return (
            isinstance(other, VariableReference) and
            self.scriptable == other.scriptable and
            self.name == other.name
        )

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "%s.%s(%r, %r)" % (self.__class__.__module__,
                self.__class__.__name__, self.scriptable, self.name)


class ListReference(object):
    """A reference to a :class:`List` owned by a :class:`Scriptable`."""

    def __init__(self, scriptable, name):
        self.scriptable = scriptable
        """The :class:`Scriptable` or :class:`Project` instance the list
        belongs to.

        """

        self.name = name
        """The name of the list, as found in :attr:`Scriptable.lists`.

        """

    @property
    def list(self):
        """Return the :class:`List` instance the reference points to."""
        return self.scriptable.lists[self.name]

    def __eq__(self, other):
        return (
            isinstance(other, ListReference) and
            self.scriptable == other.scriptable and
            self.name == other.name
        )

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "%s.%s(%r, %r)" % (self.__class__.__module__, self.__class__.__name__,
                self.scriptable, self.name)



#-- Media / Scriptable attributes --#

class Variable(object):
    """A memory value used in scripts.

    There are both :attr`global variables <Project.variables> and
    :attr:`sprite-specific variables <Sprite.variables>`.

    Some formats also have :attr:`stage-specific variables <Stage.variables>`.

    """

    def __init__(self, value=0, is_cloud=False):
        self.value = value
        """The value of the variable, usually a number or a string.

        For some formats, variables can take list values, and :class:`List` is
        not used.

        """

        self.is_cloud = bool(is_cloud)
        """Whether the value of the variable is shared with other users.

        For Scratch 2.0.

        """

    def __repr__(self):
        r = "%s.%s(%r" % (self.__class__.__module__, self.__class__.__name__, self.value)
        if self.is_cloud:
            r += ", is_cloud=%r" % self.is_cloud
        r += ")"
        return r


class List(object):
    """A sequence of items used in scripts.

    Each item takes a :class:`Variable`-like value.

    Lists cannot be nested. However, for some formats, variables can take
    list values, and this class is not used.

    """
    def __init__(self, items=None, is_cloud=False):
        self.items = list(items) if items else []
        """The items contained in the list. A Python list of unicode strings."""

        self.is_cloud = bool(is_cloud)
        """Whether the value of the list is shared with other users.

        For Scratch 2.0.

        """

        self._normalize()

    def _normalize(self):
        self.items = map(unicode, self.items)

    def __repr__(self):
        r = "<%s.%s(%i items)>" % (self.__class__.__module__,
                self.__class__.__name__, len(self.items))
        if self.is_cloud:
            r += ", is_cloud=%r" % self.is_cloud
        r += ")"
        return r


class Insert(object):
    """The specification for an argument to a :class:`BlockType`."""

    SHAPE_DEFAULTS = {
        "number": 0,
        "number-menu": 0,
        "stack": [],
    }

    SHAPE_FMTS = {
        'number': '(%s)',
        'string': '[%s]',
        'readonly-menu': '[%s v]',
        'number-menu': '(%s v)',
        'color': '[%s]',
        'boolean': '<%s>',
        'stack': '\n\t%s\n',
        'inline': '%s',
    }

    def __init__(self, shape, default=None):
        self.shape = shape
        """What kind of values this argument accepts.

        Shapes that accept a simple data value or a reporter block:

        ``'number'``
            An integer or float number.

        ``'string'``
            A unicode text value.

        ``'readonly-menu'``
            A choice of string value from a menu.

            Some readonly inserts do not accept reporter blocks.

        ``'number-menu'``
            Either a number value, or a choice of special value from a menu.

        ``'color'``
            A :class:`Color` value.

        Shapes that only accept blocks with the corresponding :attr:`shape`:

        ``'boolean'``
            Accepts a boolean block.

        ``'stack'``
            Accepts a list of stack blocks. Defaults to ``[]``.

            The block is rendered with a "mouth" into which blocks can be
            inserted.

        Special shapes:

        ``'inline'``
            Not actually an insert -- used for variable and list reporters.

        """

        # TODO self.kind -- Valid values for a ``menu`` insert.

        if default is None:
            default = Insert.SHAPE_DEFAULTS.get(shape, None)
        self.default = default
        """The default value for the insert."""

    def __repr__(self):
        r = "%s.%s(%r" % (self.__class__.__module__,
                self.__class__.__name__, self.shape)
        if self.default != Insert.SHAPE_DEFAULTS.get(self.shape, None):
            r += ", default=%r" % self.default
        r += ")"
        return r

    def __eq__(self, other):
        if isinstance(other, Insert):
            for name in ("shape", "default"):
                if getattr(self, name) != getattr(other, name):
                    return False
            else:
                return True

    def __ne__(self, other):
        return not self == other

    def similar_to(self, other):
        assert isinstance(other, Insert)
        def sim(shape):
            if shape == 'number-menu':
                return 'number'
            return shape
        return (sim(self.shape) == sim(other.shape))

    def stringify(self, value=None):
        if value is None:
            value = self.default
            if value is None:
                value = ""
        if isinstance(value, Block):
            return value.stringify(in_insert=True) # use block's shape
        else:
            if hasattr(value, "__iter__"):
                value = "\n".join(block.stringify() for block in value)
            elif hasattr(value, "stringify"):
                value = value.stringify()

            if self.shape == 'stack':
                value = value.replace("\n", "\n\t")

            return Insert.SHAPE_FMTS[self.shape] % (value,)


class BaseBlockType(object):
    """Base for :class:`BlockType` and :class:`TranslatedBlockType`.

    Defines common attributes.

    """

    SHAPE_FMTS = {
        'reporter': '(%s)',
        'boolean': '<%s>',
    }

    def __init__(self, shape, parts):
        self.shape = shape
        """The shape of the block. Valid values:

        ``'stack'``
            The default. Can connect to blocks above and below. Appear
            jigsaw-shaped.

        ``'cap'``
            Stops the script executing after this block. No blocks can be
            connected below them.

        ``'hat'``
            A block that starts a script, such as by responding to an event.
            Can connect to blocks below.

        ``'reporter'``
            Return a value. Can be placed into insert slots of other blocks as
            an argument to that block. Appear rounded.

        ``'boolean'``
            Like reporter blocks, but return a true/false value. Appear
            hexagonal.

        "C"-shaped blocks with "mouths" for stack blocks, such as ``"doIf"``,
        are specified by adding ``Insert('stack')`` to the end of
        :attr:`parts`.

        """
        # In Scratch 1.4: one of '-', 'b', 'c', 'r', 'E', 'K', 'M', 'S', 's', 't'
        # In Scratch 2.0: one of ' ', 'b', 'c', 'r', 'e', 'cf', 'f', 'h'

        self.parts = parts
        """A list describing the text and arguments of the block.

        Contains strings, which are part of the text displayed on the block,
        and :class:`Insert` instances, which are arguments to the block.

        """

    @property
    def text(self):
        """The text displayed on the block.

        String containing ``"%s"`` in place of inserts.

        eg. ``'say %s for %s secs'``

        """
        parts = [("%s" if isinstance(p, Insert) else p) for p in self.parts]
        parts = [("%%" if p == "%" else p) for p in parts] # escape percent
        return "".join(parts)

    @property
    def inserts(self):
        """The type of each argument to the block.

        List of :class:`Insert` instances.

        """
        return [p for p in self.parts if isinstance(p, Insert)]

    @property
    def defaults(self):
        """Default values for block inserts. (See :attr:`Block.args`.)"""
        return [i.default for i in self.inserts]

    def __repr__(self):
        return "<%s.%s(%r, %r)>" % (self.__class__.__module__,
                self.__class__.__name__,
                self.text % tuple(i.stringify(None) for i in self.inserts),
                self.shape)

    def stringify(self, args=None, in_insert=False):
        if args is None: args = self.defaults
        args = list(args)

        r = self.text % tuple(i.stringify(args.pop(0)) for i in self.inserts)
        for insert in self.inserts:
            if insert.shape == 'stack':
                return r + "end"

        fmt = BaseBlockType.SHAPE_FMTS.get(self.shape, "%s")
        if in_insert and fmt == "%s":
            fmt = "{%s}"

        return fmt % r


class BlockType(BaseBlockType):
    """The specification for a type of :class:`Block`.

    These are initialiased by :class:`Kurt` by combining
    :class:`TranslatedBlockType` objects from individual format plugins to
    create a single :class:`BlockType` for each command.

    """

    def __init__(self, translations):
        self._translations = OrderedDict(translations)
        """Stores :class:`TranslatedBlockType` objects for each plugin name."""

    def _add_translation(self, tb):
        """Add the given TranslatedBlockType to :attr:`_translations`.

        If the plugin already exists, replace the existing translation.

        """
        assert self.shape == tb.shape
        assert len(self.inserts) == len(tb.inserts)
        for (i, o) in zip(self.inserts, tb.inserts):
            assert i.similar_to(o)
        if tb._plugin not in self._translations:
            self._translations[tb._plugin] = tb

    def translate(self, plugin=None):
        """Return a :class:`TranslatedBlockType` for the given plugin name.

        If plugin is ``None``, return the first registered plugin.

        """
        if plugin:
            return self._translations[plugin]
        else:
            return self._translations.values()[0]

    def has_command(self, command):
        """Returns True if any of the translations have the given command."""
        for tb in self._translations.values():
            if tb.command == command:
                return True
        return False

    def has_insert(self, shape):
        """Returns True if any of the inserts have the given shape."""
        for insert in self.inserts:
            if insert.shape == shape:
                return True
        return False

    @staticmethod
    def _strip_text(text):
        """Returns text with spaces and inserts removed."""
        text = re.sub(r'[ ,?:]|%s', "", text.lower())
        for chr in "-%":
            new_text = text.replace(chr, "")
            if new_text:
                text = new_text
        return text.lower()

    @property
    def shape(self):
        return self.translate().shape

    @property
    def parts(self):
        return self.translate().parts

    @classmethod
    def get(cls, block_type):
        """Return a :class:`BlockType` instance from the given parameter.

        * If it's already a BlockType instance, return that.

        * If it exactly matches the command on a :class:`TranslatedBlockType`,
          return the corresponding BlockType.

        * If it loosely matches the text on a TranslatedBlockType, return the
          corresponding BlockType.

        """
        if isinstance(block_type, BlockType):
            return block_type

        blocks = kurt.plugin.Kurt.block_by_command(block_type)
        if blocks:
            return blocks[0]

        blocks = kurt.plugin.Kurt.block_by_text(block_type)
        if blocks:
            return blocks[0]

        raise ValueError, "Unknown block type %r" % block_type

    def __eq__(self, other):
        if isinstance(other, BlockType):
            if self.shape == other.shape and self.inserts == other.inserts:
                for t in self._translations:
                    if t in other._translations:
                        return True

    def __ne__(self, other):
        return not self == other

    def copy(self):
        """Return a new BlockType instance with the same attributes."""
        return BlockType(self.command, self.text, self.flag, self.category,
                list(self.defaults))


class TranslatedBlockType(BaseBlockType):
    """Holds plugin-specific :class:`BlockType` attributes.

    For each block concept, :class:`Kurt` builds a single BlockType that
    references a corresponding TranslatedBlockType for each plugin that
    supports that block.

    Note that whichever plugin is loaded first takes precedence.

    """

    def __init__(self, plugin, category, shape, command, parts, match=None):
        BaseBlockType.__init__(self, shape, parts)

        self._plugin = plugin
        """The format plugin the block belongs to."""

        self.command = command
        """The method name from the source code, used to identify the block.

        eg. ``'say:duration:elapsed:from:'``

        """

        self.category = category
        """Where the block is found in the interface."""
        # In Scratch 1.4, one of:
        # 'motion', 'looks', 'sound', 'pen', 'control', 'sensing', 'operators',
        # 'variables', 'list', 'motor', 'obsolete number blocks', 'obsolete
        # sound blocks', 'obsolete sprite looks blocks', 'obsolete sprite motion
        # blocks', 'obsolete image effects'
        #
        # In Scratch 2.0, one of:
        # 'control', 'motion', 'looks', 'sound', 'pen', 'data', 'events',
        # 'control', 'sensing', 'operators', 'more blocks', 'sensing', 'list',
        # 'obsolete', 'pen', 'obsolete', 'sensor', 'wedo', 'midi', 'looks',
        # 'midi'

        self._match = match
        """String -- equivalent command from other plugin.

        The plugin containing the command to match against must have been
        registered first.

        """

    def __eq__(self, other):
        if isinstance(other, TranslatedBlockType):
            if self.plugin == other.plugin and self.command == other.command:
                return True

    def __ne__(self, other):
        return not self == other


class Block(object):
    """A statement in a graphical programming language. Blocks can connect
    together to form sequences of commands, which are stored in a
    :class:`Script`.  Blocks perform different commands depending on their
    type.

    :param type:      A :class:`BlockType` instance, used to identify the
                      command the block performs.
                      Will also exact match a :attr:`command` or loosely match
                      :attr:`text`.

    :param ``*args``: List of the block's arguments.

    So the following constructors are all equivalent::

        >>> block = kurt.Block('say:duration:elapsed:from:', 'Hello!', 2)
        >>> block = kurt.Block("say %s for %s secs", "Hello!", 2)
        >>> block = kurt.Block("sayforsecs", "Hello!", 2)

    Using BlockType::

        >>> block.type
        <kurt.BlockType('say [Hello!] for (2) secs', 'stack')>
        >>> block.args
        ['Hello!', 2]
        >>> block2 = kurt.Block(block.type, "Goodbye!", 5)
        >>> block.stringify()
        'say [Hello!] for (2) secs'
        >>> block2.stringify()
        'say [Goodbye!] for (5) secs'

    """

    def __init__(self, block_type, *args):
        self.type = BlockType.get(block_type)
        """:class:`BlockType` instance. The command this block performs."""
        # TODO: accept command? or change repr.

        self.args = []
        """List of arguments to the block.

        The block's parameters are found in :attr:`type.inserts
        <BlockType.inserts>`. Default values come from :attr:`type.defaults
        <BlockType.defaults`.

        """

        self.comment = None
        """The text of the comment attached to the block. None if no comment is
        attached.

        Comments can only be attached to stack blocks.

        """

        if self.type:
            self.args = self.type.defaults[:]

        for i in xrange(len(args)):
            if i < len(self.args):
                self.args[i] = args[i]
            else:
                self.args.append(args[i])

    def _normalize(self):
        assert isinstance(self.type, BlockType)
        self.args = list(self.args)
        self.comment = unicode(self.comment)

    def __eq__(self, other):
        return (
            isinstance(other, Block) and
            self.type == other.type and
            self.args == other.args
        )

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        string = "%s.%s(%s, " % (self.__class__.__module__,
                self.__class__.__name__, repr(self.type.translate().command))
        for arg in self.args:
            if isinstance(arg, Block):
                string = string.rstrip("\n")
                string += "\n\t" + repr(arg).replace("\n", "\n\t") + ",\n"
            elif isinstance(arg, list):
                if string.endswith("\n"):
                    string += "\t"
                else:
                    string += " "
                string += "[\n"
                for block in arg:
                    string += "\t\t" + repr(block).replace("\n", "\n\t\t")
                    string += ",\n"
                string += "\t], "
            else:
                string += repr(arg) + ", "
        string = string.rstrip(" ").rstrip(",")
        return string + ")"

    def stringify(self, in_insert=False):
        return self.type.stringify(self.args, in_insert)


class Script(object):
    """A single sequence of blocks. Each :class:`Scriptable` can have many
    Scripts.

    The first block, ``self.blocks[0]`` is usually a "when" block, eg. an
    EventHatMorph.

    Scripts implement the ``list`` interface, so can be indexed directly, eg.
    ``script[0]``. All other methods like ``append`` also work.

    """

    def __init__(self, blocks=None, pos=None):
        self.blocks = blocks or []
        self.blocks = list(self.blocks)
        """The list of :class:`Blocks <Block>`."""

        self.pos = tuple(pos) if pos else None
        """``(x, y)`` position from the top-left of the script area in
        pixels.

        """

    def _normalize(self):
        self.pos = self.pos
        self.blocks = list(self.blocks)

    def __eq__(self, other):
        return (
            isinstance(other, Script) and
            self.blocks == other.blocks
        )

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        string = "%s.%s([\n" % (self.__class__.__module__,
                self.__class__.__name__)
        for block in self.blocks:
            string += "\t" + repr(block).replace("\n", "\n\t") + ",\n"
        string = string.rstrip().rstrip(",") + "]"
        if self.pos:
            string += "], pos=%r" % (self.pos,)
        return string + ")"

    def stringify(self):
        return "\n".join(block.stringify() for block in self.blocks)

    # Pretend to be a list

    def __getattr__(self, name):
        return getattr(self.blocks, name)

    def __iter__(self):
        return iter(self.blocks)

    def __len__(self):
        return len(self.blocks)

    def __getitem__(self, index):
        return self.blocks[index]

    def __setitem__(self, index, value):
        self.blocks[index] = value

    def __delitem__(self, index):
        del self.blocks[index]


class Comment(object):
    """A free-floating comment in :attr:`Scriptable.scripts`."""

    def __init__(self, comment, pos):
        self.pos = pos
        """``(x, y)`` position from the top-left of the script area in
        pixels.

        """

        self.text = u""
        """The text of the comment."""

    def _normalize(self):
        self.pos = self.pos
        self.text = unicode(self.text)


class Costume(object):
    """Describes the look of a sprite.

    The raw image data is stored in :attr:`image`.

    """

    def __init__(self, name, image, rotation_center=None):
        self.name = unicode(name)
        """Name used by scripts to refer to this Costume."""

        if not rotation_center:
            rotation_center = (int(image.width / 2), int(image.height / 2))
        self.rotation_center = tuple(rotation_center)
        """``(x, y)`` position of the center of the image from the top-left
        corner, about which the sprite rotates.

        Defaults to the center of the image.
        """

        self.image = image
        """An :class:`Image` instance containing the raw image data."""


    @classmethod
    def load(self, path):
        """Load costume from image file.

        Uses :attr:`Image.load`, but will set the Costume's name based on the
        image filename.

        """
        (folder, filename) = os.path.split(path)
        (name, extension) = os.path.splitext(filename)
        return Costume(name, Image.load(path))

    def save(self, path):
        """Save the costume to an image file at the given path.

        Uses :attr:`Image.save`, but if the path ends in a folder instead of a
        file, the filename is based on the project's :attr:`name`.

        The image format is guessed from the extension. If path has no
        extension, the image's :attr:`format` is used.

        :returns: Path to the saved file.

        """
        (folder, filename) = os.path.split(path)
        if not filename:
            filename = _clean_filename(self.name)
            path = os.path.join(folder, filename)

        return self.image.save(path)

    def resize(self, size):
        """Resize :attr:`image` in-place."""
        self.image = self.image.resize(size)

    def __repr__(self):
        return "<%s.%s name=%r rotation_center=%d,%d at 0x%X>" % (
            self.__class__.__module__, self.__class__.__name__, self.name,
            self.rotation_center[0], self.rotation_center[1], id(self)
        )


class Image(object):
    """The contents of an image file.

    Constructing from raw file contents::

        Image(file_contents, "JPEG")

    Constructing from a :class:`PIL.Image.Image` instance::

        pil_image = PIL.Image.new("RGBA", (480, 360))
        Image(pil_image)

    Loading from file::

        Image.load("path/to/image.jpg")

    Images should be considered to be immutable. If you want to modify an
    image, get a :class:`PIL.Image.Image` instance from :attr:`pil_image`,
    modify that, and use it to construct a new Image. Modifying images in-place
    may break things.

    The reason for having multiple constructors is so that kurt can implement
    lazy loading of image data -- in many cases, a PIL image will never need to
    be created.

    """

    def __init__(self, contents, format=None):
        self._path = None
        self._pil_image = None
        self._contents = None
        self._format = None
        self._size = None
        if isinstance(contents, PIL.Image.Image):
            self._pil_image = contents
        else:
            self._contents = contents
            self._format = Image._image_format(format)

    # Properties

    @property
    def pil_image(self):
        """A :class:`PIL.Image.Image` instance containing the image data."""
        if not self._pil_image:
            self._pil_image = PIL.Image.open(StringIO(self.contents))
        return self._pil_image

    @property
    def contents(self):
        """The raw file contents as a string."""
        if not self._contents:
            if self._path:
                # Read file into memory so we don't run out of file descriptors
                f = open(self._path, "rb")
                self._contents = f.read()
                f.close()
            elif self._pil_image:
                # Write PIL image to string
                f = StringIO()
                self._pil_image.save(f, self.format)
                self._contents = f.getvalue()
        return self._contents

    @property
    def format(self):
        """The format of the image file.

        An uppercase string corresponding to the
        :attr:`PIL.ImageFile.ImageFile.format` attribute.  Valid values include
        ``"JPEG"`` and ``"PNG"``.

        """
        if self._format:
            return self._format
        elif self.pil_image:
            return self.pil_image.format

    @property
    def extension(self):
        """The extension of the image's :attr:`format` when written to file.

        eg ``".png"``

        """
        return Image._image_extension(self.format)

    @property
    def size(self):
        """``(width, height)`` in pixels."""
        if self._size and not self._pil_image:
            return self._size
        else:
            return self.pil_image.size

    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    # Methods

    @classmethod
    def load(cls, path):
        """Load image from file."""
        assert os.path.exists(path), "No such file: %r" % path

        (folder, filename) = os.path.split(path)
        (name, extension) = os.path.splitext(filename)

        image = Image(None)
        image._path = path
        image._format = Image._image_format(extension)

        return image

    def convert(self, *formats):
        """Return an Image instance with the first matching format.

        For each format in ``*args``: If the image's :attr:`format` attribute
        is the same as the format, return self, otherwise try the next format.

        If none of the formats match, return a new Image instance with the
        last format.

        """
        for format in formats:
            format = Image._image_format(format)
            if self.format == format:
                return self
        else:
            return self._convert(format)

    def _convert(self, format):
        """Return a new Image instance with the given format.

        Returns self if the format is already the same.

        """
        if self.format == format:
            return self
        else:
            image = Image(self.pil_image)
            image._format = format
            return image

    def save(self, path):
        """Save image to file path.

        The image format is guessed from the extension. If path has no
        extension, the image's :attr:`format` is used.

        :returns: Path to the saved file.

        """
        (folder, filename) = os.path.split(path)
        (name, extension) = os.path.splitext(filename)

        if not name:
            raise ValueError, "name is required"

        if extension:
            format = Image._image_format(extension)
        else:
            format = self.format
            filename = name + self.extension
            path = os.path.join(folder, filename)

        image = self.convert(format)
        if image._contents:
            f = open(path, "wb")
            f.write(image._contents)
            f.close()
        else:
            image.pil_image.save(path, format)

        return path

    def resize(self, size):
        """Return a new Image instance with the given size."""
        return Image(self.pil_image.resize(size, PIL.Image.ANTIALIAS))

    # Static methods

    @staticmethod
    def _image_format(format_or_extension):
        if format_or_extension:
            format = format_or_extension.lstrip(".").upper()
            if format == "JPG":
                format = "JPEG"
            return format

    @staticmethod
    def _image_extension(format_or_extension):
        if format_or_extension:
            extension = format_or_extension.lstrip(".").lower()
            if extension == "jpeg":
                extension = "jpg"
            return "." + extension



#-- Import plugins --#

import kurt.plugin
import kurt.scratch20
import kurt.scratch14

