from pygls.server import LanguageServer
from lsprotocol import types
import logging

logging.basicConfig(filename='pygls.log', filemode='w', level=logging.DEBUG)
log = logging.getLogger(__name__)

state = {"general": {"import": [None], "working_directory": ["'None'", None], "live_config_reload": ["true", "false"], "ipc_socket": ["true", "false"]}}
server = LanguageServer("Alacritty-LanguageServer", "v0.1")

def get_section(params, document):

    line = params.position.line

    while(line >= 0 and document.lines[line][0] != "["):
        log.debug(f"Not the section line: {line}: {document.lines[line]}")
        line -= 1
 
    if line < 0:
        log.error("Reached beginning of file looking for section line but couldn't find it")
        return None

    # Do two strips, the first targeting whitespace and the second to target the toml square 
    # brackets. Could do it in one but don't want to have to deal with all the different whitespace
    # characters that could be at the end of the line e.g. ^M on windows.
    section = document.lines[line].strip().strip('[]')
    log.debug(f"Section line: {section} , on line number: {line}")

    section_components = section.split('.')
    log.debug(f"components: {section_components}")

    dictionary_depth = len(section_components)
    log.debug(f"depth: {dictionary_depth}")

    level = 0
    sub_section = state
    try:
        while(level < dictionary_depth):
            sub_section = sub_section[section_components[level]]
            log.debug(f"sub_section: {sub_section}")
            level += 1
    except:
        log.error(f"Syntax error in section definition: {'.'.join(section_components)}")
        return None

    return sub_section
    
@server.feature(types.TEXT_DOCUMENT_COMPLETION, types.CompletionOptions(trigger_characters=["="]))
def completions(params: types.CompletionParams):
    document = server.workspace.get_document(params.text_document.uri)
    current_line = document.lines[params.position.line].strip()

    current_line_components = current_line.split()
    key = current_line_components[0] if len(current_line_components) > 0 else None
    if None == key:
        log.debug("Key is None")
    else:
        log.debug(f"Completing for key: {key}")

    options = get_section(params, document)

    labels = options[key] if key != None else options

    try:
        if type(labels) == type([]):
            log.debug("Leaf key")
            return [types.CompletionItem(label=opt) for opt in labels if None != opt ] 
        elif type(labels) == type({}):
            log.debug("non leaf key")
            return [types.CompletionItem(label=opt) for opt in labels.keys() if None != opt ] 
        else:   
            log.debug("what")
    except:
        log.debug(f"Couldn't get labels")       
        return []

    # return [types.CompletionItem(label="lool"), types.CompletionItem(label="sick")]

if __name__ == "__main__":
    server.start_io()
