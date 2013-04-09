
### Block ###

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


### Script ###

    def to_block_plugin(self):
        """Returns the script in scratchblocks format."""
        string = ""
        for block in self.blocks:
            string += block.to_block_plugin() + "\n"
        return string

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


### SpriteRef ###

class SpriteRef(object):
    """Used by `kurt.scratchblocks.parser` so that compile() doesn't have to
    build all the sprites before parsing all the scripts."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'SpriteRef(%s)' % self.name






