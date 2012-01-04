from construct import Container

class UserObject(object):
    _fields = []
    
    def to_construct(self, context):
        return Container(
            classID = self.__class__.__name__,
            field_values = self.field_values,
            length = len(self.fields),
            version = self.version,
        )
    
    @classmethod
    def from_construct(cls, obj, context):
        return cls(obj.field_values, version=obj.version)
    
    def __init__(self, field_values=None, **args):
        self.fields = {}
        
        self.version = 1
        if 'version' in args:
            self.version = args.pop('version')
        
        if field_values:
            defined_fields = self._fields[:]
            defined_fields += ("undefined%i" % i for i in range(len(defined_fields), len(field_values)))
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
        for field_name, value in sorted(fields.items()):
            ordered_fields.append((field_name, value))
             
        return ordered_fields
    
    @property
    def field_values(self):
        return [value for (field_name, value) in self.ordered_fields]
    
    def __repr__(self):
        objName = getattr(getattr(self, 'objName', ''), 'value', '')
        return '<%s(%s)>' % (self.__class__.__name__, objName)
    

class Script(list):
    def __init__(self, array):
        self.pos, blocks = array
        list.__init__(self, blocks)
    
    def __repr__(self):
        return '<Script(%i blocks)>' % len(self)
    
    def to_array(self):
        return [self.pos] + [tuple(block) for block in self.blocks]


class Morph(UserObject):
    classID = 100
    _fields = ["bounds", "owner", "submorphs", "color", "flags", "properties"]
class BorderedMorph(Morph):
    classID = 101
    _fields = Morph._fields + ["borderWidth", "borderColor"]
class RectangleMorph(Morph):
    classID = 102
class EllipseMorph(Morph):
    classID = 103
class AlignmentMorph(Morph):
    classID = 104
class StringMorph(Morph):
    classID = 105
class UpdatingStringMorph(Morph):
    classID = 106
class SimpleSliderMorph(Morph):
    classID = 107
class SimpleButtonMorph(Morph):
    classID = 108
class SampledSound(Morph):
    classID = 109
class ImageMorph(Morph):
    classID = 110
class SketchMorph(Morph):
    classID = 111


class ScriptableScratchMorph(Morph):
    _fields = Morph._fields + ["objName", "vars", "blocksBin", "isClone", "media", "costume"]

class SensorBoardMorph(Morph):
    classID = 123
class ScratchSpriteMorph(ScriptableScratchMorph):
    classID = 124
    _fields = ScriptableScratchMorph._fields + ["zoom", "hPan", "vPan", "obsoleteSavedState", "sprites", "volume", "tempoBPM", "sceneStates", "lists"]
class ScratchStageMorph(ScriptableScratchMorph):
    classID = 125
    _fields = ScriptableScratchMorph._fields + ["visibility", "scalePoint", "rotationDegrees", "rotationStyle", "volume", "tempoBPM", "draggable", "sceneStates", "lists"]

class ChoiceArgMorph(Morph):
    classID = 140
class ColorArgMorph(Morph):
    classID = 141
class ExpressionArgMorph(Morph):
    classID = 142
class SpriteArgMorph(Morph):
    classID = 145
class BlockMorph(Morph):
    classID = 147
class CommandBlockMorph(Morph):
    classID = 148
class CBlockMorph(Morph):
    classID = 149
class HatBlockMorph(Morph):
    classID = 151
class ScratchScriptsMorph(BorderedMorph):
    classID = 153
class ScratchSliderMorph(Morph):
    classID = 154
class WatcherMorph(Morph):
    classID = 155
class SetterBlockMorph(Morph):
    classID = 157
class EventHatMorph(Morph):
    classID = 158
class VariableBlockMorph(Morph):
    classID = 160
class ImageMedia(Morph):
    classID = 162
    _fields = ["mediaName", "form", "rotationCenter", "textBox", "jpegBytes", "compositeForm"]
class MovieMedia(Morph):
    classID = 163
class SoundMedia(Morph):
    classID = 164
    _fields = ["mediaName", "originalSound", "volume", "balance", "compressedSampleRate", "compressedBitsPerSample", "compressedData"]
class KeyEventHatMorph(Morph):
    classID = 165
class BooleanArgMorph(Morph):
    classID = 166
class EventTitleMorph(Morph):
    classID = 167
class MouseClickEventHatMorph(Morph):
    classID = 168
class ExpressionArgMorphWithMenu(Morph):
    classID = 169
class ReporterBlockMorph(Morph):
    classID = 170
class MultilineStringMorph(Morph):
    classID = 171
class ToggleButton(Morph):
    classID = 172
class WatcherReadoutFrameMorph(Morph):
    classID = 173
class WatcherSliderMorph(Morph):
    classID = 174
