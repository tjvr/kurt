
# kurt

Kurt is a Python library for reading/writing Scratch project (.sb) and sprite files.

If you're interested in technical details of how the format works: the code should be pretty self-documenting; but check out the little [wiki](http://scratchformat.wikispaces.com/) where I documented the format in a more readable form.

**WARNING**: Make sure you take a backup of your Scratch projects before saving anything with kurt! kurt is by no means fully tested. I can't accept responsibility for corrupting your files.


## Recent Changes 

###v1.1: 

* `Script` and `Block` classes for manipulating scripts.
* **Block plugin** formatter — reads all the scripts in a project file and outputs `[scratchblocks]` syntax code for posting on the Scratch forums/wiki.
* Filled out the `_fields` list for most of the objects in `user_objects` from the Squeak source (not the unused ones), so there should now be no "undefined" fields.
* `Color` is now parsed correctly
* Added `ScratchProjectFile.sprites` shortcut as an alias for `project.stage.sprites`


## Dependencies

You'll need the awesome [Construct](http://construct.wikispaces.com/) library — used for defining the format. Make sure you get the latest version, which currently appears to be available [here](http://pypi.python.org/pypi/construct).


## Usage

You'll probably just want to use the provided `ScratchProjectFile` and `ScratchSpriteFile` classes. Load them by passing the path to the file to their constructor and use their provided `.save()` methods.

You can import just these classes them using:

    from kurt.files import *

Load a file (you'll find a preview file, `game.sb`, saved in the `tests` directory; but feel free to try it with any Scratch project file).

	# Just pass in the absolute or relative path to the file:
	project = ScratchProjectFile("tests/game.sb")
	
    # You can reload the file at any time with .load()

Inspect project:

    project.info['author'] # u'blob8108'
    project.stage # <ScratchStageMorph(Stage)>
    
    # List fields on object:
    project.stage.fields.keys() # ['volume', 'lists', 'tempoBPM', 'vars', 'sceneStates', 'color', 'media', 'rotationDegrees', 'draggable', 'bounds', 'submorphs', 'isClone', 'blocksBin', 'visibility', 'flags', 'objName', 'scalePoint', 'owner', 'rotationStyle', 'properties', 'costume']
    
    # Access fields using dot notation:
    project.stage.tempoBPM # 100
    
    # "sprites" as alias for "submorphs":
    project.stage.sprites # [<WatcherMorph(ScratchCat vx)>, <ScratchSpriteMorph(ScratchCat)>]
    # note: you can now use project.sprites instead

Most of the objects you're interested in, like `ScratchStageMorph` and `ScratchSpriteMorph`, inherit from `UserObject`. You can use `.fields.keys()` to see the available fields on one of these objects.

`FixedObjects` have a `.value` property to access their value. Inline objects, such as `int` and `bool`, are converted to their Pythonic counterparts. `Array` and `Dictionary` are now converted to `list` and `dict`, too.
    
Make changes:

    cat = project.stage.sprites[1]
    cat.vars # {u'vx': 0.0}
    cat.vars['vx'] = 100

Save:

    project.save()

Now re-open the project with Scratch!

Everything should, of course, work perfectly; if you have any problems, please file an issue, and I'll take a look! (:


## Details

Tested with **Python 2.6**. Works with **Scratch 1.4**; not tested with earlier versions, but possibly works.

[Scratch](http://scratch.mit.edu/) is created by the Lifelong Kindergarten Group at the MIT Media Lab.


## Licence

Kurt is released under the [LGPL](www.gnu.org/licenses/lgpl), version 3.

I'm not a lawyer; but I _think_ this means while you can use Kurt in your own, non-GPL'd code, any Kurt modifications must be distributed under the (L)GPL and include the source code. _(This is not legal advice and does not affect the terms as stated in the licence...)_


## Todo

* Optimise `ObjectNetworkAdapter` for building large files.	

	Kurt is currently very quick at parsing files; but pretty slow at writing them, particularly ones with very long scripts.

* Parse images
* "Default project" for building projects entirely "from scratch" (as it were) in Python code?


