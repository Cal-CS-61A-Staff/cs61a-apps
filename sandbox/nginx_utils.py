# Original Source:
# https://raw.githubusercontent.com/itsvs/dna/master/dna/utils/nginx_utils.py


class Block:
    """Represents a block in an nginx configuration

    :param name: the name of this block
    :type name: str
    :param sections: sub-blocks of this block
    :type sections: list[:class:`~dna.utils.Block`]
    :param options: variables to include in this block
    :type options: kwargs

    .. important::
        If you'd like to include a ``return`` statement
        in your block, pass its value into the constructor
        as ``ret``.
    """

    def __init__(self, name, *sections, **options):
        self.name = name
        self.sections = sections
        self.options = options

        if "ret" in self.options:
            self.options["return"] = self.options["ret"]
            del self.options["ret"]

    def _repr_indent(self, indent=""):
        """Represent this nginx block

        :param indent: the indentation block to preceed every\
            line in this representation with; add 4 indents to\
            sub-blocks
        :type indent: str
        """
        result = indent + self.name + " {\n"
        for block in self.sections:
            result += block._repr_indent(indent="    " + indent)
        for option in self.options:
            result += indent + "    " + option + " " + self.options[option] + ";\n"
        return result + indent + "}\n"

    def __repr__(self):
        return self._repr_indent(indent="")


class Server(Block):
    """A :class:`~dna.utils.Block` called ``server``"""

    def __init__(self, *sections, **options):
        super().__init__("server", *sections, **options)


class Location(Block):
    """A :class:`~dna.utils.Block` called ``location``

    :param location: the location being proxied
    :type location: str
    """

    def __init__(self, location, *sections, **options):
        super().__init__(f"location {location}", *sections, **options)
