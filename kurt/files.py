from construct import *
from objtable import ObjTable



class File(object):
    """File(path)
    Implements a basic file with save() function.
    Subclasses override _load() and _save()."""
    def __init__(self, path):
        """Loads a file.
        @param path: the path passed to open().
        """
        self.path = path
        self.load()
    
    def load(self):
        """Reload the file from disk, replacing any changes in memory.
        """
        bytes = open(self.path).read()
        self._load(bytes)
    
    def _load(self, bytes):
        """Subclasses must override this method.
        Set the attributes of this file from the given contents.
        @param bytes: str containing the file contents read from disk.
        """
        pass
    
    def save(self, path=None):
        """Save the file to disk.
        @param path: (optional) set new destination path. Future saves will go to the new location.
        """
        if path:
            self.path = path
        if not self.path:
            raise ValueError, "filepath not set."
        
        f = open(self.path, 'w')
        bytes = self._save()
        f.write(bytes)
        f.flush()
        f.close()
    
    def _save(self):
        """Subclasses must override this method.
        @return: str containing the bytes to be saved to disk.
        """
        pass


# info store
#     "thumbnail"         image showing a small picture of the stage when the project was saved
#     "author"                name of the user who saved or shared this project
#     "comment"               author's comments about the project
#     "history"               a string containing the project save/upload history
#     "scratch-version"   the version of Scratch that saved the project


import pdb

class ScratchProjectFile(File):
    """A Scratch Project file.
    Arguments: path
    """
    HEADER = "ScratchV02"
    _construct = Struct("scratch_file",
        Const(Bytes("header", 10), HEADER),
        
        UBInt32("info_size"),
        Rename("info", ObjTable),
        # object store for info (author, notes, thumbnail, etc.)
        
        #Pointer(lambda ctx: 14, 
        # this should go before the info ObjTable, hence the Pointer
        
        Rename("stage", ObjTable),
        # object store for contents, including the stage, sprites, and media
    )

    def _load(self, bytes):
        project = self._construct.parse(bytes)
        self.info = project.info
        self.stage = project.stage
    
    def _save(self):
        project = Container(
            header = self.HEADER,
            info = self.info,
            stage = self.stage,
        )
        return self._construct.build(project)


class ScratchSpriteFile(File):
    pass


__all__ = ['ScratchProjectFile', 'ScratchSpriteFile']


