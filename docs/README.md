# 61A Documentation

This app generates documentation for all 61A apps.

## Setup

1. Clone the repo and switch into the `docs` directory.
2. Set up the Python environment using `python3 -m venv env` and
`env/bin/pip install -r requirements.txt`, or simply `sicp venv`
if you have `sicp` installed.
3. Run the Sphinx autobuilder using `env/bin/sphinx-autobuild .. _build`
4. Visit [http://localhost:8000](http://localhost:8000) to see the docs.

## Writing Documentation

To write documentation for an app, we use
[MyST](https://myst-parser.readthedocs.io/en/latest/). MyST allows us to write
Sphinx documentation in a markdown equivalent of reStructuredText. The
documentation for MyST should help you write documentation, but we'll cover
some examples and tips below anyway.

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

Then, whichever app you want to document, create a `README.md` under the
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

## Full Example

You can any of the [common](https://docs.cs61a.org/common/) docs as
a reference for how a finished `index` might look. Scroll to the bottom and
click on "Show Source" to see the MyST code. You can also check out the
`README` individually in the GitHub repository.
