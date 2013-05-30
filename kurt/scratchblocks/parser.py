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

from ply import yacc
import os
from lexer import tokens, pretty_error

from kurt.scratch14.blockspecs import find_block, blocks_by_cmd
from kurt.scratch14.scripts import Block, Script, SpriteRef
from kurt.scratch14 import Symbol, Color


import htmlcolor
htmlcolor_parser = htmlcolor.Parser()


DEBUG = False



class Insert(object):
    NUMBER = "NUMBER"      # ( )
    VARIABLE = "VARIABLE"
    REPORTER = "REPORTER"
    SPECIAL = "SPECIAL"

    STRING = "STRING"                    # [ ]
    STRING_DROPDOWN = "STRING_DROPDOWN"  # [ v]

    BOOL = "BOOL"  # < >

    COLOR = "COLOR" # [#fff]
    # COLOR is only used in `insert_kind`

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

    def __repr__(self):
        return "Insert(%r, %r)" % (self.kind, self.value)


class BlockError(Exception):
    pass



special_variables = {
    'all': Symbol('all'),
    'any': Symbol('any'),
    'last': Symbol('last'),
}

special_strings = {
    'mouse-pointer': Symbol('mouse'),
}

math_functions = ['sqrt', 'abs', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
                  'ln', 'log', 'e ^', '10 ^']

insert_kind = {
    "%b": [Insert.BOOL],
    "%n": [Insert.NUMBER, Insert.VARIABLE],
    "%d": [Insert.NUMBER, Insert.VARIABLE],
    "%s": [Insert.STRING, Insert.VARIABLE],

    "%c": [Insert.COLOR], # Color
    "%C": [Insert.COLOR],

    "%m": [Insert.STRING_DROPDOWN, Insert.VARIABLE, Insert.SPECIAL], # Sprite
                                                    # Symbol('mouse')
    "%a": [Insert.STRING_DROPDOWN], # attribute of sprite
    "%e": [Insert.STRING_DROPDOWN, Insert.VARIABLE], # broadcast message
    "%k": [Insert.STRING_DROPDOWN], # key

    "%v": [Insert.STRING_DROPDOWN], # var doesn't *accept* VARIABLE Insert!
    "%L": [Insert.STRING_DROPDOWN], # List name
    "%i": [Insert.NUMBER, Insert.SPECIAL, Insert.VARIABLE], # Item
                                   # Symbol('last'), Symbol('any')
    "%y": [Insert.NUMBER, Insert.SPECIAL, Insert.VARIABLE], # Item (for delete)
                                   # Symbol('last'), Symbol('all')

    "%f": [Insert.STRING_DROPDOWN], # Math function
           # one of `math_functions`
    "%l": [Insert.STRING_DROPDOWN, Insert.VARIABLE], # Costume name
    "%g": [Insert.STRING_DROPDOWN], # graphic effect

    "%S": [Insert.STRING_DROPDOWN, Insert.VARIABLE], # sound
    "%D": [Insert.NUMBER, Insert.VARIABLE], # drum
    "%N": [Insert.NUMBER, Insert.VARIABLE], # note
    "%I": [Insert.NUMBER, Insert.VARIABLE], # instrument

    "%h": [Insert.STRING_DROPDOWN], # sensor (value)
    "%H": [Insert.STRING_DROPDOWN], # sensor (bool)
    "%W": [Insert.STRING_DROPDOWN, Insert.VARIABLE], # motor direction # TODO
}
for accept_inserts in insert_kind.values():
    if Insert.STRING_DROPDOWN in accept_inserts:
        accept_inserts.append(Insert.STRING)
for accept_inserts in insert_kind.values():
    if Insert.VARIABLE in accept_inserts:
        accept_inserts.append(Insert.REPORTER)



def parse_color(hexcode):
    if hexcode:
        try:
            rgb = htmlcolor_parser.parse(hexcode)
            return Color.from_8bit(*rgb)
        except ValueError:
            pass
    return hexcode


