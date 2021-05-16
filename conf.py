# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("."))


# -- Project information -----------------------------------------------------

project = "cs61a-apps"
copyright = "2021 CS 61A"
author = "CS 61A"

myst_substitutions = {"docs_in_charge": "Vanshaj"}


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
    "myst_parser",
]

myst_enable_extensions = [
    "linkify",
    "substitution",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**env",
    "**/*common*",
    "**/node_modules",
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# Set a custom page title.
html_title = "cs61a-apps"

# Allow Markdown files to be parsed using myst.
source_suffix = [".rst", ".md"]

# -- Options for autodoc -----------------------------------------------------

# Do not import the following libraries, just pretend like they exist.
autodoc_mock_imports = [
    "colorama",
    "cachetools",
    "sqlalchemy",
    "flask",
    "flask_oauthlib",
    "werkzeug",
    "runner",
]

# Use the following structure to shorten URL targets.
extlinks = {"repo": ("https://github.com/Cal-CS-61A-Staff/tree/master/%s", "repo ")}

# Link to parts of other software documentation, if needed.
intersphinx_mapping = {
    "flask": ("https://flask.palletsprojects.com/en/1.1.x", None),
    "flask_oauthlib": ("https://flask-oauthlib.readthedocs.io/en/latest", None),
    "python": ("https://docs.python.org/3", None),
}

# Change the order in which autodoc renders members of a file/class.
autodoc_member_order = "bysource"
