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

.. * Deprecated attribute Block.name was removed -- use Block.command instead.
