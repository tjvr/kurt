from construct import *
from functools import partial
import inspect

from fixed_objects import *
import fixed_objects
from inline_objects import field, Ref


### DBEUG
class PrintContext(Construct):
    def _parse(self, stream, context):
        print 'parse', context
    
    def _build(self, obj, stream, context):
        print 'build', context
###


class ObjectAdapter(Adapter):
    """Decodes a construct to a pythonic class representation.
    The class must have a from_construct classmethod and a to_construct instancemethod.
    Arguments: a class, list of classes, or a dictionary of obj.classID name to class mapping.
        eg ObjectAdapter({"String": String, "Array": Collection}, <subcon>...)
    NB: Must use new-style objects.
    """
    def __init__(self, classes, *args, **kwargs):
        Adapter.__init__(self, *args, **kwargs)
        
        if isinstance(classes, list):
            classes = dict((cls.__name__, cls) for cls in classes)
        self.classes = classes
    
    def get_class(self, classID):
        if inspect.isclass(self.classes):
            return self.classes
        else:
            return self.classes[classID]
    
    def _encode(self, obj, context):
        return obj.to_construct(context)
    
    def _decode(self, obj, context):
        cls = self.get_class(obj.classID)
        return cls.from_construct(obj, context)


fixed_object_classes = []
fixed_object_ids_by_name = {}
fixed_object_cons_by_name = {}

for name in dir(fixed_objects):
    if not name.startswith('_'):
        cls = getattr(fixed_objects, name)
        classID = getattr(cls, 'classID', None)
        if classID:
            fixed_object_classes.append(cls)
            fixed_object_ids_by_name[name] = classID
            fixed_object_cons_by_name[name] = cls._construct

class FixedObjectAdapter(Adapter):
    def _encode(self, obj, context):
        return obj
    
    def _decode(self, obj, context):
        cls = eval(obj.classID)
        return cls(obj.value)

FixedObjectAdapter = partial(ObjectAdapter, fixed_object_classes)

fixed_object = FixedObjectAdapter(Struct("fixed_object",
    Enum(UBInt8("classID"), **fixed_object_ids_by_name),
    Switch("value", lambda ctx: ctx.classID, fixed_object_cons_by_name),
))



### User-class objects ###

user_object_ids = {
    "Morph": 100,
    "BorderedMorph": 101,
    "RectangleMorph": 102,
    "EllipseMorph": 103,
    "AlignmentMorph": 104,
    "StringMorph": 105,
    "UpdatingStringMorph": 106,
    "SimpleSliderMorph": 107,
    "SimpleButtonMorph": 108,
    "SampledSound": 109,
    "ImageMorph": 110,
    "SketchMorph": 111,
    
    "SensorBoardMorph": 123,
    "ScratchSpriteMorph": 124,
    "ScratchStageMorph": 125,
    
    "ChoiceArgMorph": 140,
    "ColorArgMorph": 141,
    "ExpressionArgMorph": 142,
    "SpriteArgMorph": 145,
    "BlockMorph": 147,
    "CommandBlockMorph": 148,
    "CBlockMorph": 149,
    "HatBlockMorph": 151,
    "ScratchScriptsMorph": 153,
    "ScratchSliderMorph": 154,
    "WatcherMorph": 155,
    "SetterBlockMorph": 157,
    "EventHatMorph": 158,
    "VariableBlockMorph": 160,
    "ImageMedia": 162,
    "MovieMedia": 163,
    "SoundMedia": 164,
    "KeyEventHatMorph": 165,
    "BooleanArgMorph": 166,
    "EventTitleMorph": 167,
    "MouseClickEventHatMorph": 168,
    "ExpressionArgMorphWithMenu": 169,
    "ReporterBlockMorph": 170,
    "MultilineStringMorph": 171,
    "ToggleButton": 172,
    "WatcherReadoutFrameMorph": 173,
    "WatcherSliderMorph": 174,
}


class UserObject(object):
    _fields = []
    
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
    def length(self):
        return len(self)
    
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
        return '<%s(%s)>' % (self.__class__.__name__, getattr(getattr(self, 'objName', ''), 'value', ''))
    
    @property
    def classID(self):
        return self.__class__.__name__
    

