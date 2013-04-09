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

"""User-class objects with variable numbers of fields.
Most of the objects you're interested in live here.

They support dot notation for accessing fields. Use .fields.keys() to see
available fields [dir() won't show them.]
"""

from construct import Container
import os
import StringIO
from array import array

try:
    import PIL.Image
except ImportError:
    PIL = None

from inline_objects import Ref
from fixed_objects import *


def require_pil():
    if not PIL:
        raise ValueError, "Missing dependency: " \
            "PIL library needed for image support"



class UserObject(object):
    """A user-class object with a variable number of fields.
    Supports dot notation for accessing fields.
    Use .fields.keys() to see available fields [dir() won't show them.]

    Each class lists its field order in _fields.
    Unknown fields not in this list are named "undefined-%i", where i is the
    field index.
    """
    _fields = []
    _version = 1

    def to_construct(self, context):
        field_values = self.field_values[:]

        for i in range(len(field_values)):
            value = field_values[i]
            if i < len(self._fields):
                field = self._fields[i]
                field_values[i] = self._encode_field(field, value)

        return Container(
            classID = self.__class__.__name__,
            field_values = field_values,
            length = len(field_values),
            version = self.version,
        )

    def _encode_field(self, name, value):
        """Modify the field with the given name before saving, if necessary.
        Override this in subclass to modify building of specific fields.
        """
        return value

    @classmethod
    def from_construct(cls, obj, context):
        return cls(obj.field_values, version=obj.version)

    def _decode_field(cls, name, value):
        """Return value of named field passed to object's constructor.
        Override this in subclass to modify specific fields.
        """
        return value

    def set_defaults(self):
        """Set defaults on self. Return nothing.
        Subclasses can override this to setup default values.
        """
        pass

    def built(self):
        for field in self._fields:
            if field in self.fields:
                value = self.fields[field]
                self.fields[field] = self._decode_field(field, value)

    def __init__(self, field_values=None, **args):
        """Initalize a UserObject.
        @param field_values: (optional) list of fields as parsed from a file.
        @param **args: field values.
        """
        self.fields = dict(zip(self._fields, [None] * len(self._fields)))

        self.version = self._version
        if 'version' in args:
            self.version = args.pop('version')

        self.set_defaults()

        if field_values:
            defined_fields = self._fields[:]
            defined_fields += tuple("undefined-%i" % i
                for i in range(len(defined_fields), len(field_values)))
            self.fields.update(zip(defined_fields, field_values))

        self.fields.update(args)

        if "name" in self.fields:
            # make sure we use property setter
            name = self.fields["name"]
            del self.fields["name"]
            self.name = name

    def __getattr__(self, name):
        if name in self.fields:
            return self.fields[name]
        else:
            raise AttributeError, ('%s instance has no attribute %s'
                % (self.__class__.__name__, name))

    def __setattr__(self, name, value):
        if name in self._fields:
            self.fields[name] = value
        else:
            object.__setattr__(self, name, value)

    def __delattr__(self, name):
        if name in self.fields:
            del self.fields[name]
        else:
            object.__delattr__(self, name)

    def __len__(self):
        return len(self.fields)

    @property
    def ordered_fields(self):
        ordered_fields = []
        fields = self.fields.copy()
        for field_name in self._fields:
            value = None
            if field_name in self.fields:
                value = fields.pop(field_name)
            ordered_fields.append((field_name, value))

        # leftover undefined fields
        fields = sorted(fields.items(),
            key=lambda (field,value): int(field.split('-')[1])
        )
        for field_name, value in fields:
            ordered_fields.append((field_name, value))

        return ordered_fields

    @property
    def field_values(self):
        return [value for (field_name, value) in self.ordered_fields]

    def __repr__(self):
        name = getattr(self, "name", "")
        return "<%s(%s)>" % (self.__class__.__name__, name)



### Squeak & Morphic classes ###
class BaseMorph(UserObject):
    _fields = ("bounds", "owner", "submorphs", "color", "flags", "properties")

    def set_defaults(self):
        self.flags = 0
        self.submorphs = []
        self.color = Color(1023, 1023, 1023)

class Morph(BaseMorph):
    """Base class for most UserObjects."""
    classID = 100

