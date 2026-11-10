"""Static type checks for IniConfig.get / SectionWrapper.get overloads.

Never executed; checked by mypy only.
"""

from __future__ import annotations

from typing_extensions import assert_type

from iniconfig import IniConfig
from iniconfig import SectionWrapper


def check_iniconfig_get(c: IniConfig) -> None:
    assert_type(c.get("s", "k"), str | None)
    assert_type(c.get("s", "k", convert=int), int | None)
    assert_type(c.get("s", "k", None, int), int | None)
    assert_type(c.get("s", "k", default=None, convert=int), int | None)
    assert_type(c.get("s", "k", "d"), str)
    assert_type(c.get("s", "k", 0), str | int)
    assert_type(c.get("s", "k", default=0), str | int)
    assert_type(c.get("s", "k", 0, int), int)
    assert_type(c.get("s", "k", 0.5, convert=int), int | float)
    # A callable passed positionally is the default, not convert.
    assert_type(c.get("s", "k", int), str | type[int])


def check_section_get(s: SectionWrapper) -> None:
    assert_type(s.get("k"), str | None)
    assert_type(s.get("k", convert=int), int | None)
    assert_type(s.get("k", None, int), int | None)
    assert_type(s.get("k", "d"), str)
    assert_type(s.get("k", 0), str | int)
    assert_type(s.get("k", 0, int), int)
    assert_type(s.get("k", 0.5, convert=int), int | float)
    # A callable passed positionally is the default, not convert.
    assert_type(s.get("k", int), str | type[int])
