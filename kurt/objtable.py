from construct import *


### DBEUG
class PrintContext(Construct):
    def _parse(self, stream, context):
        print 'parse', context
    
    def _build(self, obj, stream, context):
        print 'build', context



### Inline fields & References ###

class Ref(object):
    def __init__(self, index):
        self.index = int(index)
    
    def __repr__(self):
        return 'Ref(%i)' % self.index
    
    def __eq__(self, other):
        return isinstance(other, Ref) and self.index == other.index
    
    def __ne__(self, other):
        return not self == other


class RefAdapter(Adapter):
    def _encode(self, obj, context):
        assert isinstance(obj, Ref)
        index1 = obj.index % 65536
        index2 = (obj.index - index1) >> 16
        return Container(classID = 'Ref', _index1=index1, _index2=index2)
        
    def _decode(self, obj, context):
        index = int(obj._index2 << 16) + obj._index1
        return Ref(index)


class FieldAdapter(Adapter):
    def _encode(self, obj, context):
        assert not isinstance(obj, str)
        
        if obj is None:
            classID = 'nil'
        elif obj is True:
            classID = 'true'
        elif obj is False:
            classID = 'false'
        elif isinstance(obj, float):
            classID = 'Float'
        elif isinstance(obj, Ref):
            classID = 'Ref'
        elif isinstance(obj, int):
            # for now, assume SmallInteger
            if obj < 65536:
                classID = 'SmallInteger16'
            else:
                classID = 'SmallInteger'
        else:
            raise NotImplementedError, 'no field type for %r' % obj
        return Container(classID=classID, value=obj)
    
    def _decode(self, obj, context):
        if isinstance(obj, Ref):
            return obj
        else:
            return obj.value


field = FieldAdapter(Struct("field",
    Enum(UBInt8("classID"),
        nil = 1,
        true = 2,
        false = 3,
        SmallInteger = 4,
        SmallInteger16 = 5,
        LargePositiveInteger = 6,
        LargeNegativeInteger = 7,
        Float = 8,
        Ref = 99,
    ),
    Switch("value", lambda ctx: ctx.classID, {
        "nil": Value("", lambda ctx: None),
        "true": Value("", lambda ctx: True),
        "false": Value("", lambda ctx: False),
        "SmallInteger": UBInt32(""),
        "SmallInteger16": UBInt16(""),
        "LargePositiveInteger": Struct("",
            UBInt16("length"),
            MetaRepeater(lambda ctx: ctx.length, UBInt8("data")),
        ),
        "LargeNegativeInteger": Struct("",
            UBInt16("length"),
            MetaRepeater(lambda ctx: ctx.length, UBInt8("data")),
        ),
        "Float": BFloat64(""),
        "Ref": RefAdapter(Struct("",
            UBInt8("_index2"),
            UBInt16("_index1"),
        )),
    })
))



### Fixed-format objects ###

class FixedObject:
    def __init__(self, value):
        self.value = value
    
    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.value == other.value
    
    def __ne__(self, other):
        return not self == other
    
    def __str__(self):
        return repr(self)
    
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.value))
        
    @property
    def classID(self):
        return self.__class__.__name__


class ContainsRefs: pass
    
class String(FixedObject): pass
class Symbol(FixedObject):
    def __repr__(self):
        return "<#%s>" % self.value

class ByteArray(FixedObject): pass
class SoundBuffer(FixedObject): pass
class Bitmap(FixedObject): pass
class UTF8(FixedObject): pass

class Collection(FixedObject, ContainsRefs):
    def __iter__(self):
        return iter(self.value)
    
    def __getattr__(self, name):
        if name in ('append', 'count', 'extend', 'index', 'insert', 'pop', 'remove', 'reverse', 'sort'):
            return getattr(self.value, name)
    
    def __getitem__(self, index):
        return self.value[index]
    
    def __setitem__(self, index, value):
        self.value[index] = value
    
    def __delitem__(self, index):
        del self.value[index]

class Array(Collection): pass
class OrderedCollection(Collection): pass
class Set(Collection): pass
class IdentitySet(Collection): pass

