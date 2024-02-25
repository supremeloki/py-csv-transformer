from __future__ import annotations

import csv
from pathlib import Path

from .core import DuplicateHeaderError, Row, TransformerError


class CsvSource:
    def __init__(self, path: Path, encoding: str = "utf-8-sig", delimiter: str = ",") -> None:
        self._path = path
        self._encoding = encoding
        self._delimiter = delimiter

    @property
    def path(self) -> Path:
        return self._path

    def read(self) -> list[Row]:
        if not self._path.exists():
            raise FileNotFoundError(f"source not found: {self._path}")
        with self._path.open(encoding=self._encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=self._delimiter)
            if reader.fieldnames is None:
                return []
            duplicates = [name for i, name in enumerate(reader.fieldnames) if name in reader.fieldnames[:i]]
            if duplicates:
                raise DuplicateHeaderError(duplicates)
            return [
                {k: (v if v is not None else "") for k, v in record.items()}
                for record in reader
            ]

    def read_stream(self, chunk_size: int = 1000):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        with self._path.open(encoding=self._encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=self._delimiter)
            chunk: list[Row] = []
            for record in reader:
                chunk.append({k: (v or "") for k, v in record.items()})
                if len(chunk) >= chunk_size:
                    yield chunk
                    chunk = []
            if chunk:
                yield chunk


class CsvSink:
    def __init__(self, path: Path, encoding: str = "utf-8", delimiter: str = ",") -> None:
        self._path = path
        self._encoding = encoding
        self._delimiter = delimiter

    def write(self, rows: list[Row], columns: list[str] | None = None) -> int:
        if not rows and columns is None:
            return 0
        fieldnames = columns or list(rows[0])
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding=self._encoding, newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=self._delimiter)
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)


class JsonlSink:
    def __init__(self, path: Path) -> None:
        import json

        self._json = json
        self._path = path

    def write(self, rows: list[Row]) -> int:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(self._json.dumps(row, ensure_ascii=False) + "\n")
        return len(rows)


def run_file(
    source_path: Path,
    sink_path: Path,
    steps_provider,
) -> tuple[int, int]:
    from .core import Transformer

    source = CsvSource(source_path)
    rows = source.read()
    transformer = Transformer()
    for step in steps_provider():
        transformer.add_step(step)
    result = transformer.run(rows)
    written = CsvSink(sink_path).write(result.rows)
    return written, result.dropped_count


__all__ = ["CsvSink", "CsvSource", "JsonlSink", "run_file", "TransformerError"]
