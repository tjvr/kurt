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

from fixed_objects import Symbol, Color, Point
from user_objects import BaseMorph

from pprint import pformat



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
    def __init__(self, command_or_type=None, *args):
        self.script = None
        self._comment = None

        if not command_or_type:
            print 'OBSOLETE?'

        self.type = None
        if isinstance(command_or_type, BlockType):
            self.type = command_or_type
        else:
            command = command_or_type
            if isinstance(command, Symbol):
                command = command.value

            if command == 'scratchComment':
                raise ValueError, "Use ScratchComment class instead"

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

            else:
                print "WARNING: unknown block type %r" % command
                self.type = BlockType(command, command)

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
    def from_array(cls, array):
        orig = array

        array = list(array)
        command = array.pop(0)

        args = []
        for arg in array:
            if isinstance(arg, list):
                if len(arg) == 0:
                    arg = Block.from_array([''])
                elif isinstance(arg[0], Symbol):
                    arg = Block.from_array(arg)
                else:
                    arg = [Block.from_array(block) for block in arg]
            args.append(arg)

        x = cls(command, *args)
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

    def set_script(self, script):
        if self.script and self.script is not script:
            if self in self.script:
                self.script.remove(self)

        for arg in self.args:
            if isinstance(arg, Block):
                arg.set_script(script)
            elif isinstance(arg, list):
                for block in arg:
                    block.set_script(script)

        self.script = script

    def __eq__(self, other):
        return (
            isinstance(other, Block) and
            self.type == other.type and
            self.args == other.args
        )

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        string = "Block(%s," % repr(self.command)
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
        return string + ")"

    @property
    def name(self):
        print "WARNING: Block.name is deprecated -- use Block.command instead"
        # DEPRECATED -- TODO: remove
        return self.command

    @property
    def command(self):
        if self.type:
            return self.type.command
        return ""

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, comment):
        if comment and not isinstance(comment, Comment):
            comment = Comment(comment=comment, anchor=self)
        self._comment = comment
        if comment and not comment.anchor is self:
            comment.anchor = self

    def add_comment(self, comment):
        if not self.comment or isinstance(comment, Comment):
            self.comment = comment
        elif comment:
            self.comment.comment += "\n" + comment

    def to_block_plugin(self):
        arguments = self.args[:]

        def get_insert(value, insert_type=None):
            insert_fmt = None
            if insert_type:
                insert_fmt = block_plugin_inserts[insert_type]

            if isinstance(value, Block):
                block = value
                if block.command in ("readVariable", "contentsOfList:"):
                    value = block.args[0]
                    insert_fmt = "(%s)"
                else:
                    value = block.to_block_plugin()
                    if insert_type in ('%n', '%d', '%s', '%m', '%e', '%l',
                                          '%S', '%y', '%i'):
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
            string = self.command
            for arg in self.args:
                arg = get_insert(arg)
                string += " " + arg

        else:
            if self.command == "MouseClickEventHatMorph":
                try:
                    morph_name = self.script.morph.name
                except AttributeError:
                    morph_name = "sprite"
                arguments[0] = morph_name

            #elif self.command == "EventHatMorph":
            #    if arguments[0] != "Scratch-StartClicked":
            #        block_type = BlockType(self.command, "when I receive %e")

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

        if self.comment:
            string += " " + self.comment.to_block_plugin()

        if block_type and block_type.flag == "c":
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

    def to_block_list(self):
        yield self
        for arg in self.args:
            if isinstance(arg, Block):
                for block in arg.to_block_list():
                    yield block
            elif isinstance(arg, list):
                for block in arg:
                    for b in block.to_block_list():
                        yield b

    def replace_sprite_refs(self, lookup_sprite_named):
        """Replace all the kurt.scratchblocks.SpriteRef objects with Sprite
        objects with the corresponding name."""
        for i in range(len(self.args)):
            arg = self.args[i]
            if isinstance(arg, SpriteRef):
                self.args[i] = lookup_sprite_named(arg.name)
            elif isinstance(arg, Block):
                arg.replace_sprite_refs(lookup_sprite_named)
            elif isinstance(arg, list):
                for block in arg:
                    block.replace_sprite_refs(lookup_sprite_named)

    def find_undefined_variables(self, stage):
        """Make sure all the readVariable blocks are valid.
        Replace them with contentsOfList: if necessary"""
        if self.type.command == "readVariable":
            assert self.args
            var = self.args[0]
            morph = self.script.morph

            if var in morph.variables or var in stage.variables:
                return # we're good
            elif var in morph.lists or var in stage.lists:
                self.type = blocks_by_cmd["contentsOfList:"][0]
                return # Fixed!
            else:
                yield var
        else:
            for arg in self.args:
                if isinstance(arg, Block):
                    for var in arg.find_undefined_variables(stage):
                        yield var
                elif isinstance(arg, list):
                    for block in arg:
                        for var in block.find_undefined_variables(stage):
                            yield var


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
    def __init__(self, pos=(20,20), blocks=None):
        self.morph = None
        if blocks is None: blocks = []
        self.pos = Point(pos)
        self.blocks = blocks

        for block in blocks:
            if isinstance(block, Block): # Might still be Refs!
                block.set_script(self)

    @classmethod
    def from_array(cls, morph, array):
        (pos, blocks) = array

        if len(blocks) == 1:
            block = blocks[0]
            if block:
                command = block[0]
                if ( isinstance(command, Symbol) and
                     command.value == 'scratchComment' ):
                    return Comment.from_array(morph, pos, block)

        script = cls(Point(pos), [Block.from_array(block) for block in blocks])
        script.morph = morph
        for block in script.blocks:
            if isinstance(block, Block):
                block.set_script(script)
        return script

    def to_array(self):
        return (Point(self.pos), [block.to_array() for block in self.blocks])

    def __eq__(self, other):
        return (
            isinstance(other, Script) and
            self.blocks == other.blocks
        )

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        string = "Script(%s, [\n" % repr(self.pos)
        for block in self.blocks:
            string += "\t" + repr(block).replace("\n", "\n\t") + ",\n"
        string = string.rstrip()
        string = string.rstrip(",")
        return string + "])"

    def to_block_plugin(self):
        """Returns the script in scratchblocks format."""
        string = ""
        for block in self.blocks:
            string += block.to_block_plugin() + "\n"
        return string

    def to_block_list(self):
        for block in self.blocks:
            for b in block.to_block_list():
                yield b

    def replace_sprite_refs(self, lookup_sprite_named):
        """Replace all the kurt.scratchblocks.SpriteRef objects with Sprite
        objects with the corresponding name."""
        for block in self.blocks:
            block.replace_sprite_refs(lookup_sprite_named)

    def find_undefined_variables(self, stage):
        assert self.morph is not None
        for block in self.blocks:
            assert block.script == self
            for var in block.find_undefined_variables(stage):
                yield var


    # Pretend to be a list #

    def __iter__(self):
        return iter(self.blocks)

    def __getattr__(self, name):
        return getattr(self.blocks, name)

    def append(self, block):
        self.blocks.append(block)
        block.set_script(self)

    def insert(self, index, block):
        self.blocks.insert(index, block)
        block.set_script(self)

    def __getitem__(self, index):
        return self.blocks[index]

    def __setitem__(self, index, value):
        self.blocks[index] = value

    def __delitem__(self, index):
        del self.blocks[index]

    def __len__(self):
        return len(self.blocks)



