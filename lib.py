"""Front-end functions which utilize libc optimized lower-level helpers."""

from abc import ABCMeta, abstractproperty
from typing import Union

import libc


def _get_opener(filename: str):
    """Helper to get the opener type based upon the filename."""
    import pathlib
    path = pathlib.Path(filename)
    if not path.is_file():
        raise OSError(f'Filename "{filename}" does not exist.')
    extension = path.suffix
    if extension == '.gz':
        import gzip
        opener = gzip.open
    else:
        opener = open
    return opener


def read_file(filename: str, opener=None, mode: str = 'rt', *args, **kwargs) -> str:
    """Generator to read a file and return one line at a time."""
    opener = opener or _get_opener(filename)
    with opener(filename, mode=mode, errors='ignore', *args, **kwargs) as handle:
        for line in handle:
            yield line


def process_file(filename: str, plugins: list, opener=None, *args, **kwargs) -> Union[str, dict, list]:
    """Process a file based upon the given plugins.

    There are three types of plugins:
    1. Match a single line, don't parse it (use simple line filters and/or regex to filter).
    2. Match a single line, regex into groups.
    3. Match a multiline group with a defined start/end pattern (use simple line filters and/or regex for start/end).
    """
    import re
    file_reader = read_file(filename=filename, opener=opener, *args, **kwargs)
    multiline_buffer = {}
    # Precompile all regex patterns if applicable:
    for plugin in plugins:
        expressions = getattr(plugin, 'expressions', None)
        if expressions:
            plugin.compiled_expressions = tuple([re.compile(expression) for expression in expressions])
    for line in file_reader:
        for plugin in plugins:
            # Simple line match first.
            if isinstance(plugin, SimpleLineFilter):
                if libc.patterns_in_line(line=line, patterns=plugin.patterns):
                    yield line
            elif isinstance(plugin, MultiLineFilter):
                if libc.patterns_in_line(line=line, patterns=plugin.patterns):
                    plugin_name = plugin.__class__.__name__
                    if plugin_name not in multiline_buffer:
                        multiline_buffer[plugin_name] = []
                    multiline_buffer[plugin_name].append(line)
            elif isinstance(plugin, NamedGroupLineFilter):
                if not libc.patterns_in_line(line=line, patterns=plugin.patterns):
                    continue
                if not libc.regexes_match_line(line=line, expressions=plugin.compiled_expressions):
                    continue
                group_dict = libc.get_regex_groups(line=line, expressions=plugin.compiled_expressions)
                for key, parser in plugin.data_types.items():
                    raw = group_dict.get(key)
                    if raw is None:
                        value = None
                    else:
                        value = parser(raw)
                    group_dict[key] = value
                yield group_dict
    # Post-processing (multiline_buffer contents):
    if multiline_buffer:
        plugin_by_name = {plugin.__class__.__name__: plugin for plugin in plugins}
        for plugin_name, lines in multiline_buffer.items():
            plugin = plugin_by_name[plugin_name]
            for group in libc.get_multiline_patterns(lines=lines, start=plugin.start, end=plugin.end):
                yield group


class Plugin(object, metaclass=ABCMeta):
    """Base metaclass for other plugin types to build upon."""

    patterns: tuple = abstractproperty(None)
    expressions: tuple = abstractproperty(None)


class SimpleLineFilter(Plugin):
    """A plugin which just matches a single line and doesn't process it."""


class MultiLineFilter(Plugin):
    """A plugin which just matches a single line and doesn't process it."""

    start: str = abstractproperty(None)
    end: str = abstractproperty(None)


class NamedGroupLineFilter(Plugin):
    """A plugin which matches a single line and then uses named groups from the regex to structure the data."""

    data_types: dict = abstractproperty(None)
