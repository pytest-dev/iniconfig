"""Property-based tests for iniconfig parsing."""

import string

import pytest
from hypothesis import example
from hypothesis import given
from hypothesis import strategies as st

from iniconfig import IniConfig
from iniconfig import ParseError
from iniconfig._parse import split_lines

SEPARATORS = "\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029"
NEWLINES = st.sampled_from(["\n", "\r\n", "\r"])

name_text = st.text(
    alphabet=string.ascii_letters + string.digits + "_-.", min_size=1, max_size=10
)
# value lines: printable, no comment chars, no surrounding whitespace
value_line = (
    st.text(
        alphabet=string.ascii_letters + string.digits + " _-./=:",
        min_size=1,
        max_size=20,
    )
    .map(str.strip)
    .filter(bool)
)
values = st.lists(value_line, min_size=0, max_size=4)
config_model = st.dictionaries(
    name_text,
    st.dictionaries(name_text.filter(lambda n: ":" not in n), values, max_size=4),
    max_size=4,
)


def render(model: dict[str, dict[str, list[str]]], nl: str) -> str:
    out = []
    for section, items in model.items():
        out.append(f"[{section}]")
        for key, lines in items.items():
            out.append(f"{key} = {lines[0] if lines else ''}")
            out.extend(f"    {line}" for line in lines[1:])
    return nl.join(out) + nl


@given(config_model, NEWLINES)
def test_roundtrip(model: dict[str, dict[str, list[str]]], nl: str) -> None:
    data = render(model, nl)
    config = IniConfig.parse("x.ini", data=data, strip_inline_comments=False)
    assert {s.name: dict(s.items()) for s in config} == {
        s: {k: "\n".join(v) for k, v in items.items()} for s, items in model.items()
    }
    # lineof agrees with the line the key was written on (1-based)
    rendered = data.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for s, items in model.items():
        for k in items:
            lineno = config.lineof(s, k)
            assert lineno is not None
            assert rendered[lineno - 1].startswith(f"{k} =")


@given(st.text())
@example("[a]\nk = v\n\x0c[b]\n")
@example("[a]\nk = v\n\u2028x = 1\n")
def test_never_crashes(data: str) -> None:
    try:
        IniConfig.parse("x.ini", data=data)
    except ParseError:
        pass


def _normalize(data: str) -> str:
    return data.replace("\r\n", "\n").replace("\r", "\n")


def _is_page_break(line: str) -> bool:
    return line.strip("\x0c") == ""


@given(st.text())
def test_split_lines_invariants(data: str) -> None:
    raw_lines = _normalize(data).split("\n")
    bad = [
        i
        for i, line in enumerate(raw_lines)
        if not _is_page_break(line) and any(c in SEPARATORS for c in line)
    ]
    if bad:
        with pytest.raises(ParseError) as excinfo:
            split_lines("x.ini", data)
        assert excinfo.value.lineno == bad[0]
        return
    lines = split_lines("x.ini", data)
    assert "".join(lines) == _normalize(data)
    assert all(line.endswith("\n") for line in lines[:-1])


@given(config_model, NEWLINES, NEWLINES)
def test_newline_style_invariance(
    model: dict[str, dict[str, list[str]]], a: str, b: str
) -> None:
    pa = IniConfig.parse("x.ini", data=render(model, a))
    pb = IniConfig.parse("x.ini", data=render(model, b))
    assert pa.sections == pb.sections
    assert pa._sources == pb._sources


fragments = st.sampled_from(
    [
        "[",
        "]",
        "=",
        ":",
        "#",
        ";",
        " ",
        "\t",
        "a",
        "b",
        "\n",
        "\r",
        "\r\n",
        "\ufeff",
        "\xa0",
    ]
    + list(SEPARATORS)
)
ini_like = st.lists(fragments, max_size=40).map("".join)


@given(ini_like)
def test_never_crashes_structured(data: str) -> None:
    try:
        c = IniConfig.parse("x.ini", data=data)
    except ParseError:
        return
    for s in c:
        for k in s:
            assert c.lineof(s.name, k) is not None


@given(
    config_model.filter(bool),
    st.sampled_from(SEPARATORS),
    st.integers(min_value=0),
    NEWLINES,
)
def test_injected_separator_errors_or_is_harmless(
    model: dict[str, dict[str, list[str]]], sep: str, pos: int, nl: str
) -> None:
    data = render(model, nl)
    pos %= len(data) + 1
    injected = data[:pos] + sep + data[pos:]
    expected = IniConfig.parse("x.ini", data=data, strip_inline_comments=False)
    try:
        got = IniConfig.parse("x.ini", data=injected, strip_inline_comments=False)
    except ParseError:
        return
    assert got.sections == expected.sections
