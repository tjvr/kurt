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

"""Classes for manipulating scripts.
    Script - a stack; contains a list of blocks.
    Block - a single block.
"""

from fixed_objects import Symbol, Color
from user_objects import BaseMorph



class Block(object):
    """A single block.
    Arguments:
        script - the parent script that this block belongs to
        command - names the command this block performs (see BlockType.command)
        args - list of arguments for each of the block's inserts (see 
               BlockType.defaults)
    Attributes:
        type - BlockType instance (found to match self.command)
        
    Methods:
        to_block_plugin() — returns the block in scratchblocks format.
    """
    def __init__(self, script, command_or_type=None, *args):
        self.script = script
        
        if not command_or_type:
            print 'OBSOLETE?'
            import pdb; pdb.set_trace()
        
        self.type = None
        if isinstance(command_or_type, BlockType):
            self.type = command_or_type
        else:
            command = command_or_type
            if isinstance(command, Symbol):
                command = command.value
            
            if command in blocks_by_cmd:
                poss_types = blocks_by_cmd[command]
                if command == "changeVariable":
                    if len(args) < 3:
                        raise ValueError, \
                            "Invalid arguments to 'changeVariable' block"
                    
                    for type in poss_types:
                        if type.defaults[1] == args[1]:
                            self.type = type
                            break
                    else:
                        raise ValueError, "Invalid argument " + repr(args[1]) \
                            + " to changeVariable block"
                
                elif command == "EventHatMorph":
                    if args[0] == "Scratch-StartClicked": # when gf clicked
                        for type in poss_types:
                            if type.defaults == ["Scratch-StartClicked"]:
                                self.type = type
                                break
                    else: # broadcast
                        for type in poss_types:
                            if type.defaults == []:
                                self.type = type
                                break
                else:
                    self.type = poss_types[0]
        
        if self.type:
            self.args = self.type.defaults[:]
        else:
            self.args = []
        
        for i in xrange(len(args)):
            if i < len(self.args):
                self.args[i] = args[i]
            else:
                self.args.append(args[i])
    
    @classmethod
    def from_array(cls, script, array):
        orig = array
        
        array = list(array)
        command = array.pop(0)
        
        args = []
        for arg in array:
            if isinstance(arg, list):
                if len(arg) == 0:
                    arg = Block.from_array(script, '')
                elif isinstance(arg[0], Symbol):
                    arg = Block.from_array(script, arg)
                else:
                    arg = [Block.from_array(script, block) for block in arg]
            args.append(arg)
        
        x = cls(script, command, *args)
        x._orig = orig
        return x
    
    def to_array(self):
        array = []
        if self.command:
            array.append(Symbol(self.command))
        else:
            array.append('')
        
        for arg in self.args:
            if isinstance(arg, Block):
                array.append(arg.to_array())
            elif isinstance(arg, list):
                array.append([block.to_array() for block in arg])
            else:
                array.append(arg)
        return array
    
    def __eq__(self, other):
        return (
            isinstance(other, Block) and
            self.type == other.type and
            self.args == other.args
        )
    
    def __ne__(self, other):
        return not self == other
    
    def __repr__(self):
        string = "<%s Block (" % repr(self.command)
        for arg in self.args:
            if isinstance(arg, Block):
                string = string.rstrip("\n")
                string += "\n\t" + repr(arg).replace("\n", "\n\t") + ",\n"
            elif isinstance(arg, list):
                if string.endswith("\n"):
                    string += "\t"
                else:
                    string += " "
                string += "[\n"
                for block in arg:
                    string += "\t\t" + repr(block).replace("\n", "\n\t\t")
                    string += ",\n"
                string += "\t], "
            else:
                string += repr(arg) + ", "
        string = string.rstrip(" ")
        string = string.rstrip(",")
        return string + ")>"
    
    @property
    def name(self):
        print "WARNING: Block.name is deprecated -- use Block.command instead" 
        # TODO — leave this out?
        return self.command
    
    @property
    def command(self):
        if self.type:
            return self.type.command
        return ""
    
    def to_block_plugin(self):
        arguments = self.args[:]
        
        def get_insert(value, insert_type=None):
            insert_fmt = None
            if insert_type:
                insert_fmt = block_plugin_inserts[insert_type]
            
            if isinstance(value, Block):
                block = value
                if block.command == "readVariable":
                    value = block.args[0]
                    insert_fmt = "(%s)"
                else:
                    value = block.to_block_plugin()
                    if insert_type in ("%s", "%d", "%l", "%y", "%i"):
                        insert_fmt = "(%s)"
                    elif insert_type == "%b":
                        if (block.type and block.type.flag != 'b'):
                            # some booleans have to be encoded as reporters
                            insert_fmt = "(%s)"
                            
                            
                if not insert_fmt: insert_fmt = "(%s)"
            
            elif value == Symbol("mouse"):
                value = "mouse-pointer"
                if not insert_fmt: insert_fmt = block_plugin_inserts["%m"]
            
            elif value in (Symbol("last"), Symbol("all"), Symbol("any")):
                value = value.value
                if not insert_fmt: insert_fmt = block_plugin_inserts["%i"]
            
            elif isinstance(value, BaseMorph):
                value = value.name
                if not insert_fmt: insert_fmt = block_plugin_inserts["%m"]
            
            elif isinstance(value, Color):
                value = value.hexcode()
                if not insert_fmt: insert_fmt = block_plugin_inserts["%c"]
            
            elif isinstance(value, str) or isinstance(value, unicode):
                if not insert_fmt: insert_fmt = block_plugin_inserts["%s"]
            
            elif value is None or value is False:
                value = ""
                if not insert_fmt: insert_fmt = "[%s]"
            
            else:
                value = unicode(value)
                if not insert_fmt: insert_fmt = "[%s]"
            
            return insert_fmt % value
        
        
        block_type = self.type

        if self.command == "changeVariable":
            change = arguments.pop(1)
            if change.value == "setVar:to:":
                text = "set %v to %s"
            elif change.value == "changeVar:by:":
                text = "change %v by %n"
            block_type = BlockType(self.command, text)
        
        if not block_type:
            if not self.command and self.args: # Empty strings are comments
                return "// %s" % self.args[0]
            
            string = self.command
            for arg in self.args:
                arg = get_insert(arg)
                string += " " + arg
            
            return string
        
        if self.command == "MouseClickEventHatMorph":
            try:
                morph_name = self.script.morph.name
            except AttributeError:
                morph_name = "sprite"
            arguments[0] = morph_name
        
        elif self.command == "EventHatMorph":
            if arguments[0] != "Scratch-StartClicked":
                block_type = BlockType(self.command, "when I receive %e")
        
        if self.command in ("not", "="): # fix weird blockplugin bug
            block_type = block_type.copy()
            block_type.text = block_type.text.replace(" ", "")
        
        string = ""
        for part in block_type.parts:
            if BlockType.INSERT_RE.match(part):
                value = ""
                if arguments:
                    value = arguments.pop(0)
                
                string += get_insert(value, insert_type=part)
            else:
                string += part
        
        if block_type.flag == "c":
            blocks = []
            if arguments:
                blocks = arguments.pop(0)
            if blocks:
                for block in blocks:
                    block_str = block.to_block_plugin()
                    string += "\n\t" + block_str.replace("\n", "\n\t")
            
            if self.command == 'doIfElse':
                string += '\nelse'
                
                blocks = []
                if arguments:
                    blocks = arguments.pop(0)
                if blocks:
                    for block in blocks:
                        block_str = block.to_block_plugin()
                        string += "\n\t" + block_str.replace("\n", "\n\t")
            
            string += "\nend"
        
        return string
        


