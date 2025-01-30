# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(".."))

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

project = "contacts"
copyright = "2025, D"
author = "D"

# -- General configuration ---------------------------------------------------
# <https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration>

extensions = ["sphinx.ext.autodoc"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# <https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output>

html_theme = "nature"
html_static_path = ["_static"]