class Script(list):
    def __init__(self, array):
        self.pos, blocks = array
        list.__init__(self, blocks)
    
    def __repr__(self):
        return '<Script(%i blocks)>' % len(self)
    
    def to_array(self):
        return [self.pos] + [tuple(block) for block in self.blocks]


class Morph(UserObject):
    _fields = ["bounds", "owner", "submorphs", "color", "flags", "properties"]
class BorderedMorph(Morph): pass
class RectangleMorph(Morph): pass
class EllipseMorph(Morph): pass
class AlignmentMorph(Morph): pass
class StringMorph(Morph): pass
class UpdatingStringMorph(Morph): pass
class SimpleSliderMorph(Morph): pass
class SimpleButtonMorph(Morph): pass
class SampledSound(Morph): pass
class ImageMorph(Morph): pass
class SketchMorph(Morph): pass

class ScriptableScratchMorph(Morph):
    _fields = Morph._fields + ["objName", "vars", "blocksBin", "isClone", "media", "costume"]

class SensorBoardMorph(Morph): pass
class ScratchSpriteMorph(ScriptableScratchMorph):
    _fields = ScriptableScratchMorph._fields + ["zoom", "hPan", "vPan", "obsoleteSavedState", "sprites", "volume", "tempoBPM", "sceneStates", "lists"]
class ScratchStageMorph(ScriptableScratchMorph):
    _fields = ScriptableScratchMorph._fields + ["visibility", "scalePoint", "rotationDegrees", "rotationStyle", "volume", "tempoBPM", "draggable", "sceneStates", "lists"]

class ChoiceArgMorph(Morph): pass
class ColorArgMorph(Morph): pass
class ExpressionArgMorph(Morph): pass
class SpriteArgMorph(Morph): pass
class BlockMorph(Morph): pass
class CommandBlockMorph(Morph): pass
class CBlockMorph(Morph): pass
class HatBlockMorph(Morph): pass
class ScratchScriptsMorph(Morph):
    _fields = Morph._fields + ["borderWidth", "borderColor"]
class ScratchSliderMorph(Morph): pass
class WatcherMorph(Morph): pass
class SetterBlockMorph(Morph): pass
class EventHatMorph(Morph): pass
class VariableBlockMorph(Morph): pass
class ImageMedia(Morph):
    _fields = ["mediaName", "form", "rotationCenter", "textBox", "jpegBytes", "compositeForm"]
class MovieMedia(Morph): pass
class SoundMedia(Morph):
    _fields = ["mediaName", "originalSound", "volume", "balance", "compressedSampleRate", "compressedBitsPerSample", "compressedData"]
class KeyEventHatMorph(Morph): pass
class BooleanArgMorph(Morph): pass
class EventTitleMorph(Morph): pass
class MouseClickEventHatMorph(Morph): pass
class ExpressionArgMorphWithMenu(Morph): pass
class ReporterBlockMorph(Morph): pass
class MultilineStringMorph(Morph): pass
class ToggleButton(Morph): pass
class WatcherReadoutFrameMorph(Morph): pass
class WatcherSliderMorph(Morph): pass
    

class UserObjectAdapter(Adapter):
    def _encode(self, obj, context):
        return obj #Container(classID = obj.__class__.__name__, fields = obj.fields)
    
    def _decode(self, obj, context):
        cls = eval(obj.classID)
        return cls(obj.field_values, version=obj.version)


user_object = UserObjectAdapter(Struct("user_object",
    Enum(UBInt8("classID"),
        **user_object_ids
    ),
    UBInt8("version"),
    UBInt8("length"),
    Rename("field_values", MetaRepeater(lambda ctx: ctx.length, field)),
))



### Objects ###

class ObjectAdapter(Adapter):
    def _encode(self, obj, context):
        classID = obj.classID
        if classID in fixed_object_ids:
            classID = fixed_object_ids[classID]
        elif classID in user_object_ids:
            classID = user_object_ids[classID]
        return Container(
            classID = classID,
            object = obj,
        )
    
    def _decode(self, obj, context):
        return obj.object

