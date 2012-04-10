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

"""Primitive fixed-format objects - eg String, Dictionary."""

from construct import Container, Struct, Embed, Rename
from construct import PascalString, UBInt32, UBInt16, UBInt8, Bytes
from construct import BitStruct, Padding, Bits
from construct import Array as StrictRepeater, Array as MetaRepeater
# We can't import the name Array, as we use it. -_-

from array import array # used by Form

from inline_objects import Field



class FixedObject(object):
    """A primitive fixed-format object - eg String, Dictionary.
    value property - contains the object's value."""
    def __init__(self, value):
        self.value = value
    
    def to_construct(self, context):
        return Container(classID = self.__class__.__name__, value = self.to_value())
    
    @classmethod
    def from_construct(cls, obj, context):
        fixed_obj = cls.from_value(obj.value)
        fixed_obj._orig_container = obj # DEBUG
        return fixed_obj
    
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
        return "%s(%s)" % (self.__class__.__name__, self.value)


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
        assert len(obj.items) == obj.length, "File corrupt?"
        return cls(obj.items)


class FixedObjectByteArray(FixedObject):
    def __repr__(self):
        name = self.__class__.__name__
        value = repr(self.value)
        if len(value) > 60:
            value = value[:97] + '...'
            return "<%s(%s)>" % (name, value)
        else:
            return "%s(%s)" % (name, value)

# Bytes

class String(FixedObjectByteArray):
    classID = 9
    _construct = PascalString("value", length_field=UBInt32("length"))


class Symbol(FixedObjectByteArray):
    classID = 10
    _construct = PascalString("value", length_field=UBInt32("length"))
    def __repr__(self):
        return "<#%s>" % self.value


class ByteArray(FixedObjectByteArray):
    classID = 11
    _construct = PascalString("value", length_field=UBInt32("length"))
    
    def __repr__(self):
        return '<%s(%i bytes)>' % (self.__class__.__name__, len(self.value))


class SoundBuffer(FixedObjectByteArray, FixedObjectWithRepeater):    
    classID = 12
    _construct = Struct("",
        UBInt32("length"),
        MetaRepeater(lambda ctx: ctx.length, UBInt16("items")),
    )

# Bitmap 13 - found later in file

class UTF8(FixedObjectByteArray):
    classID = 14
    _construct = PascalString("value", length_field=UBInt32("length"), encoding="utf8")




# Collections

class Collection(FixedObjectWithRepeater, ContainsRefs):
    _construct = Struct("",
        UBInt32("length"),
        MetaRepeater(lambda ctx: ctx.length, Rename("items", Field)),
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
    
    def __len__(self):
        return len(self.value)

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
            Rename("key", Field),
            Rename("value", Field),
        )),
    )
    
    def to_value(self):
        items = [Container(key=key, value=value) for (key, value) in dict(self.value).items()]
        return Container(items=items, length=len(items))
    
    @classmethod
    def from_value(cls, obj):
        value = dict([(item.key, item.value) for item in obj.items])
        return cls(value)
    
    def __getattr__(self, name):
        return getattr(self.value, name)

class IdentityDictionary(Dictionary):
    classID = 25



# Color

class Color(FixedObject):
    """A 32-bit RGB color value.
    Each component r, g, b has a value between 0 and 1023.
    """
    classID = 30
    _construct = BitStruct("value",
        Padding(2),
        Bits("r", 10),
        Bits("g", 10),
        Bits("b", 10),
    )
    
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
    
    def to_value(self):
        return Container(r=self.r, g=self.g, b=self.b)
    
    @classmethod
    def from_value(cls, value):
        return cls(value.r, value.g, value.b)

    @property
    def value(self):
        return (self.r, self.g, self.b)
    
    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            repr(self.value).strip("()"),
        )
    
    def to_8bit(self):
        """Returns value with components between 0-256."""
        return tuple(x >> 2 for x in self.value)
    
    def hexcode(self):
        """Returns the color value in hex/HTML format.
        eg "ff1056".
        """
        hexcode = ""
        for x in self.to_8bit():
            part = hex(x)[2:]
            if len(part) < 2: part = "0" + part
            hexcode += part
        return hexcode


