from pygls.lsp.server import LanguageServer
from pygls.workspace.text_document import TextDocument
from lsprotocol import types
from typing import Union
from configuration import config
import logging

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(filename="pygls.log", filemode="w", level=logging.DEBUG, format=FORMAT)

log = logging.getLogger(__name__)

server = LanguageServer("Alacritty-LanguageServer", "v0.1")

def get_toml_section(params: types.CompletionParams, document: TextDocument) -> str:
    """
    Gets the first TOML section definition encoutered, beginning from the current line and
    searching upwards.

    Args:
        params: Type completion parameters from pygls used to get the current line number
        document: Text document object which contains a list of each line in the document being
        edited.
    Returns:
        A string representing the TOML section value without the enclosing square brackes, or an
        empty string on failure.
    """
    line = params.position.line

    while line >= 0 and document.lines[line][0] != "[":
        log.debug(f"Not the section line: {line}: {document.lines[line]}")
        line -= 1

    if line < 0:
        log.error(
            "Reached beginning of file looking for section line but couldn't find it"
        )
        return ""

    # Do two strips, the first targeting whitespace and the second to target the toml square
    # brackets. Could do it in one but don't want to have to deal with all the different whitespace
    # characters that could be at the end of the line e.g. ^M on windows.
    section = document.lines[line].strip().strip("[]")
    log.debug(f"Section line: {section} , on line number: {line}")

    return section

def get_nested_dict_value(dictionary: dict, keys: str):
    """
    Indexes into a nested dictionary 'dictionary', using a period separated string of key values.

    E.g.

    Dict: { "Level1": { "Level2": { "Level3": "Value3" } } }

    Keys = "Level1", returns { "Level2": { "Level3": "Value3" } }
    Keys = "Level1.Level2", returns { "Level3": "Value3" }
    Keys = "Level1.Level2.Level3", returns "Value3"

    Args:
        dictionary: Dictionary to index into
        keys: Period seperated string of nested key values
    Returns:
        A nested dictionary of value from the dictionary parameter
    Raises:
        KeyError: If 'keys' tries to index into a dictionary key that doesn't exist
        IndexError: If 'keys' tries to index into a dictionary key that doesn't exist
    """

    key_components = keys.split(".")
    log.debug(f"components: {key_components}")

    key_depth = len(key_components)
    log.debug(f"depth: {key_depth}")

    level = 0
    sub_section = dictionary

    try:
        while level < key_depth:
            sub_section = sub_section[key_components[level]]
            log.debug(f"sub_section: {sub_section}")
            level += 1
    except KeyError:
        raise KeyError(f"Minor mode doesn't exist")
    except IndexError:
        raise IndexError(f"Minor mode doesn't exist")

    return sub_section


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=["="])
)
def completions(params: types.CompletionParams) -> list:
    """
    Provides completion options for the current cursor position in the alacritty TOML configuration
    file.

    Handles completion:
        1. In a section definition e.g. [gene<autocomplete reqeusted>
        2. On an empty line within a section: e.g.
            [general]
            <autocomplete requested>
        3. On a partially completed key within a section e.g.
            [general]
            wor<autocomplete requested>
        4. On a completed key within a section e.g.
            [general]
            working_directory<autocomplete requested>
        5. On a completed key within a section after the equal sign e.g.
            [general]
            working_directory = <autocomplete requested>
        6. On partially completed values within a section
            [window]
            dynamic_title = fal<autocomplete requested>
        7. On an empty line before the first section e.g.
            <start of file>
            [<autocomplete requested>
    Args:
        params: Type completion parameters from pygls used to get the current line number
    Returns:
        A list of strings that will be provided as the completion options

    """
    document = server.workspace.get_text_document(params.text_document.uri)

    current_line = document.lines[params.position.line].strip()
    current_word = document.word_at_position(params.position).strip()

    try:
        # Get section as period delimited values
        section = get_toml_section(params, document)

        # Obtain the values from the config when you index sub-dictionaries accoridng to the period
        # delimited sectoin value
        section_values = get_nested_dict_value(config, section)

        # Cases we handle:
        # Case 1: Line is empty
        #   - Provide options as to valid keys in this section
        #
        # Case 2: Line is "legitimate_unfinished_key<looking for completion here>"
        #   - Provide completion options for valid keys that start with current work in this section
        #
        # Case 3: Line is "legitimate_key = <looking for completion here>"
        #   - Provide options as to valid values for this key
        #
        # Case 4: Line is "illegitimate_key = <looking for completion here>"
        #   - Job for "Code_Actions" portion of the LSP server
        #
        # Case 5: Line is "illegitimate_unfinished_key<looking for completion here>"
        #   - Job for "Code_Actions" portion of the LSP server

        options = None
        key, _, value = current_line.split("=")

        if current_word not in section_values:
            # Handles Cases 1 & 2
            if not current_word:
                log.debug("NULL")
            log.debug(f"::{current_word}::")
            options = section_values
        else:
            # Handles Case 3
            options = section_values[current_word]

        return [types.CompletionItem(label=opt) for opt in options if None != opt]

    except KeyError as e:
        log.error(e)
        return []
    except IndexError as e:
        log.error(e)
        return []

if __name__ == "__main__":
    server.start_io()
