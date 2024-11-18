from log import log

def get_toml_section(line_number: int, document: list[str]) -> str:
    """
    Gets the first TOML section definition encoutered, beginning from the current line and
    searching upwards.

    Args:
        line_number: The current line being edited in the file
        document: List of strings representing the lines of a document
    Returns:
        A string representing the TOML section value without the enclosing square brackes, or an
        empty string on failure.
    """
    while line_number >= 0 and document[line_number][0] != "[":
        log.debug(f"Not the section line: {line_number}: {document[line_number]}".encode("unicode_escape").decode("utf-8"))
        line_number -= 1

    if line_number < 0:
        log.debug(
            "Reached beginning of file looking for section line but couldn't find it"
        )
        return ""

    # Do two strips, the first targeting whitespace and the second to target the toml square
    # brackets. Could do it in one but don't want to have to deal with all the different whitespace
    # characters that could be at the end of the line e.g. ^M on windows.
    section = document[line_number].strip().strip("[]")
    log.debug(f"Section line: {section} , on line number: {line_number}")

    return section

def get_nested_dict_value(dictionary: dict, keys: str):
    """
    Indexes into a nested dictionary 'dictionary', using a period separated string of key values.

    E.g.

    Dict: { "Level1": { "Level2": { "Level3": "Value3" } } }

    Keys = "Level1", returns { "Level2": { "Level3": "Value3" } }
    Keys = "Level1.Level2", returns { "Level3": "Value3" }
    Keys = "Level1.Level2.Level3", returns "Value3"

    If keys contain a value that doesn't exist, return back the level above what was trying to be
    indexed into.

    e.g.

    Keys = "Level1.Level6", returns { "Level2": { "Level3": "Value3" } }

    Essentially the keys string is truncated at the first instance of a bad value.

    Args:
        dictionary: Dictionary to index into
        keys: Period seperated string of nested key values
    Returns:
        A value from the dictionary parameter
    """
    if not keys:
        return dictionary

    key_components = keys.split(".")
    log.debug(f"components: {key_components}")

    key_depth = len(key_components)
    log.debug(f"depth: {key_depth}")

    level = 0
    sub_section = dictionary

    while level < key_depth:
        log.debug(f"level: {level}, key_components: {key_components}, sub_section: {sub_section}")
        if key_components[level] not in sub_section:
            return sub_section
        else:
            sub_section = sub_section[key_components[level]]
            log.debug(f"sub_section: {sub_section}")
            level += 1

    return sub_section

