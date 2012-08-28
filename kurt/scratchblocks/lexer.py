from ply import lex
import re

# Based on: http://www.drdobbs.com/web-development/184405580#l1

reserved = {
   'forever': 'FOREVER',
   'if':      'IF',
   'else':    'ELSE',
   'repeat':  'REPEAT',
   'until':   'UNTIL',
   'end':     'END',
}

tokens = [
    'INT',
    'FLOAT',
    'STRING',
    'LPAREN',
    'RPAREN',
    'LBOOL',
    'RBOOL',
    'SYMBOL',
    'NEWLINE',
    'DROPDOWN',
    'COMMENT',
] + reserved.values()

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBOOL  = r'<'
t_RBOOL  = r'>'

def t_DROPDOWN(t):
    r'v\)'
    return t


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
    
    is_dropdown = False
    if new_str.endswith(" v"):
        new_str = new_str[:-2]
        is_dropdown = True
    
    t.value = (new_str, is_dropdown)
    return t


def t_COMMENT(t):
    r'(//)[^\n]*'
    t.value = t.value[2:]
    if t.value and t.value[0] == ' ':
        t.value = t.value[1:]
    return t

# Track line numbers.
def t_NEWLINE(t):
    r'(\r\n|\n|\r)+'
    t.value = t.value.replace("\r\n", "\n")
    t.value = t.value.replace("\r", "\n")
    t.lineno += len(t.value) # Doesn't work!
    return t


# This rule must be practically last since there are so few rules concerning
# what constitutes a symbol.
def t_SYMBOL(t):
    r'[^0-9()<>\[\]][^()<>\[\]\ \t\n\/]*'
    t.type = reserved.get(t.value, 'SYMBOL') 
    return t

t_ignore = ' \t'


# def t_EOF(t):
#     r'\Z'
#     return t


# Handle errors.
def pretty_error(token, err_msg):
    input = token.lexer.lexdata
    
    lineno = input[:token.lexpos].replace('\r\n', '\n').replace('\r', '\n').count('\n')
    lines = input.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    err_msg += "on line %i\n" % (lineno + 1)
    
    err_msg += "  " + lines[lineno].strip()
    
    error = SyntaxError(err_msg)
    error.line = lines[lineno]
    raise error
    
    
def t_error(t):
    pretty_error(t, "tokenize error ")
    


# Build the lexer.
lex.lex()
