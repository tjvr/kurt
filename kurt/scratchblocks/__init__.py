try:
	import ply
except ImportError, e:
	print "Missing dependency: PLY needed for kurt.scratchblocks module"
	raise e


from lexer import lex, tokens
from parser import block_plugin_parser

def parse_block_plugin(input):
    return block_plugin_parser.parse(input, tracking=True)