class ScriptCollection(list):
    def __init__(self, scripts=None):
        if scripts is None: scripts = []
        self += scripts

    def __repr__(self):
        return pformat(list(self))



# circular imports are stupid
from blockspecs import BlockType
from blockspecs import blocks_by_cmd, block_plugin_inserts, find_block



class Comment(Script):
    type = BlockType("scratchComment", "// %s", defaults = ["", True, 112])

    def __init__(self, pos=None, comment="", showing=True, width=112, anchor=None):
        self.morph = None
        self.blocks = []
        if pos is None:
            pos = Point(0, 0)
        self.pos = pos

        self.comment = comment
        self.showing = showing
        self.width = width
        self._anchor = anchor

    def __len__(self):
        return True

    @classmethod
    def from_array(cls, morph, pos, block):
        if block[0] == Symbol('scratchComment'):
            block.pop(0)
        comment = cls(pos, *block)
        comment.morph = morph
        return comment

    def to_array(self, blocks_by_id):
        array = [Symbol('scratchComment')]
        array += [self.comment, self.showing, self.width]
        if self.anchor:
            for i in xrange(len(blocks_by_id)):
                if blocks_by_id[i] is self.anchor:
                    array.append(i + 1)
                    break
        return (self.pos, [array])

    def __repr__(self):
        return 'Comment' + repr((
            self.pos, self.comment, self.showing, self.width,
        ))

    @property
    def anchor(self):
        return self._anchor

    @anchor.setter
    def anchor(self, block):
        self._anchor = block
        if block:
            if not self.pos and block.script:
                (x, y) = block.script.pos
                self.pos = (x + 200, y)

            if not block.comment is self:
                block.comment = self

    def attach_scripts(self, blocks_by_id):
        """Attach the comment to the right block from the given scripts."""
        if self.anchor:
            if not isinstance(self.anchor, Block):
                index = self.anchor
                self.anchor = blocks_by_id[index - 1]
                self.anchor.comment = self

    def to_block_plugin(self):
        return '// ' + self.comment.replace('\r', '\n').replace('\n', ' ')



class SpriteRef(object):
    """Used by `kurt.scratchblocks.parser` so that compile() doesn't have to
    build all the sprites before parsing all the scripts."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'SpriteRef(%s)' % self.name






