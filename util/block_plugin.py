"""Block plugin formatter: read all the scripts in a Scratch project file and output [scratchblocks] formatted code for Scratch forums/wiki.

    Usage: python block_plugin.py [path/to/project_file.sb]
"""

"""
Known block plugin bugs:
    - some booleans have to be encoded as reporters.
         'touching?', 'touchingcolor?', 'coloristouching?', 'mousedown?', 'keypressed?'
    - Can't have spaces in variable names inside not block.
        - <not <mouse down?>>
        - <not<(Current Type)=(Type)>>
    - <(var) < (var)> gt & lt are really weird inside and, or, not, etc.
        eg: if <<<(x) > [-1]> and <(y) > [-1]>> and <<(x) < [20]> and <(y) < [14]>>>
    - Can't have empty dropdowns eg. broadcast [ v]
"""

try:
    import kurt
except ImportError: # try and find kurt directory
    import os, sys
    path_to_file = os.path.join(os.getcwd(), __file__)
    path_to_lib = os.path.split(os.path.split(path_to_file)[0])[0]
    sys.path.append(path_to_lib)

from kurt.files import *
from kurt import ScratchSpriteMorph


def block_plugin_format(project):
    string = ""
    
    for sprite in project.stage.sprites:
        if not isinstance(sprite, ScratchSpriteMorph):
            continue
            
        string += "=" * 60 + "\n"        
        string += sprite.objName + "\n\n"
        
        scripts = sorted(sprite.scripts, key=lambda script: script.pos.y)
        for script in scripts:            
            string += script.to_block_plugin()
            #string += "=" * 40 + "\n"
            string += "\n\n"
        
        string += "\n\n"
    
    return string


if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        print __doc__
        exit()
    
    project = ScratchProjectFile(path)
    print block_plugin_format(project)


