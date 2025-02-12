# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add the project's root directory to the Python path
sys.path.insert(0, os.path.abspath(".."))

# -- Project Information -----------------------------------------------------

project = "ALiteralNuker"
author = "literallysnowy"
release = "1.1.0"  # Change this to match your version

# -- General Configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",    # Auto-generate documentation from docstrings
    "sphinx.ext.napoleon",   # Support Google-style docstrings
    "sphinx.ext.viewcode",   # Include highlighted source code in the docs
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- HTML Output -------------------------------------------------------------

html_theme = "sphinx_rtd_theme"  # Use Read the Docs theme
html_static_path = ["_static"]

# -- Options for PDF/EPUB Output ---------------------------------------------

latex_elements = {
    "papersize": "a4paper",
    "pointsize": "11pt",
}

epub_show_urls = "footnote"
