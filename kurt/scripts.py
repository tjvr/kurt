#coding=utf8
from fixed_objects import Symbol, Color
from user_objects import BaseMorph



class Block(object):
    def __init__(self, script, name=None, *args):
        self.script = script
        if isinstance(name, Symbol):
            name = name.value
        self.name = name
        
        if self.name in blocks_by_cmd:
            block_type = blocks_by_cmd[self.name]
            self.args = block_type.defaults[:]
        else:
            self.args = []
        
        for i in xrange(len(args)):
            if i < len(self.args):
                self.args[i] = args[i]
            else:
                self.args.append(args[i])
    
    @classmethod
    def from_array(cls, script, array):
        name = array.pop(0)
        
        args = []
        for arg in array:
            if isinstance(arg, list) and isinstance(arg[0], Symbol):
                arg = Block.from_array(script, arg)
            elif isinstance(arg, list):
                arg = [Block.from_array(script, block) for block in arg]
            args.append(arg)
        
        return cls(script, name, *args)
    
    def to_array(self):
        array = []
        if self.name:
            array.append(Symbol(self.name))
        for arg in self.args:
            if isinstance(arg, Block):
                array.append(arg.to_array())
            elif isinstance(arg, list):
                array.append([block.to_array() for block in arg])
            else:
                array.append(arg)
        return array
    
    def __repr__(self):
        string = "Block(%s, " % repr(self.name)
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
                    string += "\t\t" + repr(block).replace("\n", "\n\t\t") + ",\n"
                string += "\t]"
            else:
                string += repr(arg) + ", "
        string = string.rstrip(" ")
        string = string.rstrip(",")
        return string + ')'
    
    @property
    def type(self):
        if self.name in blocks_by_cmd:
            return blocks_by_cmd[self.name]
    
    def to_block_plugin(self):
        arguments = self.args[:]
        
        def get_insert(value, insert_type=None):
            insert_fmt = None
            if insert_type:
                insert_fmt = block_plugin_inserts[insert_type]
            
            if isinstance(value, Block):
                block = value
                if block.name == "readVariable":
                    value = block.args[0]
                    insert_fmt = "(%s)"
                else:
                    value = block.to_block_plugin()
                    if insert_type in ("%s", "%d", "%l", "%y", "%i"):
                        insert_fmt = "(%s)"
                    elif insert_type == "%b":
                        #if block.name not in ( "list:contains:", "<", "=", ">", "&", "|", "not"):
                        if (block.type and block.type.flag != 'b') or block.name in (
                            "touching:", "touchingColor:", "color:sees:", "mousePressed", "keyPressed:",
                        ): # BUG: some booleans have to be encoded as reporters
                            insert_fmt = "(%s)"
                            
                            
                if not insert_fmt: insert_fmt = "(%s)"
            
            elif value == Symbol("mouse"):
                value = "mouse-pointer"
                if not insert_fmt: insert_fmt = block_plugin_inserts["%m"]
            
            elif value in (Symbol("last"), Symbol("all"), Symbol("any")):
                value = value.value
                if not insert_fmt: insert_fmt = block_plugin_inserts["%i"]
            
            elif isinstance(value, BaseMorph):
                value = value.objName
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
        
        if not block_type:
            if self.name == "changeVariable":
                change = arguments.pop(1)
                if change.value == "setVar:to:":
                    text = "set %v to %s"
                elif change.value == "changeVar:by:":
                    text = "change %v by %n"
        
                block_type = BlockType(self.name, text)
        
        if not block_type:
            string = self.name
            for arg in self.args:
                arg = get_insert(arg)
                string += " " + arg
            return string
        
        if self.name == "MouseClickEventHatMorph":
            try:
                morph_name = self.script.morph.objName
            except AttributeError:
                morph_name = "sprite"
            arguments[0] = morph_name
        
        elif self.name == "EventHatMorph":
            if arguments[0] != "Scratch-StartClicked":
                block_type = BlockType(self.name, "when I receive %e")
        
        if self.name in ("not", "="): # fix weird blockplugin bug
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
            blocks = arguments.pop(0) or []
            for block in blocks:
                block_str = block.to_block_plugin()
                string += "\n\t" + block_str.replace("\n", "\n\t")
            
            if self.name == 'doIfElse':
                string += '\nelse'
                
                blocks = arguments.pop(0)
                if blocks:
                    for block in blocks:
                        block_str = block.to_block_plugin()
                        string += "\n\t" + block_str.replace("\n", "\n\t")
            
            string += "\nend"
        
        return string
        


class Script(object):
    """A single script (stack of blocks).
    Attributes:
        pos - x, y position of script in blocks bin.
        blocks - list of blocks.
    """
    def __init__(self, morph, pos=(0,0), blocks=None):
        self.morph = morph
        if blocks is None: blocks = []
        self.pos = pos
        self.blocks = blocks
    
    @classmethod
    def from_array(cls, morph, array):
        pos, blocks = array
        script = cls(morph, pos)
        script.blocks = [Block.from_array(script, block) for block in blocks]
        return script
    
    def to_array(self):
        return (self.pos, [block.to_array() for block in self.blocks])
    
    def to_block_plugin(self):
        string = ""
        for block in self.blocks:
            string += block.to_block_plugin() + "\n"
        return string
    
    def __repr__(self):
        string = "Script(%s,\n" % repr(self.pos)
        for block in self.blocks:
            string += "\t" + repr(block).replace("\n", "\n\t") + ",\n"
        string = string.rstrip()
        string = string.rstrip(",")
        return string + ")"
    
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





from blockspecs import blocks_by_cmd, block_plugin_inserts, BlockType # YES THIS IS STUPID


