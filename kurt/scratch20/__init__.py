import zipfile
import json
import time
import os

import kurt
from kurt.plugin import Kurt, KurtPlugin

IMAGE_EXTENSIONS = ["PNG", "JPG"]


path = "/Users/tim/Dropbox/Code/kurt2/convert2.sb2"



def _add_file(name, contents, project_zip):
    """Write file contents string into archive."""
    # TODO: find a workaround to make ZipFile accept a file object.
    info = zipfile.ZipInfo(name)
    info.date_time = time.localtime(time.time())[:6]
    info.compress_type = zipfile.ZIP_DEFLATED
    project_zip.writestr(info, contents)

def _save_costume(kurt_costume, project_zip):
    return {
        "costumeName": "scene1",
        "baseLayerID": 1,
        "baseLayerMD5": "510da64cf172d53750dffd23fbf73563.png",
        "rotationCenterX": 240,
        "rotationCenterY": 180
    }

def _save_scriptable(kurt_scriptable, project_zip):
    _add_file(kurt_scriptable)

    scriptable_dict = {
        "objName": "Stage",
        "costumes": map(_save_costume, kurt_scriptable.costumes),
        "currentCostumeIndex": kurt_scriptable.costumes.index(kurt_scriptable.costume),
        "tempoBPM": 60,
    }

    if isinstance(kurt_scriptable, kurt.Sprite):
        pass


class Scratch20Plugin(KurtPlugin):
    name = "scratch20"
    display_name = "Scratch 2.0"
    extension = ".sb2"

    def load(self, path):
        project_zip = zipfile.ZipFile(path)

        project_dict = json.load(project_zip.open("project.json"))

        kurt_project = kurt.Project()

        kurt_project._original = project_dict

        return kurt_project

    def save(self, path, project):
        project_zip = zipfile.ZipFile(path, "w")

        project_dict = {
            "penLayerMD5": "279467d0d49e152706ed66539b577c00.png",
            "children": [],
            "info": {
            }
        }

        _add_file("project.json", json.dumps(project_dict), project_zip)

        return project_dict



Kurt.register(Scratch20Plugin())
