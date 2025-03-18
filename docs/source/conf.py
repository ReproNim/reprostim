# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# import reprostim

project = "ReproStim"
copyright = "2020-%Y, ReproNim Team"  # noqa: A001
author = "ReproNim Team"

# The full version, including alpha/beta/rc tags
version = "TODO_version"  # reprostim.__version__
release = "TODO_release"  # reprostim.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
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