an_obj = ObjectAdapter(Struct("object",
    Peek(UBInt8("classID")),
    IfThenElse("object", lambda ctx: ctx.classID < 99,
        fixed_object,
        user_object,
    ),
))

objt = None

class ObjectTableAdapter(Adapter):
    """Object network <--> binary object table."""
    def _encode(self, root, context):
        def get_ref(value):            
            """Returns the index of the given object in the object table, adding it if needed."""
            objects = self._objects
            if isinstance(value, UserObject) or isinstance(value, FixedObject): # or isinstance(obj, ContainsRefs):
                # must handle both back and forward refs.
                proc_objects = [getattr(obj, '_made_from', None) for obj in objects]
                
                if value in objects:
                    index = objects.index(value) + 1 # first entry's index is 1
                elif value in proc_objects:
                    index = proc_objects.index(value) + 1
                else:
                    objects.append(value)
                    index = len(objects)
                
                return Ref(index)
            else:
                # Inline value
                return value
        
        def fix_fields(obj):
            if isinstance(obj, UserObject):
                #for field_name in dict(obj.ordered_fields):
                #    value = obj.fields[field_name]
                #    value = get_ref(value)
                #    obj.fields[field_name] = value
                field_values = [get_ref(value) for value in obj.field_values]
                fixed_obj = obj.__class__(field_values, version = obj.version)
            elif isinstance(obj, Form):
                fixed_obj = obj.__class__(Container(**dict([(field, get_ref(value)) for (field, value) in obj.value])))
                #obj.value = [(field, get_ref(value)) for (field, value) in obj.value]
            elif isinstance(obj, ContainsRefs):
                fixed_obj = obj.__class__([get_ref(field) for field in obj.value])
                #obj.value = [get_ref(field) for field in obj.value]
            else:
                return obj
            
            fixed_obj._made_from = obj
            return fixed_obj
        
        i = 0
        self._objects = objects = [root]
        while i < len(objects):
            objects[i] = fix_fields(objects[i])
            i += 1
        
        return Container(
            header = "ObjS\x01Stch\x01",
            length = len(objects),
            objects = objects,
        )
    
    def _decode(self, table, context):
        assert table.length == len(table.objects) # DEBUG
        objects = table.objects
        
        def resolve_ref(obj, objects=objects):
            if isinstance(obj, Ref):
                # first entry is 1
                return objects[obj.index - 1]
            else:
                return obj
        
        for obj in objects:
            if isinstance(obj, UserObject):
                for field_name in obj.fields:
                    value = obj.fields[field_name]
                    value = resolve_ref(value)
                    obj.fields[field_name] = value
            elif isinstance(obj, Form):
                obj.value = [(field, resolve_ref(value)) for (field, value) in obj.value]
            elif isinstance(obj, ContainsRefs):
                obj.value = [resolve_ref(field) for field in obj.value]
        
        root = objects[0]
        return root

obj_table = ObjectTableAdapter(Struct("object_table",
    Const(Bytes("header", 10), "ObjS\x01Stch\x01"),
    UBInt32("length"),
    Rename("objects", MetaRepeater(lambda ctx: ctx.length, an_obj)),
))



### Test ###

stage_bin = '\x7D\x05\x15\x63\x00\x00\x02\x01\x63\x00\x00\x03\x63\x00\x00\x04\x05\x00\x00\x01\x63\x00\x00\x05\x63\x00\x00\x06\x63\x00\x00\x07\x03\x63\x00\x00\x08\x01\x08\x3F\xF0\x00\x00\x00\x00\x00\x00\x05\x00\x00\x05\x00\x00\x01\x63\x00\x00\x09\x05\x00\x64\x05\x00\x3C\x63\x00\x00\x0A\x63\x00\x00\x0B'
stage = user_object.parse(stage_bin)

file = open('/Users/tim/Code/Scratch format/Blank-musical.sprite').read()
#ot = obj_table.parse(file)



