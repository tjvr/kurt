
    # TODO: convert block flags to the new shape names. See dicts in blocks2raw


    @property
    def bounds(self):
        (x, y) = self.position

        (width, height) = self.costume.size

        pass # TODO

    @bounds.setter
    def bounds(self, value):
        (x, y, width, height) = value
        x += width / 2
        y += height / 2)




### Block ###

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
        return

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


### Script ###

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

    def to_block_list(self):
        for block in self.blocks:
            for b in block.to_block_list():
                yield b


### Comment ###

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


