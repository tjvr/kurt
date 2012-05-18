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

from fixed_objects import OrderedCollection



class UserObject(object):
    """A user-class object with a variable number of fields.
    Supports dot notation for accessing fields. 
    Use .fields.keys() to see available fields [dir() won't show them.]
    
    Each class lists its field order in _fields. 
    Unknown fields not in this list are named "undefined-%i", where i is the field index.
    """
    _fields = []
    
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
        
        self.version = 1
        if 'version' in args:
            self.version = args.pop('version')
        
        if field_values:
            defined_fields = self._fields[:]
            defined_fields += tuple("undefined-%i" % i for i in range(len(defined_fields), len(field_values)))
            self.fields.update(zip(defined_fields, field_values))
        
        self.fields.update(args)
    
    def __getattr__(self, name):
        if name in self.fields:
            return self.fields[name]
        else:
            raise AttributeError, '%s instance has no attribute %s' % (self.__class__.__name__, name)
            
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
        fields = sorted(fields.items(), key=lambda (field,value): int(field.split('-')[1]))
        for field_name, value in fields:
            ordered_fields.append((field_name, value))
             
        return ordered_fields
    
    @property
    def field_values(self):
        return [value for (field_name, value) in self.ordered_fields]
    
    @property
    def name(self):
        return getattr(self, "objName")
    
    @name.setter
    def name(self, value):
        setattr(self, "objName", value)
    
    def __repr__(self):
        name = getattr(self, "name", "")
        return "<%s(%s)>" % (self.__class__.__name__, name)
    


### Squeak & Morphic classes ###
class BaseMorph(UserObject):
    _fields = ("bounds", "owner", "submorphs", "color", "flags", "properties")

class Morph(BaseMorph):
    """Base class for most UserObjects."""
    classID = 100

class BorderedMorph(BaseMorph):
    classID = 101
    _fields = Morph._fields + ("borderWidth", "borderColor")

class RectangleMorph(BorderedMorph):
    classID = 102

class EllipseMorph(BorderedMorph):
    classID = 103

class AlignmentMorph(RectangleMorph):
    classID = 104
    _fields = RectangleMorph._fields + ("orientation", "centering", "hResizing", "vResizing", "inset") 

class StringMorph(BaseMorph):
    classID = 105
    _fields = Morph._fields + ("font_with_size", "emphasis", "contents")

class UpdatingStringMorph(StringMorph):
    classID = 106

class SimpleSliderMorph(BorderedMorph):
    classID = 107
    _fields = BorderedMorph._fields + ("slider", "value", "setValueSelector", "sliderShadow", "sliderColor", "descending", "model", "target", "actionSelector", "arguments", "actWhen")

class SimpleButtonMorph(RectangleMorph):
    classID = 108
    _fields = RectangleMorph._fields + ("target", "actionSelector", "arguments", "actWhen")

class SampledSound(UserObject):
    classID = 109
    _fields = ("envelopes", "scaledVol", "initialCount", "samples", "originalSamplingRate", "samplesSize", "scaledIncrement", "scaledInitialIndex")

class ImageMorph(BaseMorph):
    classID = 110
    _fields = Morph._fields + ("form", "transparency")

class SketchMorph(BaseMorph):
    classID = 111
    _fields = Morph._fields + ("originalForm", "rotationCenter", "rotationDegrees", "rotationStyle", "scalePoint", "offsetWhenRotated")




### Scratch-specific classes ###

class ScriptableScratchMorph(BaseMorph):
    _fields = Morph._fields + ("objName", "vars", "blocksBin", "isClone", "media", "costume")
    
    def __init__(self, *args, **kwargs):
        UserObject.__init__(self, *args, **kwargs)
        
        self.images = []
        self.sounds = []
    
    def built(self):
        UserObject.built(self)
        self.blocksBin = [Script.from_array(self, script) for script in self.blocksBin]
        
        media = self.media
        self.media = []
        for media in media:
            if isinstance(media, SoundMedia):
                self.sounds.append(media)
            elif isinstance(media, ImageMedia):
                self.images.append(media)
            else:
                self.media.append(media)
    
    def _encode_field(self, name, value):
        if name == 'blocksBin':
            return [script.to_array() for script in value]
        elif name == 'media':
            return OrderedCollection(self.sounds + self.images + self.media)
        else:
            return value

    @property
    def scripts(self):
        """Alias for blocksBin."""
        return self.blocksBin
    
    @scripts.setter
    def scripts(self, value):
        """Alias for blocksBin."""
        self.blocksBin = value



class SensorBoardMorph(BaseMorph):
    classID = 123
    _fields = BaseMorph._fields + ("unknown",) # TODO — I have NO idea what this does.


