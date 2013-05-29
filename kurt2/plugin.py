# Copyright (C) 2012 Tim Radvan
#
# This file is part of Kurt.
#
# Kurt is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# Kurt is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with Kurt. If not, see <http://www.gnu.org/licenses/>.

"""
To add support for a new file format, write a new :class:`KurtPlugin` subclass::

    import kurt2
    from kurt2.plugin import Kurt, KurtPlugin

    class MyScratchModPlugin(KurtPlugin):
        def load(self, path):
            f = open(path)
            kurt_project = kurt2.Project()
            # ... set kurt_project attributes ... #
            return kurt_project

        def save(self, path, kurt_project):
            f = open(path, "w")
            # ... save kurt_project attributes to file ...

    Kurt.register(MyScratchModPlugin())

Take a look at :mod:`kurt2.scratch20` for a more detailed example.


List available plugins
~~~~~~~~~~~~~~~~~~~~~~

To get a list of the plugins registered with :class:`Kurt`:

    >>> kurt2.plugin.Kurt.plugins
    {'scratch14': kurt.scratch14.Scratch14Plugin()}

You should see your plugin in the output, unless you forgot to :attr:`register
<Kurt.register>` it.


Notes
~~~~~

Some things to keep in mind:

* Most Scratch file formats have the *stage* as the base object -- so project
  attributes, such as the notes and the list of sprites, are stored on the
  stage object.

"""



class KurtPlugin(object):
    """Handles a specific file format.

    Loading and saving converts between a :class:`Project`, kurt's internal
    representation, and a file of this format.

    """

    name = "scratch14"
    """Short name of this file format, Python identifier style. Used internally
    by kurt.

    Examples: ``"scratch14"``, ``"scratch20.sprite"``, ``"byob3"``, ``"snap"``

    """

    display_name = "Scratch 2.0 Sprite"
    """Human-readable name of this file format. May be displayed to the user.
    Should not contain "Project" or "File".

    Examples: ``"Scratch 1.4"``, ``"Scratch 2.0 Sprite"``, ``"BYOB 3.1"``

    """

    extension = ".sb"
    """The extension used by this format, with leading dot.

    Used by :attr:`Project.load` to recognise its files.
    """

    has_stage_specific_variables = False
    """Whether the Project can have stage-specific variables and lists, in
    addition to global variables and lists (which are stored on the
    :class:`Project`).

    """


    def load(self, path):
        """Load a project from a file with this format.

        :attr:`Project.path` will be set later. :attr:`Project.name` will be
        set to the filename of ``path`` if unset.

        The file at ``path`` is not guaranteed to exist.

        :param path: Path to the file, including the plugin's extension. 
        :returns: :class:`Project`

        """

        raise NotImplementedError

    def save(self, path, project):
        """Save a project to a file with this format.

        :param path: Path to the file, including the plugin's extension.
        :param project: a :class:`Project`

        """

        raise NotImplementedError

    def __repr__(self):
        return self.__module__ + "." + self.__class__.__name__ + "()"


class Kurt(object):
    """The Kurt file format loader.

    This class manages the registering and selection of file formats. Used by
    :class:`Project`.
    """

    plugins = {}

    @classmethod
    def register(cls, plugin):
        """Register a new :class:`KurtPlugin`.

        Once registered, the plugin can be used by :class:`Project`, when:

        * :attr:`Project.load` sees a file with the right extension

        * :attr:`Project.convert` is called with the format as a parameter

        """
        cls.plugins[plugin.name] = plugin

    @classmethod
    def get_plugin(cls, **kwargs):
        """Returns the first format plugin whose attributes match kwargs.

        For example::

            get_plugin(name="scratch14")

        Will return the :class:`KurtPlugin` whose :attr:`name
        <KurtPlugin.name>` attribute is ``"scratch14"``.

        Name is used as the ``format`` parameter to :attr:`Project.load`
        and :attr:`Project.save`.

        :raises: :class:`ValueError` if the format doesn't exist.

        :returns: :class:`KurtPlugin`

        """

        if 'extension' in kwargs:
            kwargs['extension'] = kwargs['extension'].lower()

        for plugin in cls.plugins.values():
            for name in kwargs:
                if getattr(plugin, name) != kwargs[name]:
                    break
            else:
                return plugin

        raise ValueError, "Unknown format %r" % format




# - URL regexes
# - options?