def block_from_parts(parts, flag=None):
    # flag is currently unused

    text = ""
    arguments = []
    for part in parts:
        if isinstance(part, Insert):
            arguments.append(part)
        else:
            text += part

    script = None
    block = None
    poss_types = find_block(text)

    if poss_types:
        if len(poss_types) == 1:
            type = poss_types[0]
        else:
            # verify insert types against block.inserts
            for type in poss_types:
                for (insert, need_type) in zip(arguments, type.inserts):
                    if need_type == '%f':
                        if insert.value not in math_functions:
                            break # Not this type.
                    else:
                        need_kinds = insert_kind[need_type]
                        if insert.kind not in need_kinds:
                            if insert.kind in (Insert.STRING,
                                               Insert.STRING_DROPDOWN):
                                if Insert.NUMBER in need_kinds:
                                    # cast DROPDOWN / STRING to NUMBER
                                    if insert.value.strip().isdigit():
                                        continue # int
                                    elif value.strip().replace('.', '').isdigit():
                                        continue # float

                                elif Insert.COLOR in need_kinds:
                                    # COLORs are STRINGs at this point
                                    continue

                            elif (insert.kind == Insert.NUMBER and
                                  Insert.STRING in need_kinds):
                                # cast NUMBER to STRING
                                continue



                            break # Not this type.
                else:
                    break # Type is ok!
            else: # No types matched
                type = poss_types[0]
                print "WARNING: wrong args for '%s' block" % type.command
                print ' '.join(map(repr, parts))

        if type.command == "changeVariable":
            arguments.insert(1, None)
            # This gets replaced by a symbol from the blocks arguments:
            # either <#setVar:to:> or <#changeVar:by:>

        has_args = not type.command == "MouseClickEventHatMorph"
        allow_vars = not type.command in ("EventHatMorph", "KeyEventHatMorph")

        block_args = list(type.defaults)
        if has_args:
            for i in range(len(arguments)):
                insert = arguments[i]
                if insert is None:
                    continue

                kind = insert.kind
                if kind == Insert.VARIABLE and allow_vars:
                    arg = Block("readVariable", insert.value)
                else:
                    arg = insert.value

                if i < len(type.inserts):
                    insert_type = type.inserts[i]
                    need_kinds = insert_kind[insert_type]

                    if kind in (Insert.STRING,
                                Insert.STRING_DROPDOWN):
                        if insert_type == "%m":
                            arg = SpriteRef(arg)

                        elif insert_type in ("%f", "%g", "%k"):
                            arg = str(arg) # Will not accept unicode!

                        elif Insert.COLOR in need_kinds:
                                arg = parse_color(arg)

                        elif Insert.NUMBER in need_kinds:
                            # cast DROPDOWN / STRING to NUMBER
                            if arg.strip().isdigit():
                                arg = int(arg)
                            elif arg.strip().replace('.', '').isdigit():
                                arg = float(arg)

                    elif ( Insert.STRING in need_kinds and
                           insert.kind == Insert.NUMBER ):
                        # cast NUMBER to STRING
                        arg = unicode(arg)

                if i >= len(block_args):
                    block_args.append(arg)
                else:
                    block_args[i] = arg

        block = Block(type, *block_args)

    if not block:
        e = "No block type found for %r \n"%text + repr(arguments)
        raise BlockError(e)

    return block


def variable_named(variable_name):
    if variable_name.endswith(' v'):
        variable_name = variable_name[:-2]

    # make sure this is a reporter!

    if variable_name.lower() in special_variables:
        value = special_variables[variable_name].copy()
        return Insert(Insert.SPECIAL, value)
    else:
        return Insert(Insert.VARIABLE, variable_name)



# Scripts

def p_file(t):
    """file : script"""
    t[0] = Script(blocks = t[1])

def p_script_end_newlines(t):
    """script : script NEWLINE"""
    t[0] = t[1]

def p_script_begin_newlines(t):
    """script : NEWLINE script"""
    t[0] = t[2]

def p_script(t):
    """script : script NEWLINE block
              | script NEWLINE block COMMENT"""
    block = t[3]
    if len(t) > 4:
        block.add_comment(t[4])
    t[0] = t[1] + [ block ]

def p_script_one(t):
    """script : block
              | block COMMENT
    """
    block = t[1]
    if len(t) > 2:
        block.add_comment(t[2])
    t[0] = [ block ]


# C blocks

def p_c_stack(t):
    """block : c_block  c_mouth END
             | if_block c_mouth END
    """
    block = t[1]
    block.args += [ t[2] ]
    t[0] = block #Block(block.command, *args)

def p_if_else(t):
    """block : if_block c_mouth ELSE c_mouth END
             | if_block c_mouth ELSE COMMENT c_mouth END"""
    block = t[1]
    block.type = blocks_by_cmd['doIfElse'][0]
    block.args += [ t[2] ]
    if len(t) > 6:
        block.args += [ t[5] ]
        block.add_comment(t[4])
    else:
        block.args += [ t[4] ]
    t[0] = block #Block(block.type, *args)

def p_c_mouth(t):
    """c_mouth : NEWLINE script NEWLINE"""
    t[0] = t[2]