class ScratchSpriteMorph(ScriptableScratchMorph):
    """A sprite.
    Main attributes:
        scripts
        vars
        lists
        costumes
        sounds
    Use .fields.keys() to see all available fields.
    """
    classID = 124
    _fields = ScriptableScratchMorph._fields + ("visibility", "scalePoint", "rotationDegrees", "rotationStyle", "volume", "tempoBPM", "draggable", "sceneStates", "lists")
    
    @property
    def costumes(self):
        return self.images
        
    @costumes.setter
    def costumes(self, value):
        self.images = value


class ScratchStageMorph(ScriptableScratchMorph):
    """The project stage. Also contains project contents, including sprites and media.
    Main attributes:
        sprites - ordered list of sprites.
        submorphs - everything on the stage, including sprites & variable/list watchers.
        scripts
        vars
        lists
        backgrounds
        sounds
    Use .fields.keys() to see all available fields.
    """
    classID = 125
    _fields = ScriptableScratchMorph._fields + ("zoom", "hPan", "vPan", "obsoleteSavedState", "sprites", "volume", "tempoBPM", "sceneStates", "lists")
    
    @property
    def backgrounds(self):
        return self.images
    
    @backgrounds.setter
    def backgrounds(self, value):
        self.images = value


from scripts import Script
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
    _fields = BlockMorph._fields + ("commandSpec", "argMorphs", "titleMorph", "receiver", "selector", "isReporter", "isTimed", "wantsName", "wantsPossession")

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
    _fields = AlignmentMorph._fields + ("titleMorph", "readout", "readoutFrame", "scratchSlider", "watcher", "isSpriteSpecific", "unused", "sliderMin", "sliderMax", "isLarge")
    
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
    _fields = ("mediaName",)
    
    @property
    def name(self):
        return getattr(self, "mediaName")
    
    @name.setter
    def name(self, value):
        setattr(self, "mediaName", value)


class ImageMedia(ScratchMedia):
    """An image file, used for costumes and backgrounds.
    Methods:
        save(path) — save the image to an external file.
    
    Image data is stored internally on the "form" attribute.
    """
    classID = 162
    _fields = ScratchMedia._fields + ("form", "rotationCenter", "textBox", "jpegBytes", "compositeForm")
    
    def __getattr__(self, name):
        value = ScratchMedia.__getattr__(self, name)
        if value: 
            return value
        
        if name in ("width", "height"):
            return getattr(self.form, name)
    
    def save(self, path, format=None):
        """Save the image data to an external file.
        Arguments:
            path - the absolute or relative path to save to. Does not require extension.
            format - the extension to save as, "png" or "jpg". May throw an error if 
                     image format is different.
        """
        (folder, name) = os.path.split(path)
        if not format and "." in name:
            format = name.split('.')[-1]
        
        if not format:
            if self.jpegBytes:
                format = "jpg"
            else:
                format = "png"
            
        try:
            format = format.lstrip(".")
            save_func = getattr(self, "save_%s"%format)
            assert callable(save_func)
        except (AssertionError, AttributeError):
            raise ValueError, "Invalid format %r" % format
        
        save_func(path)
    
    def save_png(self, path):
        self.form.save_png(path)    
        
    def save_jpg(self, path):
        if not self.jpegBytes:
            raise ValueError, "ImageMedia object %r is not in JPEG format"
        
        if not path.endswith(".jpg"): path += ".jpg"
        
        f = open(path, "w")
        f.write(self.jpegBytes.value)
        f.flush()
        f.close()


class MovieMedia(ScratchMedia):
    """unused?"""
    classID = 163
    _fields = ScratchMedia._fields + ("fileName", "fade", "fadeColor", "zoom", "hPan", "vPan", "msecsPerFrame", "currentFrame", "moviePlaying")

class SoundMedia(ScratchMedia):
    classID = 164
    _fields = ScratchMedia._fields + ("originalSound", "volume", "balance", "compressedSampleRate", "compressedBitsPerSample", "compressedData")




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
    _fields = BorderedMorph._fields + ("font", "textColor", "selectionColor", "lines")

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
        items - (alias for cellMorphs)
    """
    classID = 175
    _fields = BorderedMorph._fields + ("listName", "cellMorphs", "target")
	#cellMorphs asArray collect: [:t3 | t3 firstSubmorph contents].
	
    @property
    def name(self):
        return getattr(self, "listName")
    
    @name.setter
    def name(self, value):
        setattr(self, "listName", value)
    
    @property
    def items(self):
        return self.cellMorphs



class ScrollingStringMorph(BaseMorph):
    """unused"""
    classID = 176