class BorderedMorph(BaseMorph):
    classID = 101
    _fields = Morph._fields + ("borderWidth", "borderColor")

    def set_defaults(self):
        BaseMorph.set_defaults(self)
        self.borderWidth = 1
        self.borderColor = Color(0, 0, 0)

class RectangleMorph(BorderedMorph):
    classID = 102

class EllipseMorph(BorderedMorph):
    classID = 103

class AlignmentMorph(RectangleMorph):
    classID = 104
    _fields = RectangleMorph._fields + ("orientation", "centering", "hResizing",
        "vResizing", "inset")

class StringMorph(BaseMorph):
    classID = 105
    _fields = Morph._fields + ("font_with_size", "emphasis", "contents")

class UpdatingStringMorph(StringMorph):
    classID = 106
    _fields = StringMorph._fields + ("format", "target", "getSelector",
        "putSelector", "parameter", "floatPrecision", "growable", "stepTime")

class SimpleSliderMorph(BorderedMorph):
    classID = 107
    _fields = BorderedMorph._fields + ("slider", "value", "setValueSelector",
        "sliderShadow", "sliderColor", "descending", "model", "target",
        "actionSelector", "arguments", "actWhen")

class SimpleButtonMorph(RectangleMorph):
    classID = 108
    _fields = RectangleMorph._fields + ("target", "actionSelector", "arguments",
        "actWhen")

class SampledSound(UserObject):
    classID = 109
    _fields = ("envelopes", "scaledVol", "initialCount", "samples",
        "originalSamplingRate", "samplesSize", "scaledIncrement",
        "scaledInitialIndex")

class ImageMorph(BaseMorph):
    classID = 110
    _fields = Morph._fields + ("form", "transparency")

class SketchMorph(BaseMorph):
    classID = 111
    _fields = Morph._fields + ("originalForm", "rotationCenter",
        "rotationDegrees", "rotationStyle", "scalePoint", "offsetWhenRotated")




### Scratch-specific classes ###

class ScriptableScratchMorph(BaseMorph):
    _fields = Morph._fields + ("name", "variables", "scripts", "isClone", "media",
        "costume")

    def __init__(self, *args, **kwargs):
        UserObject.__init__(self, *args, **kwargs)

        self.images = []
        self.sounds = []

        self.build_media() # returns silently if self.media is still a Ref

    def set_defaults(self):
        BaseMorph.set_defaults(self)

        self.scripts = ScriptCollection()
        self.media = []
        self.costume = None # defaults to first Image in self.media on save
        self.variables = {}
        self.lists = {}
        self.isClone = False

        self.volume = 100
        self.tempoBPM = 60

    def built(self):
        UserObject.built(self)

        scripts = [Script.from_array(self, script) for script in self.scripts]
        self.scripts = ScriptCollection(scripts)

        comments = []
        for script in self.scripts:
            if isinstance(script, Comment):
                comments.append(script)
        for comment in comments:
            self.scripts.remove(comment)

        blocks_by_id = list(self.blocks_by_id())

        for comment in comments:
            comment.attach_scripts(blocks_by_id)

        self.build_media()

    def build_media(self):
        if isinstance(self.media, Ref):
            return # Don't run this yet!

        media = self.media
        self.media = []
        for media in media:
            if isinstance(media, Sound):
                self.sounds.append(media)
            elif isinstance(media, Image):
                self.images.append(media)
            else:
                self.media.append(media)

    def blocks_by_id(self):
        """Return a list of all the blocks in script order but reverse script
        blocks order.
        Used to determine which block a Comment is anchored to.

        Note that Squeak arrays are 1-based, so index with:
            blocks_by_id[index - 1]
        """
        for script in self.scripts:
            for block in reversed(list(script.to_block_list())):
                yield block

    def normalize(self):
        """Called before saving"""
        if not self.costume:
            for media in self.media + self.images:
                if isinstance(media, Image):
                    self.costume = media
                    break
            else:
                raise ValueError("%r does not have a costume" % self)

        self.lists = dict(
            (unicode(name), list) for (name, list) in self.lists.items()
        )
        for list_name in self.lists:
            scratch_list = self.lists[list_name]
            if not isinstance(scratch_list, ScratchListMorph):
                scratch_list = ScratchListMorph(items=scratch_list)
                self.lists[list_name] = scratch_list
            scratch_list.name = list_name

            # This would show the list watcher on the stage:
            #scratch_list.target = self
            #if isinstance(self, Stage):
            #     scratch_list.owner = self
            #else:
            #    scratch_list.owner = self.owner

            scratch_list.normalize()

    def _encode_field(self, name, value):
        if name == 'scripts':
            scripts = [script.to_array() for script in value]
            blocks_by_id = list(self.blocks_by_id())
            for block in blocks_by_id:
                if block.comment:
                    scripts.append(block.comment.to_array(blocks_by_id))
            return scripts
        elif name == 'media':
            return OrderedCollection(self.sounds + self.images + self.media)
        else:
            return value


