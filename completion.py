from lsprotocol import types
from configuration import config

from server import server
from log import log

from utils import (
    get_toml_section,
    get_nested_dict_value
)

@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=["=", ".", "["])
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
        6. On partially completed values within a section after the equal sign
            [window]
            dynamic_title = fal<autocomplete requested>
        7. On an empty line before the first section e.g.
            <start of file>
            [<autocomplete requested>
    Unhandled secnarios:
        1. Line is "illegitimate_key = <autocomplete requested>"
        2. Line is "illegitimate_unfinished_key<autocomplete requested>"
        * Both of these cases if a job for diagnostics and/or code_action*
    Args:
        params: Type completion parameters from pygls used to get the current line number
    Returns:
        A list of strings that will be provided as the completion options

    """
    document = server.workspace.get_text_document(params.text_document.uri)

    current_line = document.lines[params.position.line].strip()

    try:
        # Get section (or partial section) as period delimited values
        current_section = get_toml_section(params.position.line, document.lines)
        section_value_space = get_nested_dict_value(config, current_section)
        completion_options = None

        if current_line and current_line[0] == "[":
            # We are completing a section line
            completion_options = section_value_space
        else:
            # We are completing an entry line
            key = current_line.split("=")[0].strip()
            value = None
            if len(current_line.split("=")) == 2:
                value = current_line.split("=")[1].strip()

            if value or (key in section_value_space):
                completion_options = section_value_space[key]
            else:
                completion_options = section_value_space

        return [types.CompletionItem(label=opt) for opt in completion_options if None != opt]

    except KeyError as e:
        log.error(e)
        return []
    except IndexError as e:
        log.error(e)
        return []

if __name__ == "__main__":
    server.start_io()
