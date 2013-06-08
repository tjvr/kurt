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

"""Load blocks list by parsing blockspecs from Scratch's Squeak source code."""

import re

from construct import *
from construct.text import *

import kurt

from kurt.scratch14.fixed_objects import Symbol
from kurt.scratch14.blockspecs_src import *



#-- Squeak blockspecs parser --#

string = QuotedString("string", start_quote="'", end_quote="'", esc_char="\\")

symbol = Struct("symbol",
    Literal("#"),
    StringAdapter(GreedyRange(CharOf("value", set("+*/\<>=&|~:-0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"))))
    # _=@%?!`^$
)

spacer = Struct("spacer",
    Literal("#"),
    CharOf("", "~-"),
    Whitespace(),
    Value("is_block", lambda c: False)
)

value = Select("value",
    symbol,
    string,
    FloatNumber("value"),
    DecNumber("value"),
    Struct("negative number",
        Literal("-"),
        DecNumber("number"),
        Value("value", lambda ctx: -ctx['number']),
    ),

)

blockspec = Struct("blockspec",
    Literal("("),
    Whitespace(),
    Rename("text", string),
    Whitespace(),
    Rename("flag", symbol),
    Whitespace(),
    Rename("command", symbol),
    Whitespace(),
    OptionalGreedyRepeater(Rename("defaults", Struct("",
        value,
        Whitespace(),
    ))),
    Whitespace(),
    Literal(")"),
    Whitespace(),

    Value("is_block", lambda c: True)
)

category = Struct("category",
    Rename("name", string),
    Whitespace(),
    Rename("blocks", OptionalGreedyRepeater(
        Select("",
            blockspec,
            spacer,
        ),
    )),
    Whitespace(),
)

blockspecs = Struct("blockspecs",
    Rename("categories", OptionalGreedyRepeater(category)),
    #StringAdapter(OptionalGreedyRange(Char("leftovers"))), # used for DEBUG
    Terminator,
)


def parse_blockspec(squeak_code):
    parsed = blockspecs.parse(squeak_code)
    categories = parsed.categories

    blocks = []
    for category in categories:
        for block in category.blocks:
            if not block.is_block:
                continue

            defaults = []
            for default in block.defaults:
                default = default.value
                if isinstance(default, Container):
                    default = default.value
                defaults.append(default)

            block = S14BlockType(
                block.command.value,
                block.text,
                block.flag.value,
                category.name,
                defaults,
            )
            blocks.append(block)

    return blocks



#-- old BlockType class --#

class S14BlockType:
    INSERT_RE = re.compile(r'(%.)')

    def __init__(self, command, text, flag='-', category='', defaults=None):
        self.command = command
        self.text = text
        self.flag = flag
        self.category = category
        if defaults is None: defaults = []
        self.defaults = defaults

    def copy(self):
        return S14BlockType(
            self.command, self.text, self.flag, self.category, self.defaults[:]
        )

    def __repr__(self):
        return '<S14BlockType(%s)>' % self.command



#-- build lists --#

blocks = (list(parse_blockspec(squeak_blockspecs)) +
    list(parse_blockspec(squeak_stage_blockspecs)) +
    list(parse_blockspec(squeak_sprite_blockspecs)) +
    list(parse_blockspec(squeak_obsolete_blockspecs)))

blocks += [
    # variable reporters
    S14BlockType("readVariable", "%x", "r", category="variables",
       defaults = ['var']),
    S14BlockType("contentsOfList:", "%X", "r", category="variables",
        defaults=["list"]),

    # Blocks with different meaning depending on arguments.
    # These are special-cased inside load_block/save_block.
    S14BlockType("changeVar:by:", "change %v by %n", category="variables"),
    S14BlockType("setVar:to:", "set %v to %s", category="variables"),
    S14BlockType("whenGreenFlag", "when green flag clicked", "S",
        category="control", defaults = ["Scratch-StartClicked"]),
    S14BlockType("whenIReceive", "when I receive %e", "E", category="control",
        defaults=[""]),
]

