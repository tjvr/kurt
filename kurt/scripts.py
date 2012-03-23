#coding=utf8
from fixed_objects import Symbol


class Block(object):
    def __init__(self, name=None, *args):
        self.name = name
        self.args = list(args)
    
    @classmethod
    def from_array(cls, array):
        name = array.pop(0)
        
        args = []
        for arg in array:
            if isinstance(arg, list) and isinstance(arg[0], Symbol):
                arg = Block.from_array(arg)
            elif isinstance(arg, list):
                arg = [Block.from_array(block) for block in arg]
            args.append(arg)
        
        return cls(name, *args)
    
    def to_array(self):
        array = []
        if self.name:
            array.append(self.name)
        for arg in self.args:
            if isinstance(arg, Block):
                array.append(arg.to_array())
            elif isinstance(arg, list):
                array.append([block.to_array() for block in arg])
            else:
                array.append(arg)
        return array
    
    def __repr__(self):
        string = "Block(%s, " % self.name
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


class Script(object):
    """A single script (stack of blocks).
    Attributes:
        pos - x, y position of script in blocks bin.
        blocks - list of blocks.
    """
    def __init__(self, pos=(0,0), blocks=None):
        if blocks is None: blocks = []
        self.pos = pos
        self.blocks = blocks
    
    @classmethod
    def from_array(cls, array):
        pos, blocks = array
        blocks = [Block.from_array(block) for block in blocks]
        return cls(pos, blocks)
    
    def to_array(self):
        return (self.pos, [block.to_array() for block in self.blocks])
    
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





