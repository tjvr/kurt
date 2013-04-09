Changes from kurt 1.4
=====================

This section describes the changes between kurt version 1.4 and version 2.0,
and how to upgrade your code for the new interface. If you've never used kurt before, skip this section.

Kurt 2.0 includes support for multiple file formats, and so has a brand-new,
shiny interface. The old ``kurt`` interface has moved to ``kurt.scratch14``.
The old entry point ``kurt.ScratchProjectFile`` has been deprecated, but is still
accessible at the same place so that existing code still works.



.. * Deprecated attribute Block.name was removed -- use Block.command instead.
