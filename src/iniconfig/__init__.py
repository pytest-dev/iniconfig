""" brain-dead simple parser for ini-style files.
(C) Ronny Pfannschmidt, Holger Krekel -- MIT licensed
"""
from __future__ import annotations
from typing import (
    Callable,
    Iterator,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
    TYPE_CHECKING,
    NoReturn,
    NamedTuple,
    overload,
    cast,
)


if TYPE_CHECKING:
    from typing_extensions import Final

__all__ = ["IniConfig", "ParseError"]

COMMENTCHARS = "#;"

_D = TypeVar("_D")
_T = TypeVar("_T")


_str_default = cast(Callable[[str], str], str)


class _ParsedLine(NamedTuple):
    lineno: int
    section: str | None
    name: str | None
    value: str | None


class ParseError(Exception):
    path: Final[str]
    lineno: Final[int]
    msg: Final[str]

    def __init__(self, path: str, lineno: int, msg: str):
        Exception.__init__(self, path, lineno, msg)
        self.path = path
        self.lineno = lineno
        self.msg = msg

    def __str__(self) -> str:
        return f"{self.path}:{self.lineno + 1}: {self.msg}"


class SectionWrapper:
    config: Final[IniConfig]
    name: Final[str]

    def __init__(self, config: IniConfig, name: str):
        self.config = config
        self.name = name

    def lineof(self, name: str) -> int | None:
        return self.config.lineof(self.name, name)

    def get(
        self,
        key: str,
        default: _D | None = None,
        convert: Callable[[str], _T] | None = None,
    ) -> _D | _T | str | None:
        return self.config.get(self.name, key, convert=convert, default=default)

    def __getitem__(self, key: str) -> str:
        return self.config.sections[self.name][key]

    def __iter__(self) -> Iterator[str]:
        section: Mapping[str, str] = self.config.sections.get(self.name, {})

        def lineof(key: str) -> int:
            return self.config.lineof(self.name, key)  # type: ignore

        yield from sorted(section, key=lineof)

    def items(self) -> Iterator[tuple[str, str]]:
        for name in self:
            yield name, self[name]


class IniConfig:
    path: Final[str]
    sections: Final[Mapping[str, Mapping[str, str]]]

    def __init__(
        self, path: str, data: str | None = None, encoding: str = "utf-8"
    ) -> None:
        self.path = str(path)  # convenience
        if data is None:
            with open(self.path, encoding=encoding) as fp:
                data = fp.read()

        tokens = self._parse(data.splitlines(True))

        self._sources = {}
        sections_data: dict[str, dict[str, str]]
        self.sections = sections_data = {}

        for lineno, section, name, value in tokens:
            if section is None:
                self._raise(lineno, "no section header defined")
            self._sources[section, name] = lineno
            if name is None:
                if section in self.sections:
                    self._raise(lineno, f"duplicate section {section!r}")
                sections_data[section] = {}
            else:
                if name in self.sections[section]:
                    self._raise(lineno, f"duplicate name {name!r}")
                assert value is not None
                sections_data[section][name] = value

    def _raise(self, lineno: int, msg: str) -> NoReturn:
        raise ParseError(self.path, lineno, msg)

    def _parse(self, line_iter: list[str]) -> list[_ParsedLine]:
        result: list[_ParsedLine] = []
        section = None
        for lineno, line in enumerate(line_iter):
            name, data = self._parseline(line, lineno)
            # new value
            if name is not None and data is not None:
                result.append(_ParsedLine(lineno, section, name, data))
            # new section
            elif name is not None and data is None:
                if not name:
                    self._raise(lineno, "empty section name")
                section = name
                result.append(_ParsedLine(lineno, section, None, None))
            # continuation
            elif name is None and data is not None:
                if not result:
                    self._raise(lineno, "unexpected value continuation")
                last = result.pop()
                if last.name is None:
                    self._raise(lineno, "unexpected value continuation")

                if last.value:
                    last = last._replace(value=f"{last.value}\n{data}")
                else:
                    last = last._replace(value=data)
                result.append(last)
        return result

    def _parseline(self, line: str, lineno: int) -> tuple[str | None, str | None]:
        # blank lines
        if iscommentline(line):
            line = ""
        else:
            line = line.rstrip()
        if not line:
            return None, None
        # section
        if line[0] == "[":
            realline = line
            for c in COMMENTCHARS:
                line = line.split(c)[0].rstrip()
            if line[-1] == "]":
                return line[1:-1], None
            return None, realline.strip()
        # value
        elif not line[0].isspace():
            try:
                name, value = line.split("=", 1)
                if ":" in name:
                    raise ValueError()
            except ValueError:
                try:
                    name, value = line.split(":", 1)
                except ValueError:
                    self._raise(lineno, "unexpected line: %r" % line)
            return name.strip(), value.strip()
        # continuation
        else:
            return None, line.strip()

    def lineof(self, section: str, name: str | None = None) -> int | None:
        lineno = self._sources.get((section, name))
        return None if lineno is None else lineno + 1

    @overload
    def get(
        self,
        section: str,
        name: str,
    ) -> str | None:
        ...

    @overload
    def get(
        self,
        section: str,
        name: str,
        convert: Callable[[str], _T],
    ) -> _T | None:
        ...

    @overload
    def get(
        self,
        section: str,
        name: str,
        default: None,
        convert: Callable[[str], _T],
    ) -> _T | None:
        ...

    @overload
    def get(
        self, section: str, name: str, default: _D, convert: None = None
    ) -> str | _D:
        ...

    @overload
    def get(
        self,
        section: str,
        name: str,
        default: _D,
        convert: Callable[[str], _T],
    ) -> _T | _D:
        ...

    def get(  # type: ignore
        self,
        section: str,
        name: str,
        default: _D | None = None,
        convert: Callable[[str], _T] | None = None,
    ) -> _D | _T | str | None:
        try:
            value: str = self.sections[section][name]
        except KeyError:
            return default
        else:
            if convert is not None:
                return convert(value)
            else:
                return value

    def __getitem__(self, name: str) -> SectionWrapper:
        if name not in self.sections:
            raise KeyError(name)
        return SectionWrapper(self, name)

    def __iter__(self) -> Iterator[SectionWrapper]:
        for name in sorted(self.sections, key=self.lineof):  # type: ignore
            yield SectionWrapper(self, name)

    def __contains__(self, arg: str) -> bool:
        return arg in self.sections


def iscommentline(line: str) -> bool:
    c = line.lstrip()[:1]
    return c in COMMENTCHARS
