# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os

# import sys
# sys.path.insert(0, os.path.abspath("../../src"))

# Set environment variable to specify special sphinx or rtd build environment
os.environ["REPROSTIM_DOCS"] = "True"

from docutils import nodes
from sphinx.transforms import SphinxTransform

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

# pyaudio is not installed on RTD
autodoc_mock_imports = [
    "pyaudio",
    "sounddevice",
    "psychopy",
    "psutil",
    "qrcode",
    "pyzbar",
]

napoleon_google_docstring = False
napoleon_numpy_docstring = True
default_role = "py:obj"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "furo"
html_theme = "alabaster"
html_static_path = ["_static"]
html_context = {
    "version": version,
    "release": release,
}
html_sidebars = {
    "**": [
        "about.html",
        "searchfield.html",
        "navigation.html",
        "index.html",
    ]
}
html_logo = "_static/images/logo256.png"

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

suppress_warnings = [
    "myst.header",
    "myst.xref_missing",  # Note: to be fixed in README.md relative link
]

# def on_source_read(app, docname, source):
#     print("$1%-"+docname)
#     if docname == "overview/intro":
#         print("[CONTENT] "+source[0])

# def on_include_read(app, relative_path, parent_docname, content):
#     print(f"ON_INCLUDE_READ: {content}")

# define URI mapping if any to substitute/fix some links
_URI_MAP = {
    "docs/images/clion_version_auto_inc.png": "../../../src/reprostim-capture/docs/images/clion_version_auto_inc.png",  # noqa
    "docs/images/project_structure.png": "../../../src/reprostim-capture/docs/images/project_structure.png",  # noqa
    # "./src/reprostim-capture/README.md" : "https://github.com/
    # ReproNim/reprostim/tree/master/src/reprostim-capture/README.md", #noqa
    # "./Parsing/repro-vidsort" : "https://github.com/
    # ReproNim/reprostim/tree/master/Parsing/repro-vidsort", #noqa
}


class UriTransform(SphinxTransform):
    default_priority = 500

    # replace URI link value if any
    def replace(self, node, attr):
        # if "attrs" in node  and "class" in node.attrs:
        #     print("CLASS=" + str(node.attrs["class"]))

        global _URI_MAP
        if attr in node:
            v = _URI_MAP.get(node[attr])
            if v:
                node[attr] = v
                # node["uri"] = v

    def apply(self):
        # for node in self.document.traverse(nodes.reference):
        #     self.replace(node, 'refuri')
        #     # self.replace(node, 'reftarget')

        for node in self.document.traverse(nodes.image):
            # print(f"image_uri={node['uri']}")
            self.replace(node, "uri")


def setup(app):
    #     app.connect('source-read', on_source_read)
    #     app.connect('include-read', on_include_read)
    app.add_transform(UriTransform)
    app.add_css_file("custom.css")
    # app.add_stylesheet('custom.css')
