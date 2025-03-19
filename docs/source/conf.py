# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import reprostim.__about__

project = "ReproStim"
copyright = "2020-%Y, ReproNim Team"  # noqa: A001
author = "ReproNim Team"

# The full version, including alpha/beta/rc tags
version = reprostim.__about__.__version__
release = reprostim.__about__.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = []


autodoc_default_options = {
    "members": True,
    "undoc-members": True,
}

napoleon_google_docstring = False
napoleon_numpy_docstring = True
default_role = "py:obj"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
# html_theme = 'alabaster'
# html_static_path = ['_static']

# configure myst_parser

#
# myst_enable_extensions = [
#     "substitution",
# ]
#
# Note: in .md use {{ key1 }}
#
# myst_substitutions = {
#   "key1": "Value1"
# }
#

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

suppress_warnings = ["myst.header"]

# def on_source_read(app, docname, source):
#     print("$1%-"+docname)
#     if docname == "overview/intro":
#         print("[CONTENT] "+source[0])

# def on_include_read(app, relative_path, parent_docname, content):
#     print("$2% -" + content)

# def setup(app):
#     app.connect('source-read', on_source_read)
#     app.connect('include-read', on_include_read)