class SensorBoardMorph(BaseMorph):
    classID = 123
    _fields = BaseMorph._fields + ("unknown",)
                                  # TODO — I have NO idea what this does.


class Sprite(ScriptableScratchMorph):
    """A sprite.
    Main attributes:
        scripts
        variables
        lists
        costumes
        sounds
    Use .fields.keys() to see all available fields.
    """
    classID = 124
    _fields = ScriptableScratchMorph._fields + ("visibility", "scalePoint",
        "rotationDegrees", "rotationStyle", "volume", "tempoBPM", "draggable",
        "sceneStates", "lists")
    _version = 3

    def set_defaults(self):
        ScriptableScratchMorph.set_defaults(self)

        self.name = "Sprite1"
        self.color = Color(0, 0, 1023)
        # self.owner — Stage
        # self.bounds = Rectangle() - default to size of costume?

        self.visibility = 100
        self.scalePoint = Point(1.0, 1.0)
        self.rotationDegrees = 0.0
        self.rotationStyle = Symbol("normal")
        self.draggable = False
        self.sceneStates = {}

    def normalize(self):
        """Called before saving"""
        ScriptableScratchMorph.normalize(self)

        if not self.bounds:
            try:
                self.bounds = Rectangle(
                    [0, 0, self.costume.width, self.costume.height])
            except ValueError:
                # invalid costume, or maybe JPG
                self.bounds = Rectangle([0, 0, 100, 100])

    @property
    def costumes(self):
        return self.images

    @costumes.setter
    def costumes(self, value):
        self.images = value


class SpriteCollection(OrderedCollection):
    """Provides indexing by sprite name as well as index"""
    # TODO: use OrderedDict?
    def __getitem__(self, item):
        try:
            index = int(item)
        except ValueError:
            for sprite in self.value:
                if sprite.name == item:
                    return sprite
        return self.value[index]

    def __repr__(self):
        return repr(self.value)

    def __contains__(self, item):
        if item in self.value:
            return True
        for sprite in self.value:
            if sprite.name == item:
                return True
        return False
        


class Stage(ScriptableScratchMorph):
    """The project stage. Contains project contents including sprites and media.
    Main attributes:
        sprites - ordered list of sprites.
        submorphs - everything on the stage, including sprites &
                    variable/list watchers.
        scripts
        variables
        lists
        backgrounds
        sounds
    Use .fields.keys() to see all available fields.
    """
    classID = 125
    _fields = ScriptableScratchMorph._fields + ("zoom", "hPan", "vPan",
        "obsoleteSavedState", "sprites", "volume", "tempoBPM", "sceneStates",
        "lists")
    _version = 5

    def set_defaults(self):
        ScriptableScratchMorph.set_defaults(self)

        self.name = "Stage"
        self.bounds = Rectangle([0, 0, 480, 360])
        self.color = Color(1023, 1023, 1023)

        self.zoom = 1.0
        self.hPan =  0
        self.vPan =  0
        self.sprites = SpriteCollection()
        self.sceneStates = {}

        image = Image(
            name = "background",
            form = ColorForm(
                width = 480,
                height = 360,
                depth = 1,
                bits = ByteArray("\xf5\x18\xff\x00\x00Ta\x00"),
            ),
        )

        self.media = [image]
        self.images = [image]
        self.costume = image

    def normalize(self):
        """Called before saving"""
        ScriptableScratchMorph.normalize(self)

        for sprite in self.sprites:
            if sprite not in self.submorphs:
                self.submorphs.append(sprite)
            sprite.owner = self
            sprite.normalize()

    def built(self):
        ScriptableScratchMorph.built(self)
        self.sprites = SpriteCollection(self.sprites)

    def _encode_field(self, name, value):
        value = ScriptableScratchMorph._encode_field(self, name, value)

        if name == 'sprites':
            return OrderedCollection(self.sprites)
        else:
            return value

    @property
    def background(self):
        return self.costume

    @background.setter
    def background(self, value):
        self.costume = value

    @property
    def backgrounds(self):
        return self.images

    @backgrounds.setter
    def backgrounds(self, value):
        self.images = value


