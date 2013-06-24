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

"""Experimental block plugin syntax parser.

The syntax is the same as the ``scratchblocks`` tag used on the Scratch Forums
and Wiki. See: http://wiki.scratch.mit.edu/wiki/Block_Plugin

Soon to be replaced by a new parser with a much less restrictive syntax (but
keeping the same interface).

"""

import ply

from lexer import lex, tokens
from parser import block_plugin_parser

def parse(text, scriptable):
    """Return a :class:`kurt.Script` from the given code syntax.

    :param text: Code with blocks separated by ``\\n``.

    :param scriptable: The :class:`.kurtScriptable` object the script will be
                       added to, for context.

    """
    return block_plugin_parser.parse(text, tracking=True)
