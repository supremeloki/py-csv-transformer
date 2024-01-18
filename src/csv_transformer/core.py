from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

Row = dict[str, str]


class RowTransform(Protocol):
    def apply(self, row: Row) -> Row | None: ...


@dataclass(frozen=True)
class PipelineResult:
    rows: list[Row]
    dropped_count: int
    touched_columns: frozenset[str]


class TransformerError(Exception):
    pass


class UnknownColumnError(TransformerError):
    def __init__(self, column: str) -> None:
        super().__init__(f"column not found in header: {column!r}")


class DuplicateHeaderError(TransformerError):
    def __init__(self, columns: list[str]) -> None:
        super().__init__(f"duplicate headers: {columns}")


@dataclass
class Transformer:
    steps: list[RowTransform] = field(default_factory=list)

    def add_step(self, step: RowTransform) -> "Transformer":
        self.steps.append(step)
        return self

    def run(self, rows: list[Row]) -> PipelineResult:
        kept: list[Row] = []
        dropped = 0
        touched: set[str] = set()
        for row in rows:
            current = dict(row)
            for step in self.steps:
                result = step.apply(current)
                if result is None:
                    dropped += 1
                    break
                touched.update(result.keys() - current.keys())
                touched.update(key for key in result if result[key] != current.get(key))
                current = result
            else:
                kept.append(current)
        return PipelineResult(rows=kept, dropped_count=dropped, touched_columns=frozenset(touched))


class ColumnMapper:
    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = dict(mapping)
        self._renames = {
            src: dst
            for src, dst in self._mapping.items()
            if dst != src
        }

    @property
    def required_source_columns(self) -> set[str]:
        return set(self._mapping)

    def apply(self, row: Row) -> Row | None:
        collision_sources = [
            (src, dst)
            for src, dst in self._renames.items()
            if dst in row and src != dst
        ]
        for src, dst in collision_sources:
            if src in row:
                raise DuplicateHeaderError([dst])
        renamed = {self._mapping.get(k, k): v for k, v in row.items()}
        seen: set[str] = set()
        for key in renamed:
            if key in seen:
                raise DuplicateHeaderError([key])
            seen.add(key)
        return renamed


class DefaultValueFiller:
    def __init__(self, defaults: dict[str, str], columns: set[str]) -> None:
        self._defaults = defaults
        self._columns = columns
        missing = set(defaults) - columns
        if missing:
            raise UnknownColumnError(sorted(missing)[0])

    def apply(self, row: Row) -> Row | None:
        filled = dict(row)
        for column, value in self._defaults.items():
            filled.setdefault(column, value)
        return filled


class ExpressionCast:
    _CASTERS: dict[str, Callable[[str], object]] = {
        "int": int,
        "float": float,
        "upper": str.upper,
        "lower": str.lower,
        "strip": str.strip,
    }

    def __init__(self, casts: dict[str, str], columns: set[str]) -> None:
        self._casts: dict[str, Callable[[str], object]] = {}
        for column, name in casts.items():
            if column not in columns:
                raise UnknownColumnError(column)
            caster = self._CASTERS.get(name)
            if caster is None:
                raise TransformerError(f"unknown cast: {name!r}")
            self._casts[column] = caster

    def apply(self, row: Row) -> Row | None:
        casted = dict(row)
        for column, caster in self._casts.items():
            try:
                casted[column] = caster(casted[column])
            except (KeyError, ValueError) as exc:
                raise TransformerError(f"cast failed for {column!r}: {exc}") from exc
        return casted


class RowFilter:
    def __init__(self, predicate: Callable[[Row], bool]) -> None:
        self._predicate = predicate

    def apply(self, row: Row) -> Row | None:
        return row if self._predicate(row) else None


class ColumnDropper:
    def __init__(self, drop: set[str]) -> None:
        self._drop = drop

    def apply(self, row: Row) -> Row | None:
        return {k: v for k, v in row.items() if k not in self._drop}
