#!/usr/bin/env python
"""Load images into a new Scratch project.

Usage:
    images.py "path/to/images/*.jpg" myproject.sb[2]

Example kurt script."""

import sys
import os
import re
import glob

# try and find kurt directory
path_to_file = os.path.join(os.getcwd(), __file__)
path_to_lib = os.path.split(os.path.split(path_to_file)[0])[0]
sys.path.append(path_to_lib)
import kurt



def sort_nicely(l):
    """Sort the given list in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    l.sort(key=alphanum_key)

def every_other(seq):
    is_other = True
    for x in seq:
        if is_other:
            yield x
        is_other = not is_other



if len(sys.argv) != 3:
    print __doc__
else:
    (_, image_pathname, project_path) = sys.argv

    image_paths = glob.glob(image_pathname)

    #image_paths = list(every_other(image_paths))

    sort_nicely(image_paths)

    p = kurt.Project()
    sprite = kurt.Sprite(p, "frames")
    p.sprites.append(sprite)

    for image_path in image_paths:
        costume = kurt.Costume.load(image_path)
        sprite.costumes.append(costume)

    sprite.parse("""
    when green flag clicked
    forever
        next costume
    end
    """)

    print "%i costumes" % len(sprite.costumes)
    print "Saving"
    out_path = p.save(project_path)
    print "Output: %r" % out_path