class Dictionary(Collection): pass
class IdentityDictionary(Collection): pass

class Color(FixedObject): pass
class TranslucentColor(FixedObject): pass
class Point(FixedObject): pass
class Rectangle(FixedObject): pass
class Form(FixedObject, ContainsRefs): pass
class ColorForm(FixedObject, ContainsRefs, Form): pass


class FixedObjectAdapter(Adapter):    
    def _encode(self, obj, context):
        return obj
    
    def _decode(self, obj, context):
        cls = eval(obj.classID)
        return cls(obj.value)


# Tuples
class TupleAdapter(Adapter):
    def __init__(self, fields, subcon):
        Adapter.__init__(self, subcon)
        self.fields = fields
    
    def _encode(self, obj, context):
        return Container(**dict(zip(self.fields, obj)))
    
    def _decode(self, obj, context):
        return tuple(obj[field] for field in self.fields)

# Collection
class CollectionAdapter(Adapter):
    def _encode(self, obj, context):
        obj = list(obj)
        return Container(items=obj, length=len(obj))
    
    def _decode(self, obj, context):
        assert len(obj.items) == obj.length # DEBUG
        return obj.items

_collection = CollectionAdapter(Struct("collection",
    UBInt32("length"),
    MetaRepeater(lambda ctx: ctx.length, Rename("items", field)),
))

# Dictionary
class DictionaryAdapter(Adapter):
    def _encode(self, obj, context):
        return [Container(key=key, value=value) for (key, value) in dict(obj).items()]
    
    def _decode(self, obj, context):
        return dict([(item.key, item.value) for item in obj])

_dictionary = DictionaryAdapter(CollectionAdapter(Struct("dictionary",
    UBInt32("length"),
    MetaRepeater(lambda ctx: ctx.length, Struct("items",
        Rename("key", field),
        Rename("value", field),
    )),
)))

# Form
_form = Struct("form",
    Rename("width", field),
    Rename("height", field),
    Rename("depth", field),
    Rename("privateOffset", field),
    Rename("bits", field),
)


fixed_object_ids = {
    "String": 9,
    "Symbol": 10,
    "ByteArray": 11,
    "SoundBuffer": 12,
    "Bitmap": 13,
    "UTF8": 14,
    
    "Array": 20,
    "OrderedCollection": 21,
    "Set": 22,
    "IdentitySet": 23,
    "Dictionary": 24,
    "IdentityDictionary": 25,
    
    "Color": 30,
    "TranslucentColor": 31,
    "Point": 32,
    "Rectangle": 33,
    "Form": 34,
    "ColorForm": 35,
}

fixed_object = FixedObjectAdapter(Struct("fixed_object",
    Enum(UBInt8("classID"),
        **fixed_object_ids
    ),
    Switch("value", lambda ctx: ctx.classID, {
        "String": PascalString("value", length_field=UBInt32("length")),
        "Symbol": PascalString("value", length_field=UBInt32("length")),
        "ByteArray": PascalString("value", length_field=UBInt32("length")),
        "SoundBuffer": Struct("",
            UBInt32("length"),
            MetaRepeater(lambda ctx: ctx.length * 2, UBInt8("bytes")),
        ),
        "Bitmap": Struct("",
            UBInt32("length"),
            MetaRepeater(lambda ctx: ctx.length, UBInt32("")),
        ),
        "UTF8": PascalString("value", length_field=UBInt32("length"), encoding="utf8"),
        
        "Array": _collection,
        "OrderedCollection": _collection,
        "Set": _collection,
        "IdentitySet": _collection,
        
        "Dictionary": _dictionary,
        "IdentityDictionary": _dictionary,
        
        "Color": UBInt32("value"),
        "TranslucentColor": Struct("", UBInt32("color"), UBInt8("more_color")),
        "Point": TupleAdapter(('x', 'y'), Struct("",
            Rename("x", field),
            Rename("y", field),
        )),
        "Rectangle": StrictRepeater(4, field),
        "Form": _form,
        "ColorForm": Struct("",
            Embed(_form),
            Rename("colors", field),
        ),
    }),
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
ot = obj_table.parse(file)



