from ply import lex
import re

# Based on: http://www.drdobbs.com/web-development/184405580#l1

tokens = (
    'INT',
    'FLOAT',
    'STRING',
    'LPAREN',
    'RPAREN',
    'LBOOL',
    'RBOOL',
    'SYMBOL',
)

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBOOL = r'<'
t_RBOOL = r'>'

# This rule must come before the int rule.
def t_FLOAT(t):
    r'-?\d+\.\d*(e-?\d+)?'
    t.value = float(t.value)
    return t

def t_INT(t):
    r'-?\d+'
    t.value = int(t.value)
    return t

# C-like string. Supports the following backslash sequences:
#    \", \\, \n, and \t.
def t_STRING(t):
    r'\[([^\\\]]|(\\.))*\]'
    escaped = 0
    str = t.value[1:-1]
    new_str = ""
    for i in range(0, len(str)):
        c = str[i]
        if escaped:
            if c == "t":
                c = "\t"
            new_str += c
            escaped = 0
        else:
            if c == "\\":
                escaped = 1
            else:
                new_str += c
    
    if new_str.endswith(" v"):
        new_str = new_str[:-2]
    
    t.value = new_str
    return t


# Ignore comments.
def t_comment(t):
    r'([#]|\\)[^\n]*'
    pass

# Track line numbers.
def t_newline(t):
    r'\n+'
    t.lineno += len(t.value)

# This rule must be practically last since there are so few rules concerning
# what constitutes a symbol.
def t_SYMBOL(t):
    r'[^0-9()<>\[\]][^()<>\[\]\ \t\n]*'
    return t

t_ignore = ' \t'

# Handle errors.
def t_error(t):
    raise SyntaxError("syntax error on line %d near '%s'" % (t.lineno, t.value))


# Build the lexer.
lex.lex()
