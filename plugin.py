import os
from pylsp import hookimpl, lsp
from memestra import memestra

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
            deprecated_uses = memestra(
                code,
                decorator=(settings.get('decorator_module'),
                           settings.get('decorator_function')),
                reason_keyword=settings.get('reason_keyword'),
                recursive=settings.get('recursive'),
                cache_dir=settings.get('cache_dir'),
                search_paths=search_paths)
            # calling format text_that is defined below
            diagnostics = format_text(deprecated_uses, diagnostics)
    except SyntaxError as e:
        logger.error('Syntax error at {} - {} ({})', e.line, e.column, e.message)
        raise e
    
    return diagnostics

def format_text(deprecated_uses, diagnostics):
    # Formatting the error messages that comes up this is what is returned. I was going to 
    # try to remove as much as I can but the line number requires memestra that parses to return
    # the error chracters (line number)
    for fname, fd, lineno, colno, reason in deprecated_uses:
        err_range = {
            'start': {'line': lineno - 1, 'character': colno},
            'end': {'line': lineno - 1, 'character': colno + len(fname)},
        }
        if reason and reason != "reason":
            diagnostics.append({
                'source': 'memestra',
                'range': err_range,
                'message': "HELLO WORLD! you were trying to use " + fname + " here. But you should know " + reason,
                'severity': lsp.DiagnosticSeverity.Information,
            })
        else:
            diagnostics.append({
                'source': 'memestra',
                'range': err_range,
                'message': "HELLO WORLD! you were trying to use " + fname + " here.",
                'severity': lsp.DiagnosticSeverity.Information,
            })
    return diagnostics
