from typing import Literal, TypeAlias

__all__ = ["PveBool"]

PveBool: TypeAlias = Literal[0, 1] | bool
"""A boolean as PVE sends it.

Perl has no booleans: unless a handler explicitly returns JSON::true or
JSON::false, or is implemented in Rust, PVE sends documented booleans as 0/1.
Values read from configuration files are always numbers
(PVE::SectionConfig::check_value). Truth tests and ``== True`` work on both
forms; models returned by ``method.model(...)`` convert them to ``bool``.
"""
