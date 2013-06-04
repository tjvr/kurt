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

import re

import kurt
from kurt.scratch20.commands_src import commands, extras


CATEGORY_IDS = {
    1:  "motion",
    2:  "looks",
    3:  "sound",
    4:  "pen",
    5:  "events",
    6:  "control",
    7:  "sensing",
    8:  "operators",
    9:  "variables",
    10: "more blocks",
    12: "list",
    20: "sensor",
    21: "wedo",
    30: "midi",
    91: "midi",
    98: "obsolete", # --> we should use the 1.4 blockspecs for these instead
    99: "obsolete", # scrolling

    # for stage?
    102: "looks",
    104: "pen",
    106: "control",
    107: "sensing",
}

SHAPE_FLAGS = {
    ' ':  'stack',
    'b':  'boolean',
    'c':  'stack', # cblock
    'r':  'reporter',
    'e':  'stack', # eblock
    'cf': 'cap', # cblock
    'f':  'cap',
    'h':  'hat',
}

INSERT_SHAPES = {
    '%b': 'boolean',
    '%c': 'color',
    '%d': 'number-menu',
    '%m': 'readonly-menu',
    '%n': 'number',
    '%s': 'string',
}


INSERT_RE = re.compile(r'(%.(?:\.[A-z]+)?)')


def blockify(blockspec):
    if len(blockspec) > 1:
        (text, flag, category_id, command) = blockspec[:4]
        defaults = blockspec[4:]

        shape = SHAPE_FLAGS[flag]
        category = CATEGORY_IDS[category_id]

        parts = []
        for part in filter(None, INSERT_RE.split(text)):
            if INSERT_RE.match(part):
                default = defaults.pop(0) if defaults else None
                part = kurt.Insert(INSERT_SHAPES[part[:2]], default=default)
            parts.append(part)

        if "c" in flag:
            parts += [kurt.Insert("stack")]
        elif "e" in flag:
            parts += [kurt.Insert("stack"), "else", kurt.Insert("stack")]

        return kurt.TranslatedBlockType("scratch20", category, shape, command,
                parts)
    else:
        return None

def make_block_types():
    # Add extras
    for spec in extras:
        if len(spec) > 1:
            (flag, text, command) = spec[:3]
            commands.append([text, flag, 20, command] + spec[3:])
        else:
            commands.append(spec)

    # Blockify
    return map(blockify, commands)


