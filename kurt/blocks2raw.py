
# Comment/Script superclass?
# -> meh.
import kurt
from kurt2 import BlockType

import itertools



categories20 = {
    1:  "motion",
    2:  "looks",
    3:  "sound",
    4:  "pen",
    5:  "events",
    6:  "control",
    7:  "sensing",
    8:  "operators",
    9:  "variables",
    10: "more blocks",
    12: "list",
    20: "sensor",
    21: "wedo",
    30: "midi",
    91: "midi",
    98: "obsolete", # --> we should use the 1.4 blockspecs for these instead
    99: "obsolete", # scrolling

    # for stage?
    102: "looks",
    104: "pen",
    106: "control",
    107: "sensing",
}

categories14 = set([
    'motion',
    'looks',
    'sound',
    'pen',
    'control',
    'sensing',
    'operators',
    'variables',
    'list',
    'motor',

    'obsolete number blocks', 
    'obsolete sound blocks',
    'obsolete sprite looks blocks', 
    'obsolete sprite motion blocks', 
    'obsolete image effects'
])

inserts20 = {
    '%b': 'boolean',
    '%c': 'color',
    '%d': ['number', 'menu'],
    '%m': 'readonly',
    '%n': 'number',
    '%s': 'string',
}

flags14 = {
    '-': '',
    'b': 'boolean',
    'c': 'cblock',
    'r': 'reporter',
    'E': 'hat',
    'K': 'hat',
    'M': 'hat',
    'S': 'hat',
    's': 'special',
    't': '', # timed blocks, all stack
}

kurt.blocks_by_cmd['doReturn'][0].shape = "cap"

flags20 = {
    ' ':  '',
    'b':  'boolean',
    'c':  'cblock',
    'r':  'reporter',
    'e':  'eblock',
    'cf': 'cap cblock',
    'f':  'cap',
    'h':  'hat',
}


plugin_defaults = {
    '%n': '0',
    '%d': '0',
    '%b': '',
}

plugin_inserts20 = {
    '%b': '<%s>',
    '%n': '(%s)',
    '%d': '(%s v)',
    '%s': '[%s]',
    '%m': '[%s v]',
    '%c': '[#ff00ff]',
}

from kurt2.scratch20.scratch2_as import blocks as blocks20

def blockify(blockspec):
    if len(blockspec) > 1:
        (text, flag, category_id, command) = blockspec[:4]
        defaults = blockspec[4:]
        category = categories20[category_id]
        return BlockType(command, text, flag, category, defaults)
    else:
        return None


def strip_text(block):
    text = "".join(filter(lambda p: p[0] != "%", block.parts))
    return text.lower().replace(" ", "")


blocks20 = map(blockify, blocks20)

blocks20_by_cmd = dict((block.command, block) for block in blocks20 if block)



plugin_specials = {
    "@greenFlag": "green flag",
    "@turnLeft": "cw",
    "@turnRight": "ccw",
    "_myself_": "myself",
    "_mouse_": "mouse",
}

plugin_class_annotations = {
    "@greenFlag": "-green-flag",
    "@turnLeft": "-turn-arrow",
    "@turnRight": "-turn-arrow",
}

plugin_flag_classes = {
    "h": "hat",
    "c":  "cstart",
    "e":  "cstart",
    "cf": "cstart cap",
    "f":  "cap",
}

plugin_category_classes = {
    "sensor": "purple",
    "wedo": "purple",
    "midi": "purple", # What colour are the midi blocks, anyway?
}

def scratchblocks2_definitions():
    done_block_text = set()

    def format_part(part, defaults):
        if part in plugin_specials:
            return plugin_specials[part]
        if part[0] == "%":
            if part[:2] in plugin_inserts20:
                insert = plugin_inserts20[part[:2]]
                if "%s" in insert:
                    value = plugin_defaults.get(part[:2], " ")
                    if defaults:
                        value = defaults.pop(0)
                    insert %= value
                return insert
        return part

    last_category = None
    for (category, blocks) in itertools.groupby(blocks20, key=lambda b: b and b.category):
        if category is None or not blocks:
            yield
            continue

        if category != last_category:
            yield
            yield
            yield
            yield "## %s ##" % plugin_category_classes.get(category, category)

        for block in blocks: 
            if block:
                if strip_text(block) not in done_block_text:
                    defaults = list(block.defaults)
                    code = "".join(map(lambda part: format_part(part, defaults),
                            block.parts))

                    if block.flag in ("r", "b"):
                        code = "(%s)" % code

                    classes = set()
                    if block.flag in plugin_flag_classes:
                        classes.add(plugin_flag_classes[block.flag])
                    for (match, class_name) in plugin_class_annotations.items():
                        if match in code:
                            classes.add(class_name)

                    
                    for (match, replacement) in plugin_specials.items():
                        if match in code:
                            code = code.replace(match, replacement)

                    if classes:
                        code += " ## " + " ".join(classes)


                    yield code

                    if block.command == "doIf":
                        yield "else ## celse"
                        yield "end ## cend"

                    done_block_text.add(strip_text(block))
            else:
                yield

        last_category = category


def definitions_for_test():
    for line in scratchblocks2_definitions():
        if line:
            if line.startswith("##"):
                print "// " + line
            else:
                is_cstart = "cstart" in line
                if "##" in line:
                    line = line[:line.index("##")]
                print line
                if is_cstart and not line.strip() == "if <> then":
                    print "end"
        else:
            print


def definitions_for_js():
    print 'scratchblocks2.blocks = "\\'
    for line in scratchblocks2_definitions():
        if line:
            print line  +  " " * 3  +  "\\"
        else:
            print "\\"
    print '";'