def p_c_mouth_empty(t):
    """c_mouth : NEWLINE"""
    t[0] = None

def p_c_block(t):
    """c_block : c_block_def
               | c_block_def COMMENT
    """
    block = t[1]
    if len(t) > 2:
        block.add_comment(t[2])
    t[0] = block

def p_c_block_def(t):
    """c_block_def : FOREVER
                   | FOREVER IF insert
                   | REPEAT insert
                   | REPEAT UNTIL insert
    """
    t[0] = block_from_parts(t[1:])

def p_if_block(t):
    """if_block : if_block_def
                | if_block_def COMMENT
    """
    block = t[1]
    if len(t) > 2:
        block.add_comment(t[2])
    t[0] = block

def p_if_block_def(t):
    """if_block_def : IF insert"""
    block = block_from_parts(t[1:])
    t[0] = block


# Block

def p_block(t):
    """block : parts"""
    t[0] = block_from_parts(t[1])


# Parts

def p_parts(t):
    """parts : parts part"""
    t[0] = t[1] + [ t[2] ]

def p_part(t):
    """parts : part"""
    t[0] = [ t[1] ]


# Part

def p_insert_part(t):
    """part : insert"""
    t[0] = t[1]

def p_symbol_part(t):
    """part : SYMBOL"""
    t[0] = t[1]


# Inserts

def p_bool_insert(t):
    """insert : LBOOL parts RBOOL"""
    block = block_from_parts(t[2], "b")
    t[0] = Insert(Insert.BOOL, block)

def p_empty_bool_insert(t):
    """insert : LBOOL RBOOL"""
    t[0] = Insert(Insert.BOOL, False)

def p_string_insert(t):
    """insert : STRING"""
    (value, is_dropdown) = t[1]
    if value.lower() in special_strings:
        value = special_strings[value].copy()
        t[0] = Insert(Insert.SPECIAL, value)
    else:
        if is_dropdown:
            t[0] = Insert(Insert.STRING_DROPDOWN, value)
        else:
            t[0] = Insert(Insert.STRING, value)

def p_reporter_insert(t):
    """insert : LPAREN parts RPAREN"""
    parts = t[2]
    try: # Reporter block.
        block = block_from_parts(parts, "r")
        t[0] = Insert(Insert.REPORTER, block)

    except BlockError, e:
        # Maybe it's a variable? Check there are no args.
        for part in parts:
            if isinstance(part, Insert):
                raise e # Give up: not a block or a variable.

        # Variable!
        t[0] = variable_named(' '.join(parts))
        # TODO: allow multiple spaces in var names

def p_empty_reporter_insert(t):
    """insert : LPAREN RPAREN"""
    t[0] = Insert(Insert.REPORTER, None)

def p_number_insert(t):
    """insert : LPAREN number RPAREN
              | LPAREN number DROPDOWN
    """
    t[0] = Insert(Insert.NUMBER, t[2])

def p_variable_insert(t):
    """insert : LPAREN SYMBOL RPAREN
              | LPAREN SYMBOL DROPDOWN
    """
    variable_name = t[2]
    try: # Might be a reporter like 'costume #'
        block = block_from_parts(t[2], "r")
        t[0] = Insert(Insert.REPORTER, block)

    except BlockError:
        t[0] = variable_named(variable_name)

def p_number_int(t):
    """number : INT"""
    t[0] = t[1]

def p_number_float(t):
    """number : FLOAT"""
    t[0] = t[1]



# Override to make lt/gt < > work.
#
# This assumes )>( and )>( are never valid in any other context -- you can never
# have a boolean insert directly followed by a reporter, or vice versa.

def p_boolean_expr(t):
    """parts : insert LBOOL insert
             | insert RBOOL insert
    """
    t[0] = [ t[1], t[2], t[3] ]


# Keywords sometimes used in block text

def p_keyword_part(t):
    """part : IF
            | UNTIL
    """
    t[0] = t[1]



# Syntax errors.
def p_error(p):
    if p:
        err_msg = "Unexpected %(type)s: %(value)s " % p.__dict__
        pretty_error(p, err_msg)
    else:
        # EOF
        raise SyntaxError("invalid syntax")



# Build the parser.
path_to_file = os.path.join(os.getcwd(), __file__)
path_to_folder = os.path.split(path_to_file)[0]

block_plugin_parser = yacc.yacc(debug=DEBUG, write_tables=0)
                               #outputdir=path_to_folder,

# TODO: figure out how to make pip/setup.py be nice to PLY
# so parsetab.py can be writeable