blocks_by_cmd = {}
for block in blocks:
    cmd = block.command
    if cmd not in blocks_by_cmd:
        blocks_by_cmd[cmd] = []
    blocks_by_cmd[cmd].append(block)



#-- various fixes --#

del blocks_by_cmd['EventHatMorph']

assert blocks_by_cmd['MouseClickEventHatMorph'][0].text == 'when %m clicked'
blocks_by_cmd['MouseClickEventHatMorph'][0].defaults = ["Scratch-MouseClickEvent"]

blocks_by_cmd['KeyEventHatMorph'][0].defaults = ["space"]
blocks_by_cmd['doIfElse'][0].defaults = [False, None]



#-- convert to kurt 2 blocks --#

CATEGORIES = set([
    'motion',
    'looks',
    'sound',
    'pen',
    'control',
    'sensing',
    'operators',
    'variables',
    'list',
    'motor',

    'obsolete number blocks',
    'obsolete sound blocks',
    'obsolete sprite looks blocks',
    'obsolete sprite motion blocks',
    'obsolete image effects'
])

SHAPE_FLAGS = {
    '-': 'stack',
    'b': 'boolean',
    'c': 'stack',
    'r': 'reporter',
    'E': 'hat',
    'K': 'hat',
    'M': 'hat',
    'S': 'hat',
    's': 'stack',
    't': 'stack', # timed blocks, all stack
}

INSERT_SHAPES = {
    '%b': 'boolean',
    '%n': 'number',
    '%d': 'number',        # direction ( )
    '%s': 'string',        # string [ ]
    '%c': 'color',         # color picker with menu [#hexcode]
    '%C': 'color',         # color [#hexcode]

    '%m': 'readonly-menu', # morph reference [Sprite1 v]
    '%a': 'readonly-menu', # attribute of sprite [x position v]
    '%e': 'readonly-menu', # broadcast message [Play v]
    '%k': 'readonly-menu', # key [space v]

    '%v': 'readonly-menu', # variable [var v]
    '%L': 'readonly-menu', # list name [list v]
    '%i': 'number-menu',   # item ( ) 1/last/any
    '%y': 'number-menu',   # delete line %y of list ( ) 1/last/all

    '%f': 'readonly-menu', # math function [sqrt v]

    '%l': 'readonly-menu', # costume name [Costume1 v]
    '%g': 'readonly-menu', # graphic effect menu [ghost v]

    '%S': 'readonly-menu', # sound selector [meow v]
    '%D': 'number-menu',   # MIDI drum (48 v)
    '%N': 'number-menu',   # MIDI note (60 v)
    '%I': 'number-menu',   # MIDI instrument (1 v)

    '%h': 'readonly-menu', # Numerical sensor board selector menu
    '%H': 'readonly-menu', # Boolean sensor board selector menu
    '%W': 'readonly-menu', # motor direction

    # special
    '%x': 'inline',
    '%X': 'inline',
}

MATCH_COMMANDS = {
    'KeyEventHatMorph': 'whenKeyPressed',
    '\\\\': '%', # mod
    # play drum
}


INSERT_RE = re.compile(r'(%.(?:\.[A-z]+)?)')


def blockify(block):
    shape = SHAPE_FLAGS[block.flag]
    if block.text in ('stop script', 'stop all', 'forever', 'forever if %b'):
        shape = 'cap'

    defaults = block.defaults

    parts = []
    for part in filter(None, INSERT_RE.split(block.text)):
        if INSERT_RE.match(part):
            default = defaults.pop(0) if defaults else None
            if isinstance(default, Symbol):
                default = default.value
            part = kurt.Insert(INSERT_SHAPES[part], default=default)
        parts.append(part)

    match = MATCH_COMMANDS.get(block.command, None)

    if block.command == "doIfElse":
        parts += [kurt.Insert("stack"), "else", kurt.Insert("stack")]
    elif block.flag == "c":
        parts += [kurt.Insert("stack")]

    return kurt.TranslatedBlockType("scratch14", block.category, shape,
            block.command, parts, match=match)


block_list = map(blockify, sum(blocks_by_cmd.values(), []))
