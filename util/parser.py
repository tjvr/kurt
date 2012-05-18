"""Parses [scratchblocks] syntax to Script/Block objects."""

from construct import *
from construct.text import *


# DEBUG: this isn't needed here
try:
    import kurt
except ImportError: # try and find kurt directory
    import os, sys
    path_to_file = os.path.join(os.getcwd(), __file__)
    path_to_lib = os.path.split(os.path.split(path_to_file)[0])[0]
    sys.path.append(path_to_lib)

from kurt.scripts import Script, Block
from kurt.blockspecs import find_block
from kurt import Point


class ParseError(Exception):
    pass



def log(x):
    print x




class Arg(object):
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return "Arg(%r)" % self.value


# Adapters

class PartsAdapter(Adapter):
    def _decode(self, obj, context):
        parts = []
        for x in obj:
            part = x[0]
            if part:
                parts.append(part)
        return parts


class BlockAdapter(Adapter):
    def _decode(self, obj, context, flag=None):
        parts = obj
        
        if not parts:
            raise ConstructError
        
        text = ""
        args = []
        for part in parts:
            if isinstance(part, str):
                text += part
            elif isinstance(part, Arg):
                args.append(part.value)
            else:
                args.append(part)
        
        script = None
        block = None
        poss_types = find_block(text)
        if poss_types:
            type = poss_types[0]
            
            if flag and type.flag and type.flag != flag:
                summary = " ".join(repr(o) for o in obj)
                raise ParseError("wrong flag %r for %r\n" % (flag, summary) + repr(args))
            
            if type.command == "changeVariable":
                args.insert(1, None)
            
            block_args = type.defaults[:]
            for i in range(len(args)):
                arg = args[i]
                if i >= len(block_args):
                    block_args.append(arg)
                elif arg:
                    block_args[i] = arg
            
            block = Block(script, type, *block_args)
        
        else:
            #if text == "end": # DEBUG
            #    return Block(script, "end")
            
            if flag == "r" and len(parts) == 1 and isinstance(parts[0], str):
                var = parts[0]
                block = Block(script, "readVariable", var)
        
        if not block:
            e = "No block type found for %r \n"%text + repr(args)
            log(e)
            raise ConstructError(e)
        return block


class ReporterAdapter(BlockAdapter):
    def _decode(self, obj, context):
        (flag, value) = obj
        
        if flag == "string":            
            if value.endswith(" v"): # Dropdown
                value = value[:-2]
            
            elif value.startswith("#"):
                color = value.strip()
                if len(color) == 6:
                    pass # TODO: colors
                    
            return Arg(value)
        
        else:
            value = value[0]
            if isinstance(value, list):
                return BlockAdapter._decode(self, value[0], context, flag=flag)
            
            else:
                return Arg(value)



# Macros

ws = Whitespace(" \t")
rws = Whitespace(" \t", optional = False)

newline = Whitespace("\n\r")
rnewline = Whitespace("\n\r", optional=False)

def EmbedSeq(name, *subcons):
    return Sequence(name, *subcons, nested=False)

def SeqWithSep(name, subcon, sep):
    return RepeatUntil(lambda obj, ctx: obj[1],
        Select(name,
            EmbedSeq("", subcon, sep, Value("end", lambda ctx: False)),
            EmbedSeq("", subcon, Value("end", lambda ctx: True)),
        ),
    )


reporter = LazyBound("reporter", lambda: reporter)
stack = LazyBound("stack", lambda: stack)
block = LazyBound("block", lambda: block)


# Grammar

insert = ReporterAdapter(Select("insert",
    EmbedSeq("b",
        Literal("<"),
        reporter,
        Literal(">"),
    ),
    
    EmbedSeq("r",
        Literal("("),
        Select("value",
            FloatNumber("number"),
            DecNumber("number"),
            reporter,
        ),
        Literal(")"),
    ),
    
    QuotedString("string", start_quote="[", end_quote="]", esc_char="\\", encoding="utf8"),
include_name=True))


