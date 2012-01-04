import os, sys
path_to_lib = os.path.split(os.getcwd())[0]
sys.path.append(path_to_lib)

from kurt import *
from testing import *


### Inline values & references

#nil
test_cons(field, '\x01', None)
#true
test_cons(field, '\x02', True)
#false
test_cons(field, '\x03', False)
#SmallInteger
test_cons(field, '\x04\x00\x01\x00\x00', 65536)
#SmallInteger16
test_cons(field, '\x05\xff\xff', 65535)
#LargePositiveInteger
#LargeNegativeInteger
#Float
test_cons(field, '\x08\x3F\xF0\x00\x00\x00\x00\x00\x00', 1.0)
#Ref
test_cons(field, '\x63\x00\x01\x00', Ref(256))
test_cons(field, '\x63\x01\x01\x00', Ref(65792))



### Fixed-format objects

# String
test_cons(fixed_object, '\x09\x00\x00\x00\x0C\x42\x6C\x61\x6E\x6B\x2E\x73\x70\x72\x69\x74\x65',
    String('Blank.sprite')
)
# Symbol - TODO
# ByteArray - TODO
# SoundBuffer - TODO
# Bitmap
test_cons(fixed_object, '\r\x00\x00\x00\x01\xff\x00\x00\x08', Bitmap([4278190088L]))
# UTF8
test_cons(fixed_object, '\x0E\x00\x00\x00\x05\x42\x6C\x61\x6E\x6B', UTF8('Blank'))

# Array
test_cons(fixed_object, '\x14\x00\x00\x00\x01\x63\x00\x00\x0C', Array([Ref(12)]))
# OrderedCollection - TODO
test_cons(fixed_object, '\x15\x00\x00\x00\x00', OrderedCollection([]))
# Set - TODO
# IdentitySet - TODO
# Dictionary
test_cons(fixed_object, '\x18\x00\x00\x00\x00', Dictionary({}))
test_cons(fixed_object, '\x18\x00\x00\x00\x01\x05\x00\x01\x05\x00\x42', Dictionary({1: 66}))
# IdentityDictionary - TODO

# Color
test_cons(fixed_object, '\x1E\x3F\xFF\xFF\xFF', Color(1073741823))
# TranslucentColor
# Point
test_cons(fixed_object, '\x20\x05\x00\x00\x05\x00\x00', Point((0, 0)))
test_cons(fixed_object, '\x20\x08\x3F\xF0\x00\x00\x00\x00\x00\x00\x08\x3F\xF0\x00\x00\x00\x00\x00\x00', Point((1.0, 1.0)))

# Rectangle
test_cons(fixed_object, '\x21\x05\x02\x16\x05\x00\x47\x05\x02\x48\x05\x00\x6F', 
    Rectangle([534, 71, 584, 111])
)
# Form
# ColorForm



def test_file(path):
    bytes = open(path).read()
    ot = obj_network.parse(bytes)
    built_bytes = obj_network.build(ot)
    assert bytes == built_bytes
    print 'Tested file! :D'

test_file('/Users/tim/Code/python/kurt/tests/var.sprite')


# print summary
tests_finish()


