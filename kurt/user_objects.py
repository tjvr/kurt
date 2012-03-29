#coding=utf8
from construct import Container

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
        self.fields = {}
        
        self.version = 1
        if 'version' in args:
            self.version = args.pop('version')
        
        if field_values:
            defined_fields = self._fields[:]
            defined_fields += ("undefined-%i" % i for i in range(len(defined_fields), len(field_values)))
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
    
    def __repr__(self):
        objName = getattr(self, 'objName', '')
        return '<%s(%s)>' % (self.__class__.__name__, objName)
    



class BaseMorph(UserObject):
    _fields = ["bounds", "owner", "submorphs", "color", "flags", "properties"]

class Morph(BaseMorph):
    """Base class for most UserObjects."""
    classID = 100
class BorderedMorph(BaseMorph):
    classID = 101
    _fields = Morph._fields + ["borderWidth", "borderColor"]
class RectangleMorph(BaseMorph):
    classID = 102
class EllipseMorph(BaseMorph):
    classID = 103
class AlignmentMorph(BaseMorph):
    classID = 104
class StringMorph(BaseMorph):
    classID = 105
class UpdatingStringMorph(BaseMorph):
    classID = 106
class SimpleSliderMorph(BaseMorph):
    classID = 107
class SimpleButtonMorph(BaseMorph):
    classID = 108
class SampledSound(BaseMorph):
    classID = 109
class ImageMorph(BaseMorph):
    classID = 110
class SketchMorph(BaseMorph):
    classID = 111



from scripts import Script



class ScriptableScratchMorph(BaseMorph):
    _fields = Morph._fields + ["objName", "vars", "blocksBin", "isClone", "media", "costume"]
    
    def _encode_field(self, name, value):
        """Return a list of field values that should be saved.
        Override this in subclass to modify building of specific fields.
        """
        if name == 'blocksBin':
            return [script.to_array() for script in value]
        else:
            return value

    def _decode_field(cls, name, value):
        """Return list of field values passed to object's constructor.
        Override this in subclass to modify specific fields.
        """
        if name == 'blocksBin':
            return [Script.from_array(script) for script in value]
        else:
            return value
    #def _decode_field(cls, name, value):
    #    """Return list of field values passed to object's constructor.
    #    Override this in subclass to modify specific fields.
    #    """
    #    if name == 'blocksBin':

    @property
    def scripts(self):
        """Alias for blocksBin."""
        return self.blocksBin


class SensorBoardMorph(BaseMorph):
    classID = 123

class ScratchSpriteMorph(ScriptableScratchMorph):
    classID = 124
    _fields = ScriptableScratchMorph._fields + ["zoom", "hPan", "vPan", "obsoleteSavedState", "sprites", "volume", "tempoBPM", "sceneStates", "lists"]

class ScratchStageMorph(ScriptableScratchMorph):
    """The project stage. Also contains project contents, including sprites and media.
    Attributes include .sprites, an alias for submorphs.
    Use .fields.keys() to see all available fields.
    """
    classID = 125
    _fields = ScriptableScratchMorph._fields + ["visibility", "scalePoint", "rotationDegrees", "rotationStyle", "volume", "tempoBPM", "draggable", "sceneStates", "lists"]
    
    @property
    def sprites(self):
        """Alias for submorphs."""
        return self.submorphs
    


from scripts import Script # Yes, this is stupid. Circular dependencies ftw. -_-


class ChoiceArgMorph(BaseMorph):
    classID = 140
class ColorArgMorph(BaseMorph):
    classID = 141
class ExpressionArgMorph(BaseMorph):
    classID = 142
class SpriteArgMorph(BaseMorph):
    classID = 145
class BlockMorph(BaseMorph):
    classID = 147
class CommandBlockMorph(BaseMorph):
    classID = 148
class CBlockMorph(BaseMorph):
    classID = 149
class HatBlockMorph(BaseMorph):
    classID = 151
class ScratchScriptsMorph(BorderedMorph):
    classID = 153
class ScratchSliderMorph(BaseMorph):
    classID = 154
class WatcherMorph(BaseMorph):
    classID = 155
class SetterBlockMorph(BaseMorph):
    classID = 157
class EventHatMorph(BaseMorph):
    classID = 158
class VariableBlockMorph(BaseMorph):
    classID = 160
class ImageMedia(BaseMorph):
    classID = 162
    _fields = ["mediaName", "form", "rotationCenter", "textBox", "jpegBytes", "compositeForm"]
class MovieMedia(BaseMorph):
    classID = 163
class SoundMedia(BaseMorph):
    classID = 164
    _fields = ["mediaName", "originalSound", "volume", "balance", "compressedSampleRate", "compressedBitsPerSample", "compressedData"]
class KeyEventHatMorph(BaseMorph):
    classID = 165
class BooleanArgMorph(BaseMorph):
    classID = 166
class EventTitleMorph(BaseMorph):
    classID = 167
class MouseClickEventHatMorph(BaseMorph):
    classID = 168
class ExpressionArgMorphWithMenu(BaseMorph):
    classID = 169
class ReporterBlockMorph(BaseMorph):
    classID = 170
class MultilineStringMorph(BaseMorph):
    classID = 171
class ToggleButton(BaseMorph):
    classID = 172
class WatcherReadoutFrameMorph(BaseMorph):
    classID = 173
class WatcherSliderMorph(BaseMorph):
    classID = 174
class WatcherSliderMorph(BorderedMorph):
    classID = 175
class ScrollingStringMorph(BaseMorph):
    """unused"""
    classID = 176