class TranslucentColor(Color):
    classID = 31
    _construct = Struct("",
        Embed(Color._construct),
        UBInt8("alpha"), # I think.
    )
    _construct_32 = Struct("",
        UBInt8("alpha"),
        UBInt8("r"),
        UBInt8("g"),
        UBInt8("b"),
    )

    def __init__(self, r, g, b, alpha):
        self.r = r
        self.g = g
        self.b = b
        self.alpha = alpha
    
    def to_value(self):
        return Container(r=self.r, g=self.g, b=self.b, alpha=self.alpha)
    
    @classmethod
    def from_value(cls, value):
        return cls(value.r, value.g, value.b, value.alpha)
    
    @classmethod
    def from_32bit_raw(cls, raw):
        container = cls._construct_32.parse(raw)
        color = cls.from_value(container)
        return cls(*(x << 2 for x in color.value))
    
    @property
    def value(self):
        return (self.r, self.g, self.b, self.alpha)

    def hexcode(self, include_alpha=True):
        """Returns the color value in hex/HTML format.
        eg "ff1056ff".
        Argument include_alpha: default True.
        """
        hexcode = Color.hexcode(self)
        if not include_alpha: hexcode = hexcode[:-2]
        return hexcode



# Dimensions

class Point(FixedObject):  
    classID = 32
    _construct = Struct("",
        Rename("x", Field),
        Rename("y", Field),
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
    _construct = StrictRepeater(4, Field)




# Form/images

class Bitmap(FixedObjectByteArray, FixedObjectWithRepeater):
    classID = 13
    _construct = Struct("",
        UBInt32("length"),
        Bytes("items", lambda ctx: ctx.length * 4),
    )

    @classmethod
    def from_value(cls, obj):
        assert len(obj.items) == obj.length * 4, "File corrupt?"
        return cls(obj.items)

    def to_value(self):
        return Container(items = self.value, length = len(self.value) / 4)

    @classmethod
    def make_construct(depth):
        pass
    
    @classmethod
    def encode_pixels(cls, depth):
        pass # must pass raw bytes to Bitmap constructor.
        # length must be a multiple of 4.

    def decode_pixels(self, depth, colors=None):
        if depth == 32:
            assert colors is None
            length = len(self.value) / 4

            for i in range(length):
                i *= 4
                raw = self.value[i: i + 4]
                color = TranslucentColor.from_32bit_raw(raw)
                yield color
                pixels.append(color)
        
        else:
            assert colors is not None
            length = len(self.value) * 8 / depth
            _construct = BitStruct("",
                MetaRepeater(length,
                    Bits("pixels", depth),
                ),
            )
            for pixel in _construct.parse(self.value).pixels:
                yield pixel
        
        # [Color(1008, 0, 8), Color(1023, 960, 0), Color(1008, 63, 850), Color(1008, 16, 767)]
        # red, yellow, pink, pink

        # 000008 black
        # 0042ff blue
        # 00ce42 green
        # ff0000 red
        # ffffff white



class Form(FixedObject, ContainsRefs):
    """A rectangular array of pixels, used for holding images.
    Attributes:
        width, height - dimensions
        depth - how many bits are used to specify the color at each pixel.
        bits - a Bitmap with varying internal structure, depending on depth.
        privateOffset - ?
    
    Note: do not modify the dict returned from the .value property.
    """
    classID = 34
    _construct = Struct("form",
        Rename("width", Field),
        Rename("height", Field),
        Rename("depth", Field),
        Rename("privateOffset", Field),
        Rename("bits", Field), # Bitmap
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
    
    def __repr__(self):
        return "<%s(%ix%i)>" % (
            self.__class__.__name__,
            self.width, self.height,
        )
    
    def built(self):
        self.bits = Bitmap(self.bits.value)
    
    def _to_pixels(self):
        assert self.depth == 32
        return self.bits.decode_pixels(self.depth)
    
    def to_color_map(self):
        pixels = self._to_pixels()
        assert len(pixels) == self.width * self.height
        
        n = self.width
        bitmap = [pixels[i:i+n] for i in range(0, len(pixels), n)]
        return bitmap
    
    def to_array(self):
        rgb = array('B') #unsigned byte
        alpha = None
        for color in self._to_pixels():
            rgb.append(color.r)
            rgb.append(color.g)
            rgb.append(color.b)
            if alpha is None:
                try:
                    color.alpha
                    alpha = True
                except AttributeError:
                    alpha = False
            if alpha:
                rgb.append(color.alpha)
        return (self.width, self.height, rgb)


class ColorForm(Form):
    """A rectangular array of pixels, used for holding images.
    width, height - dimensions
    depth - how many bits are used to specify the color at each pixel.
    bits - a Bitmap with varying internal structure, depending on depth.
    colors - the colors pointed to by the bits array. (I think?)
    privateOffset - ?
    """
    classID = 35
    _construct = Struct("",
        Embed(Form._construct),
        Rename("colors", Field), # Array
    )
    
    def _to_pixels(self):
        assert len(self.colors) == 2**self.depth
        return self.bits.decode_pixels(self.depth, self.colors)


        




