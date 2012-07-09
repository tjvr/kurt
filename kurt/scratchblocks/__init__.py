try:
	import ply
except ImportError, e:
	print "Missing dependency: PLY needed for kurt.scratchblocks module"
	raise e


from lexer import lex, tokens
from parser import yacc

parse_scratchblocks = yacc.parse
