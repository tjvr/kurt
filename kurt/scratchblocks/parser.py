from ply import yacc
import os
from lexer import tokens

DEBUG = True



class Insert(object):
    NUMBER = "number"
    VARIABLE = "variable"
    STRING = "string"
    
    BOOL = "bool"

    def __init__(self, value, kind):
        self.value = value
        self.kind = kind
    
    def __repr__(self):
        return "Insert(%s, %s)" % (self.value, self.kind)


def p_parts(t):
    """
    parts : part parts
	      | part
    """
    if len(t) == 3:
        t[0] = [t[1]] + t[2]
    elif len(t) == 2:
        t[0] = [t[1]]


def p_number_int(t):
    """number : INT"""
    t[0] = t[1]

def p_number_float(t):
    """number : FLOAT"""
    t[0] = t[1]

def p_number_insert(t):
    """insert : LPAREN number RPAREN"""
    t[0] = Insert(t[2], Insert.NUMBER)

def p_variable_insert(t):
    """insert : LPAREN SYMBOL RPAREN"""
    t[0] = Insert(t[2], Insert.VARIABLE)

def p_string_insert(t):
    """insert : STRING"""
    t[0] = Insert(t[2], Insert.STRING)


#def p_insert_ltgt(t):
#    """
#    part : LBOOL
#    part : RBOOL
#    """
#    t[0] = t[1]


def p_part_insert(t):
    """part : insert"""
    t[0] = t[1]

def p_part_symbol(t):
    """part : SYMBOL"""
    t[0] = t[1]

def p_part_boolean(t):
    """part : LBOOL parts RBOOL"""
    t[0] = Insert(t[2], Insert.BOOL)



# Syntax errors.
def p_error(p):
    if p:
        raise SyntaxError("invalid syntax" + repr(p.__dict__))
	else:
		# EOF
		raise SyntaxError("invalid syntax")



# Build the parser.
path_to_file = os.path.join(os.getcwd(), __file__)
path_to_folder = os.path.split(path_to_file)[0]
print path_to_folder
yacc.yacc(debug=DEBUG, outputdir=path_to_folder)
