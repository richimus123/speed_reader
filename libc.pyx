"""Cython optimized filtering and related logic."""

cimport cython

# cython: embedsignature=True
# CAVEAT: The above ensures that docstrings are properly formatted when imported.


cpdef bint patterns_in_line(str line, tuple patterns):
    """Return if any of the patterns is in the line."""
    cpdef bint matched = False
    cpdef int index, num_patterns = len(patterns)
    cpdef str pattern
    for index in range(num_patterns):
        pattern = patterns[index]
        if pattern in line:
            matched = True
            break
    return matched


cpdef bint regexes_match_line(str line, tuple expressions):
    """Return if any of the regex patterns match the line."""
    cpdef bint matched = False
    for expression in expressions:
        if expression.match(line):
            matched = True
            break
    return matched


cpdef bint regexes_search_line(str line, tuple expressions):
    """Return if any of the regex patterns have results while searching the line."""
    cpdef bint matched = False
    for expression in expressions:
        if expression.search(line):
            matched = True
            break
    return matched


cpdef dict get_regex_groups(str line, tuple expressions):
    """Get regular expression groups from a line, if it matches any of the given regular expressions."""
    cpdef dict group = {}
    for expression in expressions:
        matched = expression.match(line)
        if not matched:
            continue
        group = dict(matched.groupdict())
    return group


cpdef list get_multiline_patterns(list lines, str start, str end):
    """Get lines between a start and end pattern."""
    cpdef bint started = False
    cpdef list group = []
    cpdef list groups = []
    cpdef str line
    cpdef int index
    cpdef int num_lines = len(lines)
    for index in range(num_lines):
        line = lines[index]
        if not started:
            if start in line:
                started = True
        if started:
            # The group of lines has ended.
            if end in line:
                started = False
            group.append(line)
            if not started:
                groups.append(group)
                group = []
    if group:
        groups.append(group)
    return groups
