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

import kurt



DEBUG = False



class Arg(object):
    NUMBER = "NUMBER"      # ( )
    VARIABLE = "VARIABLE"
    REPORTER = "REPORTER"
    SPECIAL = "SPECIAL"

    STRING = "STRING"                    # [ ]
    STRING_DROPDOWN = "STRING_DROPDOWN"  # [ v]

    BOOL = "BOOL"  # < >

    COLOR = "COLOR" # [#fff]
    # COLOR is only used in `arg_kind`

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

    def __repr__(self):
        return "Arg(%r, %r)" % (self.kind, self.value)


class BlockError(Exception):
    pass


BLOCK_TEXT_ALIASES = {
    'whengfclicked': 'whengreenflagclicked',
    'turnleftdegrees': 'turnccwdegrees',
    'turnrightdegrees': 'turncwdegrees',
}

# TODO: Symbols
special_variables = {
    'all': 'all',
    'any': 'any',
    'last': 'last',
}

special_strings = {
    'mouse-pointer': '_mouse_',
}

SHAPE_ALLOW = {
    "boolean": [Arg.BOOL],
    "number": [Arg.NUMBER, Arg.VARIABLE],
    "number-menu": [Arg.NUMBER, Arg.VARIABLE],
    "string": [Arg.STRING, Arg.VARIABLE],
    "color": [Arg.COLOR], # Color
    "readonly-menu": [Arg.STRING_DROPDOWN, Arg.VARIABLE, Arg.SPECIAL,
        Arg.STRING],
}
for accept_args in SHAPE_ALLOW.values():
    if Arg.VARIABLE in accept_args:
        accept_args.append(Arg.REPORTER)


def fits(arg, insert):
    if insert.shape in ('readonly-menu', 'number-menu'):
        if arg.value in insert.options():
            return True
        elif arg.kind == Arg.DROPDOWN:
            return True
    elif insert.shape in ('number-menu', 'number'):
        if arg.kind == Arg.NUMBER:
            return True
        elif arg.kind in (Arg.STRING, Arg.STRING_DROPDOWN):
            # cast DROPDOWN / STRING to NUMBER
            if arg.value.strip().isdigit(): # int
                return True
            elif value.strip().replace('.', '').isdigit(): # float
                return True
    elif insert.shape == 'string':
        if arg.kind in (Arg.STRING, Arg.NUMBER):
            return True
    elif insert.shape == 'color':
        if arg.kind in (Arg.STRING, Arg.STRING_DROPDOWN):
            # COLORs are STRINGs at this point
            return True

def fits(arg, insert):
    need_kinds = SHAPE_ALLOW[insert.shape]
    if insert.kind == 'mathOp':
        return arg.value in insert.options()
    else:
        if arg.kind in need_kinds:
            return True
        else:
            if arg.kind in (Arg.STRING, Arg.STRING_DROPDOWN):
                if Arg.NUMBER in need_kinds:
                    # cast DROPDOWN / STRING to NUMBER
                    if arg.value.strip().isdigit():
                        return True # int
                    elif arg.value.strip().replace('.', '').isdigit():
                        return True # float
                elif Arg.COLOR in need_kinds:
                    # COLORs are STRINGs at this point
                    return True
            elif (arg.kind == Arg.NUMBER and
                  Arg.STRING in need_kinds):
                # cast NUMBER to STRING
                return True
            return False


