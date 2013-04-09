# Copyright (C) 2012 Tim Radvan
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

"""A Kurt plugin for Scratch 1.4.


INTERNALS:

The main classes used by this package are ScratchProjectFile and
ScratchSpriteFile classes.

Most of the objects, like Stage and Sprite, inherit from :class:`UserObject`.
You can use ``.fields.keys()`` to see the available fields on one of these
objects.

:class:`FixedObjects` have a ``.value`` property to access their value. Inline
objects, such as int and bool, are converted to their Pythonic counterparts.
Array and Dictionary are converted to list and dict.

"""

from kurt.scratch14.objtable import *
from kurt.scratch14.files import *
from kurt.scratch14.scripts import *

try:
    from kurt.scratchblocks import parse_block_plugin
except ImportError:
    print "WARNING: parser not available, requires PLY"