part = EmbedSeq("part",
    ws,
    Select("part",
        insert,
        NoneOf(StringUpto("word", " []()<>\t\n\r\n"), ""),
    ),
    ws,
)

parts = PartsAdapter(Rename("parts", OptionalGreedyRepeater(part)))

reporter = Sequence("reporter",
    parts, #OptionalGreedyRepeater(part),
)

class PrintContext(Construct):
    def _parse(self, obj, context):
        print context.block

class CBlockAdapter(Adapter):
    def _decode(self, stack, context):
        block = stack[0]
        for sub_block in stack[1:]:
            if sub_block:
                block.args += sub_block
        return (block)


block = CBlockAdapter(EmbedSeq("block",
    ws,
    Rename("block", BlockAdapter(parts)),
    ws,
    newline,
    
    If (lambda ctx: ctx.block and ctx.block.type and ctx.block.type.flag == "c",
        EmbedSeq("inner",
            stack,
            ws,
            Literal("end"),
            ws,
            newline,
        ),
    ),
))

class StackAdapter(Adapter):
    def _decode(self, obj, context):
        return obj

stack = StackAdapter(Sequence("stack",
    OptionalGreedyRepeater(block),
    Anchor("position"),
))


"""
when green flag clicked
set x to (0)
forever
	if <key [right arrow v] pressed?>
		change [vx v] by (2)
	end
	if <key [left arrow v] pressed?>
		change [vx v] by (-2)
	end
	set [vx v] to ((vx) * (0.8))
	change x by (vx)
end


Script(Point(23, 36.0),
	Block('EventHatMorph', 'Scratch-StartClicked'),
	Block('xpos:', 0),
	Block('doForever',  [
			Block('doIf', 
				Block('keyPressed:', 'right arrow'),
				[
					Block('changeVariable', u'vx', <#changeVar:by:>, 2),
				]),
			Block('doIf', 
				Block('keyPressed:', 'left arrow'),
				[
					Block('changeVariable', u'vx', <#changeVar:by:>, -2),
				]),
			Block('changeVariable', u'vx', <#setVar:to:>, 
				Block('*', 
					Block('readVariable', u'vx'),
				0.80000000000000004),
			),
			Block('changeXposBy:', 
				Block('readVariable', u'vx'),
			),
		]))
"""


def get_lines(data):
    data = data.replace("\r\n", "\n")
    data = data.replace("\r", "\n")
    lines = data.split("\n")
    for line in lines:
        yield line.strip()



def parse_blocks(data):
    data = data.strip()
    
    #try:
    (blocks, leftovers) = stack.parse(data.strip())
    #except ConstructError, e:
    #    import pdb; pdb.set_trace()
    
    if leftovers:
        print leftovers
    
    return blocks
    

def parse_script_file(morph, file):
    settings = {
        "pos": "(20, 20)",
    }
    
    while 1:
        try:
            line = file.readline()
        except EOFError:
            raise ParseError("no blocks found")
        line = line.strip()
        
        if line:
            try:
                (name, value) = line.split(":")
            except ValueError:
                raise ParseError("invalid line: "+line)
            
            name = name.strip().lower()
            value = value.strip()
            for setting in settings.keys():
                if name.startswith(setting):
                    settings[setting] = value
                    break
            else:
                settings[name] = value
        
        else:
            break
    
    print settings
    
    pos = Point.from_string(settings["pos"])

    data = ""
    while 1:
        more_data = file.read()
        if not more_data: break
        data += more_data    
    print data
    
    data = str(data)
    blocks = parse_blocks(data)
    script = Script(morph, pos, blocks)
    
    """TODO:
    * negative numbers
    """
    
    
    return script



if __name__ == "__main__": # DEBUG: to be removed
    import sys
    path = sys.argv[1]
    f = open(path)
    blocks = parse_script_file(None, f)
    print blocks
    print blocks.to_block_plugin()
