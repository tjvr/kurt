Changes from kurt 1.4
=====================

.. include:: warning.rst

This section describes the changes between kurt version 1.4 and version 2.0,
and how to upgrade your code for the new interface. If you've never used kurt
before, skip this section.

Kurt 2.0 includes support for multiple file formats, and so has a brand-new,
shiny interface. As the API breaks support with previous versions, the major
version has been updated.

Ideally you should rewrite your code to use the :doc:`new interface <kurt>`.
It's much cleaner, and you get support for multiple file formats for free!

A quick, very incomplete list of some of the names that have changed:

* ``kurt.ScratchProjectFile.new()`` -> ``kurt.Project()``
* ``kurt.ScratchProjectFile(path)`` -> ``kurt.Project.load(path)``
* ``project.stage.variables`` -> ``project.variables``
* ``project.stage.lists`` -> ``project.lists``
* ``sprite.scripts.append(kurt.parse_block_plugin(text)`` -> ``sprite.parse(text)``
* ``kurt.Image.from_image(name, pil_image)`` -> ``kurt.Costume(name, kurt.Image(pil_image)))``
* ``sprite.lists[name] = kurt.ScratchListMorph(name='bob', items=[1, 2])`` -> ``sprite.lists['bob'] = kurt.List([1, 2])``
* ``kurt.Point(20, 100)`` -> ``(20, 100)``
