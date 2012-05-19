#coding=utf8

# Copyright © 2012 Tim Radvan
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

"""Function for parsing `[scratchblocks]` syntax to Script/Block objects.
This is the opposite of `Script.to_block_plugin()`.

Note: classes for manipulating Scripts and Blocks are found in `kurt.scripts`.

Functions:
    parse_scratchblocks

Example:
when gf clicked
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

Should parse to:
    [
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
        ]),
    ]
    
Errors are not currently very helpful :P
"""

from construct import *
from construct.text import *

from scripts import Script, Block
from blockspecs import find_block
from fixed_objects import Point



class ParseError(Exception):
    pass



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
            if flag == "r" and len(parts) == 1 and isinstance(parts[0], str):
                var = parts[0]
                block = Block(script, "readVariable", var)
        
        if not block:
            e = "No block type found for %r \n"%text + repr(args)
            raise ConstructError(e)
        return block


class ReporterAdapter(BlockAdapter):
    def _decode(self, obj, context):
        (flag, value) = obj
        
        print flag, value
        
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
                value = value[0]
                
                if len(value) == 1 and isinstance(value[0], str):
                    try:
                        number = float(value[0])
                        return Arg(number)
                    except ValueError:
                        pass
                
                return BlockAdapter._decode(self, value, context, flag=flag)
            
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

stack = OptionalGreedyRepeater(block)

script = Sequence("stack",
    OptionalGreedyRepeater(block),
    Anchor("position"),
)


def get_lines(data):
    data = data.replace("\r\n", "\n")
    data = data.replace("\r", "\n")
    lines = data.split("\n")
    for line in lines:
        yield line.strip()



def parse_scratchblocks(data):
    """Parses scratchblocks formatted code. Returns a list of Blocks.
    The opposite of Script.to_block_plugin().
    @param data: str, the scratchblocks code
    """
    data = data.strip()
    data = data.replace("\r\n", "\n")
    data = data.replace("\r", "\n")
    
    (blocks, leftovers) = script.parse(data.strip())
    
    if leftovers < len(data):
        line_no = 0
        char_count = 0
        for line in data.split("\n"):
            char_count += len(line)
            line_no += 1
            if char_count > leftovers:
                break
        
        msg = "Error in data after %r on line #%i" % (line, line_no)
        raise ParseError(msg)
    
    return list(blocks)



if __name__ == "__main__": # DEBUG: to be removed
    import sys
    path = sys.argv[1]
    f = open(path)
    blocks = parse_script_file(None, f)
    print blocks
    print blocks.to_block_plugin()
