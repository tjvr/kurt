
### Block ###

class _(object):
    def to_json(self):
        array = []
        if self.command:
            array.append(self.command)
        else:
            array.append('')

        for arg in self.args:
            if isinstance(arg, Block):
                array.append(arg.to_json())
            elif isinstance(arg, list):
                array.append([block.to_json() for block in arg])
            elif isinstance(arg, Sprite):
                array.append(arg.name)
            else:
                array.append(arg)
        return array


