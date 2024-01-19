from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

Row = dict[str, str]


class RowTransform(Protocol):
    def apply(self, row: Row) -> Row | None: ...

