import kurt

p = lambda x: kurt.text.parse_block_plugin(x, kurt.Project())


def command_getter(self):
    return self.type.translate('scratch14').command
kurt.Block.command = property(command_getter)


assert p("say (length of [hello])")[0].args[0].command == 'stringLength:'
assert p("say (length of (var))")[0].args[0].command == 'stringLength:'
assert p("say (length of [list v])")[0].args[0].command == 'lineCountOfList:'

assert p(u'[x position v] of [Sprite1]')[0].command == 'getAttribute:of:'
assert p(u'[x position v] of [Sprite1 v]')[0].command == 'getAttribute:of:'
assert p(u'[sqrt v] of (6)')[0].command == 'computeFunction:of:'
assert p(u'[sqrt v] of [6]')[0].command == 'computeFunction:of:'

assert p(u'[x position v] of (var)')[0].command == 'getAttribute:of:'
assert p(u'[sqrt v] of (var)')[0].command == 'computeFunction:of:'
for mf in kurt.Insert('number', 'mathOp').options():
    assert p(u'[%s v] of (var)' % mf)[0].command == 'computeFunction:of:'

assert p('set pen color to [#faa41a]')[0] == kurt.Block('penColor:',
        kurt.Color('#faa41a'))
assert p('set pen color to (0)')[0] == kurt.Block('setPenHueTo:', 0)



def check(x):
    b = p(x)
    assert p(b.stringify()) == b

check("""
if <>
say [hi]
else
play sound [pop v]
end
""")

check("""
if <>
move (10) steps
end
""")

check("""
repeat(10)
  turn cw (4) degrees
end
""")


assert p("when I receive (cheese)")[0] == kurt.Block('whenIreceive', 'cheese')

