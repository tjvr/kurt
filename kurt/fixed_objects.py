from construct import Container, Struct, Embed, Rename
from construct import PascalString, UBInt32, UBInt8
from construct import MetaRepeater, StrictRepeater

from inline_objects import field



class FixedObject(object):
    def __init__(self, value):
        self.value = value
    
    def to_construct(self, context):
        return Container(classID = self.__class__.__name__, value = self.to_value())
    
    @classmethod
    def from_construct(cls, obj, context):
        return cls.from_value(obj.value)
    
    def to_value(self):
        return self.value
    
    @classmethod
    def from_value(cls, value):
        return cls(value)
    
    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.value == other.value
    
    def __ne__(self, other):
        return not self == other
    
    def __str__(self):
        return repr(self)
    
    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.value))


class ContainsRefs: pass

class FixedObjectWithRepeater(FixedObject):
    """Used internally to handle things like
        Struct("",
            UBInt32("length"),
            MetaRepeater(lambda ctx: ctx.length, UBInt32("items")),
        )
    """
    def to_value(self):
        return Container(items = self.value, length = len(self.value))
    
    @classmethod
    def from_value(cls, obj):
        assert len(obj.items) == obj.length # DEBUG
        return cls(obj.items)



# Bytes
class String(FixedObject):
    classID = 9
    _construct = PascalString("value", length_field=UBInt32("length"))


class Symbol(FixedObject):
    classID = 10
    _construct = PascalString("value", length_field=UBInt32("length"))
    def __repr__(self):
        return "<#%s>" % self.value


class ByteArray(FixedObject):
    classID = 11
    _construct = PascalString("value", length_field=UBInt32("length"))


class SoundBuffer(FixedObjectWithRepeater):
    classID = 12
    _construct = Struct("",
        UBInt32("length"),
        MetaRepeater(lambda ctx: ctx.length * 2, UBInt8("items")),
    )

class Bitmap(FixedObjectWithRepeater):
    classID = 13
    _construct = Struct("",
        UBInt32("length"),
        MetaRepeater(lambda ctx: ctx.length, UBInt32("items")),
    )

class UTF8(FixedObject):
    classID = 14
    _construct = PascalString("value", length_field=UBInt32("length"), encoding="utf8")


# Collections
class Collection(FixedObjectWithRepeater, ContainsRefs):
    _construct = Struct("",
        UBInt32("length"),
        MetaRepeater(lambda ctx: ctx.length, Rename("items", field)),
    )
    
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

class Array(Collection):
    classID = 20
class OrderedCollection(Collection):
    classID = 21
class Set(Collection):
    classID = 22
class IdentitySet(Collection):
    classID = 23


# Dictionary
class Dictionary(Collection):
    classID = 24
    _construct = Struct("dictionary",
        UBInt32("length"),
        MetaRepeater(lambda ctx: ctx.length, Struct("items",
            Rename("key", field),
            Rename("value", field),
        )),
    )
    
    def to_value(self):
        items = [Container(key=key, value=value) for (key, value) in dict(self.value).items()]
        return Container(items=items, length=len(items))
    
    @classmethod
    def from_value(cls, obj):
        value = dict([(item.key, item.value) for item in obj.items])
        return cls(value)

class IdentityDictionary(Dictionary):
    classID = 25


# Color
class Color(FixedObject):
    classID = 30
    _construct = UBInt32("value")

class TranslucentColor(FixedObject):
    classID = 31
    _construct = Struct("", UBInt32("color"), UBInt8("more_color"))


# Dimensions
class Point(FixedObject):  
    classID = 32
    _construct = Struct("",
        Rename("x", field),
        Rename("y", field),
    )
    
    def __init__(self, x, y=None):
        if y is None: (x, y) = x
        self.x = x
        self.y = y
    
    @property
    def value(self):
        return (self.x, self.y)
    
    def __repr__(self):
        return 'Point(%r, %r)' % self.value
    
    def to_value(self):
        return Container(x = self.x, y = self.y)
    
    @classmethod
    def from_value(cls, value):
        return cls(value.x, value.y)

class Rectangle(FixedObject):
    classID = 33
    _construct = StrictRepeater(4, field)


# Form
class Form(FixedObject, ContainsRefs):
    classID = 34
    _construct = Struct("form",
        Rename("width", field),
        Rename("height", field),
        Rename("depth", field),
        Rename("privateOffset", field),
        Rename("bits", field),
    )
    
    @property
    def value(self):
        return dict((k, getattr(self, k)) for k in self.__dict__ if not k.startswith("_"))
    
    def to_value(self):
        return Container(**self.value)
    
    @classmethod
    def from_value(cls, value):
        return cls(**dict(value))
    
    def __init__(self, **fields):
        self.__dict__.update(fields)


class ColorForm(Form):
    classID = 35
    _construct = Struct("",
        Embed(Form._construct),
        Rename("colors", field),
    )