from scripts import Script, Comment, ScriptCollection
# Yes, this is stupid. Circular dependencies ftw. -_-




class ChoiceArgMorph(BaseMorph):
    """unused?"""
    classID = 140

class ColorArgMorph(BaseMorph):
    """unused?"""
    classID = 141

class ExpressionArgMorph(BaseMorph):
    """unused?"""
    classID = 142

class SpriteArgMorph(BaseMorph):
    """unused?"""
    classID = 145

class BlockMorph(BaseMorph):
    """unused?"""
    classID = 147
    _fields = Morph._fields + ("isSpecialForm", "oldColor")

class CommandBlockMorph(BlockMorph):
    """unused?"""
    classID = 148
    _fields = BlockMorph._fields + ("commandSpec", "argMorphs", "titleMorph",
        "receiver", "selector", "isReporter", "isTimed", "wantsName",
        "wantsPossession")

class CBlockMorph(BaseMorph):
    """unused?"""
    classID = 149

class HatBlockMorph(BaseMorph):
    """unused?"""
    classID = 151

class ScratchScriptsMorph(BorderedMorph):
    classID = 153

    def __iter__(self):
        return iter(self.submorphs)

class ScratchSliderMorph(BaseMorph):
    """unused?"""
    classID = 154

class WatcherMorph(AlignmentMorph):
    """A variable watcher."""
    classID = 155
    _fields = AlignmentMorph._fields + ("titleMorph", "readout", "readoutFrame",
        "scratchSlider", "watcher", "isSpriteSpecific", "unused", "sliderMin",
        "sliderMax", "isLarge")
    _version = 5

    @property
    def name(self):
        return self.titleMorph.contents

    @name.setter
    def name(self, value):
        self.titleMorph.contents = value

class SetterBlockMorph(BaseMorph):
    """unused?"""
    classID = 157

class EventHatMorph(BaseMorph):
    """unused?"""
    classID = 158

class VariableBlockMorph(CommandBlockMorph):
    """unused?"""
    classID = 160
    _fields = CommandBlockMorph._fields + ("isBoolean",)




class ScratchMedia(UserObject):
    _fields = ("name",)


