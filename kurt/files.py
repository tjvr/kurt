#coding=utf8
from construct import Container, Struct, Const, Bytes, Rename
from objtable import ObjTable, InfoTable



class File(object):
    """File(path)
    Implements a basic file with save() function.
    Subclasses override _load() and _save()."""
    
    EXTENSION = None
    
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
        raise NotImplementedError()
    
    def save(self, path=None):
        """Save the file to disk.
        @param path: (optional) set new destination path. Future saves will go to the new location.
        """
        if path:
            self.path = path
        if not self.path:
            raise ValueError, "filepath not set."
        
        bytes = self._save()
        if not bytes:
            print "Can't write zero bytes to file, aborting"
            return
        
        f = open(self.path, 'w')
        f.write(bytes)
        f.flush()
        f.close()
    
    def _save(self):
        """Subclasses must override this method.
        @return: str containing the bytes to be saved to disk.
        """
        raise NotImplementedError()


class ScratchProjectFile(File):
    """A Scratch Project file.
    @param path: path to .sb file.
    
    Attributes:
        info - a Dictionary containing project info (author, notes, thumbnail...)
        stage - the stage. Contains project contents, including sprites and media.
    """
    
    EXTENSION = "sb"
    
    HEADER = "ScratchV02"
    _construct = Struct("scratch_file",
        Const(Bytes("header", 10), HEADER),
        
        Rename("info", InfoTable),
        
        Rename("stage", ObjTable),
    )

    def _load(self, bytes):
        project = self._construct.parse(bytes)
        self.info = project.info
        #self.info.__doc__ = InfoTable.__doc__
        self.stage = project.stage
    
    def _save(self):
        project = Container(
            header = self.HEADER,
            info = self.info,
            stage = self.stage,
        )
        return self._construct.build(project)


class ScratchSpriteFile(File):
    """A Scratch sprite file.
    @param path: path to .sprite file.
    
    Attributes:
        stage - the root object of the file (Sprite files actually contain a serialised ScratchStageMorph)
        sprite - convenience property for accessing the first (only) sprite in the file.
    """

    EXTENSION = "sprite"
    
    def _load(self, bytes):
        self.stage = ObjTable.parse(bytes)
    
    def _save(self):
        return ObjTable.build(self.stage)
    
    @property
    def sprite(self):
        return self.stage.sprites[0]



__all__ = ['ScratchProjectFile', 'ScratchSpriteFile']


