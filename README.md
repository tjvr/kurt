
# kurt

Python library for parsing Scratch format project (.sb) and sprite files.

The code should be pretty self-documenting; but if you're interested, check out the little [wiki](http://scratchformat.wikispaces.com/) where I documented the file format in a more readable form.

**WARNING**: Make sure you take a backup of your Scratch projects before saving anything with kurt! kurt is by no means fully tested. I can't accept responsibility for corrupting your files.

## Dependencies

You'll need the awesome [Construct](http://construct.wikispaces.com/) library — used for defining the format. Make sure you get the latest version, which currently appears to be available [here](http://pypi.python.org/pypi/construct).


## Usage

You'll probably just want to use the provided `ScratchProjectFile` and `ScratchSpriteFile` classes. Load them by passing the path to the file to their constructor and use their provided `.save()` methods.

You can import just these classes them using:

    from kurt.files import *

Load a file (you'll find a preview file, `game.sb`, saved in the `tests` directory; but feel free to try it with any Scratch project file).

	# Just pass in the absolute or relative path to the file:
	project = ScratchProjectFile('tests/game.sb')
	
    # You can reload the file at any time with .load()

Inspect project:

    project.info['author'] # u'blob8108'
    project.stage # <ScratchStageMorph(Stage)>
    
    # List fields on object:
    project.stage.fields.keys() # ['volume', 'lists', 'tempoBPM', 'vars', 'sceneStates', 'color', 'media', 'rotationDegrees', 'draggable', 'bounds', 'submorphs', 'isClone', 'blocksBin', 'visibility', 'flags', 'objName', 'scalePoint', 'owner', 'rotationStyle', 'properties', 'costume']
    
    # Access fields using dot notation:
    project.stage.tempoBPM # 100
    
    # "sprites" as alias for "submorphs":
    project.stage.sprites # [<WatcherMorph()>, <ScratchSpriteMorph(ScratchCat)>]

Most of the objects you're interested in, like `ScratchStageMorph` and `ScratchSpriteMorph`, inherit from `UserObject`. You can 
use `.fields.keys()` to see the available fields on one of these objects.

`FixedObjects` have a `.value` property to access their value. Inline objects, such as `int` and `bool`, are converted to their Pythonic counterparts.
    
Make changes:

    cat = project.stage.sprites[1]
    cat.vars # {u'vx': 0.0}
    cat.vars['vx'] = 100

Save:

    project.save()

Now re-open the project with Scratch!

Everything should, of course, work perfectly; if you have any problems, please file an issue, and I'll take a look! (:


## Details

Tested with Python 2.6.
Works with Scratch 1.4; not tested with earlier versions, but probably works.
[Scratch](http://scratch.mit.edu/) is created by the Lifelong Kindergarten Group at the MIT Media Lab.

kurt is currently very quick at parsing files; but pretty slow at writing them, particularly very large ones.


## Todo

- Fill out the `_fields` list for each object in `user_objects`.
	
	(Need to look at the Squeak source to find the field names.)

- Implement some nice Pythonic classes for manipulating scripts.
- Optimise `ObjectNetworkAdapter` for building large files.
- Parse images
- "Default project" for building projects entirely "from scratch" (as it were) in Python code?