def block_from_parts(parts, flag=None):
    # flag is currently unused

    text = ""
    arguments = []
    for part in parts:
        if isinstance(part, Arg):
            arguments.append(part)
        else:
            text += part

    script = None
    block = None

    text = kurt.BlockType._strip_text(text)
    text = BLOCK_TEXT_ALIASES.get(text, text)
    poss_types = kurt.plugin.Kurt.blocks_by_text(text)

    if poss_types:
        if len(poss_types) == 1:
            type = poss_types[0]
        else:
            if text == 'of':
                if poss_types[0].has_command('getAttribute:of:'):
                    poss_types.reverse()
            # verify arg types against block.inserts
            for type in poss_types:
                for (arg, insert) in zip(arguments, type.inserts):
                    if not fits(arg, insert):
                        break # Not this type
                else:
                    break # Type is ok!

            else: # No types matched
                type = poss_types[0]
                print "WARNING: wrong args for %r" % type
                print arguments

        has_args = not type.has_command("whenClicked")
        allow_vars = not (type.has_command("whenGreenFlag") or
                type.has_command("whenIreceive"))

        block_args = list(type.defaults)
        if has_args:
            for i in range(len(arguments)):
                arg = arguments[i]
                if arg is None:
                    continue

                kind = arg.kind
                if kind == Arg.VARIABLE and allow_vars:
                    value = kurt.Block("readVariable", arg.value)
                else:
                    value = arg.value

                if i < len(type.inserts):
                    insert = type.inserts[i]

                    if kind in (Arg.STRING, Arg.STRING_DROPDOWN):
                        if insert.shape == 'color':
                            value = kurt.Color(value)

                        elif (insert.shape in ('number', 'number-menu')):
                            # cast DROPDOWN / STRING to NUMBER
                            if value.strip().isdigit():
                                value = int(value)
                            elif value.strip().replace('.', '').isdigit():
                                value = float(value)

                    elif (kind == Arg.NUMBER and
                            insert.shape in ('readonly-menu', 'string')):
                        # cast NUMBER to STRING
                        value = unicode(value)

                if i >= len(block_args):
                    block_args.append(value)
                else:
                    block_args[i] = value

        block = kurt.Block(type, *block_args)

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
        return Arg(Arg.SPECIAL, value)
    else:
        return Arg(Arg.VARIABLE, variable_name)



# Scripts

def p_file(t):
    """file : script"""
    t[0] = kurt.Script(blocks = t[1])

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
        if block.comment: block.comment += '\n'
        block.comment += t[4]
    t[0] = t[1] + [ block ]

def p_script_one(t):
    """script : block
              | block COMMENT
    """
    block = t[1]
    if len(t) > 2:
        if block.comment: block.comment += '\n'
        block.comment += t[2]
    t[0] = [ block ]


# C blocks

def p_c_stack(t):
    """block : c_block  c_mouth END
             | if_block c_mouth END
    """
    block = t[1]
    block.args[-1] = t[2]
    t[0] = block #Block(block.command, *args)

def p_if_else(t):
    """block : if_block c_mouth ELSE c_mouth END
             | if_block c_mouth ELSE COMMENT c_mouth END"""
    block = t[1]
    block.type = kurt.BlockType.get('doIfElse')
    block.args = [block.args[0]]
    block.args += [ t[2] ]
    if len(t) > 6:
        block.args += [ t[5] ]
        if block.comment: block.comment += '\n'
        block.comment += t[4]
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
        if block.comment: block.comment += '\n'
        block.comment += t[2]
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
        if block.comment: block.comment += '\n'
        block.comment += t[2]
    t[0] = block

def p_if_block_def(t):
    """if_block_def : IF insert
                    | IF insert THEN
    """
    block = block_from_parts(t[1])
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


# Args

def p_bool_insert(t):
    """insert : LBOOL parts RBOOL"""
    block = block_from_parts(t[2], "b")
    t[0] = Arg(Arg.BOOL, block)

def p_empty_bool_insert(t):
    """insert : LBOOL RBOOL"""
    t[0] = Arg(Arg.BOOL, False)

def p_string_insert(t):
    """insert : STRING"""
    (value, is_dropdown) = t[1]
    if value.lower() in special_strings:
        value = special_strings[value].copy()
        t[0] = Arg(Arg.SPECIAL, value)
    else:
        if is_dropdown:
            t[0] = Arg(Arg.STRING_DROPDOWN, value)
        else:
            t[0] = Arg(Arg.STRING, value)

def p_reporter_insert(t):
    """insert : LPAREN parts RPAREN"""
    parts = t[2]
    try: # Reporter block.
        block = block_from_parts(parts, "r")
        t[0] = Arg(Arg.REPORTER, block)

    except BlockError, e:
        # Maybe it's a variable? Check there are no args.
        for part in parts:
            if isinstance(part, Arg):
                raise e # Give up: not a block or a variable.

        # Variable!
        t[0] = variable_named(' '.join(parts))
        # TODO: allow multiple spaces in var names

def p_empty_reporter_insert(t):
    """insert : LPAREN RPAREN"""
    t[0] = Arg(Arg.REPORTER, None)

def p_number_insert(t):
    """insert : LPAREN number RPAREN
              | LPAREN number DROPDOWN
    """
    t[0] = Arg(Arg.NUMBER, t[2])

def p_variable_insert(t):
    """insert : LPAREN SYMBOL RPAREN
              | LPAREN SYMBOL DROPDOWN
    """
    variable_name = t[2]
    try: # Might be a reporter like 'costume #'
        block = block_from_parts(t[2], "r")
        t[0] = Arg(Arg.REPORTER, block)

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

