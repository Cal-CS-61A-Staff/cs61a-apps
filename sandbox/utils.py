from contextlib import contextmanager
from common.db import connect_db


@contextmanager
def db_lock(db, username):
    try:
        with connect_db() as db:
            locked = db(
                f"SELECT locked FROM {db} WHERE username=%s", [username]
            ).fetchone()
            if locked is None:
                # environment does not exist
                db(
                    f"INSERT INTO {db} (username, initialized, locked) VALUES (%s, FALSE, TRUE)",
                    [username],
                )
                yield
            else:
                [locked] = locked
                if locked:
                    # TODO: Some way to force an unlock from the CLI
                    raise BlockingIOError(
                        f"Another operation is currently taking place on {db}"
                    )
                else:
                    db(
                        f"UPDATE {db} SET locked=TRUE WHERE username=%s",
                        [username],
                    )
                    yield

    finally:
        with connect_db() as db:
            db(f"UPDATE {db} SET locked=FALSE WHERE username=%s", [username])


# Some utilities for NGINX follow. These are originally sourced from:
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
    :param proxy_set_header: a dictionary of proxy\
        headers to pass into nginx
    :type proxy_set_header: dict
    """

    def __init__(self, location, *sections, proxy_set_header={}, **options):
        location = f"location {location}"
        proxy_set_header = {
            f"proxy_set_header {header}": value
            for (header, value) in proxy_set_header.items()
        }
        super().__init__(location, *sections, **options, **proxy_set_header)
