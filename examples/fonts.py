"""
Load fonts into Scratch as costumes, complete with a script for stamping text.

Each font is loaded into a sprite, and can write any message you please — feel
free to export any of the sprites and use them in your own projects!

Customise the options below...

"""
from PIL import Image, ImageDraw, ImageFont
import kurt
import os
import sys
import re

################################################################################



### SETTINGS: ###


# Text color (r, g, b)
TEXT_COLOR = (0, 0, 0)

# Background color
BG_COLOR = (255, 255, 255)

# Height of character images in pixels
FONT_SIZE = 24

# Name of the .sb file
PROJECT_NAME = "fonts"

FONT_PATHS = [
    # Add the full path to your font files here, for example:
    "/Library/Fonts/Museo500-Regular.otf",

    # Will make a sprite for each font
]

# The list of characters 
# Default is A-z, 0-9, and ' !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
CHARACTERS = ''.join(map(chr, range(32, 127)))

# Set the Fonts.Message variable
# Used in the demo script
MESSAGE = "The quick brown fox jumps over the lazy dog. "


### End of settings ###



################################################################################



def text_to_image(font, text, color):
    (w, h) = font.getsize(text)
    image = Image.new("RGB", (w, h), BG_COLOR) #(w*2, h*2))
    draw = ImageDraw.Draw(image)
    draw.text((0,0), text, color, font=font)
    draw.fontmode = "1"
    #image = image.resize((w, h), Image.ANTIALIAS)
    return image



project = kurt.ScratchProjectFile.new(PROJECT_NAME)
if os.path.exists(project.path):
    print "%s exists!" % project.path
    exit(1)

y = 170

stage_script = """
when gf clicked  // Example script, delete me!
clear
set [Fonts.Message v] to [{MESSAGE}]
set [Fonts.x v] to (-230)
set [Fonts.y v] to (170)
set [Fonts.line_height v] to (::line_height::)
""".format(**locals())

line_height = 0

for font_path in FONT_PATHS:
    try:
        font = ImageFont.truetype(font_path, FONT_SIZE)
    except IOError:
        continue
    (_, font_name) = os.path.split(font_path)
    if "." in font_name:
        font_name = ".".join(font_name.split(".")[:-1])
    font_name = font_name.replace("_", "")
    if font_name in project.sprites:
        continue
    print font_name

    sprite = kurt.Sprite(name=font_name)

    sprite.variables = dict(map(lambda x: (x, 0), [
        "i", "j", "word x", "message",
    ]))

    widths_list = kurt.ScratchListMorph(name="widths")
    sprite.lists[widths_list.name] = widths_list
    
    error = False
    for char in CHARACTERS:
        image = text_to_image(font, char, TEXT_COLOR)

        try:
            costume = kurt.Image.from_image(char, image)
        except SystemError:
            error = True
            break
        costume.rotationCenter = kurt.Point(0, 0)
        sprite.costumes.append(costume)
        if char == 'A':
            sprite.costume = costume

        widths_list.items.append(costume.width)
        line_height = max(line_height, costume.height)

    if error:
        continue
    
    sprite.scripts.append(kurt.parse_block_plugin("""
    when gf clicked
    hide
    """))

    writer_script = kurt.parse_block_plugin("""
    when I receive [Fonts.Write]
    if <not <(Fonts.Font) = [{font_name}]>>
        stop script
    end
    hide
    go to x:(Fonts.x) y:(Fonts.y)
    set [i v] to [1]
    set [message v] to (Fonts.Message)
    repeat until <(i) > ((length of (message)) - (1))>
        set [word x v] to (x position)
        set [j v] to (i)
        switch to costume [! v]
        repeat until <<(costume #)=[1]> or <(j) > ((length of (message)) - (1))>>
            switch to costume (letter (j) of (message))
            change [word x v] by (item (costume #) of [widths v])
            if <(word x) > [230]>
                set x to (-230)
                change y by (() - (Fonts.line_height))
                if <(y position) < (-170)>
                    wait (1) secs
                    clear
                    set y to (170)
                end
                switch to costume ((1) + (0))
                set [j v] to [0]
            else
                change [j v] by (1)
            end
            if <(costume #)=[1]>
                change [j v] by (-1)
            end
        end
        repeat until <(i) > (j)>
            switch to costume (letter (i) of (message))
            stamp
            change x by (item (costume #) of [widths v])
            change [i v] by (1)
        end
    end
    switch to costume [A v]
    set [Fonts.x v] to (x position)
    set [Fonts.y v] to (y position)
    """.format(**locals()))
    writer_script.pos = kurt.Point(20, 100)
    sprite.scripts.append(writer_script)

    stage_script += """
    set [Fonts.Font v] to [{font_name}]
    broadcast [Fonts.Write] and wait
    """.format(**locals())

    project.sprites.append(sprite)
    y -= 100


stage_script = stage_script.replace("::line_height::", str(line_height))
stage_script_parsed = kurt.parse_block_plugin(stage_script)
stage_script_parsed.pos = kurt.Point(20, 200)
project.stage.scripts.append(stage_script_parsed)

project.stage.scripts.append(kurt.parse_block_plugin("""
set [Fonts.Message v] to [Hello there!] // How to use
set [Fonts.x v] to [0]
set [Fonts.y v] to [0]
set [Fonts.Font v] to [HelveticaCY]
broadcast [Fonts.Write] and wait
"""))


print
print "Saving %i fonts..." % len(project.sprites)
project.save()
