import kurt

import itertools



def strip_text(block):
    return kurt.BlockType._strip_text(block.type.text)


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
    "midi": "purple",
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
