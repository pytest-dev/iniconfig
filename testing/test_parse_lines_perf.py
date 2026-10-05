"""Regression tests for the O(n^2) line-continuation bug in parse_lines().

Each continuation line used to be merged into the accumulated value with
f"{last.value}\n{data}", which rebuilds and copies the entire accumulated
string on every single continuation line. For a value built from N
continuation lines that's O(N) work per line, O(N^2) total - confirmed
locally: 50k lines ~1.6s, 100k lines ~7.7s, 200k lines ~32.6s, consistent
with quadratic scaling, not linear.

The fix accumulates fragments in a list and joins once. test_matches_oracle
below is a differential test against a reimplementation of the *original*
algorithm, run across a range of edge cases (empty values, falsy
continuations interleaved with real ones, continuations immediately after
section headers, etc.) to make sure the rewrite didn't change any of the
original's slightly subtle falsy-value-replaces-rather-than-concatenates
semantics.
"""

from __future__ import annotations

import time

import pytest

from iniconfig._parse import ParsedLine
from iniconfig._parse import _parseline
from iniconfig._parse import parse_lines as current_parse_lines
from iniconfig.exceptions import ParseError


def oracle_parse_lines(
    path: str,
    line_iter: list[str],
    *,
    strip_inline_comments: bool = False,
    strip_section_whitespace: bool = False,
) -> list[ParsedLine]:
    """The original O(n^2) implementation, kept here only as a test oracle."""
    result: list[ParsedLine] = []
    section = None
    for lineno, line in enumerate(line_iter):
        name, data = _parseline(
            path, line, lineno, strip_inline_comments, strip_section_whitespace
        )
        if name is not None and data is not None:
            result.append(ParsedLine(lineno, section, name, data))
        elif name is not None and data is None:
            if not name:
                raise ParseError(path, lineno, "empty section name")
            section = name
            result.append(ParsedLine(lineno, section, None, None))
        elif name is None and data is not None:
            if not result:
                raise ParseError(path, lineno, "unexpected value continuation")
            last = result.pop()
            if last.name is None:
                raise ParseError(path, lineno, "unexpected value continuation")
            if last.value:
                last = last._replace(value=f"{last.value}\n{data}")
            else:
                last = last._replace(value=data)
            result.append(last)
    return result


DIFFERENTIAL_CASES = [
    "key=value",
    "key=",
    "key=\n value\n more",
    "key=\n\n value",
    "key=first\n second\n third",
    "key=\n\n\n value\n\n another",
    "[section]\nkey=1\nkey2=\n cont1\n cont2",
    "[s]\nkey=\n\nkey2=val",
    "key=value\n cont\n\n more\n\n",
    "key1=a\nkey2=b\n cont_of_b\nkey3=c",
]


@pytest.mark.parametrize("data", DIFFERENTIAL_CASES)
def test_matches_oracle(data: str) -> None:
    lines = data.split("\n")
    expected = oracle_parse_lines("x", lines)
    actual = current_parse_lines("x", lines)
    assert actual == expected


@pytest.mark.parametrize("data", DIFFERENTIAL_CASES)
def test_matches_oracle_with_options(data: str) -> None:
    lines = data.split("\n")
    for strip_comments in (False, True):
        for strip_ws in (False, True):
            expected = oracle_parse_lines(
                "x",
                lines,
                strip_inline_comments=strip_comments,
                strip_section_whitespace=strip_ws,
            )
            actual = current_parse_lines(
                "x",
                lines,
                strip_inline_comments=strip_comments,
                strip_section_whitespace=strip_ws,
            )
            assert actual == expected


def test_matches_oracle_error_cases() -> None:
    error_cases = [
        " leading continuation with nothing before it",
        "[section]\n continuation right after a header",
    ]
    for data in error_cases:
        lines = data.split("\n")
        oracle_exc = None
        actual_exc = None
        try:
            oracle_parse_lines("x", lines)
        except ParseError as e:
            oracle_exc = (e.lineno, str(e))
        try:
            current_parse_lines("x", lines)
        except ParseError as e:
            actual_exc = (e.lineno, str(e))
        assert oracle_exc is not None, f"oracle did not raise for {data!r}"
        assert actual_exc == oracle_exc


def test_long_continuation_is_linear_not_quadratic() -> None:
    """Confirms the fix: previously quadratic, now near-linear scaling."""

    def time_parse(n: int) -> float:
        lines = ["key=start"] + ["    " + "x" * 50] * n
        start = time.perf_counter()
        current_parse_lines("x", lines)
        return time.perf_counter() - start

    # Warm up (import/JIT-ish effects).
    time_parse(1000)

    t_small = time_parse(20_000)
    t_large = time_parse(80_000)  # 4x the lines

    # Quadratic scaling would make this ~16x slower; linear should be
    # roughly 4x. Allow generous headroom for noise, but this comfortably
    # distinguishes linear from quadratic.
    ratio = t_large / max(t_small, 1e-6)
    assert ratio < 8, (
        f"scaling looks quadratic, not linear: {t_small=:.4f}s {t_large=:.4f}s "
        f"ratio={ratio:.2f} (expected well under 8 for ~4x more input)"
    )