class Script(object):
    """A single stack of blocks.
    
    The first block self.blocks[0] is usually a “when” block, eg. an 
    EventHatMorph.
    
    Scripts implement the `list` interface, so can be indexed directly; eg 
    `script[0]` is the same as `script.blocks[0]`. All other methods like
    `append` also work. 
    
    Arguments/attributes:
        morph - ScriptableScratchMorph (Stage or Sprite) instance that this 
                script belongs to
        pos - (x, y) position of script in the “blocks bin”, the script pane in 
              the Scratch interface.
        blocks - list of blocks.
    
    Methods:
        to_block_plugin() — returns the script in scratchblocks format.
    """
    def __init__(self, morph, pos=(0,0), blocks=None):
        self.morph = morph
        if blocks is None: blocks = []
        self.pos = pos
        self.blocks = blocks
        for block in blocks:
            block.script = self
    
    @classmethod
    def from_array(cls, morph, array):
        pos, blocks = array
        script = cls(morph, pos)
        script.blocks = [Block.from_array(script, block) for block in blocks]
        return script
    
    def to_array(self):
        return (self.pos, [block.to_array() for block in self.blocks])
    
    def __eq__(self, other):
        return (
            isinstance(other, Script) and
            self.blocks == other.blocks
        )
    
    def __ne__(self, other):
        return not self == other
    
    def to_block_plugin(self):
        """Returns the script in scratchblocks format."""
        string = ""
        for block in self.blocks:
            string += block.to_block_plugin() + "\n"
        return string
    
    def __repr__(self):
        string = "Script(%s, [\n" % repr(self.pos)
        for block in self.blocks:
            string += "\t" + repr(block).replace("\n", "\n\t") + ",\n"
        string = string.rstrip()
        string = string.rstrip(",")
        return string + "])"
    
    def __iter__(self):
        return iter(self.blocks)
    
    def __getattr__(self, name):
        return getattr(self.blocks, name)
    
    def __getitem__(self, index):
        return self.blocks[index]
    
    def __setitem__(self, index, value):
        self.blocks[index] = value
    
    def __delitem__(self, index):
        del self.blocks[index]
    
    def __len__(self):
        return len(self.blocks)





from blockspecs import *
    #blocks_by_cmd, block_plugin_inserts, BlockType, find_block
# YES THIS IS STUPID


