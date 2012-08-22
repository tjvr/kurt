from ply import yacc
import os
from lexer import tokens

from kurt.blockspecs import find_block, blocks_by_cmd
from kurt.scripts import Block, Script
from kurt import Symbol

DEBUG = True


special_variables = {
    'all': Symbol('all'),
}


class Insert(object):
    NUMBER = "number"
    VARIABLE = "variable"
    STRING = "string"
    
    BOOL = "bool"
    REPORTER = "reporter"
    
    SPECIAL = "special"

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value
    
    def __repr__(self):
        return "Insert(%r, %r)" % (self.kind, self.value)




class BlockError(Exception):
    pass



def block_from_parts(parts, flag=None):
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
        if text == 'of':
            if len(arguments) < 2:
                raise BlockError, "'of' block needs 2 arguments"
            
            if arguments[1].kind == Insert.STRING:
                type = blocks_by_cmd['getAttribute:of:'][0]
            else:
                type = blocks_by_cmd['computeFunction:of:']
            
        else:
            type = poss_types[0]

            if type.command == "changeVariable":
                arguments.insert(1, None)
                # This gets replaced by a symbol from the blocks arguments:
                # either <#setVar:to:> or <#changeVar:by:>

        # if flag and type.flag and type.flag != flag:
        #     summary = " ".join(repr(o) for o in obj)
        #     raise ParseError(
        #         "wrong flag %r for %r\n" % (flag, summary) + repr(args))

        block_args = type.defaults[:]
        for i in range(len(arguments)):
            arg = arguments[i]
            if arg:
                if arg.kind == Insert.VARIABLE:
                    arg = Block(script, "readVariable", arg.value)
                else:
                    arg = arg.value
                
                # TODO: verify kind of args against block.parts

                if i >= len(block_args):
                    block_args.append(arg)
                else:
                    block_args[i] = arg

        block = Block(script, type, *block_args)

    if not block:
        e = "No block type found for %r \n"%text + repr(arguments)
        raise BlockError(e)

    return block


def variable_named(variable_name):
    if variable_name.endswith(' v'):
        variable_name = variable_name[:-2]
    
    if variable_name.lower() in special_variables:
        value = special_variables[variable_name].copy()
        return Insert(Insert.SPECIAL, value)
    else:
        return Insert(Insert.VARIABLE, variable_name)



# Scripts

def p_script_end_newlines(t):
    """script : script NEWLINE"""
    t[0] = t[1]

def p_script_begin_newlines(t):
    """script : NEWLINE script"""
    t[0] = t[2]

def p_script(t):
    """script : script NEWLINE block"""
    t[0] = Script(None, blocks=t[1].blocks + [ t[3] ])

def p_script_one(t):
    """script : block"""
    t[0] = Script(None, blocks=[ t[1] ])
    # this is wrong. do script as whole file.


# C blocks

def p_empty_c_stack(t):
    """block : c_block  NEWLINE END
             | if_block NEWLINE END
    """
    block = t[1]
    args = block.args + [ [] ]
    t[0] = Block(block.script, block.command, *args)

def p_c_stack(t):
    """block : c_block  NEWLINE script NEWLINE END
             | if_block NEWLINE script NEWLINE END
    """
    block = t[1]
    args = block.args + [ t[3].blocks ]
    t[0] = Block(block.script, block.command, *args)

def p_if_empty_else(t):
    """block : if_block NEWLINE ELSE NEWLINE script NEWLINE END"""
    block = t[1]
    block.type = blocks_by_cmd['doIfElse'][0]
    args = block.args + [ ] + [ t[5].blocks ]
    t[0] = Block(block.script, block.type, *args)

def p_if_else_empty(t):
    """block : if_block NEWLINE script NEWLINE ELSE NEWLINE END"""
    block = t[1]
    block.type = blocks_by_cmd['doIfElse'][0]
    args = block.args + [ t[3].blocks ] + [ ]
    t[0] = Block(block.script, block.type, *args)

def p_if_else(t):
    """block : if_block NEWLINE script NEWLINE ELSE NEWLINE script NEWLINE END"""
    block = t[1]
    block.type = blocks_by_cmd['doIfElse'][0]
    args = block.args + [ t[3].blocks ] + [ t[7].blocks ]
    t[0] = Block(block.script, block.type, *args)

def p_c_block(t):
    """c_block : FOREVER
               | FOREVER IF insert
               | REPEAT insert
               | REPEAT UNTIL insert
    """
    t[0] = block_from_parts(t[1:])

def p_if_block(t):
    """if_block : IF insert"""
    t[0] = block_from_parts(t[1:])


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

def p_string_insert(t):
    """insert : STRING"""
    t[0] = Insert(Insert.STRING, t[1])

def p_bool_insert(t):
    """insert : LBOOL parts RBOOL"""
    block = block_from_parts(t[2], "b")
    t[0] = Insert(Insert.BOOL, block)

def p_empty_bool_insert(t):
    """insert : LBOOL RBOOL"""
    t[0] = Insert(Insert.BOOL, None)

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
        t[0] = variable_named( ' '.join(parts))
        # TODO: allow multiple spaces in var names

def p_empty_reporter_insert(t):
    """insert : LPAREN RPAREN"""
    t[0] = Insert(Insert.REPORTER, None)

def p_number_insert(t):
    """insert : LPAREN number RPAREN"""
    t[0] = Insert(Insert.NUMBER, t[2])

def p_variable_insert(t):
    """insert : LPAREN SYMBOL RPAREN"""
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

    
# Until is sometimes used in block text!
    
def p_until_part(t):
    """part : UNTIL"""
    t[0] = t[1]



# Syntax errors.
def p_error(p):
    if p:
        e = "unexpected %s" % p.type
        e += "\n"
        for key in dir(p):
            if not key.startswith("_"):
                e += "    %s: %r\n" % (key, getattr(p, key))
        raise SyntaxError(e)
    else:
        # EOF
        raise SyntaxError("invalid syntax")



# Build the parser.
path_to_file = os.path.join(os.getcwd(), __file__)
path_to_folder = os.path.split(path_to_file)[0]

import logging
logging.basicConfig(
    level = logging.DEBUG,
    filename = "parselog.txt",
    filemode = "w",
    format = "%(filename)10s:%(lineno)4d:%(message)s"
)
log = logging.getLogger()

yacc.yacc(debug=True,debuglog=log)


# "if <<(x) > (3)> and <(y) < (4)>>\n    say [hi]\nend"
