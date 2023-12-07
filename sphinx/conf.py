# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import importlib.metadata

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = 'asynckivy-ext-queue'
copyright = '2023, Mitō Nattōsai'
author = 'Mitō Nattōsai'
release = importlib.metadata.version(project)


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    # 'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    # 'sphinx_tabs.tabs',

]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
language = 'en'
add_module_names = False
gettext_auto_build = False
gettext_location = False


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "furo"
html_static_path = ['_static']
# html_theme_options = {
#     "use_repository_button": True,
#     "repository_url": r"https://github.com/asyncgui/asynckivy-ext-queue",
#     "use_download_button": False,
# }


# -- Options for todo extension ----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html#configuration
todo_include_todos = True


# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'kivy': ('https://kivy.org/doc/master', None),
    # 'trio': ('https://trio.readthedocs.io/en/stable/', None),
    # 'trio_util': ('https://trio-util.readthedocs.io/en/latest/', None),
    'asyncgui': ('https://asyncgui.github.io/asyncgui/', None),
    'asynckivy': ('https://asyncgui.github.io/asynckivy/', None),
}


# -- Options for autodoc extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration
autodoc_mock_imports = ['kivy', ]
autodoc_member_order = 'bysource'

autodoc_default_options = {
   'members': True,
   'undoc-members': True,
   'no-show-inheritance': True,
   'special-members': "__aiter__",
}


def modify_signature(app, what: str, name: str, obj, options, signature, return_annotation: str,
                     prefix="asynckivy_ext.queue.",
                     len_prefix=len("asynckivy_ext.queue."),
                     group1={'QueueState', },
                     ):
    if not name.startswith(prefix):
        return (signature, return_annotation, )
    name = name[len_prefix:]
    if name in group1:
        print(f"Hide the signature of {name!r}")
        return ('', return_annotation)
    return (signature, return_annotation, )


def setup(app):
    app.connect('autodoc-process-signature', modify_signature)
