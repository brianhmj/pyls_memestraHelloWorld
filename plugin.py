import os
from pylsp import hookimpl, lsp
# from memestra import memestra
from .parseImport import get_imports

import logging
# Setting up basic configuration, logging everything that has an ERROR level 
# Also found out through debugging that the logger that is defined here is NOT logger that prints
# to terminal when you run Jupyter Lab (Instead I think it's something to do with )
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Hookimpl is from pylsp, do not touch this. Setting helps with making sure that Memestra works.
# The pylsp hooks corresponds to Language Server Protocol messages
# can be found https://microsoft.github.io/language-server-protocol/specification
# https://github.com/python-lsp/python-lsp-server/blob/develop/pylsp/hookspecs.py
@hookimpl
def pylsp_settings():
    return {
        "plugins": {
            "pyls-memestra": {
                "enabled": True,
                "recursive": False,
                "decorator_module": "deprecated",
                "decorator_function": "deprecated",
                "reason_keyword": "reason",
                "cache_dir": None,
                "additional_search_paths": []
            }
        }
    }

# Find this corresponding hook in documentation
@hookimpl
def pylsp_lint(config, document):

    # Define vaiables here
    diagnostics = []

    # Set up settings and search paths (Using OS)
    settings = config.plugin_settings('pyls-memestra',
                                      document_path=document.path)
    search_paths = [os.path.dirname(os.path.abspath(document.path))]
    search_paths.extend(settings.get('additional_search_paths'))

    # try-except to catch any expections that rises
    try:
        with open(document.path, 'r') as code: #opens the current code in the backend for parsing
            importCases = get_imports(code)
            diagnostics = format_text(importCases, [])
    except SyntaxError as e:
        logger.error('Syntax error at {} - {} ({})', e.line, e.column, e.message)
        raise e
    
    return diagnostics

def format_text(import_cases, diagnostics):
    # Formatting the error messages that comes up this is what is returned. I was going to 
    # try to remove as much as I can but the line number requires memestra that parses to return
    # the error chracters (line number)
    if import_cases:
        for x in range(len(import_cases)):
            err_range = {
                'start': {'line': import_cases[x][3] - 1, 'character': import_cases[x][4]},
                'end': {'line': import_cases[x][3] - 1, 'character': import_cases[x][5]},
            }
            diagnostics.append({
                'source': 'Brian',
                'range': err_range,
                'message': "You have imported " + import_cases[x][1][0] + " here.",
                'severity': lsp.DiagnosticSeverity.Information,
            })

    return diagnostics
