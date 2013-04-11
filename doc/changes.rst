Changes from kurt 1.4
=====================

.. include:: warning.rst

This section describes the changes between kurt version 1.4 and version 2.0,
and how to upgrade your code for the new interface. If you've never used kurt before, skip this section.

Kurt 2.0 includes support for multiple file formats, and so has a brand-new,
shiny interface. **The old ``kurt`` interface has moved to ``kurt.scratch14``**.

As most code only uses kurt to inspect the scripts inside a Scratch project,
``kurt.ScratchProjectFile`` points to ``kurt.scratch14.ScratchProjectFile``,
and ``kurt.scripts`` points to ``kurt.scratch14.scripts``.  These interfaces
are DEPRECATED, but are still accessible at the same place so that existing
code still works.

If you just want to make sure your existing code works with all future versions
of kurt, use the following code to import kurt::

    from distutils.version import StrictVersion

    import kurt
    if StrictVersion(kurt.__version__) >= "2.0":
        import kurt.scratch14 as kurt

Ideally you should rewrite your code to use the :doc:`new interface <kurt>`.
It's much cleaner, and you get support for multiple file formats for free!

.. * Deprecated attribute Block.name was removed -- use Block.command instead.
