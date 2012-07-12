from ply import yacc
import os
from lexer import tokens

DEBUG = True



class Insert(object):
    NUMBER = "number"
    VARIABLE = "variable"
    STRING = "string"
    
    BOOL = "bool"

    REPORTER = "reporter"

    def __init__(self, kind, value):
        self.kind = kind
        self.value = value
    
    def __repr__(self):
        return "Insert(%r, %r)" % (self.kind, self.value)



def p_parts(t):
    """parts : parts part"""
    t[0] = t[1] + [ t[2] ]

def p_part(t):
    """parts : part"""
    t[0] = [ t[1] ]



def p_insert_part(t):
    """part : insert"""
    t[0] = t[1]

def p_symbol_part(t):
    """part : SYMBOL"""
    t[0] = t[1]



def p_number_int(t):
    """number : INT"""
    t[0] = t[1]

def p_number_float(t):
    """number : FLOAT"""
    t[0] = t[1]

def p_number_insert(t):
    """insert : LPAREN number RPAREN"""
    t[0] = Insert(Insert.NUMBER, t[2])

def p_variable_insert(t):
    """insert : LPAREN SYMBOL RPAREN"""
    t[0] = Insert(Insert.VARIABLE, t[2])

def p_string_insert(t):
    """insert : STRING"""
    t[0] = Insert(Insert.STRING, t[1])

def p_boolean_insert(t):
    """insert : LBOOL parts RBOOL"""
    t[0] = Insert(Insert.BOOL, t[2])

def p_reporter_insert(t):
    """insert : LPAREN parts RPAREN"""
    t[0] = Insert(Insert.REPORTER, t[2])
    


def p_boolean_expr(t):
    """parts : insert LBOOL insert
             | insert RBOOL insert
    """
    t[0] = [ t[1], t[2], t[3] ]



# Syntax errors.
def p_error(p):
    if p:
        raise SyntaxError("unexpected %r" % p.value + " —— " + repr(p.__dict__))
    else:
        # EOF
        raise SyntaxError("invalid syntax")



# Build the parser.
path_to_file = os.path.join(os.getcwd(), __file__)
path_to_folder = os.path.split(path_to_file)[0]

yacc.yacc(debug=DEBUG, outputdir=path_to_folder)