class Image(ScratchMedia):
    """An image file, used for costumes and backgrounds.

    You can't modify image data in-place (excepting `textBox`) -- create a new
    image object using load() or from_image() instead.

    Class methods:
        load(path) — load a PNG or JPEG image
        from_image(name, image) — create Image from a PIL.Image.Image object

    Instance methods:
        save(path) — save the image to an external file.
        get_image() — return a PIL.Image.Image object
    """

    classID = 162
    _fields = ScratchMedia._fields + ("form", "rotationCenter", "textBox",
        "jpegBytes", "compositeForm")
    _version = 4

    def built(self):
        # Called after loading from file
        if self.compositeForm:
            self.form_without_text = self.form
            self.form = self.compositeForm

        if not self.size and self.form:
            self.size = (self.form.width, self.form.height)

    def _encode_field(self, name, value):
        if name == 'name':
            return unicode(value)
        return value

    @classmethod
    def load(cls, path):
        """Load image file and return an Image."""
        require_pil()

        (_, name) = os.path.split(path)
        if "." in name:
            name_without_extension = ".".join(name.split(".")[:-1])
        else:
            name_without_extension = name

        image_file = PIL.Image.open(path) # Doesn't read raster data yet :)

        if image_file.format == "JPEG":
            f = open(path, "rb")
            jpegBytes = f.read()
            f.close()

            image = cls(
                name = name_without_extension,
                jpegBytes = ByteArray(jpegBytes),
            )
            image.size = image_file.size
            return image

        else:
            return cls.from_image(name_without_extension, image_file)


    @classmethod
    def from_image(cls, name, image_file):
        """Create Image from a PIL.Image.Image object"""
        name = unicode(name)
        if image_file.format == "JPEG":
            f = StringIO.StringIO()
            image_file.save(f, format="JPEG")

            f.seek(0)
            jpegBytes = f.read()

            image = cls(
                name = name,
                jpegBytes = ByteArray(jpegBytes),
            )

        else:
            image_file = image_file.convert("RGBA")
            assert image_file.mode == "RGBA"

            (width, height) = image_file.size
            rgba_string = image_file.tostring()

            image = cls(
                name = name,
                form = Form.from_string(width, height, rgba_string),
            )

        image.size = image_file.size
        return image


    def set_defaults(self):
        ScratchMedia.set_defaults(self)
        self.rotationCenter = Point(0, 0)

        self.form_without_text = None
        self.size = None


    @property
    def width(self):
        (width, height) = self.size
        return width


    @property
    def height(self):
        (width, height) = self.size
        return height


    def get_image(self):
        """Return a PIL.Image.Image object"""
        if self.jpegBytes:
            image = PIL.Image.open(StringIO.StringIO(self.jpegBytes.value))
        else:
            (width, height, rgba_array) = self.form.to_array()
            size = (width, height)
            image = PIL.Image.fromstring("RGBA", size, rgba_array)

        return image


    def save(self, path, format=None):
        """Save the image data to an external file.
        Returns the filename with extension.
        Arguments:
            path - absolute/relative path to save to. Doesn't require extension.
            format - "PNG", "JPEG", etc: passed to PIL.
        """
        guessed_from_extension = False
        (folder, name) = os.path.split(path)
        if "." in name:
            format = name.split('.')[-1]
            format = format.lstrip(".").upper()
            if format == "JPG": format = "JPEG"
            guessed_from_extension = True

        if not format:
            if self.jpegBytes:
                format = "JPEG"
            else:
                format = "PNG"

        if not guessed_from_extension:
            extension = format.lower()
            if extension == "jpeg": extension = "jpg"
            path += "." + extension
            name += "." + extension

        image = self.get_image()
        image.save(path, format)
        return name

    def save_png(self, path):
        """Deprecated. Use .save(path, "PNG") instead"""
        self.save(path, "PNG")

    def save_jpg(self, path):
        """Deprecated. Use .save(path, "JPEG") instead"""
        self.save(path, "JPEG")


class MovieMedia(ScratchMedia):
    """unused?"""
    classID = 163
    _fields = ScratchMedia._fields + ("fileName", "fade", "fadeColor", "zoom",
        "hPan", "vPan", "msecsPerFrame", "currentFrame", "moviePlaying")

class Sound(ScratchMedia):
    classID = 164
    _fields = ScratchMedia._fields + ("originalSound", "volume", "balance",
        "compressedSampleRate", "compressedBitsPerSample", "compressedData")




class KeyEventHatMorph(BaseMorph):
    """unused?"""
    classID = 165

class BooleanArgMorph(BaseMorph):
    """unused?"""
    classID = 166

class EventTitleMorph(BaseMorph):
    """unused?"""
    classID = 167

class MouseClickEventHatMorph(BaseMorph):
    """unused?"""
    classID = 168

class ExpressionArgMorphWithMenu(BaseMorph):
    """unused?"""
    classID = 169

class ReporterBlockMorph(BaseMorph):
    """unused?"""
    classID = 170

class MultilineStringMorph(BorderedMorph):
    """Used for costume text."""
    classID = 171
    _fields = BorderedMorph._fields + ("font", "textColor", "selectionColor",
        "lines")

class ToggleButton(SimpleButtonMorph):
    """unused?"""
    classID = 172

class WatcherReadoutFrameMorph(BorderedMorph):
    """unused?"""
    classID = 173

class WatcherSliderMorph(SimpleSliderMorph):
    """unused?"""
    classID = 174

class ScratchListMorph(BorderedMorph):
    """List of items.
    Attributes:
        name - required
        items
    """
    classID = 175
    _fields = BorderedMorph._fields + ("name", "items", "target")
    _version = 2

    def set_defaults(self):
        BorderedMorph.set_defaults(self)

        self.borderColor = Color(594, 582, 582)
        self.borderWidth = 2
        self.bounds = Rectangle([0, 0, 150, 360]) # ?
        self.color = Color(774, 786, 798)

        self.items = []

    def normalize(self):
        """Called before saving"""
        self.items = [unicode(item) for item in self.items]



class ScrollingStringMorph(BaseMorph):
    """unused"""
    classID = 176




