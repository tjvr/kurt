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

"""Converts Scripts <--> text files in [scratchblocks] format.
"""

try:
    import kurt
except ImportError: # try and find kurt directory
    import os, sys
    path_to_file = os.path.join(os.getcwd(), __file__)
    path_to_lib = os.path.split(os.path.split(path_to_file)[0])[0]
    sys.path.append(path_to_lib)

from kurt.scripts import *
from kurt import ScratchSpriteMorph


