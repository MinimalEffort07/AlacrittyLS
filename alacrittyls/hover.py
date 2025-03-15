from log import log
from server import server
from configuration import (
    config_descriptions,
    config,
)
from utils import (
    get_toml_section,
    get_current_word,
)

from lsprotocol import types
from pygls.lsp.server import LanguageServer

@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: types.HoverParams):
    pos = params.position
    document_uri = params.text_document.uri
    document = ls.workspace.get_text_document(document_uri)

    line = document.lines[pos.line]

    word = get_current_word(line, pos.character).strip()
    if not word or word == "":
        return

    word_is_section = False
    if word[0] == "[":
        word_is_section = True
        word = word.strip("[]")

    log.debug(f"got word: {word}")

    toml_section = get_toml_section(pos.line, document.lines)
    if toml_section not in config or word_is_section:
        key = word
    else:
        key = toml_section + "." + word

    log.debug(f"key: {key}")

    hover_content = [ config_descriptions[key] ]

    return types.Hover(
        contents=types.MarkupContent(
            kind=types.MarkupKind.Markdown,
            value="\n".join(hover_content),
        ),
        range=types.Range(
            start=types.Position(line=pos.line, character=0),
            end=types.Position(line=pos.line + 1, character=0),
        ),
    )
