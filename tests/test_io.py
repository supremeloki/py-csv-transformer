import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from csv_transformer import CsvSink, CsvSource, DuplicateHeaderError, JsonlSink


def _write_csv(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_csv_source_reads_with_bom(tmp_path: Path):
    src = _write_csv(tmp_path / "in.csv", "name,qty\na,1\nb,2\n")
    rows = CsvSource(src).read()
    assert rows == [{"name": "a", "qty": "1"}, {"name": "b", "qty": "2"}]


def test_csv_source_empty_file_returns_empty(tmp_path: Path):
    src = _write_csv(tmp_path / "empty.csv", "")
    assert CsvSource(src).read() == []


def test_csv_source_duplicate_headers_raise(tmp_path: Path):
    src = _write_csv(tmp_path / "dup.csv", "name,name\na,b\n")
    with pytest.raises(DuplicateHeaderError):
        CsvSource(src).read()


def test_csv_source_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        CsvSource(tmp_path / "ghost.csv").read()


def test_stream_chunks(tmp_path: Path):
    lines = "n\n" + "".join(f"{i}\n" for i in range(7))
    src = _write_csv(tmp_path / "s.csv", lines)
    chunks = list(CsvSource(src).read_stream(chunk_size=3))
    assert [len(c) for c in chunks] == [3, 3, 1]


def test_sink_write_roundtrip(tmp_path: Path):
    out = tmp_path / "out.csv"
    written = CsvSink(out).write([{"x": "1"}])
    assert written == 1
    assert out.read_text(encoding="utf-8").splitlines()[0] == "x"


def test_jsonl_sink_writes_lines(tmp_path: Path):
    out = tmp_path / "out.jsonl"
    JsonlSink(out).write([{"a": "۱"}, {"a": "2"}])
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"a": "۱"}
