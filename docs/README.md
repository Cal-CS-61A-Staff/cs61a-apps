# 61A Documentation

This app generates documentation for all 61A apps. If you need any help or have
questions at any point during the process, please message {{ docs_in_charge }}!

## Setup

1. Clone the repo and switch into the `docs` directory.
2. Create a new branch for your project using `git checkout -b docs/app-name`,
   where `app-name` is the name of the app you're documenting (use hyphens if
   the name is multiple words). If someone has already created this branch,
   omit the `-b` flag.
3. Set up the Python environment using `python3 -m venv env` and
   `env/bin/pip install -r requirements.txt`, or simply `sicp venv`
   if you have `sicp` installed.
4. Run the Sphinx autobuilder using
   `env/bin/sphinx-autobuild -b dirhtml .. _build`
5. Visit http://localhost:8000 to see the docs.

Alternatively, to compile all docs once, run
`env/bin/sphinx-build -b dirhtml .. _build`. This will generate an output
folder `_build` containing the compiled documentation. Useful for when you
don't want to run the file watcher.

## Writing Documentation

To write documentation for an app, we use a combination of
[reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
and [MyST](https://myst-parser.readthedocs.io/en/latest/). MyST allows us to
write Sphinx documentation in a markdown equivalent of reStructuredText. The
documentation for MyST should help you write the `index` and `README` files,
but we'll cover some examples and tips below anyway. The documentation for
reStructuredText will help you write the inline Python documentation.

### Text Editor Setup

First thing you should do is set up your text editor's vertical ruler to let
you know when you're hitting an 80-character limit (this is a standard, but not
a rule). In Visual Studio Code, this can be achieved by adding the following to
your `settings.json`:

```json
"editor.rulers": [
    {
        "column": 80,
        "color": "#555"
    },
]
```

### Creating the README

```{note}
We will use [MyST](https://myst-parser.readthedocs.io/en/latest/) for the
README.
```

Then, for whichever app you want to document, create a `README.md` under the
directory for that app, and set it up like so:

```md
# App Name

A brief description of what the app is meant to do.

## Setup

Include some steps to tell people how to develop this app locally.

## Other Sections

Include details that could help people develop or use the app.
```

### Creating the Index

```{note}
We will use [MyST](https://myst-parser.readthedocs.io/en/latest/) for the
index.
```

In order to place this app on the navbar, create an `index.md` under the same
directory, and set it up like so:

````
```{include} README.md
```

## Code Segment 1

```{eval-rst}
.. automodule:: app_directory.module_name
    :members:
```
````

Code segments like the one at the end of the example will auto-include the code
documentation for the various components of the app.

### Documenting Code

```{note}
We will use
[reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
for inline Python documentation.
```

To document a method in a Python file, format it like so:

```python
def function(param1, param2 = 2):
    """Description of the function.

    Can span multiple lines or paragraphs, if needed!

    :param param1: one line about the first parameter
    :type param1: str
    :param param2: one line about the second parameter
    :type param2: int

    :return: one line about the return value (including type)
    """
    # function body is here
```

Where `str` and `int` should be replaced with the actual type of the parameter.
This will result in the following rendered documentation:

```{eval-rst}
.. py:function:: function(param1, param2 = 2)

   Description of the function.

   Can span multiple lines or paragraphs, if needed!

   :param param1: one line about the first parameter
   :type param1: str
   :param param2: one line about the second parameter
   :type param2: int

   :return: one line about the return value (including type)
```

### Documenting `rpc` Methods

You do not have to write documentation for methods that are bound to RPC. For
example, if you're documenting `howamidoing`, when you get to `upload_grades`,
you can simply write the following (see emphasized line):

```{eval-rst}
.. code-block:: python
    :emphasize-lines: 4

    @rpc_upload_grades.bind(app)
    @only("grade-display", allow_staging=True)
    def upload_grades(data: str):
        """See :func:`~common.rpc.howamidoing.upload_grades`."""
        with transaction_db() as db:
            set_grades(data, get_course(), db)
```

### Linking to Other Documentation

If you mention another function, method, or class, please include a link to the
documentation for such. If this is in a MyST file, you can do this as follows:

```
{func}`common.shell_utils.sh`
{meth}`common.hash_utils.HashState.update`
{class}`~subprocess.Popen`
```

This will appear as {func}`common.shell_utils.sh`, 
{meth}`common.hash_utils.HashState.update`, and {class}`~subprocess.Popen`.

If this is in a Python file (using rST), you can do this as follows:

```
:func:`common.shell_utils.sh`
:meth:`~common.hash_utils.HashState.update`
:class:`subprocess.Popen`
```

This will appear as {func}`common.shell_utils.sh`, 
{meth}`~common.hash_utils.HashState.update`, and {class}`subprocess.Popen`.

```{note}
Per the examples above, if you insert a `~` before the path to the
documentation, Sphinx will render the link using only the name of the object
itself, and will drop the path itself. This is desirable for cleanliness, so
use this whenever linking to a document.
```

If you want to refer to something that is documented outside of this project,
the Python docs, and the Flask docs, message {{ docs_in_charge }} with what
you're trying to document, as well as a link to the documentation for the
relevant project. He will then add it to `intersphinx_mapping` dictionary in
the configuration, so that you can link to it as you would anything else. As an
example, to link to Flask's `redirect` function, you can use
``{func}`~flask.redirect` ``. This will render as {func}`~flask.redirect`.

## Full Example

### Sample README

Here's what the `common` README file looks like:

```{eval-rst}
.. literalinclude:: ../common/README.md
    :language: markdown
```

### Sample Index

Here's what the `common` index file looks like:

```{eval-rst}
.. literalinclude:: ../common/index.md
```

### Sample Code Documentation

Here's what the {func}`common.db.connect_db` docs look like:

```{eval-rst}
.. literalinclude:: ../common/db.py
    :pyobject: connect_db
```

Here's what the {func}`common.shell_utils.sh` docs look like:
```{eval-rst}
.. literalinclude:: ../common/shell_utils.py
    :pyobject: sh
```
