from construct import *
from construct import Array as MetaRepeater
# We can't import the name Array, as we use it. -_-


### inline fields & Refs ###

class Ref(object):
    """A reference to an object located in a serialized object table.
    Used internally for parsing obj_tables.
    Allows for complex interlinked object networks to be serialized to a list of objects.
    Found in UserObjects and certain FixedObjects.
    """
    def __init__(self, index):
        """Initialise a reference.
        @param index: the index in the object table that the reference points to.
        Note that the first index is 1.
        """
        self.index = int(index)
    
    @classmethod
    def to_construct(self, context):
        index1 = self.index % 65536
        index2 = (self.index - index1) >> 16
        return Container(classID = 'Ref', _index1 = index1, _index2 = index2)
    
    @classmethod
    def from_construct(cls, obj, context):
        index = int(obj._index2 << 16) + obj._index1
        return Ref(index)
    
    def __repr__(self):
        return 'Ref(%i)' % self.index
    
    def __eq__(self, other):
        return isinstance(other, Ref) and self.index == other.index
    
    def __ne__(self, other):
        return not self == other
    
    def __hash__(self):
        return hash(self.index)


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


Field = FieldAdapter(Struct("field",
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
        "SmallInteger": SBInt32(""),
        "SmallInteger16": SBInt16(""),
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
Field.__doc__ = """Construct for simple inline field values and references.
Converts pythonic types - eg None, True, int - to binary data.
Encoded inline and not stored directly in an object table. Do not contain references.
"""



